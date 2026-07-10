import threading
import time
import psutil
import subprocess
import re
from typing import Optional, Callable, Dict, List
from datetime import datetime
from collections import defaultdict, deque
import os
import sys

from utils import writable_path

# =========================
# 통합 로거 클래스
# =========================
class SecurityLogger:
    def __init__(self, page2_instance=None, page3_instance=None, log_file=None):
        self.page3_instance = page3_instance
        self.page2_instance = page2_instance
        self.log_file = log_file or writable_path("data/security.log")
        os.makedirs(os.path.dirname(self.log_file), exist_ok=True)

    def log(self, message: str, level: str = "INFO", page3_data: Optional[List[str]] = None):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        formatted = f"[{timestamp}] [{level}] {message}"

        # 콘솔 출력
        print(formatted)

        # 파일 로그
        try:
            with open(self.log_file, "a", encoding="utf-8") as f:
                f.write(formatted + "\n")
        except Exception:
            pass

        # # Page3 연동
        # if self.page3_instance and page3_data:
        #     try:
        #         self.page3_instance.add_log_entry(page3_data)
        #     except Exception:
        #         pass


# =========================
# 스레드 기반 데몬
# =========================
class ThreadDaemon:
    def __init__(self, interval: float = 1.0, task: Optional[Callable[[], None]] = None):
        self._interval = interval
        self._task = task
        self._stop_event = threading.Event()
        self._thread: Optional[threading.Thread] = None

    def set_task(self, task: Callable[[], None]):
        self._task = task

    def _run(self):
        while not self._stop_event.is_set():
            try:
                if self._task:
                    self._task()
            except Exception:
                pass
            finally:
                remaining = self._interval
                step = 0.05 if self._interval > 0.1 else self._interval
                while remaining > 0 and not self._stop_event.is_set():
                    time.sleep(min(step, remaining))
                    remaining -= step

    def start(self):
        if self._thread and self._thread.is_alive():
            return
        self._stop_event.clear()
        self._thread = threading.Thread(target=self._run, name="LavenderDaemon", daemon=True)
        self._thread.start()

    def stop(self, timeout: float = 2.0):
        if not self._thread:
            return
        self._stop_event.set()
        self._thread.join(timeout=timeout)
        self._thread = None


# =========================
# 네트워크 이상 감시기
# =========================
class NetworkAbuseWatcher:
    def __init__(self, logger: SecurityLogger, threshold_kb_per_sec: int = 400000, sustain_seconds: int = 5):
        self.logger = logger
        self.threshold_bytes_per_sec = threshold_kb_per_sec * 1024
        self.sustain_seconds = sustain_seconds
        self._prev_counters = None
        self._last_check_ts = None
        self._over_threshold_flags = deque(maxlen=sustain_seconds)
        self._cooldown_ips = {}
        self._cooldown_seconds = 300

    def _get_top_incoming_ip(self) -> Optional[str]:
        if sys.platform.startswith("win"):
            try:
                remote_counts = defaultdict(int)
                for connection in psutil.net_connections(kind="inet"):
                    if connection.status != psutil.CONN_ESTABLISHED or not connection.raddr:
                        continue
                    remote_ip = connection.raddr.ip
                    if remote_ip not in {"127.0.0.1", "::1"}:
                        remote_counts[remote_ip] += 1
                if not remote_counts:
                    return None
                return max(remote_counts.items(), key=lambda item: item[1])[0]
            except (OSError, psutil.Error):
                return None

        try:
            cmd = ["nettop", "-P", "-L", "1", "-x", "-J", "bytes_in,tcpsrc,udpsrc"]
            proc = subprocess.run(cmd, capture_output=True, text=True, check=False)
            if proc.returncode != 0:
                return None
            bytes_in_by_ip = defaultdict(int)
            for line in proc.stdout.splitlines():
                try:
                    pairs = dict(part.split("=", 1) for part in line.split() if "=" in part)
                    ip_port = pairs.get("tcpsrc") or pairs.get("udpsrc")
                    bytes_in_str = pairs.get("bytes_in")
                    if not ip_port or not bytes_in_str:
                        continue
                    ip = ip_port.split(":")[0]
                    bytes_in_by_ip[ip] += int(bytes_in_str)
                except Exception:
                    continue
            if not bytes_in_by_ip:
                return None
            return max(bytes_in_by_ip.items(), key=lambda kv: kv[1])[0]
        except Exception:
            return None

    def _append_blocked_if_needed(self, ip: str):
        self.logger.log(f"자동 차단 등록: {ip}", "WARN", [
            "대응", ip, "0", "0.0.0.0", "0", "네트워크 수신량 임계값 초과로 자동 차단"
        ])

        page2_instance.add_row(["ANY", "*", ip, "auto-blocked by daemon"], "blocked")
        page3_instance.add_log_entry(["대응", datetime.now().strftime("%Y-%m-%d %H:%M:%S"), ip, "*", "Localhost", "*", "네트워크 수신량 임계치 초과로 자동 차단" ])
        

    def tick(self):
        try:
            counters = psutil.net_io_counters()
            now = time.time()
            if self._prev_counters is None:
                self._prev_counters = counters
                self._last_check_ts = now
                return

            elapsed = max(1e-6, now - self._last_check_ts)
            rate_bps = (counters.bytes_recv - self._prev_counters.bytes_recv) / elapsed
            over = rate_bps >= self.threshold_bytes_per_sec
            self._over_threshold_flags.append(over)
            self._prev_counters, self._last_check_ts = counters, now

            if len(self._over_threshold_flags) == self.sustain_seconds and all(self._over_threshold_flags):
                ip = self._get_top_incoming_ip()
                if ip:
                    self._append_blocked_if_needed(ip)
        except Exception as e:
            self.logger.log(f"네트워크 감시 오류: {e}", "ERROR")


# =========================
# ARP 스푸핑 감시기
# =========================
arp_history = defaultdict(lambda: deque(maxlen=10))
suspicious_ips = set()
blocked_ips = set()

def get_arp_table() -> Dict[str, str]:
    try:
        kwargs = {"capture_output": True, "text": True, "errors": "replace"}
        if sys.platform.startswith("win"):
            kwargs["creationflags"] = getattr(subprocess, "CREATE_NO_WINDOW", 0)
        result = subprocess.run(["arp", "-a"], **kwargs)
        if result.returncode != 0:
            return {}
        arp_table = {}
        for line in result.stdout.strip().split("\n"):
            if sys.platform.startswith("win"):
                m = re.search(
                    r"^\s*(\d+\.\d+\.\d+\.\d+)\s+([a-fA-F0-9-]{17})\s+",
                    line,
                )
            else:
                m = re.search(r"\((\d+\.\d+\.\d+\.\d+)\)\s+at\s+([a-fA-F0-9:]{17})", line)
            if m:
                ip, mac = m.groups()
                arp_table[ip] = mac.replace("-", ":").upper()
        return arp_table
    except Exception:
        return {}


def analyze_arp_patterns(logger: SecurityLogger, table: Dict[str, str]) -> List[str]:
    detected = []
    for ip, mac in table.items():
        prev_macs = arp_history[ip]
        prev_mac = prev_macs[-1] if prev_macs else None
        arp_history[ip].append(mac)
        # (1) MAC 변경된 경우에만 경고
        if prev_mac and mac != prev_mac:
            if len(set(arp_history[ip])) > 1 and ip not in suspicious_ips:
                suspicious_ips.add(ip)
                detected.append(ip)
                logger.log(f"🚨 ARP Spoofing 탐지: {ip} → MAC 변경 ({prev_mac} → {mac})", "WARN")
        # (2) 게이트웨이 IP의 MAC 변경도 실제 변화일 때만
        if ip.endswith(".1") and prev_mac and mac != prev_mac:
            if ip not in suspicious_ips:
                suspicious_ips.add(ip)
                detected.append(ip)
                logger.log(f"🚨 Gateway Spoofing 탐지: 게이트웨이 {ip}의 MAC 변경 ({prev_mac} → {mac})", "WARN")
    return detected

def arp_spoofing_monitor(logger: SecurityLogger):
    arp_table = get_arp_table()
    if not arp_table:
        return

    # allowed_ips = set()
    # if page2_instance:
    #     model = page2_instance.model_allowed
    #     for row in range(model.rowCount()):
    #         ip_item = model.item(row, 3)  # IP 컬럼
    #         if ip_item:
    #             allowed_ips.add(ip_item.text())

    allowed_ips, blocked_ips = get_allowed_and_blocked_sets_from_page2()

    suspicious = analyze_arp_patterns(logger, arp_table)
    for ip in suspicious:
        if ip in allowed_ips:
            continue
        if ip not in blocked_ips:
            page2_instance.add_row(["ARP", "*", ip, "auto-blocked"], "blocked")
            page3_instance.add_log_entry(["대응", datetime.now().strftime("%Y-%m-%d %H:%M:%S"), ip, "*", "Localhost", "*", "Arp Spoofing 탐지 - 자동 차단"])
            blocked_ips.add(ip)

# =========================
# 통합 작업
# =========================
def combined_monitoring_task():
    arp_spoofing_monitor(logger)


# =========================
# 인스턴스 초기화
# =========================

page3_instance = None
page2_instance = None
logger = SecurityLogger(page2_instance, page3_instance)

_abuse_watcher = NetworkAbuseWatcher(logger, threshold_kb_per_sec=1, sustain_seconds=5)
daemon = ThreadDaemon(interval=5.0, task=combined_monitoring_task)
network_daemon = ThreadDaemon(interval=1.0, task=_abuse_watcher.tick)

def get_allowed_and_blocked_sets_from_page2():
    allowed = set()
    blocked = set()
    if page2_instance is None:
        return allowed, blocked

    try:
        # blocked 모델 읽기
        blocked_model = page2_instance.model_blocked
        for r in range(blocked_model.rowCount()):
            item = blocked_model.item(r, 3)  # IP 컬럼
            if item and item.text():
                blocked.add(item.text())

        # allowed 모델 읽기
        allowed_model = page2_instance.model_allowed
        for r in range(allowed_model.rowCount()):
            item = allowed_model.item(r, 3)
            if item and item.text():
                allowed.add(item.text())
    except Exception as e:
        logger.log(f"Page2 모델에서 정책 읽기 실패: {e}", "ERROR")

    return allowed, blocked
