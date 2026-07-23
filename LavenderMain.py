# LavenderMain.py

import sys
import os
from PySide6.QtWidgets import QApplication, QWidget, QMainWindow, QHBoxLayout
from PySide6.QtGui import QIcon, QPainter, QPainterPath, QColor, QRegion
from PySide6.QtCore import QSize, Qt
from components.page1.Page1 import Page1
from components.page2.Page2 import Page2
from components.page3.Page3 import Page3
from utils import IS_WINDOWS, configure_application, load_ui_file, resource_path
from util.daemon.daemon import daemon, network_daemon, page3_instance
import util.daemon.daemon as daemon_module

_ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
_UTILS_DIR = os.path.join(_ROOT_DIR, "utils")
if _UTILS_DIR not in sys.path:
    sys.path.insert(0, _UTILS_DIR)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.selectedMenu = 0
        self.old_pos = None  # 드래그용 위치 저장
        self.setWindowFlag(Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)

        self.ui = load_ui_file(resource_path("MainWindow.ui"))
        self.setCentralWidget(self.ui)
        self.ui.setAttribute(Qt.WA_TranslucentBackground, True)
        self.ui.setAutoFillBackground(False)
        self.ui.setStyleSheet("background: transparent;")

        self.setFixedSize(960, 545)
        self.configure_window_controls()

        self.show()

        self.content_widget = self.ui.findChild(QWidget, "horizontalLayoutWidget")
        if self.content_widget is None:
            raise RuntimeError("horizontalLayoutWidget 위젯을 찾을 수 없습니다. .ui 파일 확인 필요.")
        self.content_container = self.content_widget.layout()
        self.update_content_mask()
        print(self.content_container)

        self.page1 = Page1()
        
        self.page3 = Page3()
        daemon_module.page3_instance = self.page3
        self.page2 = Page2()
        daemon_module.page2_instance = self.page2
        self.page2.page3_instance = self.page3
        print(f"Page2 인스턴스가 daemon에 등록 : {daemon_module.page2_instance is not None}")
        print(f"Page3 인스턴스가 daemon에 등록 : {daemon_module.page3_instance is not None}")

        

        self.ui.menuButton1.clicked.connect(self.menu1_clicked)
        self.ui.menuButton2.clicked.connect(self.menu2_clicked)
        self.ui.menuButton3.clicked.connect(self.menu3_clicked)

        self.ui.exitButton.clicked.connect(self.close)
        self.ui.minimizeButton.clicked.connect(self.showMinimized)

        self.menu1_clicked()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing, True)

        r = self.rect().adjusted(0, 0, -1, -1)

        path = QPainterPath()
        path.addRoundedRect(r, 10, 10)

        painter.fillPath(path, QColor(34, 34, 34))

    def configure_window_controls(self):
        """Use Windows title-bar controls without changing the macOS layout."""
        if not IS_WINDOWS:
            return

        button_width = 40
        button_height = 45
        right_margin = 20
        maximize_slot_width = button_width
        minimize_icon = resource_path("images/windows_minimize.svg")
        close_icon = resource_path("images/windows_close.svg")

        self.ui.minimizeButton.setGeometry(
            self.width() - right_margin - button_width * 2 - maximize_slot_width,
            0,
            button_width,
            button_height,
        )
        self.ui.exitButton.setGeometry(
            self.width() - right_margin - button_width,
            0,
            button_width,
            button_height,
        )
        self.ui.dummyButton.hide()

        self.ui.minimizeButton.setIcon(QIcon(minimize_icon))
        self.ui.minimizeButton.setIconSize(QSize(15, 15))
        self.ui.exitButton.setIcon(QIcon(close_icon))
        self.ui.exitButton.setIconSize(QSize(12, 13))

        self.ui.minimizeButton.setCursor(Qt.ArrowCursor)
        self.ui.exitButton.setCursor(Qt.ArrowCursor)
        self.ui.minimizeButton.setToolTip("최소화")
        self.ui.exitButton.setToolTip("닫기")
        self.ui.minimizeButton.setAccessibleName("최소화")
        self.ui.exitButton.setAccessibleName("닫기")

        self.ui.minimizeButton.setStyleSheet(f"""
            QPushButton {{
                background: transparent;
                border: none;
            }}
            QPushButton:hover {{ background-color: #3a3a3a; }}
            QPushButton:pressed {{ background-color: #4a4a4a; }}
        """)
        self.ui.exitButton.setStyleSheet(f"""
            QPushButton {{
                background: transparent;
                border: none;
                border-top-right-radius: 10px;
            }}
            QPushButton:hover {{ background-color: #c42b1c; }}
            QPushButton:pressed {{ background-color: #8f1d13; }}
        """)
        self.ui.minimizeButton.raise_()
        self.ui.exitButton.raise_()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if hasattr(self, "content_widget"):
            self.update_content_mask()

    def update_content_mask(self):
        """Keep table rows inside the window's rounded bottom corners."""
        rect = self.content_widget.rect()
        radius = 10

        path = QPainterPath()
        path.moveTo(rect.left(), rect.top())
        path.lineTo(rect.right(), rect.top())
        path.lineTo(rect.right(), rect.bottom() - radius)
        path.quadTo(rect.right(), rect.bottom(), rect.right() - radius, rect.bottom())
        path.lineTo(rect.left() + radius, rect.bottom())
        path.quadTo(rect.left(), rect.bottom(), rect.left(), rect.bottom() - radius)
        path.closeSubpath()

        self.content_widget.setMask(QRegion(path.toFillPolygon().toPolygon()))

    def clear_content(self):
        for i in reversed(range(self.content_container.count())):
            widget = self.content_container.itemAt(i).widget()
            if widget:
                widget.setParent(None)

    def load_page1(self):
        self.clear_content()
        self.content_container.addWidget(self.page1)

    def load_page2(self):
        self.clear_content()
        self.content_container.addWidget(self.page2)

    def load_page3(self):
        self.clear_content()
        self.content_container.addWidget(self.page3)

    def menuChange(self, menuNum):
        self.ui.menuButton1.setStyleSheet(f"border-image:url('{resource_path('images/menu1_off.png')}');")
        self.ui.menuButton2.setStyleSheet(f"border-image:url('{resource_path('images/menu2_off.png')}');")
        self.ui.menuButton3.setStyleSheet(f"border-image:url('{resource_path('images/menu3_off.png')}');")
        if menuNum == 1:
            self.ui.menuButton1.setStyleSheet(f"border-image:url('{resource_path('images/menu1_on.png')}');")
            self.load_page1()
        elif menuNum == 2:
            self.ui.menuButton2.setStyleSheet(f"border-image:url('{resource_path('images/menu2_on.png')}');")
            self.load_page2()
        elif menuNum == 3:
            self.ui.menuButton3.setStyleSheet(f"border-image:url('{resource_path('images/menu3_on.png')}');")
            self.load_page3()

    def menu1_clicked(self):
        if self.selectedMenu != 1:
            self.selectedMenu = 1
            self.menuChange(1)

    def menu2_clicked(self):
        if self.selectedMenu != 2:
            self.selectedMenu = 2
            self.menuChange(2)

    def menu3_clicked(self):
        if self.selectedMenu != 3:
            self.selectedMenu = 3
            self.menuChange(3)


    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.old_pos = event.globalPosition().toPoint()

    def mouseMoveEvent(self, event):
        if self.old_pos:
            delta = event.globalPosition().toPoint() - self.old_pos
            self.move(self.x() + delta.x(), self.y() + delta.y())
            self.old_pos = event.globalPosition().toPoint()

    def mouseReleaseEvent(self, event):
        self.old_pos = None

if __name__ == "__main__":
    app = QApplication(sys.argv)
    configure_application(app)
    window = MainWindow()
    daemon.start()
    network_daemon.start()

    exit_code = app.exec()

    daemon.stop()
    network_daemon.stop()
    sys.exit(exit_code)
