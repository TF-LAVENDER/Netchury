# Netchury Agents Guide

이 문서는 Codex 같은 코드 에이전트가 Netchury 프로젝트에서 작업할 때 따라야 할 프로젝트별 지침입니다.  
Netchury는 단순한 UI 앱처럼 보이지만, 일부 코드가 실제 macOS 네트워크/방화벽 상태에 접근하므로 실행과 테스트에 주의해야 합니다.

## 프로젝트 요약

Netchury는 Lavender 팀이 만든 개인 사용자용 네트워크 보안 관리 프로그램입니다.

- Python 기반 데스크톱 앱입니다.
- UI는 PySide6와 Qt Designer `.ui` 파일을 사용합니다.
- 네트워크 사용량을 실시간으로 표시합니다.
- IP 차단/허용 목록을 CSV로 관리합니다.
- 이상 징후와 사용자 활동을 날짜별 CSV 로그로 저장합니다.
- macOS와 Windows를 지원하며, OS별 방화벽 및 네트워크 명령은 조건부 분기로 분리되어 있습니다.

## 주요 기술 스택

- Runtime: Python
- UI: PySide6, PySide6.QtCharts, Qt Designer `.ui`
- Network metrics: `psutil`
- Data storage: CSV files
- Packaging: PyInstaller
- Target OS behavior: macOS 동작을 기준으로 유지하면서 Windows 호환 계층을 적용

`requirements.txt`의 핵심 의존성:

- `psutil==7.1.0`
- `PySide6==6.9.2`
- `PySide6_Addons==6.9.2`
- `PySide6_Essentials==6.9.2`
- `shiboken6==6.9.2`

## 실행 구조

### 진입점

- `LavenderMain.py`
  - `QApplication`과 `MainWindow`를 생성합니다.
  - `MainWindow.ui`를 동적으로 로드합니다.
  - `Page1`, `Page2`, `Page3` 인스턴스를 생성합니다.
  - `util.daemon.daemon` 모듈의 전역 `page2_instance`, `page3_instance`에 페이지 인스턴스를 연결합니다.
  - 앱 실행 시 `daemon.start()`와 `network_daemon.start()`를 호출합니다.
  - 앱 종료 후 데몬을 정지합니다.

### 공통 유틸

- `utils.py`
  - `resource_path(relative_path)`: PyInstaller `_MEIPASS` 환경과 일반 실행 환경 모두에서 리소스 경로를 계산합니다.
  - `writable_path(relative_path)`: Windows에서는 `%LOCALAPPDATA%/Netchury`, macOS에서는 기존 프로젝트 경로를 사용합니다.
  - `configure_application(app)`: Windows에서만 폰트 크기와 기본 한글 폰트를 보정합니다.
  - `load_ui_file(path)`: `QUiLoader`로 `.ui` 파일을 동적으로 로드합니다.

리소스 경로를 직접 하드코딩하지 말고 가능하면 `resource_path()`를 사용하세요.

## 주요 화면과 책임

### Page1: 네트워크 사용량 시각화

경로:

- `components/page1/Page1.py`
- `components/page1/page1.ui`
- `components/page1/images/`

역할:

- `psutil.net_io_counters()`로 전체 송수신량을 측정합니다.
- `QSplineSeries`, `QChart`, `QChartView`로 최근 60초 그래프를 표시합니다.
- macOS에서는 `WAN_IFACE = "en0"`, `LAN_IFACE = "en1"` 기준으로 인터페이스별 사용량을 계산합니다.
- Windows에서는 활성 네트워크 어댑터를 트래픽 순으로 자동 선택합니다.
- 1초마다 `QTimer`로 `update_chart()`를 호출합니다.

주의:

- `en0`, `en1`은 macOS 기준 이름입니다. 다른 OS나 장비에서는 없을 수 있습니다.
- 네트워크 카운터는 누적값 기반이므로 이전 값 갱신 순서를 조심하세요.
- UI 요소 이름은 `.ui` 파일과 강하게 연결되어 있습니다. 위젯 objectName 변경 시 Python 코드도 같이 확인해야 합니다.
- 굵은 `recv_send_ratio`는 macOS에서 좌우 PNG 마스크를 사용하고, Windows에서는 추가로 둥근 `QRegion` 클리핑을 적용합니다. macOS 마스크 배치와 Windows 조건 분기를 함께 유지하세요.

### Page2: IP 차단/허용 목록 관리

경로:

- `components/page2/Page2.py`
- `components/page2/page2.ui`
- `components/page2/sub/NetworkPopup.py`
- `components/page2/sub/NetworkPopup.ui`
- `components/page2/images/`

역할:

- 차단 목록과 허용 목록을 각각 `QStandardItemModel`로 관리합니다.
- CSV 파일에서 초기 목록을 읽고 저장합니다.
- 규칙 추가/삭제 시 Page3 로그를 추가합니다.
- 차단 규칙 추가/삭제 시 macOS는 `pfctl`, Windows는 `netsh advfirewall`을 사용합니다.

데이터 파일:

- `data/blocked.csv`
- `data/allowed.csv`

CSV 컬럼 구조:

1. 인덱스
2. 프로토콜
3. 포트
4. IP
5. 비고

주의:

- `add_firewall_rule()`과 `delete_firewall_rule()`은 `sudo pfctl`을 호출할 수 있습니다.
- Windows 빌드는 방화벽 변경을 위해 UAC 관리자 권한을 요청합니다.
- 에이전트는 사용자 승인 없이 실제 방화벽 명령을 실행하면 안 됩니다.
- `get_pfctl_rules_file()`은 `/tmp/netchury_rules.pf`를 사용합니다.
- 코드상 차단 규칙 문자열이 `pass in ...` 형태로 생성됩니다. 방화벽 정책을 수정할 때는 의도와 실제 효과를 반드시 확인하세요.
- `Page2.page3_instance`가 설정되지 않은 상태에서 `add_row()`가 호출되면 로그 추가 시 예외가 날 수 있습니다. `LavenderMain.py`의 인스턴스 연결 흐름을 유지하세요.
- `data/`는 `.gitignore`에 포함되어 있으므로 로컬 사용자 데이터로 취급하세요. 테스트로 내용을 덮어쓰거나 삭제하지 마세요.

### NetworkPopup: 규칙 입력 팝업

경로:

- `components/page2/sub/NetworkPopup.py`

역할:

- 프로토콜 선택을 `QComboBox`로 제공합니다.
- 포트는 단일 포트, 범위, `*`를 허용합니다.
- IP는 IPv4 또는 CIDR 표기법을 허용합니다.

주의:

- `keyPressEvent()`가 Enter 입력 시 곧바로 `accept()`를 호출합니다. 검증을 우회할 수 있으므로 수정 시 `on_confirm()`과의 일관성을 확인하세요.
- IP 검증은 `ipaddress.ip_network(..., strict=False)`를 사용합니다.

### Page3: 로그 표시

경로:

- `components/page3/Page3.py`
- `components/page3/page3.ui`

역할:

- 날짜별 CSV 로그를 읽어 테이블에 표시합니다.
- 새 로그는 `add_log_entry()`로 맨 위에 추가됩니다.
- 저장 경로는 `logs/YYYY-MM-DD.csv`입니다.

로그 컬럼 구조:

1. 유형
2. 시간
3. 송신 주소
4. 송신 포트
5. 수신 주소
6. 수신 포트
7. 비고

주의:

- `logs/`는 현재 저장소에 포함된 샘플/기존 로그가 있습니다. 임의 삭제하지 마세요.
- `save_logs_to_csv()`는 현재 테이블 전체를 날짜 파일에 다시 씁니다. 테스트 시 실제 로그 파일이 바뀔 수 있습니다.

## 백그라운드 감시 로직

경로:

- `util/daemon/daemon.py`

구성:

- `ThreadDaemon`
  - 지정된 interval마다 task를 반복 실행하는 데몬 스레드 래퍼입니다.
- `SecurityLogger`
  - 콘솔과 `data/security.log`에 로그를 남깁니다.
- `NetworkAbuseWatcher`
  - `psutil.net_io_counters()`로 수신량 임계치 초과를 감시합니다.
  - macOS에서는 `nettop`, Windows에서는 `psutil.net_connections()`로 원격 IP를 찾으려 시도합니다.
  - 조건 충족 시 Page2에 자동 차단 규칙을 추가하고 Page3에 로그를 남깁니다.
- ARP 감시 함수들
  - OS별 `arp -a` 출력 형식을 분석해 IP별 MAC 변경을 감지합니다.
  - 의심 IP가 허용 목록에 없고 차단 목록에도 없으면 자동 차단합니다.

주의:

- 데몬은 실제 시스템 명령(`arp`, macOS의 `nettop`)과 네트워크 상태에 의존합니다.
- `_abuse_watcher = NetworkAbuseWatcher(logger, threshold_kb_per_sec=1, sustain_seconds=5)`로 설정되어 있어 임계치가 매우 낮습니다. 앱 실행만으로 자동 차단 로직이 쉽게 작동할 수 있습니다.
- `page2_instance`, `page3_instance`는 모듈 전역 변수입니다. 이 구조를 바꿀 때는 `LavenderMain.py`, `Page2.py`, `daemon.py`의 순환 참조와 초기화 순서를 같이 점검하세요.
- 데몬의 예외 처리 중 일부는 조용히 무시됩니다. 디버깅 시 필요한 최소 범위에서 로그를 보강하세요.

## 빌드

경로:

- `build.py`

역할:

- PyInstaller로 `LavenderMain.py`를 `Netchury` 앱으로 패키징합니다.
- `MainWindow.ui`, `images`, `components`, `icon.icns`를 포함합니다.

주의:

- macOS 빌드는 기존 `icon.icns`를 사용하고, Windows 빌드는 `--uac-admin` 매니페스트를 사용합니다.
- 플랫폼 분기를 수정할 때 macOS의 기존 동작 경로가 바뀌지 않는지 확인하세요.
- 빌드 산출물(`build/`, `dist/`, `*.spec`)은 `.gitignore` 대상입니다.

## UI 파일과 생성 파일 정책

이 저장소에는 `.ui` 원본 파일과 `*_ui.py` 파일이 함께 있습니다.

- `.ui` 파일: Qt Designer 원본입니다.
- `*_ui.py` 파일: `.ui`에서 생성된 코드일 가능성이 큽니다.
- 현재 런타임은 주로 `load_ui_file()`로 `.ui`를 직접 로드합니다.

작업 원칙:

- UI 레이아웃 변경은 가능하면 `.ui` 파일을 기준으로 하세요.
- `*_ui.py`를 직접 고칠 때는 실제로 import/사용되는지 먼저 확인하세요.
- objectName을 바꾸면 Python 코드의 `self.ui.<name>` 접근도 같이 수정해야 합니다.
- 이미지 리소스 경로와 폴더 구조를 유지하세요.

## 데이터와 로그 취급

다음은 사용자/실행 데이터로 취급합니다.

- `data/blocked.csv`
- `data/allowed.csv`
- `data/security.log`
- `logs/*.csv`
- `/tmp/netchury_rules.pf`

주의:

- 테스트를 위해 실제 사용자 데이터를 지우거나 덮어쓰지 마세요.
- 필요하면 임시 파일이나 백업 복사본을 사용하세요.
- `data/`는 `.gitignore`에 포함되어 있으므로 새 파일이 Git에 안 보일 수 있습니다.
- 로그 파일 변경이 작업 목적과 무관하면 커밋 대상에 포함하지 마세요.

## 안전 규칙

에이전트는 다음 작업을 사용자 승인 없이 수행하지 마세요.

- `sudo pfctl` 실행
- `netsh advfirewall` 실행
- 방화벽 규칙 추가/삭제
- `/tmp/netchury_rules.pf` 삭제 또는 덮어쓰기
- 실제 네트워크 차단 테스트
- 관리자 권한이 필요한 명령 실행
- `logs/` 또는 `data/`의 실제 사용 데이터 삭제
- 빌드 산출물 대량 삭제

네트워크/보안 기능을 수정할 때는 다음을 우선 확인하세요.

- 차단과 허용의 의미가 UI 문구와 실제 동작에서 일치하는지
- 자동 차단이 허용 목록을 제대로 존중하는지
- 오탐 시 사용자가 복구할 수 있는지
- 로그에 충분한 근거가 남는지

## 개발/검증 명령

의존성 설치:

```bash
python -m pip install -r requirements.txt
```

문법 검사:

```bash
python -m py_compile LavenderMain.py utils.py build.py components/page1/Page1.py components/page2/Page2.py components/page2/sub/NetworkPopup.py components/page3/Page3.py util/daemon/daemon.py
```

앱 실행:

```bash
python LavenderMain.py
```

빌드:

```bash
python build.py
```

주의:

- 앱 실행은 데몬을 시작하므로 실제 네트워크 감시와 자동 차단 흐름이 작동할 수 있습니다.
- GUI 실행, 방화벽 명령, 빌드는 환경에 영향을 줄 수 있으므로 필요할 때만 수행하세요.

## 코딩 스타일

- 기존 코드 스타일과 한국어 주석/문구 톤을 유지하세요.
- 큰 리팩터링보다 요청 범위에 맞는 작은 변경을 선호하세요.
- UI 이벤트 핸들러, 데이터 저장, 시스템 명령 실행 로직을 가능한 한 분리하세요.
- 예외를 무조건 삼키기보다 사용자가 이해할 수 있는 로그 또는 메시지를 남기세요.
- 크로스 플랫폼 개선을 할 때는 macOS 전용 명령과 일반 Python 로직을 분리하세요.

## 변경 전 체크리스트

- 이 변경이 UI 원본 `.ui`와 Python 코드 중 어디에 필요한가?
- 이 변경이 실제 방화벽/네트워크 상태를 바꾸는가?
- 이 변경이 `data/` 또는 `logs/` 파일을 덮어쓰는가?
- `Page2`와 `Page3` 인스턴스 연결을 깨뜨리지 않는가?
- PyInstaller 리소스 경로에서도 동작하는가?

## 변경 후 체크리스트

- 수정한 Python 파일에 문법 오류가 없는가?
- 관련 `.ui` objectName과 Python 접근 코드가 일치하는가?
- CSV 컬럼 순서가 유지되는가?
- 로그가 7개 컬럼 구조를 유지하는가?
- 방화벽/자동 차단 로직 변경 시 사용자 승인 없는 실제 시스템 명령 실행이 없었는가?
- 작업과 무관한 `.DS_Store`, 로그, 데이터 파일 변경이 섞이지 않았는가?

## Git 주의사항

- `.DS_Store`는 `.gitignore` 대상이며 작업과 무관하면 건드리지 마세요.
- 현재 프로젝트는 `.github/workflows/notify.yml`에서 main 브랜치 push 시 Discord 알림을 보냅니다.
- `data/`는 `.gitignore`에 포함되어 있습니다.
- 빌드 산출물과 캐시 파일은 커밋하지 마세요.
