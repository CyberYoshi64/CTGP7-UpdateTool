import sys
import os
import shutil

from PySide2.QtWidgets import (
    QApplication, QDialog, QMainWindow, QMessageBox, QFileDialog
)
from PySide2.QtCore import (
    QRunnable, Slot, Signal, QThreadPool, QObject
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

    def __init__(self, basedir):
        super(CTGP7InstallerWorker, self).__init__()
        self.signals = WorkerSignals()
        self.basedir = basedir
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
            self.updater = CTGP7Updater(True)
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
        self.setStartButtonState(0)
        self.scanForNintendo3DSSD()
        self.installerworker = None
        self.threadpool = QThreadPool()
        self.didSaveBackup = False
    
    def reportProgress(self, data: dict):
        if "m" in data:
            self.progressInfoLabel.setText(data["m"])
        if "p" in data:
            self.progressBar.setEnabled(True)
            self.progressBar.setValue((data["p"][0] / data["p"][1]) * 100)

    def installOnError(self, err:str):
        msg = QMessageBox(parent=self)
        msg.setIcon(QMessageBox.Critical)
        msg.setText("An error has occurred during the CTGP-7 Installation<br>If this error keeps happening, ask for help in the <a href='https://discord.com/invite/0uTPwYv3SPQww54l'>CTGP-7 Discord Server</a>.")
        msg.setDetailedText(str(err))
        msg.setWindowTitle("Error")
        for b in msg.buttons():
            if (msg.buttonRole(b) == QMessageBox.ActionRole):
                b.click()
                break
        msg.exec_()
        self.close()
    
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
        self.close()

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


    def startStopButtonPress(self):
        if (self.startButtonState == 1):
            self.miscInfoLabel.setText("")
            if not self.doSaveBackup(): return
            self.installerworker = CTGP7InstallerWorker(self.sdRootText.text())
            self.installerworker.signals.progress.connect(self.reportProgress)
            self.installerworker.signals.success.connect(self.installOnSuccess)
            self.installerworker.signals.error.connect(self.installOnError)
            self.setStartButtonState(2)
            self.sdBrowseButton.setEnabled(False)
            self.helpButton.setEnabled(False)
            self.sdRootText.setEnabled(False)
            self.threadpool.start(self.installerworker)
        elif (self.startButtonState == 2):
            if (self.installerworker):
                self.installerworker.signals.stop.emit()
            self.setStartButtonState(0)

    def setStartButtonState(self, state):
        self.startButtonState = state
        if (state == 0):
            self.startStopButton.setText("")
            self.startStopButton.setEnabled(False)
            self.startStopButton.clearFocus()
        elif (state == 1):
            self.startStopButton.setText("INSTALL")
            self.startStopButton.setEnabled(True)
        elif (state == 2):
            self.startStopButton.setText("CANCEL")
            self.startStopButton.setEnabled(True)

    def applySDFolder(self, folder: str):
        if (folder == ""):
            self.miscInfoLabel.setText("")
            return
        if (os.path.exists(folder)):
            if (os.path.exists(os.path.join(folder, "Nintendo 3DS"))):
                self.miscInfoLabel.setText("Valid 3DS SD card detected")
                self.miscInfoLabel.setStyleSheet("color: green")
            else:
                self.miscInfoLabel.setText("Folder exists, but is not a valid 3DS SD card")
                self.miscInfoLabel.setStyleSheet("color: orange")
            self.setStartButtonState(1)
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
        QMessageBox.information(self, "About", "CTGP-7 Installer v1.0<br><br>If you are having issues, ask for help in the <a href='https://discord.com/invite/0uTPwYv3SPQww54l'>CTGP-7 Discord Server</a>.")

    def connectSignalsSlots(self):
        self.sdBrowseButton.clicked.connect(self.selectSDDirectory)
        self.sdRootText.textChanged.connect(lambda s: self.applySDFolder(s))
        self.helpButton.clicked.connect(self.showHelpDialog)
        self.startStopButton.clicked.connect(self.startStopButtonPress)

def startUpdaterApp():
    app = QApplication(sys.argv)
    win = Window()
    try:
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(u"ctgp7.ctgp7.installer.1_0") # So that the taskbar shows the window icon on windows
    except:
        pass
    win.show()
    sys.exit(app.exec_())