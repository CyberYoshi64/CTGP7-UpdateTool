#!/usr/bin/python3

from urllib.request import urlopen
from sys import argv
import os, struct, psutil, shutil

_FILEDWN_PART_EXT = ".part"
_FILELIST_METHODS = ["M","D","T","F","S"] # Modified, Deleted, To (rename), From (rename), Size Calc
_BASE_URL_DYN_LINK = "https://ctgp7.page.link/baseCDNURL" # Future-proof, CTGP-7 updates will be on a CDN
_INSTALLER_FILE_DIFF = "installinfo.txt" # Installer
_UPDATER_CHGLOG_FILE = "changeloglist" # Updater
_UPDATER_FILE_URL = "fileListPrefix.txt" # Updater
_FILES_LOCATION = "data" # https://[baseCDN]/data/... - Sub path from base CDN (redundant but whatever)
_LATEST_VER_LOCATION = "latestver" # Used by installer
_DL_ATTEMPT_TOTALCNT = 30 # 30 attempts... quite generous, if I'm honest
_VERSION_FILE_PATH = "/CTGP-7/config/version.bin" # Current version
_PENDINGUPDATE_PATH = "/CTGP-7/config/pendingUpdate.bin" # Pending update location
_TOOINSTALL_PATH = "/CTGP-7/cia/tooInstall"
_TOOINSTALL_CIA_PATH = "/CTGP-7/cia/CTGP-7"
_TOOINSTALL_HB_PATH = "/3ds/CTGP-7"
_SLACK_FREE_SPACE = 19851264 # Potential space used during installation (besides the main space used during install)

# Console-only, have to obnoxiously await any chance for pesky users to abort.
_STR_USERABORT = "The user aborted the operation." # It appears so often, no need to type it out everywhere.

def fileDelete(file:str) -> None:
    try: os.stat(file)    # Windows refuses to rename
    except: pass          # if destination exists, so
    else: os.remove(file) # delete beforehand.

def fileMove(oldf:str, newf:str) -> None:
    fileDelete(newf)
    os.rename(oldf,newf)

# File List struct from:
# https://github.com/PabloMK7/CTGP-7_Launcher/blob/master/source/updater.c#L15-L20

class FileListEntry:
    def __init__(self, ver=0, method="M", path="/") -> None: # Defaults for whatever reason
        self.filePath = path # File path
        self.forVersion = ver # Unused, for compatibility with launcher
        self.fileMethod = method
        
    # Export struct for pendingUpdate.bin
    def export(self) -> bytes:
        import struct
        return struct.pack("<BI", \
            ord(self.fileMethod),\
            self.forVersion) + \
            self.filePath.encode("utf8") + b'\0' # null-byte as string can be any length
    
    # Import from pendingUpdate.bin
    def importFromPend(self,fdb,off) -> int:
        self.fileMethod = chr(fdb[off])
        self.forVersion, = struct.unpack("<I",fdb[off+1:off+5])
        self.filePath = b''
        for off in range(off+5,len(fdb)):
            if fdb[off]: self.filePath += int.to_bytes(fdb[off],1,"little")
            else: break
        self.filePath = self.filePath.decode("utf8")
        return off+1

    def perform(self) -> int:
        global baseURL, shownDlCounter, shownDlTotal
        global fileMng_OldFileName, usrCancel
        global tooInstalling
        url = baseURL+_FILES_LOCATION+self.filePath
        fout = self.filePath
        if self.fileMethod == "M": # Modify
            for i in range(_DL_ATTEMPT_TOTALCNT):
                try: downloadToFileWIndicator(url, fout,\
                "({}/{}) {}".format(\
                    shownDlCounter+1, shownDlTotal, \
                    fout[fout.rfind("/")+1:]
                ))
                except KeyboardInterrupt: usrCancel=True; break
                except Exception as e: print("[fail]",e)
                else: break
            else: raise Exception("Failed to download '{}'.\nPlease try again later.".format(fout[fout.rfind("/")+1:]))
            shownDlCounter += 1
        if self.fileMethod == "D": # Delete
            fileDelete(fout)
        if self.fileMethod == "F": # (Rename) From
            fileMng_OldFileName = fout
        if self.fileMethod == "T": # (Rename) To
            fileMove(fileMng_OldFileName, fout)

# Console only, want to provide some automation in console version too
def checkForValidSD(path:str) -> bool:
    if os.path.exists(os.path.join(path,"Nintendo 3DS")):
        return True
    elif os.path.exists(path): 
        print("The path exists, but this does not appear to be a SD Card of a Nintendo 3DS.")
        try: return input("Continue anyway? [Y/N] ").upper()[0]=="Y"
        except: return False
    else:
        print("The path specified does not exist. Make sure you typed in the path correctly")
        return False
    return True

# equivalent to GUI's downloadString()
def downloadWithIndicator(url:str, prefix:str="", newLine:bool=True) -> bytes:
    outbuffer = b''
    u = urlopen(url, timeout=10)
    doprint = len(prefix)>0
    contentLength = int(u.getheader("Content-Length"))
    indicatorStr = "\x1b[2K"+prefix+"... "
    if doprint: print(indicatorStr,end="\r")
    block_sz = 8192
    while True:
        buffer = u.read(block_sz)
        if not buffer:
            break
        outbuffer += buffer
        if doprint: print(indicatorStr + "(%3.1f%%)"%((len(outbuffer)/contentLength)*100),end="\r")
    if newLine and doprint: print("")
    return outbuffer

# Again, but output as file.
def downloadToFileWIndicator(url:str, path:str, prefix:str="", newLine:bool=True, showsize:bool=True) -> None:
    global installPath
    if path[0]!="/": path="/"+path
    fullpath = "%s/CTGP-7%s"%(installPath,path)
    os.makedirs(fullpath[:fullpath.rfind("/")],exist_ok=True)
    u = urlopen(url, timeout=10)
    doprint = len(prefix)>0
    contentLength = int(u.getheader("Content-Length"))
    writeProg = 0; indicatorStr = "%s ... "%prefix
    if doprint: print(indicatorStr,end="\r")
    try: os.stat(fullpath+_FILEDWN_PART_EXT) # Instead of writing to the file directly …
    except: pass
    else: os.remove(fullpath+_FILEDWN_PART_EXT) # … write to a part file …
    with open(fullpath+_FILEDWN_PART_EXT,"xb") as outfile:
        while True:
            buffer = u.read(4096)
            if not buffer: break
            
            writeProg += len(buffer)
            outfile.write(buffer)
            if doprint: print(indicatorStr + ("("+"{0}/{1}"*showsize+"{2:.1%}"*(not showsize)+")").format(mkSzFmt(writeProg, "%.1f", 1), mkSzFmt(contentLength, "%.1f", 1), writeProg/contentLength),end="    \r")
        outfile.flush()
    outfile.close()
    if newLine and doprint: print("")
    fileMove(fullpath+_FILEDWN_PART_EXT, fullpath) # … and then replace the real file, if download succeeded.
    return 0

# Convenience function - Bytes -> *iB
# fr, Windows says MB but it's MiB, cuz Windows is a stinky :P
def mkSzFmt(size:int, fmts:str, lim:int=0):
    szstr=["bytes", "KiB", "MiB", "GiB"]; szpow:int=0
    nsz:float=size
    while abs(nsz)>=2048 or szpow<lim: nsz=nsz/1024; szpow += 1
    return fmts%nsz + " %s"%szstr[szpow]

# Ensure the version.bin wasn't tampered with
def ctgpververify(s:str)->bool:
    p="0123456789." # decimal + dot
    for i in range(len(s)):
        if p.find(s[i])<0: return False
    l=p.split(".") # maj.min / maj.min.mic (Pablo, correct me when you change)
    if len(l)<2 or len(l)>3: return False
    return True

# Split changelog in list, whereas the inner tuples are:
# (versionNumber, changelogText)
def splitChangelogData(filecnt:str):
    mode=0; arr=[]; vern=""; chng=""; char=""

    # Strip empty lines used for the official updater
    while filecnt.find(": :")>=0: filecnt=filecnt.replace(": :",":")
    while filecnt.find("::")>=0: filecnt=filecnt.replace("::",":")

    for idx in range(len(filecnt)):
        char=filecnt[idx]
        
        if char==":":
            mode+=1
            if mode>1: chng += "\n"
            continue
        if char==";":
            arr.append((vern,chng))
            vern=""; chng=""; mode=0
            continue
        
        if mode==0:
            vern += char
        else:
            chng += char
            
    if mode>0: arr.append((vern,chng))
    
    # Incase I missed empty lines, strip them out
    while arr.count(("","")): arr.remove(("",""))
    
    return arr

# Self-explanatory
def parseAndSortDlList(dll:list):
    global totalDownloadSize, shownDlTotal
    fileN=[]; fileM=[]; fileV=[]; newDl=[]; oldf=""
    filemode=_FILELIST_METHODS

    for i in range(len(dll)):
        ms=dll[i][0]; mf=dll[i][1]; mv=dll[i][2]

        if ms=="S":
            totalDownloadSize = int(mf[1:])
        else:
            fileNC=-1
            try: 	fileNC=fileN.index(mf)
            except:
                fileN.append(mf); fileM.append(ms); fileV.append(mv)
            else:
                fileN.pop(fileNC); fileM.pop(fileNC); fileV.pop(fileNC)
                fileN.append(mf); fileM.append(ms); fileV.append(mv)
            oldf=""
    
    for i in range(len(fileN)):
        if fileM[i]=="M": shownDlTotal += 1
        newDl.append(FileListEntry(fileV[i], fileM[i], fileN[i]))

    return newDl

def findCVerInCList(lst:list,ver:str):
    for idx in range(len(lst)):
        if lst[idx][0]==ver: break
    else: return 0 # Break out, you're too outdated, mate.
    return idx

# Trying to automate stuff, like the GUI
def scanForNintendo3DSSD()->list:
        try:
            mount_points = psutil.disk_partitions()
            candidates = []
            for m in mount_points:
                try:
                    if (os.path.exists(os.path.join(m.mountpoint, "Nintendo 3DS"))):
                        candidates.append(m.mountpoint)
                except:
                    pass
            return candidates
        except:
            pass

def showTooInstallMsg()->None:
    print("""
Please install the new launcher CIA.
  Open FBI and select SD > CTGP-7 > cia > CTGP-7.cia > Install CIA
""")
    input("Press any key to continue.")

### Entrypoint
if __name__ == "__main__":
    appProgress = 0; totalDownloadSize = 0
    confidence2Install = 0; deviceSussy = False
    shownDlTotal = 0; shownDlCounter = 0
    dlCounter = 0; dlTotal = 0; usrCancel = False
    fileMng_OldFileName = "" # New way I will treat "F"
    versionToUpdateTo = ""; tooInstalling = False
    updateFlistPrefix = ""; dlExcept = ""

    print("CTGP-7 Update/Installation Tool v1.1.2")

    try:
        if len(argv)>1 and argv[1].upper()!="INSTALL":
            installPath = argv[1]
            # User already supplied path
        else:
            # if not, try finding SD Card ourselves...
            candidates = scanForNintendo3DSSD()
            if len(candidates)==1:
                installPath=candidates[0]
                print("""Found SD Card: %s
    If this path is not correct, press Ctrl+C and specify
    the path as an argument.\n"""%installPath)
            elif len(candidates):
                print("Detected amount of SD Cards: {}\n".format(len(candidates)))
                for i in candidates:
                    try: os.stat(os.path.join(i, "CTGP-7"))
                    except: j=""
                    else: j=" [installed]"
                    print("{}{}".format("..."*(len(i)>32)+i[-32:], j))
                print("\nPlease specify as an argument, which SD Card you would like.")
                exit(2)
            else:
                print("""No SD Card found or path specified.

    If you want to use the automatic detection,
    make sure the SD Card is mounted.""")
                exit(3)

        for i in range(1,len(argv)):
            if argv[i].upper()=="INSTALL": confidence2Install = 2; break
        installPath = os.path.realpath(installPath).replace("\\","/")
        if installPath[-1]=="/": installPath=installPath[:-1]
        if installPath[-6:]=="CTGP-7": installPath=installPath[:-7]

        if not checkForValidSD(installPath):
            raise Exception(_STR_USERABORT)
        print("\nPreparing...")
        
        # Get base URL
        for dlAttempt in range(_DL_ATTEMPT_TOTALCNT):
            try: baseURL = urlopen(_BASE_URL_DYN_LINK, timeout=10).read().decode("utf8")
            except KeyboardInterrupt: usrCancel = True; break
            except Exception as dlExcept: pass
            else: break
        else: raise Exception("Failed preparing the updater:\n{}".format(dlExcept))
        if usrCancel: raise Exception(_STR_USERABORT)
        baseURL = baseURL.strip()
        
        # Get URL for file lists
        url = baseURL+_UPDATER_FILE_URL
        for dlAttempt in range(_DL_ATTEMPT_TOTALCNT):
            try: updateFlistPrefix = downloadWithIndicator(url).decode("utf8").strip()
            except KeyboardInterrupt: usrCancel = True; break
            except Exception as dlExcept: pass
            else: break
        else: raise Exception("Failed obtaining the latest version:\n{}".format(dlExcept))
        if usrCancel: raise Exception(_STR_USERABORT)
        
        # Make folders
        os.makedirs(installPath+"/3ds",exist_ok=True)
        os.makedirs(installPath+"/CTGP-7",exist_ok=True)
        
        # Obtain changelog and parse it …
        appProgress = 1
        url = baseURL+_UPDATER_CHGLOG_FILE; curver = 0
        for dlAttempt in range(_DL_ATTEMPT_TOTALCNT):
            try: changelog = splitChangelogData(downloadWithIndicator(url).decode("utf8"))
            except KeyboardInterrupt: usrCancel = True; break
            except Exception as dlExcept: pass
            else: break
        else: raise Exception("Failed obtaining the changelog:\n{}".format(dlExcept))
        if usrCancel: raise Exception(_STR_USERABORT)
        
        # … then ensure the current version is supported (or file doesn't exist/was changed)
        try: os.stat(installPath+_VERSION_FILE_PATH)
        except: confidence2Install=True; deviceSussy = True
        else:
            configBinFD = open(installPath+_VERSION_FILE_PATH,"rb")
            configBinary = configBinFD.read().decode("utf8")
            curver = findCVerInCList(changelog, configBinary)
            configBinFD.close()
            versionToUpdateTo = changelog[-1][0]
            if len(configBinary)<2 or not ctgpververify(configBinary) or curver <= 0:
                deviceSussy = True
                if confidence2Install<1: confidence2Install=1
            elif confidence2Install:
                print("""\
    You already have a valid CTGP-7 installation.

    Proceeding will wipe this installation.
    (The save files will be backed up if available.)
    """)
                try: a=input("Continue anyway? [Y/N] ").upper()[0]=="Y"
                except: a=False
                if not a: raise Exception(_STR_USERABORT)
        
        # We're sure to update or reinstall (if user wants to continue)
        print("Taking action: "+("Update","(Re-)Install")[bool(confidence2Install)])
        flist_presort = []
        
        if confidence2Install:
            if deviceSussy and confidence2Install!=2:
                print("""You're about to reinstall CTGP-7.
    An update is not feasible for the following potential reasons:

        - There is no CTGP-7 installation located here.
        - Your installation is incredibly outdated.
        - The CTGP-7 installation might be corrupted or tampered with.
    """)
                try: a=input("Continue anyway? [Y/N] ").upper()[0]=="Y"
                except: a=False
                if not a: raise Exception(_STR_USERABORT)
            elif deviceSussy and confidence2Install==2:
                print("""You're choosing to reinstall CTGP-7.

    I recommend this, as this I think the installation is broken.
    If you have a save file, it will be backed up.
    """)
                try: a=input("Continue anyway? [Y/N] ").upper()[0]=="Y"
                except: a=False
                if not a: raise Exception(_STR_USERABORT)
            
            # Backing up save, if it exists…
            srcfolder = os.path.join(installPath, "CTGP-7", "savefs")
            backupfolder = os.path.join(installPath, "CTGP-7savebak")
            if (os.path.exists(srcfolder)):
                if (os.path.exists(backupfolder)):
                    shutil.rmtree(backupfolder)
                os.rename(srcfolder,backupfolder)
                print("\nThe backup of the CTGP-7 save data is found in:\n%s"%backupfolder)
            
            # get list of files to download
            url = baseURL+_INSTALLER_FILE_DIFF
            for dlAttempt in range(_DL_ATTEMPT_TOTALCNT):
                try: installerList = downloadWithIndicator(url).decode("utf8")
                except KeyboardInterrupt: usrCancel = True; break
                except Exception as dlExcept: pass
                else: break
            else: raise Exception("Failed preparing installation:\n{}".format(dlExcept))
            if usrCancel: raise Exception(_STR_USERABORT)
            
            # what's the latest version to use?
            url = baseURL+_LATEST_VER_LOCATION
            for dlAttempt in range(_DL_ATTEMPT_TOTALCNT):
                try: versionToUpdateTo = downloadWithIndicator(url).decode("utf8")
                except KeyboardInterrupt: usrCancel = True; break
                except Exception as dlExcept: pass
                else: break
            else: raise Exception("Failed obtaining the latest version:\n{}".format(dlExcept))
            if usrCancel: raise Exception(_STR_USERABORT)
            
            # Parse the list.
            installerList=installerList.split("\n")
            for i in installerList:
                if i=="": break
                flist_presort.append((i[0],i[1:],0))
                
            print("\nRemoving the previous installation...")
            shutil.rmtree(os.path.join(installPath, "CTGP-7"))
            
        else:
            a=False; print("Current version: %s"%configBinary)
            
            # Up-to-date already, quit immediately
            if curver == len(changelog)-1:
                fileDelete(installPath+_PENDINGUPDATE_PATH)
                print("No updates available at this time. Try again later.")
                exit(0)
            
            # Not up-to-date, but is there an update pending?
            try:
                os.stat(installPath+_PENDINGUPDATE_PATH)
            
            except: # if not…
                
                # Gather all file lists up to latest version …
                fmax = len(changelog) - curver; fliststr=b''
                for i in range(curver, len(changelog)):
                    print("({:6.1%}) Searching for updates...".format((i-curver)/fmax),end="\r")
                    for dlAttempt in range(_DL_ATTEMPT_TOTALCNT):
                        try: fliststr = downloadWithIndicator(updateFlistPrefix % changelog[i][0])
                        except KeyboardInterrupt: raise Exception(_STR_USERABORT)
                        except Exception as dlExcept: pass
                        else: break
                    else: raise Exception("Failed preparing the update:\n{}".format(dlExcept))
                    flistprs=fliststr.decode("utf8").split("\n")
                    for j in flistprs:
                        if j=="": break
                        flist_presort.append((j[0],j[1:],i))
                print("Got file lists!"+" "*28) # Windows doesn't like escape codes much
                print("\nThe update to {} is ready!".format(versionToUpdateTo))
                try: a=input("Would you like to continue? [Y/N] ").upper()[0]=="Y"
                except: a=False
                if not a: raise Exception(_STR_USERABORT)
            else: # update is pending, so …
            
                # Open file and get back the file list …
                pendupdf = open(installPath+_PENDINGUPDATE_PATH,"rb")
                
                dlTotal, = struct.unpack("<I",pendupdf.read(4))
                
                versionToUpdateTo = b''
                while True: # FIXME: no verification, trusting file as-is; will likely backfire
                    char = pendupdf.read(1)
                    if char != b'\0': versionToUpdateTo += char
                    else: break
                versionToUpdateTo = versionToUpdateTo.decode("utf8")
                
                # Asking user to continue update
                print("A pending update to {} was detected!".format(versionToUpdateTo))
                try: a=input("Would you like to continue that update? [Y/N] ").upper()[0]=="Y"
                except: a=False
                if not a: raise Exception(_STR_USERABORT)
                
                a = pendupdf.read()
                pendupdf.close(); j=0
                
                # FIXME: Cheap approach; why not making it a standalone function?
                for i in range(dlTotal):
                    c = FileListEntry()
                    j = c.importFromPend(a,j)
                    flist_presort.append((c.fileMethod, c.filePath, c.forVersion))

        flist = parseAndSortDlList(flist_presort); appProgress=2
        
        # My code is so bad, I keep messing up. :weary:
        # If download size was specified, check against current storage space
        storageSpace = psutil.disk_usage(installPath).free
        if totalDownloadSize > 0 and storageSpace < (totalDownloadSize + _SLACK_FREE_SPACE):
            raise Exception("Not enough space available.\nAdditional {} required to proceed.".format(mkSzFmt(totalDownloadSize + _SLACK_FREE_SPACE - storageSpace, "%.1f", 1)))
        
        dlTotal = len(flist)
        for dlCounter in range(dlTotal):
            flist[dlCounter].perform()
            if usrCancel: raise Exception(_STR_USERABORT)
        
        # Download done, check for tooInstall
        appProgress=3
        try: os.stat(installPath+_TOOINSTALL_PATH+".3dsx")
        except: pass
        else:
            shutil.copyfile(installPath+_TOOINSTALL_PATH+".3dsx", installPath+_TOOINSTALL_HB_PATH+".3dsx")
            fileMove(installPath+_TOOINSTALL_PATH+".3dsx", installPath+_TOOINSTALL_CIA_PATH+".3dsx")

        try: os.stat(installPath+_TOOINSTALL_PATH+".cia")
        except: pass
        else:
            fileMove(installPath+_TOOINSTALL_PATH+".cia", installPath+_TOOINSTALL_CIA_PATH+".cia")
            tooInstalling = True

        # Cleaning up and setting version
        fileDelete(installPath+_PENDINGUPDATE_PATH)
        fileDelete(installPath+_VERSION_FILE_PATH)
        configBinFD = open(installPath+_VERSION_FILE_PATH,"xb")
        configBinFD.write(versionToUpdateTo.encode("utf8"))
        configBinFD.close()
        appProgress=4
        print(("Update","Installation")[bool(confidence2Install)]+" successful.")
        if tooInstalling: showTooInstallMsg()
        exit(0)
    except (KeyboardInterrupt, EOFError):
        pass # Don't throw weird errors, just exit.
    except Exception as e:
        print("An error has occured: %s"%e)

    if appProgress>=2 and appProgress<4:
        
        print("\nCleaning up...")
        
        # If update failed or user aborted, save the file lists in pendingupdate.bin
        os.makedirs(os.path.join(installPath,"CTGP-7","config"),exist_ok=True)
        a=os.path.join(installPath+"CTGP-7")
        fileDelete(a+flist[dlCounter].filePath+_FILEDWN_PART_EXT)
        if not confidence2Install:
            a=installPath+_PENDINGUPDATE_PATH
            fileDelete(a+_FILEDWN_PART_EXT)
            pendupdf = open(a+_FILEDWN_PART_EXT,"xb")
            pendupdf.write(struct.pack("I",dlTotal-dlCounter))
            pendupdf.write(versionToUpdateTo.encode("utf8")+b'\0')
            for i in range(dlCounter, dlTotal):
                pendupdf.write(flist[i].export())
            pendupdf.close()
            fileMove(a+_FILEDWN_PART_EXT,a)

    if tooInstalling: showTooInstallMsg()
    exit(1) # An error had occured, or user exited
