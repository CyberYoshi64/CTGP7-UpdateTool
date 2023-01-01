# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'mainyVoaKI.ui'
##
## Created by: Qt User Interface Compiler version 5.15.7
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from PySide2.QtCore import *  # type: ignore
from PySide2.QtGui import *  # type: ignore
from PySide2.QtWidgets import *  # type: ignore

import CTGP7UpdaterApp.resources_rc

class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        if not MainWindow.objectName():
            MainWindow.setObjectName(u"MainWindow")
        MainWindow.resize(600, 400)
        MainWindow.setMinimumSize(QSize(600, 400))
        MainWindow.setMaximumSize(QSize(16777215, 16777215))
        icon = QIcon()
        icon.addFile(u":/images/window_icon.png", QSize(), QIcon.Normal, QIcon.Off)
        MainWindow.setWindowIcon(icon)
        self.centralwidget = QWidget(MainWindow)
        self.centralwidget.setObjectName(u"centralwidget")
        self.verticalLayout = QVBoxLayout(self.centralwidget)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.horizontalLayout = QHBoxLayout()
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.horizontalSpacer = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

        self.horizontalLayout.addItem(self.horizontalSpacer)

        self.label = QLabel(self.centralwidget)
        self.label.setObjectName(u"label")
        sizePolicy = QSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.label.sizePolicy().hasHeightForWidth())
        self.label.setSizePolicy(sizePolicy)
        self.label.setMaximumSize(QSize(384, 96))
        self.label.setLayoutDirection(Qt.LeftToRight)
        self.label.setPixmap(QPixmap(u":/images/logo.png"))
        self.label.setScaledContents(True)
        self.label.setAlignment(Qt.AlignCenter)

        self.horizontalLayout.addWidget(self.label)

        self.horizontalSpacer_2 = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

        self.horizontalLayout.addItem(self.horizontalSpacer_2)


        self.verticalLayout.addLayout(self.horizontalLayout)

        self.label_2 = QLabel(self.centralwidget)
        self.label_2.setObjectName(u"label_2")
        font = QFont()
        font.setPointSize(18)
        font.setBold(True)
        font.setWeight(75)
        self.label_2.setFont(font)
        self.label_2.setAlignment(Qt.AlignCenter)

        self.verticalLayout.addWidget(self.label_2)

        self.verticalSpacer_2 = QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding)

        self.verticalLayout.addItem(self.verticalSpacer_2)

        self.horizontalLayout_2 = QHBoxLayout()
        self.horizontalLayout_2.setObjectName(u"horizontalLayout_2")
        self.horizontalSpacer_4 = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

        self.horizontalLayout_2.addItem(self.horizontalSpacer_4)

        self.label_3 = QLabel(self.centralwidget)
        self.label_3.setObjectName(u"label_3")

        self.horizontalLayout_2.addWidget(self.label_3)

        self.sdRootText = QLineEdit(self.centralwidget)
        self.sdRootText.setObjectName(u"sdRootText")
        sizePolicy1 = QSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        sizePolicy1.setHorizontalStretch(0)
        sizePolicy1.setVerticalStretch(0)
        sizePolicy1.setHeightForWidth(self.sdRootText.sizePolicy().hasHeightForWidth())
        self.sdRootText.setSizePolicy(sizePolicy1)
        self.sdRootText.setMinimumSize(QSize(256, 0))

        self.horizontalLayout_2.addWidget(self.sdRootText)

        self.sdBrowseButton = QPushButton(self.centralwidget)
        self.sdBrowseButton.setObjectName(u"sdBrowseButton")

        self.horizontalLayout_2.addWidget(self.sdBrowseButton)

        self.horizontalSpacer_3 = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

        self.horizontalLayout_2.addItem(self.horizontalSpacer_3)


        self.verticalLayout.addLayout(self.horizontalLayout_2)

        self.miscInfoLabel = QLabel(self.centralwidget)
        font = QFont()
        font.setBold(True)
        self.miscInfoLabel.setFont(font)
        self.miscInfoLabel.setObjectName(u"miscInfoLabel")
        self.miscInfoLabel.setAlignment(Qt.AlignCenter)

        self.verticalLayout.addWidget(self.miscInfoLabel)

        self.verticalSpacer = QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding)

        self.verticalLayout.addItem(self.verticalSpacer)

        self.startStopButton = QPushButton(self.centralwidget)
        self.startStopButton.setObjectName(u"startStopButton")
        self.startStopButton.setMinimumSize(QSize(0, 40))
        font1 = QFont()
        font1.setBold(True)
        font1.setWeight(75)
        self.startStopButton.setFont(font1)

        self.verticalLayout.addWidget(self.startStopButton)

        self.horizontalLayout_3 = QHBoxLayout()
        self.horizontalLayout_3.setObjectName(u"horizontalLayout_3")
        self.horizontalSpacer_5 = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

        self.horizontalLayout_3.addItem(self.horizontalSpacer_5)

        self.helpButton = QPushButton(self.centralwidget)
        self.helpButton.setObjectName(u"helpButton")

        self.horizontalLayout_3.addWidget(self.helpButton)

        self.horizontalSpacer_6 = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

        self.horizontalLayout_3.addItem(self.horizontalSpacer_6)


        self.verticalLayout.addLayout(self.horizontalLayout_3)

        self.verticalSpacer_3 = QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding)

        self.verticalLayout.addItem(self.verticalSpacer_3)

        self.progressInfoLabel = QLabel(self.centralwidget)
        self.progressInfoLabel.setObjectName(u"progressInfoLabel")
        self.progressInfoLabel.setAlignment(Qt.AlignCenter)

        self.verticalLayout.addWidget(self.progressInfoLabel)

        self.progressBar = QProgressBar(self.centralwidget)
        self.progressBar.setObjectName(u"progressBar")
        self.progressBar.setValue(0)

        self.verticalLayout.addWidget(self.progressBar)

        MainWindow.setCentralWidget(self.centralwidget)

        self.retranslateUi(MainWindow)

        QMetaObject.connectSlotsByName(MainWindow)
    # setupUi

    def retranslateUi(self, MainWindow):
        MainWindow.setWindowTitle(QCoreApplication.translate("MainWindow", u"CTGP-7 Installer", None))
        self.label.setText("")
        self.label_2.setText(QCoreApplication.translate("MainWindow", u"Welcome to the CTGP-7 Installer", None))
        self.label_3.setText(QCoreApplication.translate("MainWindow", u"Select target:", None))
        self.sdBrowseButton.setText(QCoreApplication.translate("MainWindow", u"Browse", None))
        self.startStopButton.setText(QCoreApplication.translate("MainWindow", u"START", None))
        self.helpButton.setText(QCoreApplication.translate("MainWindow", u"Help", None))
        self.progressInfoLabel.setText(QCoreApplication.translate("MainWindow", u"Progress Information", None))
    # retranslateUi

