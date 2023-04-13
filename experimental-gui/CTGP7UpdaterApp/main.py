import sys
import os
import shutil

from PySide2.QtWidgets import (
    QApplication, QDialog, QMainWindow, QMessageBox, QFileDialog
)
from PySide2.QtCore import (
    QRunnable, Slot, Signal, QThreadPool, QObject, QUrl
)

from PySide2.QtGui import (
    QDesktopServices
)

import psutil

from CTGP7UpdaterApp.ui_main import Ui_MainWindow
from CTGP7UpdaterApp.CTGP7Updater import CTGP7Updater
import ctypes

class WorkerSignals(QObject):
    progress = Signal(dict)
    error = Signal(str)
    success = Signal(str)
    stop = Signal()

class CTGP7InstallerWorker(QRunnable):

    def __init__(self, basedir, isInstall, isCitra):
        super(CTGP7InstallerWorker, self).__init__()
        self.signals = WorkerSignals()
        self.basedir = basedir
        self.isInstall = isInstall
        self.isCitra = isCitra
        self.signals.stop.connect(self.onStop)
        self.updater = None

    def logData(self, data: dict):
        self.signals.progress.emit(data)
    
    def onStop(self):
        if (self.updater):
            self.updater.stop()

    @Slot()  # QtCore.Slot
    def run(self):
        try:
            self.logData({"m": "Starting CTGP-7 Installation..."})
            self.updater = CTGP7Updater(self.isInstall, self.isCitra)
            self.updater.fetchDefaultCDNURL()
            self.updater.setLogFunction(self.logData)
            self.updater.setBaseDirectory(self.basedir)
            self.updater.cleanInstallFolder()
            self.updater.getLatestVersion()
            self.updater.loadUpdateInfo()
            self.updater.verifySpaceAvailable()
            self.updater.startUpdate()
        except Exception as e:
            self.signals.error.emit(str(e))
        else:
            self.signals.success.emit(self.updater.latestVersion)

class Window(QMainWindow, Ui_MainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setupUi(self)
        self.connectSignalsSlots()
        self.progressBar.setEnabled(False)
        self.progressInfoLabel.setText("")
        self.workerMode = CTGP7Updater._MODE_INSTALL
        self.isCitraPath = None
        self.hasPending = False
        self.didSaveBackup = False
        self.setStartButtonState(0)
        self.scanForNintendo3DSSD()
        self.installerworker = None
        self.threadpool = QThreadPool()
    
    def reportProgress(self, data: dict):
        if "m" in data:
            self.progressInfoLabel.setText(data["m"])
        if "p" in data:
            self.progressBar.setEnabled(True)
            self.progressBar.setValue((data["p"][0] / data["p"][1]) * 100)
 
    def reSetup(self):
        self.progressBar.setEnabled(False)
        self.sdBrowseButton.setEnabled(True)
        self.helpButton.setEnabled(True)
        self.sdRootText.setEnabled(True)
        self.progressInfoLabel.setText("")
        self.applySDFolder(self.sdRootText.text())
        self.menuFile.setEnabled(True)
        self.menuExperimental.setEnabled(True)
    
    def installOnError(self, err:str):
        msg = QMessageBox(parent=self)
        msg.setIcon(QMessageBox.Critical)
        msg.setText(
            "An error has occurred.<br><br>"+
            "If this error keeps happening, ask for help in the "+
            "<a href='https://discord.com/invite/0uTPwYv3SPQww54l'>"+
            "CTGP-7 Discord Server</a>."
        )
        msg.setDetailedText(str(err))
        msg.setWindowTitle("Error")
        for b in msg.buttons():
            if (msg.buttonRole(b) == QMessageBox.ActionRole):
                b.click()
                break
        msg.exec_()
        self.reSetup()#self.close()
    
    def installOnSuccess(self, ver:str):
        QMessageBox.information(self, "Installation finished", "Installation finished successfully! (v{})<br>Make sure to install the cia file in the CTGP-7 -> cia folder in the SD card.".format(ver))
        if (self.didSaveBackup):
            if (QMessageBox.question(self, "Save backup", "Would you like to restore the save backup done previously?", QMessageBox.Yes | QMessageBox.No) == QMessageBox.Yes):
                savefolder = os.path.join(self.sdRootText.text(), "CTGP-7", "savefs")
                backupfolder = os.path.join(self.sdRootText.text(), "CTGP-7savebak")
                try:
                    shutil.copytree(backupfolder, savefolder)
                except Exception as e:
                    self.installOnError("Failed to restore save backup, please restore it manually: {}".format(e))
                    return
        self.reSetup()#self.close()

    def doSaveBackup(self):
        try:
            savefolder = os.path.join(self.sdRootText.text(), "CTGP-7", "savefs")
            backupfolder = os.path.join(self.sdRootText.text(), "CTGP-7savebak")
            if (os.path.exists(savefolder)):
                self.reportProgress({"m": "Doing save backup..."})
                if (os.path.exists(backupfolder)):
                    shutil.rmtree(backupfolder)
                os.rename(savefolder, backupfolder)
                self.didSaveBackup = True
                QMessageBox.information(self, "Save backup", "Save data backup of the previous CTGP-7 installation has been made in {}".format(backupfolder))
            return True
        except Exception as e:
            self.installOnError("Failed to create save backup: {}".format(e))
            return False

    def scanForNintendo3DSSD(self):
        folder = CTGP7Updater.findNintendo3DSRoot()
        if (folder is not None):
            self.sdRootText.setText(folder)
        elif (os.path.exists(CTGP7Updater.getCitraDir())):
            self.sdRootText.setText(CTGP7Updater.getCitraDir())
            QMessageBox.information(self, "Couldn't find SD Card", "Couldn't detect an SD Card but a Citra build was found.\n\nIf you want to install/update CTGP-7 for a 3DS console, use the \"Browse\" button to navigate to the SD Card of your console.")
            
    def updateButtonPress(self):
        if self.hasPending and (QMessageBox.question(self, "Pending update", "A pending update was detected. You must finish it first, before updating again. Do you want to continue this update?", QMessageBox.Yes | QMessageBox.No) == QMessageBox.No): return
        self.workerMode = CTGP7Updater._MODE_UPDATE
        self.miscInfoLabel.setText("")
        self.installerworker = CTGP7InstallerWorker(self.sdRootText.text(), self.workerMode, self.isCitraPath)
        self.installerworker.signals.progress.connect(self.reportProgress)
        self.installerworker.signals.success.connect(self.installOnSuccess)
        self.installerworker.signals.error.connect(self.installOnError)
        self.setStartButtonState(4)
        self.sdBrowseButton.setEnabled(False)
        self.helpButton.setEnabled(False)
        self.sdRootText.setEnabled(False)
        self.menuFile.setEnabled(False)
        self.menuExperimental.setEnabled(False)
        self.threadpool.start(self.installerworker)
    
    def startStopButtonPress(self):
        if (self.startButtonState > 0 and self.startButtonState < 4):
            if self.startButtonState == 2 and (QMessageBox.question(self, "Confirm re-installation", "You are about to re-install CTGP-7.<br>Any modifications via MyStuff will be deleted.<br><br>Do you want to continue?<br>(Your save data will be backed up, if possible.)", QMessageBox.Yes | QMessageBox.No) == QMessageBox.No): return
            if self.startButtonState == 3 and (QMessageBox.question(self, "Broken CTGP-7 installation", "This installation is either corrupted or was flagged for removal. Proceeding will wipe this installation and create a new one.<br><br>Do you want to proceed anyway?<br>(Your save data will be backed up, if possible.)", QMessageBox.Yes | QMessageBox.No) == QMessageBox.No): return

            if self.workerMode and (self.isCitraPath == None):
                dlg = QMessageBox(self)
                dlg.setWindowTitle("Select a platform to install for")
                dlg.setIcon(QMessageBox.Question)
                dlg.setText("Unable to determine, whether this installation is meant for a 3DS or Citra.<br><br>Please select which platform you want to install CTGP-7 for.")
                dlgIs3DS = dlg.addButton("3DS", QMessageBox.NoRole)
                dlgisCitra = dlg.addButton("Citra", QMessageBox.NoRole)
                dlgCancel = dlg.addButton("Cancel", QMessageBox.NoRole)
                dlg.setDefaultButton(dlgCancel)
                dlg.exec_()
                if dlg.clickedButton() == dlgCancel: return
                self.isCitraPath = (dlg.clickedButton() == dlgisCitra)

            if self.workerMode and not self.doSaveBackup(): return
            self.workerMode = CTGP7Updater._MODE_INSTALL
            self.miscInfoLabel.setText("")
            self.installerworker = CTGP7InstallerWorker(self.sdRootText.text(), self.workerMode, self.isCitraPath)
            self.installerworker.signals.progress.connect(self.reportProgress)
            self.installerworker.signals.success.connect(self.installOnSuccess)
            self.installerworker.signals.error.connect(self.installOnError)
            self.setStartButtonState(4)
            self.sdBrowseButton.setEnabled(False)
            self.helpButton.setEnabled(False)
            self.sdRootText.setEnabled(False)
            self.menuFile.setEnabled(False)
            self.menuExperimental.setEnabled(False)
            self.threadpool.start(self.installerworker)
        elif (self.startButtonState == 4):
            if (self.installerworker):
                self.installerworker.signals.stop.emit()
            self.setStartButtonState(0)

    def setStartButtonState(self, state):
        self.startButtonState = state
        self.startStopButton.setEnabled(state != 0)
        self.updateButton.setText("Continue update" if self.hasPending else "Update")
        self.updateButton.setEnabled(True)
        self.updateButton.setHidden(True)
        if (state == 0):
            self.startStopButton.setText("")
            self.startStopButton.clearFocus()
            self.updateButton.setText("")
            self.updateButton.clearFocus()
        elif (state == 1):
            self.startStopButton.setText("Install")
        elif (state == 2):
            self.startStopButton.setText("Re-install")
            self.updateButton.setHidden(False)
        elif (state == 3):
            self.startStopButton.setText("Re-install")
        elif (state == 4):
            self.startStopButton.setText("Cancel")
        self.updateButton.setEnabled(not self.updateButton.isHidden())
        self.actionInstallMod.setEnabled(self.startStopButton.isEnabled())
        self.actionUpdateMod.setEnabled(self.updateButton.isEnabled())

    def applySDFolder(self, folder: str):
        if (folder == "" or folder[-1]==" "):
            self.miscInfoLabel.setText("")
            self.setStartButtonState(0)
            return
        self.isCitraPath = CTGP7Updater.isCitraDirectory(folder)
        if (os.path.exists(folder)):
            bmsk = CTGP7Updater.checkForInstallOfPath(folder)
            self.miscInfoLabel.setText("Ready to install CTGP-7.")
            self.miscInfoLabel.setStyleSheet("color: #084")
            if not os.path.exists(os.path.join(folder,"Nintendo 3DS")):
                self.miscInfoLabel.setText("This path appears to not be of a 3DS SD Card.")
                self.miscInfoLabel.setStyleSheet("color: #c60")
            if (bmsk & 3)==2:
                self.miscInfoLabel.setText("Corrupted CTGP-7 installation detected.")
                self.miscInfoLabel.setStyleSheet("color: #f40")
                self.setStartButtonState(3)
            elif bmsk & 8:
                self.miscInfoLabel.setText("Broken CTGP-7 installation detected.")
                self.miscInfoLabel.setStyleSheet("color: #f24")
                self.setStartButtonState(3)
            elif bmsk & 1:
                self.setStartButtonState(1)
            else:
                self.hasPending = bool(bmsk & 4)
                self.miscInfoLabel.setText("Valid CTGP-7 installation detected.")
                self.miscInfoLabel.setStyleSheet("color: #480")
                self.setStartButtonState(2)
        else:
            self.miscInfoLabel.setText("Folder does not exist")
            self.miscInfoLabel.setStyleSheet("color: red")
            self.setStartButtonState(0)

    def selectSDDirectory(self):
        dialog = QFileDialog()
        folder_path = dialog.getExistingDirectory(self, "Select 3DS SD Card", self.sdRootText.text())
        if (folder_path != ""):
            folder_path = folder_path.replace("/", os.path.sep).replace("\\", os.path.sep)
            self.sdRootText.setText(folder_path)
    
    def showHelpDialog(self):
        QMessageBox.information(self, "About", 
            "CTGP-7 Installer v"+CTGP7Updater.VERSION_NUMBER+"<br><br>"+
            "Having issues? Ask for help in the "+
            "<a href='https://discord.com/invite/0uTPwYv3SPQww54l'>"+
            "CTGP-7 Discord Server</a><br><br>"+
            "2021-2023 CyberYoshi64, PabloMK7"
        )

    def aboutQt(self):
        QMessageBox.aboutQt(self)

    def openBrowserGitHub(self):
        QDesktopServices.openUrl(QUrl("https://github.com/CyberYoshi64/CTGP7-UpdateTool/issues"))

    def openBrowserGameBanana(self):
        QDesktopServices.openUrl(QUrl("https://gamebanana.com/mods/50221"))

    def quitApp(self):
        self.close()

    def featureNotImplemented(self):
        QMessageBox.warning(self, "Feature not implemented","This feature is not available at the moment. Check again later.")

    def connectSignalsSlots(self):
        self.sdBrowseButton.clicked.connect(self.selectSDDirectory)
        self.sdRootText.textChanged.connect(lambda s: self.applySDFolder(s))
        self.helpButton.clicked.connect(self.showHelpDialog)
        self.actionAboutThisApp.triggered.connect(self.showHelpDialog)
        self.startStopButton.clicked.connect(self.startStopButtonPress)
        self.updateButton.clicked.connect(self.updateButtonPress)
        self.actionInstallMod.triggered.connect(self.startStopButtonPress)
        self.actionUpdateMod.triggered.connect(self.updateButtonPress)
        self.actionExit.triggered.connect(self.quitApp)
        self.actionAboutQt.triggered.connect(self.aboutQt)
        self.actionHelpGamebanana.triggered.connect(self.openBrowserGameBanana)
        self.actionHelpGitHub.triggered.connect(self.openBrowserGitHub)

        self.actionShowChangelog.setEnabled(False)
        self.actionInstallCIA.setEnabled(False)
        self.actionIntegChk.triggered.connect(self.featureNotImplemented)

def startUpdaterApp():
    app = QApplication(sys.argv)
    win = Window()
    try:
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(u"ctgp7.ctgp7.installer.1_1") # So that the taskbar shows the window icon on windows
    except:
        pass
    win.show()
    sys.exit(app.exec_())