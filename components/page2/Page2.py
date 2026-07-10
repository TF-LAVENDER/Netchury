import csv
from datetime import datetime
import os
from PySide6.QtWidgets import QWidget, QTableView, QHeaderView
from PySide6.QtGui import QStandardItemModel, QStandardItem
from components.page2.sub.NetworkPopup import NetworkPopup
from util.daemon.daemon import page3_instance
from utils import IS_WINDOWS, load_ui_file, resource_path
import subprocess
import ipaddress

class Page2(QWidget):
    def __init__(self):
        super().__init__()
        self.ui = load_ui_file(resource_path("components/page2/page2.ui"))
        self.setLayout(self.ui.layout())

        self.ui.blockedButton.clicked.connect(self.blocked_clicked)
        self.ui.allowedButton.clicked.connect(self.allowed_clicked)
        self.ui.addButton.clicked.connect(self.show_network_popup)
        self.ui.delButton.clicked.connect(self.delete_selected_row)

        self.ui.blockedButton.setFlat(True)
        self.ui.allowedButton.setFlat(True)

        if IS_WINDOWS:
            self.ui.blockedButton.setStyleSheet(
                f"border-image: url('{resource_path('components/page2/images/blocked_on.png')}'); margin: 0;"
            )
            self.ui.allowedButton.setStyleSheet(
                f"border-image: url('{resource_path('components/page2/images/allowed_off.png')}'); margin: 0;"
            )
            self.ui.addButton.setStyleSheet(
                f"border-image: url('{resource_path('components/page2/images/add_rule.png')}'); margin: 0;"
            )
            self.ui.delButton.setStyleSheet(
                f"border-image: url('{resource_path('components/page2/images/delete_rule.png')}'); margin: 0;"
            )

        self.model_blocked = QStandardItemModel(0, 5)
        self.model_blocked.setHorizontalHeaderLabels(["", "프로토콜", "포트", "IP", "비고"])
        self.model_allowed = QStandardItemModel(0, 5)
        self.model_allowed.setHorizontalHeaderLabels(["", "프로토콜", "포트", "IP", "비고"])

        self.current_mode = "blocked"  # blocked or allowed
        self.ui.blockedTableView.setModel(self.model_blocked)
        self.ui.blockedTableView.horizontalHeader().setStretchLastSection(True)
        self.ui.blockedTableView.verticalHeader().hide()
        self.ui.blockedTableView.setSelectionBehavior(QTableView.SelectRows)
        self.ui.blockedTableView.setSelectionMode(QTableView.SingleSelection)
        self.ui.blockedTableView.setEditTriggers(QTableView.NoEditTriggers)

        self.ui.blockedTableView.horizontalHeader().setSectionResizeMode(QHeaderView.Fixed)
        header_height = 30
        if IS_WINDOWS:
            header_height = max(header_height, self.ui.blockedTableView.fontMetrics().height() + 10)
        self.ui.blockedTableView.horizontalHeader().setFixedHeight(header_height)
        self.ui.blockedTableView.setColumnWidth(0, 45)
        self.ui.blockedTableView.setColumnWidth(1, 75)
        self.ui.blockedTableView.setColumnWidth(2, 75)
        self.ui.blockedTableView.setColumnWidth(3, 200)

        for row in range(self.model_blocked.rowCount()):
            self.ui.blockedTableView.setRowHeight(row, 40)
        for row in range(self.model_allowed.rowCount()):
            self.ui.blockedTableView.setRowHeight(row, 40)

        self.page3_instance = None

        self.load_from_csvs()

    def menuChange(self, menuNum):
        self.ui.blockedButton.setStyleSheet(f"border-image: url('{resource_path('components/page2/images/blocked_off.png')}');")
        self.ui.allowedButton.setStyleSheet(f"border-image: url('{resource_path('components/page2/images/allowed_off.png')}');")
        if menuNum == 1:
            self.ui.blockedButton.setStyleSheet(f"border-image: url('{resource_path('components/page2/images/blocked_on.png')}');")
            self.ui.blockedTableView.setModel(self.model_blocked)
            self.current_mode = "blocked"
        elif menuNum == 2:
            self.ui.allowedButton.setStyleSheet(f"border-image: url('{resource_path('components/page2/images/allowed_on.png')}');")
            self.ui.blockedTableView.setModel(self.model_allowed)
            self.current_mode = "allowed"

    def blocked_clicked(self):
        self.menuChange(1)

    def allowed_clicked(self):
        self.menuChange(2)

    def show_network_popup(self):
        dialog = NetworkPopup(self)
        if dialog.exec():
            row_data = dialog.get_data()
            self.add_row(row_data)
            self.save_to_csvs()  # 저장

    def add_row(self, row_data, mode = None):
        if mode == None :
            mode = self.current_mode
        # 인덱스는 현재 행 개수 + 1
        if mode == "blocked":
            idx = self.model_blocked.rowCount() + 1
            items = [QStandardItem(str(idx))] + [QStandardItem(field) for field in row_data]
            self.model_blocked.appendRow(items)
            self.ui.blockedTableView.setRowHeight(self.model_blocked.rowCount() - 1, 40)
            
            # 방화벽 규칙 추가 (CIDR 지원)
            if len(row_data) >= 4:
                protocol = row_data[0]  # 프로토콜
                port = row_data[1]      # 포트
                ip = row_data[2]        # IP (CIDR 지원)
                add_firewall_rule(port, ip, protocol)
            
            self.page3_instance.add_log_entry(["사용자 활동", datetime.now().strftime("%H:%M:%S"), ip, port, "", "", f"사용자 차단 규칙 추가 - {ip}:{port}({protocol})"])
        else:
            idx = self.model_allowed.rowCount() + 1
            items = [QStandardItem(str(idx))] + [QStandardItem(field) for field in row_data]
            self.model_allowed.appendRow(items)
            self.ui.blockedTableView.setRowHeight(self.model_allowed.rowCount() - 1, 40)
            self.page3_instance.add_log_entry(["사용자 활동", datetime.now().strftime("%H:%M:%S"), row_data[2], row_data[1], "", "", f"사용자 허용 규칙 추가 - {row_data[2]}:{row_data[1]}({row_data[0]})"])

    def save_to_csvs(self):
        with open(resource_path("data/blocked.csv"), mode="w", newline="", encoding="utf-8") as file:
            writer = csv.writer(file)
            for row in range(self.model_blocked.rowCount()):
                row_values = [
                    self.model_blocked.item(row, col).text() if self.model_blocked.item(row, col) else ""
                    for col in range(self.model_blocked.columnCount())
                ]
                writer.writerow(row_values)
        with open(resource_path("data/allowed.csv"), mode="w", newline="", encoding="utf-8") as file:
            writer = csv.writer(file)
            for row in range(self.model_allowed.rowCount()):
                row_values = [
                    self.model_allowed.item(row, col).text() if self.model_allowed.item(row, col) else ""
                    for col in range(self.model_allowed.columnCount())
                ]
                writer.writerow(row_values)

    def load_from_csvs(self):
        # blocked
        if os.path.exists(resource_path("data/blocked.csv")):
            with open(resource_path("data/blocked.csv"), mode="r", newline="", encoding="utf-8") as file:
                reader = csv.reader(file)
                idx = 1
                for row in reader:
                    # 기존 csv에 인덱스 컬럼이 없으면 자동 부여
                    if len(row) == 4:
                        items = [QStandardItem(str(idx))] + [QStandardItem(field) for field in row]
                    else:
                        items = [QStandardItem(field) for field in row]
                    self.model_blocked.appendRow(items)
                    self.ui.blockedTableView.setRowHeight(self.model_blocked.rowCount() - 1, 40)
                    idx += 1
        # allowed
        if os.path.exists(resource_path("data/allowed.csv")):
            with open(resource_path("data/allowed.csv"), mode="r", newline="", encoding="utf-8") as file:
                reader = csv.reader(file)
                idx = 1
                for row in reader:
                    if len(row) == 4:
                        items = [QStandardItem(str(idx))] + [QStandardItem(field) for field in row]
                    else:
                        items = [QStandardItem(field) for field in row]
                    self.model_allowed.appendRow(items)
                    self.ui.blockedTableView.setRowHeight(self.model_allowed.rowCount() - 1, 40)
                    idx += 1

    def delete_selected_row(self):
        selection_model = self.ui.blockedTableView.selectionModel()
        indexes = selection_model.selectedRows()

        if not indexes:
            return

        model = self.model_blocked if self.current_mode == "blocked" else self.model_allowed
        for index in sorted(indexes, key=lambda x: x.row(), reverse=True):
            if self.current_mode == "blocked":
                # 프로토콜, 포트, IP 정보를 가져와서 방화벽 규칙 삭제
                protocol_item = model.item(index.row(), 1)  # 프로토콜
                port_item = model.item(index.row(), 2)      # 포트
                ip_item = model.item(index.row(), 3)        # IP
                
                if protocol_item and port_item and ip_item:
                    protocol = protocol_item.text()
                    port = port_item.text()
                    ip = ip_item.text()
                    delete_firewall_rule(port, ip, protocol)
            else:
                protocol = model.item(index.row(), 1).text()
                port = model.item(index.row(), 2).text()
                ip = model.item(index.row(), 3).text()
            model.removeRow(index.row())
        # 삭제 후 인덱스 재정렬
        for row in range(model.rowCount()):
            model.setItem(row, 0, QStandardItem(str(row + 1)))
        self.save_to_csvs()
        self.page3_instance.add_log_entry(["사용자 활동", datetime.now().strftime("%H:%M:%S"), ip, port, "", "", f"사용자 {'차단' if self.current_mode == 'blocked' else '허용'} 규칙 삭제 - {ip}:{port}({protocol})"])

    def edit_selected_row(self, index):
        if not index.isValid():
            return

        model = self.model_blocked if self.current_mode == "blocked" else self.model_allowed
        row = index.row()
        current_data = [
            model.item(row, 1).text(),  # 프로토콜
            model.item(row, 2).text(),  # 포트
            model.item(row, 3).text(),  # IP
            model.item(row, 4).text() if model.columnCount() > 4 else ""  # 비고
        ]

        # 팝업 열고 기존 데이터 설정
        dialog = NetworkPopup(self)
        dialog.protocol_combo.setCurrentText(current_data[0])
        dialog.ui.portRangeLane.setText(current_data[1])
        dialog.ui.ipLane.setText(current_data[2])
        dialog.ui.descriptionLane.setText(current_data[3])

        if dialog.exec():
            new_data = dialog.get_data()
            # 인덱스는 그대로 두고 나머지 값만 수정
            for col, value in enumerate(new_data):
                model.setItem(row, col + 1, QStandardItem(value))
            self.save_to_csvs()
            self.page3_instance.add_log_entry(["사용자 활동", datetime.now().strftime("%H:%M:%S"), model.item(row, 3).text(), model.item(row, 2).text(), "", "", f"사용자 {'차단' if self.current_mode == 'blocked' else '허용'} 규칙 수정 - {model.item(row, 3).text()}:{model.item(row, 2).text()}({model.item(row, 1).text()})"])


def get_pfctl_rules_file():
    """macOS 방화벽 규칙 파일 경로 반환"""
    return "/tmp/netchury_rules.pf"
def add_firewall_rule(port, ip_address=None, protocol="TCP"):
    """
    macOS 방화벽 규칙 추가 (CIDR 지원)
    """
    import ipaddress
    import os
    
    # 프로토콜 변환 (TCP -> tcp, UDP -> udp)
    proto = protocol.lower()
    port_clause = "" if not port or port == "*" else f" port {port}"
    # pfctl 규칙 생성
    if ip_address:
        try:
            # CIDR 표기법인지 확인
            if "/" in ip_address:
                # CIDR 표기법인 경우
                network = ipaddress.ip_network(ip_address, strict=False)
                rule = f"pass in proto {proto} from {str(network)} to any{port_clause}"
            else:
                # 단일 IP인 경우
                rule = f"pass in proto {proto} from {ip_address} to any{port_clause}"
        except ValueError:
            # IP 주소가 잘못된 경우 단일 IP로 처리
            rule = f"pass in proto {proto} from {ip_address} to any{port_clause}"
    else:
        # 모든 IP에서 허용
        rule = f"pass in proto {proto} to any{port_clause}"
    
    # 기존 규칙 파일 읽기
    rules_file = get_pfctl_rules_file()
    existing_rules = []
    
    if os.path.exists(rules_file):
        with open(rules_file, 'r') as f:
            existing_rules = f.readlines()
    
    # 새 규칙 추가 (중복 확인)
    rule_line = f"{rule}\n"
    if rule_line not in existing_rules:
        existing_rules.append(rule_line)
        
        # 규칙 파일에 저장
        with open(rules_file, 'w') as f:
            f.write("# Netchury firewall rules\n")
            f.writelines(existing_rules)
        
        try:
            # 올바른 pfctl 명령어 구조
            subprocess.run([
                "sudo", "pfctl", "-a", "netchury_rules", 
                "-f", rules_file
            ], check=True)
            print(f"방화벽 규칙 추가: {rule.strip()}")
        except subprocess.CalledProcessError as e:
            print(f"방화벽 규칙 추가 실패: {e}")
    else:
        print(f"방화벽 규칙이 이미 존재합니다: {rule.strip()}")

def delete_firewall_rule(port, ip_address=None, protocol="TCP"):
    """
    macOS 방화벽 규칙 삭제 (CIDR 지원)
    """
    # 프로토콜 변환 (TCP -> tcp, UDP -> udp)
    proto = protocol.lower()
    port_clause = "" if not port or port == "*" else f" port {port}"
    # 삭제할 규칙 생성
    if ip_address:
        try:
            # CIDR 표기법인지 확인
            if "/" in ip_address:
                # CIDR 표기법인 경우
                network = ipaddress.ip_network(ip_address, strict=False)
                rule = f"pass in proto {proto} from {str(network)} to any{port_clause}"
            else:
                # 단일 IP인 경우
                rule = f"pass in proto {proto} from {ip_address} to any{port_clause}"
        except ValueError:
            # IP 주소가 잘못된 경우 단일 IP로 처리
            rule = f"pass in proto {proto} from {ip_address} to any{port_clause}"
    else:
        # 모든 IP에서 허용
        rule = f"pass in proto {proto} to any{port_clause}"
    
    # 기존 규칙 파일 읽기
    rules_file = get_pfctl_rules_file()
    
    if os.path.exists(rules_file):
        with open(rules_file, 'r') as f:
            existing_rules = f.readlines()
        
        # 삭제할 규칙 제거
        rule_line = f"{rule}\n"
        if rule_line in existing_rules:
            existing_rules.remove(rule_line)
            
            # 남은 규칙이 있으면 파일에 저장하고 로드
            if len(existing_rules) > 1:  # 헤더 주석 제외
                with open(rules_file, 'w') as f:
                    f.writelines(existing_rules)
                
                try:
                    # pfctl로 업데이트된 규칙 로드
                    subprocess.run([
                        "sudo", "pfctl", "-f", rules_file,
                        "-a", "netchury_rules"
                    ], check=True)
                    print(f"방화벽 규칙 삭제: {rule.strip()}")
                except subprocess.CalledProcessError as e:
                    print(f"방화벽 규칙 삭제 실패: {e}")
            else:
                # 규칙이 없으면 파일 삭제하고 pfctl 비활성화
                os.remove(rules_file)
                try:
                    subprocess.run([
                        "sudo", "pfctl", "-a", "netchury_rules",
                        "-d"
                    ], check=True)
                    print(f"방화벽 규칙 삭제: {rule.strip()}")
                except subprocess.CalledProcessError as e:
                    print(f"방화벽 규칙 삭제 실패: {e}")
        else:
            print(f"삭제할 방화벽 규칙을 찾을 수 없습니다: {rule.strip()}")
    else:
        print("방화벽 규칙 파일이 존재하지 않습니다.")

