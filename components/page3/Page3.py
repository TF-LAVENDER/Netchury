import csv
import os
from datetime import datetime
from PySide6.QtWidgets import QWidget, QTableView, QHeaderView
from PySide6.QtGui import QStandardItemModel, QStandardItem
from utils import IS_WINDOWS, load_ui_file, resource_path, writable_path

class Page3(QWidget):
    def __init__(self):
        super().__init__()
        self.ui = load_ui_file(resource_path("components/page3/page3.ui"))
        self.setLayout(self.ui.layout())
        self.row_height = 40

       # 테이블 초기화 시
        self.model_logs = QStandardItemModel(0, 7)
        self.model_logs.setHorizontalHeaderLabels([
            "유형", "시간", "송신 주소", "송신 포트", "수신 주소", "수신 포트", "비고"
        ])

        # 테이블 뷰 설정
        self.ui.logsTableView.setModel(self.model_logs)
        self.ui.logsTableView.horizontalHeader().setSectionResizeMode(QHeaderView.Fixed)
        header_height = 30
        if IS_WINDOWS:
            header_height = max(header_height, self.ui.logsTableView.fontMetrics().height() + 16)
            self.row_height = max(self.row_height, self.ui.logsTableView.fontMetrics().height() + 18)
        self.ui.logsTableView.horizontalHeader().setFixedHeight(header_height)
        self.ui.logsTableView.verticalHeader().hide()

        # 컬럼 너비 설정
        self.ui.logsTableView.setColumnWidth(0, 100)   # 유형
        self.ui.logsTableView.setColumnWidth(1, 90)  # 날짜
        self.ui.logsTableView.setColumnWidth(2, 140)  # 송신 주소
        self.ui.logsTableView.setColumnWidth(3, 84)   # 송신 포트
        self.ui.logsTableView.setColumnWidth(4, 140)  # 수신 주소
        self.ui.logsTableView.setColumnWidth(5, 84)   # 수신 포트
        self.ui.logsTableView.horizontalHeader().setStretchLastSection(True)  # 비고

        self.load_logs_from_csv()

    def add_log_entry(self, log_data):
        # current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # 데이터 준비: [유형, 날짜, 송신주소, 송신포트, 수신주소, 수신포트, 비고]
        # row_data = [log_data[0], current_time] + log_data[1:]
        # items = [QStandardItem(field) for field in row_data]
        items = [QStandardItem(field) for field in log_data]
        
        # 맨 위에 추가 (역순 표시)
        self.model_logs.insertRow(0, items)
        
        # 행 높이 설정
        self.ui.logsTableView.setRowHeight(0, self.row_height)
        
        # CSV 저장
        self.save_logs_to_csv(datetime.now().strftime("%Y-%m-%d"))
        # self.refresh_display()

    def load_logs_from_csv(self):
        """오늘 날짜의 로그 파일에서 로그 데이터 로드"""
        current_date = datetime.now().strftime("%Y-%m-%d")
        csv_path = writable_path(f"logs/{current_date}.csv")
        
        if os.path.exists(csv_path):
            with open(csv_path, mode="r", newline="", encoding="utf-8") as file:
                reader = csv.reader(file)
                for row in reader:
                    if len(row) >= 7:  # 8개 컬럼이 모두 있는지 확인
                        display_row = row.copy()

                        if len(display_row) >= 3:
                            display_row[1] = display_row[1].split(" ")[1] if " " in display_row[1] else display_row[1]
                        items = [QStandardItem(field) for field in display_row]
                        self.model_logs.appendRow(items)
                        # 행 높이 설정
                        self.ui.logsTableView.setRowHeight(self.model_logs.rowCount() - 1, self.row_height)
            self.ui.logsTableView.repaint()

    def save_logs_to_csv(self, date_str=None):
        """현재 로그 데이터를 날짜별 CSV 파일에 저장"""
        if date_str is None:
            date_str = datetime.now().strftime("%Y-%m-%d")
        
        # logs 디렉토리가 없으면 생성
        logs_dir = writable_path("logs")
        if not os.path.exists(logs_dir):
            os.makedirs(logs_dir)
        
        csv_path = writable_path(f"logs/{date_str}.csv")
        
        with open(csv_path, mode="w", newline="", encoding="utf-8") as file:
            writer = csv.writer(file)
            for row in range(self.model_logs.rowCount()):
                row_values = [
                    self.model_logs.item(row, col).text() if self.model_logs.item(row, col) else ""
                    for col in range(self.model_logs.columnCount())
                ]
                writer.writerow(row_values)

        

    def refresh_display(self):
        """테이블 새로고침"""
        self.ui.logsTableView.repaint()
