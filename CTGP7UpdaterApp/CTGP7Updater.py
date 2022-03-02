import os
from urllib.request import urlopen
import shutil
import psutil

class CTGP7Updater:

    _BASE_URL_DYN_LINK = "https://ctgp7.page.link/baseCDNURL"
    _INSTALLER_FILE_DIFF = "installinfo.txt"
    _FILES_LOCATION = "data"
    _LATEST_VER_LOCATION = "latestver"
    _UPDATE_FILEFLAGMD = ["M","D","T","F","S"]
    _DL_ATTEMPT_TOTALCNT = 30
    _VERSION_FILE_PATH = "config/version.bin"
    _SLACK_FREE_SPACE = 20000000

    def __init__(self, isInstaller=True) -> None:
        self.isInstaller = isInstaller
        self.basePath = ""
        self.downloadCount = 0
        self.currDownloadCount = 0
        self.fileDownCurr = 0
        self.fileDownSize = 0
        self.fileList = []
        self.latestVersion = ""
        self.logFunction = None
        self.isStopped = False
        self.downloadSize = 0
        
        try:
            self.baseURL = self._downloadString(CTGP7Updater._BASE_URL_DYN_LINK).replace("\r", "").replace("\n", "")
        except Exception as e:
            raise Exception("Failed to init updater: {}".format(e))
        pass

    def _mkFoldersForFile(self, fol:str):
        g=fol[0:fol.rfind(os.path.sep)]
        os.makedirs(g, exist_ok=True)
    
    def _parseAndSortDlList(self, dll:list):
        fileN=[]; fileM=[]; fileO=[]; newDl=[]; oldf=""
        filemode=CTGP7Updater._UPDATE_FILEFLAGMD
        self.downloadCount = 0

        for i in range(len(dll)):
            ms=dll[i][0]; mf=dll[i][1]

            if ms=="S":
                try:
                    self.downloadSize = int(mf[1:])
                except Exception as e:
                    raise Exception("Failed to parse needed download size: {}".format(e))
            elif ms=="F":
                # Next element is expected to use method "T", which should be always true
                # In order to prevent renaming without downloading first, just store as reference
                oldf=mf
            else:
                fileNC=-1
                try: 	fileNC=fileN.index(mf)
                except:
                    fileN.append(mf); fileM.append(ms); fileO.append(oldf)
                else:
                    fileN.pop(fileNC); fileM.pop(fileNC); fileO.pop(fileNC)
                    fileN.append(mf); fileM.append(ms); fileO.append(oldf)
                oldf="" # Non-rename shouldn't have the reference
        
        #for m in filemode:
        for i in range(len(fileN)):
                #if fileM[i]==m:
                if fileM[i]=="M": self.downloadCount+=1
                newDl.append((filemode.index(fileM[i]), fileN[i], fileO[i]))

        return newDl

    def _downloadString(self, url: str) -> str:
        try:
            output = urlopen(url, timeout=10).read()
            return output.decode('utf-8')
        except:
            raise Exception("Failed download string from URL: {}".format(url))

    def stop(self):
        self.isStopped = True

    def setLogFunction(self, func):
        self.logFunction = func

    def _log(self, msg: str):
        if (self.logFunction):
            self.logFunction({"m":msg})

    def _prog(self, curr: float, tot: float):
        if (self.logFunction):
            self.logFunction({"p":(curr, tot)})

    def setBaseDirectory(self, path: str):
        if not (os.path.exists(path)):
            raise Exception("Installation path invalid.")
        self.basePath = path

    def getLatestVersion(self):
        self._log("Fetching latest version...")
        try:
            self.latestVersion = self._downloadString(self.baseURL + CTGP7Updater._LATEST_VER_LOCATION).replace("\n", "").replace("\r", "")
        except Exception as e:
            raise Exception("Failed to get latest version: {}".format(e))

    def loadUpdateInfo(self):
        if (self.isInstaller):
            self._log("Downloading file list...")
            try:
                fileList = self._downloadString(self.baseURL + CTGP7Updater._INSTALLER_FILE_DIFF).split("\n")
                fileModeList = []
                for file in fileList:
                    if file=="": continue
                    fileModeList.append((file[0],file[1:]))
                self.fileList = self._parseAndSortDlList(fileModeList)

            except Exception as e:
                raise Exception("Failed to get list of files: {}".format(e))
    
    def verifySpaceAvailable(self):
        if (self.downloadSize):
            available_space = psutil.disk_usage(self.basePath).free
            if (self.downloadSize + CTGP7Updater._SLACK_FREE_SPACE > available_space):
                raise Exception("Not enough free space on destination folder. Additional {} MB needed to proceed with installation.".format((self.downloadSize + CTGP7Updater._SLACK_FREE_SPACE - available_space) // 1000000))

    def startUpdate(self):
        mainfolder = os.path.join(self.basePath, "CTGP-7")
        hbrwfolder = os.path.join(self.basePath, "3ds")
        try:
            os.makedirs(mainfolder, exist_ok=True)
            os.makedirs(hbrwfolder, exist_ok=True)
        except Exception as e:
            raise Exception("Failed to create CTGP-7 directory: {}".format(e))

        self.currDownloadCount = 0
        for i in range(len(self.fileList)):
            if (self.isStopped):
                raise Exception("User cancelled installation")
            fmode=self.fileList[i][0]; f=self.fileList[i][1]; f1=self.fileList[i][2]
            rep=0
            if fmode==CTGP7Updater._UPDATE_FILEFLAGMD.index("M"):
                self.currDownloadCount += 1
            url=self.baseURL + CTGP7Updater._FILES_LOCATION + f
            filePath = os.path.join(mainfolder, f.replace("/", os.path.sep)[1:])
            fileOnlyName = filePath[filePath.rfind(os.path.sep) + 1:]
            if fmode==0:
                countRetry = 0
                while (True):
                    try:
                        self._prog(self.currDownloadCount + 1, self.downloadCount)
                        self._mkFoldersForFile(filePath)
                        u = urlopen(url, timeout=10)
                        with open(filePath, 'wb') as downFile:

                            self.fileDownSize = int(u.getheader("Content-Length"))

                            self.fileDownCurr = 0
                            block_sz = 1024 * 8
                            while True:
                                if (self.isStopped):
                                    raise Exception("User cancelled installation")
                                buffer = u.read(block_sz)
                                if not buffer:
                                    break

                                self.fileDownCurr += len(buffer)
                                downFile.write(buffer)

                                self._log("Downloading file {} / {}: \"{}\" ({:.2f}%)".format(self.currDownloadCount + 1, self.downloadCount, fileOnlyName, (self.fileDownCurr / self.fileDownSize) * 100))
                            break
                    except Exception as e:
                        if (countRetry >= CTGP7Updater._DL_ATTEMPT_TOTALCNT or self.isStopped):
                            raise Exception("Failed to download file \"{}\": {}".format(filePath, e))
                        else:
                            pass
            
            elif fmode==1:
                try: fsprop=os.stat(filePath)
                except: pass
                else:
                    try:
                        os.remove(filePath)
                    except Exception as e:
                        raise Exception("Failed to remove file \"{}\": {}".format(filePath, e))
            elif fmode==2:
                filePath1 = os.path.join(mainfolder, f1.replace("/", os.path.sep))
                try: os.stat(filePath1)
                except: raise Exception("Rename from file is missing: {}".format(filePath1))
                else:
                    try: os.rename(src=mainfolder+f1, dst=mainfolder+f)
                    except Exception as e: raise Exception("Failed to rename file: {}".format(e))
            else:
                raise Exception("Unknown file mode: {}".format(fmode))

        ciaFile = os.path.join(mainfolder, "cia", "CTGP-7.cia")
        tooInstallCiaFile = os.path.join(mainfolder, "cia", "tooInstall.cia")
        hbrwFile = os.path.join(mainfolder, "cia", "CTGP-7.3dsx")
        hbrwFileFinal = os.path.join(hbrwfolder, "CTGP-7.3dsx")
        tooInstallHbrwFile = os.path.join(mainfolder, "cia", "tooInstall.3dsx")

        self._log("Completing installation...")

        try:
            if os.path.exists(tooInstallCiaFile) or os.path.exists(tooInstallHbrwFile):
                try: os.stat(ciaFile)
                except: pass
                else: os.remove(ciaFile)
                os.rename(src=tooInstallCiaFile,dst=ciaFile)
                try: os.stat(hbrwFile)
                except: pass
                else: os.remove(hbrwFile)
                os.rename(src=tooInstallHbrwFile,dst=hbrwFile)
                shutil.copyfile(src=hbrwFile,dst=hbrwFileFinal)
        except Exception as e:
            raise Exception("Failed to finish cleanup: {}".format(e))

        try:
            with open(os.path.join(mainfolder, CTGP7Updater._VERSION_FILE_PATH), "wb") as vf:
                vf.write(self.latestVersion.encode("ascii"))
        except Exception as e:
            raise Exception("Failed to write version info: {}".format(e))
        
        self._log("Installation complete!")

    def cleanInstallFolder(self):
        mainfolder = os.path.join(self.basePath, "CTGP-7")
        if (os.path.exists(mainfolder)):
            self._log("Cleaning up previous CTGP-7 installation...")
            shutil.rmtree(mainfolder)