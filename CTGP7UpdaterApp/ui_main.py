# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'mainfvFCAH.ui'
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
        MainWindow.resize(640, 400)
        MainWindow.setMinimumSize(QSize(512, 384))
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
        self.sdRootText.setMinimumSize(QSize(272, 0))

        self.horizontalLayout_2.addWidget(self.sdRootText)

        self.sdBrowseButton = QPushButton(self.centralwidget)
        self.sdBrowseButton.setObjectName(u"sdBrowseButton")

        self.horizontalLayout_2.addWidget(self.sdBrowseButton)

        self.horizontalSpacer_3 = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

        self.horizontalLayout_2.addItem(self.horizontalSpacer_3)


        self.verticalLayout.addLayout(self.horizontalLayout_2)

        self.miscInfoLabel = QLabel(self.centralwidget)
        self.miscInfoLabel.setObjectName(u"miscInfoLabel")
        font = QFont()
        font.setBold(True)
        font.setWeight(75)
        self.miscInfoLabel.setFont(font)
        self.miscInfoLabel.setAlignment(Qt.AlignCenter)

        self.verticalLayout.addWidget(self.miscInfoLabel)

        self.verticalSpacer = QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding)

        self.verticalLayout.addItem(self.verticalSpacer)

        self.horizontalLayout_4 = QHBoxLayout()
        self.horizontalLayout_4.setObjectName(u"horizontalLayout_4")
        self.horizontalLayout_4.setContentsMargins(-1, 0, -1, 0)
        self.horizontalSpacer_7 = QSpacerItem(64, 20, QSizePolicy.Fixed, QSizePolicy.Minimum)

        self.horizontalLayout_4.addItem(self.horizontalSpacer_7)

        self.startStopButton = QPushButton(self.centralwidget)
        self.startStopButton.setObjectName(u"startStopButton")
        self.startStopButton.setMinimumSize(QSize(0, 40))
        self.startStopButton.setFont(font)

        self.horizontalLayout_4.addWidget(self.startStopButton)

        self.updateButton = QPushButton(self.centralwidget)
        self.updateButton.setObjectName(u"updateButton")
        self.updateButton.setEnabled(True)
        sizePolicy2 = QSizePolicy(QSizePolicy.Minimum, QSizePolicy.Fixed)
        sizePolicy2.setHorizontalStretch(0)
        sizePolicy2.setVerticalStretch(0)
        sizePolicy2.setHeightForWidth(self.updateButton.sizePolicy().hasHeightForWidth())
        self.updateButton.setSizePolicy(sizePolicy2)
        self.updateButton.setMinimumSize(QSize(0, 40))
        self.updateButton.setFont(font)

        self.horizontalLayout_4.addWidget(self.updateButton)

        self.horizontalSpacer_8 = QSpacerItem(64, 20, QSizePolicy.Fixed, QSizePolicy.Minimum)

        self.horizontalLayout_4.addItem(self.horizontalSpacer_8)


        self.verticalLayout.addLayout(self.horizontalLayout_4)

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
        self.progressBar.setTextVisible(True)

        self.verticalLayout.addWidget(self.progressBar)

        MainWindow.setCentralWidget(self.centralwidget)

        self.retranslateUi(MainWindow)

        QMetaObject.connectSlotsByName(MainWindow)
    # setupUi

    def retranslateUi(self, MainWindow):
        MainWindow.setWindowTitle(QCoreApplication.translate("MainWindow", u"CTGP-7 Installer", None))
        self.label.setText("")
        self.label_3.setText(QCoreApplication.translate("MainWindow", u"Select target:", None))
        self.sdBrowseButton.setText(QCoreApplication.translate("MainWindow", u"Browse", None))
        self.miscInfoLabel.setText(QCoreApplication.translate("MainWindow", u"Miscelaneous Information", None))
        self.startStopButton.setText(QCoreApplication.translate("MainWindow", u"Button 1", None))
        self.updateButton.setText(QCoreApplication.translate("MainWindow", u"Button 2", None))
        self.helpButton.setText(QCoreApplication.translate("MainWindow", u"Help", None))
        self.progressInfoLabel.setText(QCoreApplication.translate("MainWindow", u"Progress Information", None))
    # retranslateUi

