# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'MainWindow.ui'
##
## Created by: Qt User Interface Compiler version 6.9.2
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from PySide6.QtCore import (QCoreApplication, QDate, QDateTime, QLocale,
    QMetaObject, QObject, QPoint, QRect,
    QSize, QTime, QUrl, Qt)
from PySide6.QtGui import (QBrush, QColor, QConicalGradient, QCursor,
    QFont, QFontDatabase, QGradient, QIcon,
    QImage, QKeySequence, QLinearGradient, QPainter,
    QPalette, QPixmap, QRadialGradient, QTransform)
from PySide6.QtWidgets import (QApplication, QHBoxLayout, QLayout, QMainWindow,
    QMenuBar, QPushButton, QSizePolicy, QWidget)

class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        if not MainWindow.objectName():
            MainWindow.setObjectName(u"MainWindow")
        MainWindow.resize(960, 545)
        MainWindow.setStyleSheet(u"")
        self.centralwidget = QWidget(MainWindow)
        self.centralwidget.setObjectName(u"centralwidget")
        self.menuButton1 = QPushButton(self.centralwidget)
        self.menuButton1.setObjectName(u"menuButton1")
        self.menuButton1.setGeometry(QRect(300, 9, 120, 30))
        self.menuButton1.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.menuButton1.setStyleSheet(u"border-image: url(\"images/menu1_on.png\")")
        self.menuButton2 = QPushButton(self.centralwidget)
        self.menuButton2.setObjectName(u"menuButton2")
        self.menuButton2.setGeometry(QRect(420, 9, 120, 30))
        self.menuButton2.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.menuButton2.setStyleSheet(u"border-image: url(\"images/menu2_off.png\")")
        self.menuButton3 = QPushButton(self.centralwidget)
        self.menuButton3.setObjectName(u"menuButton3")
        self.menuButton3.setGeometry(QRect(540, 9, 120, 30))
        self.menuButton3.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.menuButton3.setStyleSheet(u"border-image: url(\"images/menu3_off.png\")")
        self.horizontalLayoutWidget = QWidget(self.centralwidget)
        self.horizontalLayoutWidget.setObjectName(u"horizontalLayoutWidget")
        self.horizontalLayoutWidget.setGeometry(QRect(0, 45, 960, 500))
        self.contentArea = QHBoxLayout(self.horizontalLayoutWidget)
        self.contentArea.setSpacing(0)
        self.contentArea.setObjectName(u"contentArea")
        self.contentArea.setSizeConstraint(QLayout.SizeConstraint.SetDefaultConstraint)
        self.contentArea.setContentsMargins(0, 0, 0, 0)
        self.widget = QWidget(self.horizontalLayoutWidget)
        self.widget.setObjectName(u"widget")
        self.widget.setEnabled(False)

        self.contentArea.addWidget(self.widget)

        self.exitButton = QPushButton(self.centralwidget)
        self.exitButton.setObjectName(u"exitButton")
        self.exitButton.setGeometry(QRect(18, 17, 12, 12))
        self.exitButton.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.exitButton.setStyleSheet(u"QPushButton {\n"
"    background-color: #ff5f57;\n"
"    border-radius: 6px;\n"
"    border: 1px solid #cc4c46;\n"
"}\n"
"\n"
"QPushButton:hover {\n"
"    background-color: #ff7a72; \n"
"    border: 1px solid #d95b54; \n"
"}")
        self.minimizeButton = QPushButton(self.centralwidget)
        self.minimizeButton.setObjectName(u"minimizeButton")
        self.minimizeButton.setGeometry(QRect(38, 17, 12, 12))
        self.minimizeButton.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.minimizeButton.setStyleSheet(u"QPushButton {\n"
"    background-color: #FEBC2E;\n"
"    border-radius: 6px;\n"
"    border: 1px solid #cb9625;\n"
"}\n"
"\n"
"QPushButton:hover {\n"
"    background-color: #FFC94A; \n"
"    border: 1px solid #D4A230;  \n"
"}")
        self.dummyButton = QPushButton(self.centralwidget)
        self.dummyButton.setObjectName(u"dummyButton")
        self.dummyButton.setGeometry(QRect(58, 17, 12, 12))
        self.dummyButton.setCursor(QCursor(Qt.CursorShape.ForbiddenCursor))
        self.dummyButton.setStyleSheet(u"background-color: #DED8DE;\n"
"border-radius: 6px;\n"
"border: 1px solid #bcb6bc;")
        MainWindow.setCentralWidget(self.centralwidget)
        self.menubar = QMenuBar(MainWindow)
        self.menubar.setObjectName(u"menubar")
        self.menubar.setGeometry(QRect(0, 0, 960, 33))
        self.menubar.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        MainWindow.setMenuBar(self.menubar)

        self.retranslateUi(MainWindow)

        QMetaObject.connectSlotsByName(MainWindow)
    # setupUi

    def retranslateUi(self, MainWindow):
        MainWindow.setWindowTitle(QCoreApplication.translate("MainWindow", u"MainWindow", None))
        self.menuButton1.setText("")
        self.menuButton2.setText("")
        self.menuButton3.setText("")
        self.exitButton.setText("")
        self.minimizeButton.setText("")
        self.dummyButton.setText("")
    # retranslateUi
