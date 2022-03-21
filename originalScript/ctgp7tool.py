#!/usr/bin/python3

import shutil
from urllib.request import urlopen
from sys import argv
import os, struct, psutil, time

_FILELIST_METHODS = ["M","D","T","F","S"] # Modify, Delete, To (rename), From (rename), Storage space required
_BASE_URL_DYN_LINK = "https://ctgp7.page.link/baseCDNURL" # Future-proof, CTGP-7 updates will be on a CDN
_INSTALLER_FILE_DIFF = "installinfo.txt" # Installer
_UPDATER_CHGLOG_FILE = "changeloglist" # Updater
_UPDATER_FILE_URL = "https://github.com/PabloMK7/CTGP-7updates/releases/download/v{}/filelist.txt" # Updater
_FILES_LOCATION = "data" # https://[baseCDN]/data/... - Where the files are located
_LATEST_VER_LOCATION = "latestver" # No idea why Pablo uses this, I can just get it from the changelog
_DL_ATTEMPT_TOTALCNT = 30 # 30 attempts... generous, if I'm honest
_VERSION_FILE_PATH = "/CTGP-7/config/version.bin"
_PENDINGUPDATE_PATH = "/CTGP-7/config/pendingUpdate.bin"
_TOOINSTALL_PATH = "/CTGP-7/cia/tooInstall"
_TOOINSTALL_CIA_PATH = "/CTGP-7/cia/CTGP-7"
_TOOINSTALL_HB_PATH = "/3ds/CTGP-7"
_SLACK_FREE_SPACE = 19851264

# Console-only, have to obnoxiously await any chance for pesky users to abort.
_STR_USERABORT = "The user aborted the operation." # It appears so often, no need to type it out everywhere.

# File List struct from:
# https://github.com/PabloMK7/CTGP-7_Launcher/blob/master/source/updater.c#L15-L20

class FileListEntry:
    def __init__(self, ver=0, method="M", path="/") -> None: # Defaults for whatever reason
        self.filePath = path # File path
        self.forVersion = ver # Effectively useless, only used for compatibility with the launcher
        try: self.fileMethod = method
        except: pass
    
    ## Export struct for pendingUpdate.bin
    def export(self) -> bytes:
        import struct
        return struct.pack("<BI", \
            ord(self.fileMethod),\
            self.forVersion) + \
            self.filePath.encode("utf8") + b'\0'
    
    ## Import from pendingUpdate.bin
    ## @param fdb : Content of file (as bytes object)
    ## @param off : Offset to start reading properties
    ## @return : Offset for next file in list
    def importFromPend(self,fdb,off)->int:
        self.fileMethod = chr(fdb[off])
        self.forVersion, = struct.unpack("<I",fdb[off+1:off+5])
        self.filePath = b''
        for off in range(off+5,len(fdb)):
            if fdb[off]: self.filePath += int.to_bytes(fdb[off],1,"little")
            else: break
        self.filePath = self.filePath.decode("utf8")
        return off+1

    ## Internal use - Return print()-able string
    def debug(self) -> str:
        return self.fileMethod+", "+str(self.forVersion)+", "+self.filePath

    ## Perform the action
    def perform(self) -> int:
        global baseURL, shownDlCounter, shownDlTotal
        global fileMng_OldFileName, usrCancel
        global tooInstalling
        url = baseURL+_FILES_LOCATION+self.filePath
        fout = ""+self.filePath
        if self.fileMethod == "M": # Modified
            for i in range(_DL_ATTEMPT_TOTALCNT):
                try: downloadToFileWIndicator(url, fout,\
                "({}/{}) {}".format(\
                    #shownDlCounter / shownDlTotal,\
                    shownDlCounter+1, shownDlTotal, \
                    fout[fout.rfind("/")+1:]
                ))
                except KeyboardInterrupt: usrCancel=True; break
                except: pass
                else: break
            shownDlCounter += 1
        if self.fileMethod == "D": # Deleted
            try: os.stat(fout)
            except: pass
            else: os.remove(fout)
        if self.fileMethod == "F": # From
            
            # This, as-is, does nothing.
            # Just remember this file to rename it
            # when the next file's method is "T".
            
            fileMng_OldFileName = fout
        if self.fileMethod == "T": # To
            try: os.stat(fout)
            except: pass
            else: # Right here, actually
                os.remove(fout)
                os.rename(fileMng_OldFileName, fout)

# Console only, want to provide some automation in console version too
def checkForValidSD(path:str) -> bool:
    if os.path.exists(os.path.join(path+"/Nintendo 3DS")):
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
    writeProg = 0; indicatorStr = "\x1b[2K"+"%s "%(prefix)+"... "
    if doprint: print(indicatorStr,end="\r")
    block_sz = 8192
    try: os.stat(fullpath+".part") # Instead of writing to the file directly …
    except: pass
    else: os.remove(fullpath+".part") # … write to a .part file …
    with open(fullpath+".part","xb") as outfile:
        while True:
            buffer = u.read(block_sz)
            if not buffer:
                break
            
            writeProg += len(buffer)
            outfile.write(buffer)
            if doprint: print(indicatorStr + ("("+"{0}/{1}"*showsize+"{2:.1%}"*(not showsize)+")").format(mkSzFmt(writeProg, "%.1f", 1), mkSzFmt(contentLength, "%.1f", 1), writeProg/contentLength),end="\r")
    outfile.flush()
    outfile.close()
    if newLine and doprint: print("")
    try: os.stat(fullpath)
    except: pass
    else: os.remove(fullpath)
    os.rename(fullpath+".part", fullpath) # … and then overwrite the actual, if download succeeded.
    return 0

# Convenience function - Bytes -> *iB (get it right, Pablo!)
# fr, Windows says it's MB but it actually MiB, cuz Windows sucks
def mkSzFmt(size:int, fmts:str, lim:int=0):
    szstr=["bytes", "KiB", "MiB", "GiB"]; szpow:int=0
    nsz:float=size
    while abs(nsz)>=1024 or szpow<lim: nsz=nsz/1024; szpow += 1
    return fmts%nsz + " %s"%szstr[szpow]

# Ensure the version.bin wasn't tampered with
def ctgpververify(s:str)->bool:
    p="0123456789." # decimal + dot
    for i in range(len(s)):
        if p.find(s[i])<0: return False
    l=p.split(".") # maj.min / maj.min.mic (Pablo, correct me when you change)
    if len(l)<2 or len(l)>3: return False
    return True

# Split changelog in list, whereas the tuples inside are:
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

# Take an unsorted file list…
def parseAndSortDlList(dll:list):
    global totalDownloadSize, shownDlTotal
    fileN=[]; fileM=[]; fileV=[]; newDl=[]; oldf=""
    filemode=_FILELIST_METHODS

    for i in range(len(dll)):
        ms=dll[i][0]; mf=dll[i][1]; mv=dll[i][2]

        if ms=="S": # New! Needed space estimate (likely install-only)
            totalDownloadSize = int(mf[1:])
        else:
            fileNC=-1
            try: 	fileNC=fileN.index(mf)
            except:
                fileN.append(mf); fileM.append(ms); fileV.append(mv)
            else:
                fileN.pop(fileNC); fileM.pop(fileNC); fileV.pop(fileNC)
                fileN.append(mf); fileM.append(ms); fileV.append(mv)
            oldf="" # Non-rename shouldn't have the reference
    
    for i in range(len(fileN)):
        if fileM[i]=="M": shownDlTotal += 1
        #newDl.append((filemode.index(fileM[i]), fileN[i], fileO[i], fileV[i]))
        newDl.append(FileListEntry(fileV[i], fileM[i], fileN[i]))

    return newDl # … and sort! So simple.

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

### Entrypoint
appProgress = 0; totalDownloadSize = 0
confidence2Install = False; deviceSussy = False
shownDlTotal = 0; shownDlCounter = 0
dlCounter = 0; dlTotal = 0; usrCancel = False
fileMng_OldFileName = "" # New way I will treat "F"
versionToUpdateTo = ""; tooInstalling = False

print("CTGP-7 Update/Installation Tool v1.1")

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
            print("Detected amount of SD Cards: {}\n")
            for i in candidates:
                try: os.stat(i+"CTGP-7")
                except: j=""
                else: j="[installed]"
                print("{}{}".format(\
                    "..."*(len(i)>32)+i[-32:],\
                    j
                ))
            print("\nPlease specify as an argument, which SD Card you would like.")
            exit(2)
        else:
            print("""No SD Card found or path specified.

Make sure that you plugged in your Nintendo 3DS SD Card{}.
if you want to use the automatic detection.""".format(" and mounted it"*os.name!="nt"))
            exit(3)

    for i in range(1,len(argv)):
        if argv[i].upper()=="INSTALL": confidence2Install = True; break
    installPath = os.path.realpath(installPath).replace("\\","/")
    if installPath[-1]=="/": installPath=installPath[:-1]
    if installPath[-6:]=="CTGP-7": installPath=installPath[:-7]

    if not checkForValidSD(installPath):
        raise Exception("User aborted operation.")
    for dlAttempt in range(_DL_ATTEMPT_TOTALCNT):
        try: baseURL = urlopen(_BASE_URL_DYN_LINK, timeout=10).read().decode("utf8")
        except KeyboardInterrupt: usrCancel = True; break
        except Exception as dlExcept: pass
        else: break
    else: raise Exception("Failed preparing the updater:\n{}".format(dlExcept))
    if usrCancel: raise Exception(_STR_USERABORT)
    baseURL = baseURL.strip()
    os.makedirs(installPath+"/3ds",exist_ok=True)
    os.makedirs(installPath+"/CTGP-7",exist_ok=True)
    appProgress = 1
    url = baseURL+_UPDATER_CHGLOG_FILE; curver = 0
    for dlAttempt in range(_DL_ATTEMPT_TOTALCNT):
        try: changelog = splitChangelogData(downloadWithIndicator(url).decode("utf8"))
        except KeyboardInterrupt: usrCancel = True; break
        except Exception as dlExcept: pass
        else: break
    else: raise Exception("Failed obtaining the changelog:\n{}".format(dlExcept))
    if usrCancel: raise Exception(_STR_USERABORT)
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
            confidence2Install = True
        elif confidence2Install:
            print("""\
You already have a valid CTGP-7 installation.

Proceeding will wipe this installation.
(The save files will be backed up if available.)
""")
            try: a=input("Continue anyway? [Y/N] ").upper()[0]=="Y"
            except: a=False
            if not a: raise Exception(_STR_USERABORT)
    print("Preparing to "+("update","install")[bool(confidence2Install)]+" CTGP-7...\n")
    
    flist_presort = []
    
    if confidence2Install:
        if deviceSussy:
            print("""You're about to reinstall CTGP-7.
An update is not feasible for the following potential reasons:

    - There is no CTGP-7 installation located here.
    - The CTGP-7 installation might be corrupted.
    - Critical files for the launcher were modified.
""")
            try: a=input("Continue anyway? [Y/N] ").upper()[0]=="Y"
            except: a=False
            if not a: raise Exception(_STR_USERABORT)
        srcfolder = installPath+"/CTGP-7/savefs"
        backupfolder = installPath+"/CTGP-7savebak"
        if (os.path.exists(srcfolder)):
            if (os.path.exists(backupfolder)):
                shutil.rmtree(backupfolder)
            os.rename(srcfolder,backupfolder)
            print("The backup of the CTGP-7 save is found in:\n%s"%backupfolder)
        url = baseURL+_INSTALLER_FILE_DIFF
        for dlAttempt in range(_DL_ATTEMPT_TOTALCNT):
            try: installerList = downloadWithIndicator(url).decode("utf8")
            except KeyboardInterrupt: usrCancel = True; break
            except Exception as dlExcept: pass
            else: break
        else: raise Exception("Failed obtaining the file lists:\n{}".format(dlExcept))
        if usrCancel: raise Exception(_STR_USERABORT)
        installerList=installerList.split("\n")
        for i in installerList:
            if i=="": break
            flist_presort.append((i[0],i[1:],0))
        storageSpace = psutil.disk_usage(installPath).free
        print("Wiping previous installation..."); shutil.rmtree(installPath+"/CTGP-7")
        if storageSpace < (totalDownloadSize + _SLACK_FREE_SPACE):
            raise Exception("Not enough free space on destination folder.\nAdditional {} are required to proceed with the installation.".format(mkSzFmt(totalDownloadSize + _SLACK_FREE_SPACE - storageSpace, "%.1f", 1)))
        
    else:
        if curver == len(changelog)-1:
            print("You're up-to-date already. No updates can be performed.")
            exit(0)
        try:
            os.stat(installPath+_PENDINGUPDATE_PATH)
        except:
            # When no update is pending.
            fmax = len(changelog) - curver; fliststr=b''
            for i in range(curver, len(changelog)):
                print("\x1b[2K({:.1%}) Obtaining file lists...".format((i-curver)/fmax),end="\r")
                for dlAttempt in range(_DL_ATTEMPT_TOTALCNT):
                    try: fliststr = downloadWithIndicator(_UPDATER_FILE_URL.format(changelog[i][0]))
                    except KeyboardInterrupt: raise Exception(_STR_USERABORT)#usrCancel = True; break
                    except Exception as dlExcept: pass
                    else: break
                else: raise Exception("Failed obtaining the file lists:\n{}".format(dlExcept))
                if usrCancel: raise Exception(_STR_USERABORT)
                flistprs=fliststr.decode("utf8").split("\n")
                for j in flistprs:
                    if j=="": break
                    flist_presort.append((j[0],j[1:],i))
            print("\x1b[2KGot file lists!")
        else:
            pendupdf = open(installPath+_PENDINGUPDATE_PATH,"rb")
            dlTotal, = struct.unpack("<I",pendupdf.read(4))
            versionToUpdateTo = b''
            while True:
                char = pendupdf.read(1)
                if char != b'\0': versionToUpdateTo += char
                else: break
            versionToUpdateTo = versionToUpdateTo.decode("utf8")
            print("A pending update to {} was detected!".format(versionToUpdateTo))
            try: a=input("Would you like to continue that update? [Y/N] ").upper()[0]=="Y"
            except: a=False
            if not a: raise Exception(_STR_USERABORT)
            a = pendupdf.read()
            pendupdf.close(); j=0
            for i in range(dlTotal):
                c = FileListEntry()
                j = c.importFromPend(a,j)
                flist_presort.append((c.fileMethod, c.filePath, c.forVersion))

    flist = parseAndSortDlList(flist_presort)
    appProgress=2
    dlTotal = len(flist) # Convenience variable
    for dlCounter in range(len(flist)):
        flist[dlCounter].perform()
        if usrCancel: raise Exception(_STR_USERABORT)
    appProgress=3
    try: os.stat(installPath+_TOOINSTALL_PATH+".3dsx")
    except: pass
    else:
        shutil.copyfile(installPath+_TOOINSTALL_PATH+".3dsx", installPath+_TOOINSTALL_HB_PATH+"CTGP-7.3dsx")
        os.rename(installPath+_TOOINSTALL_PATH+".3dsx", installPath+_TOOINSTALL_CIA_PATH+".3dsx")

    try: os.stat(installPath+_TOOINSTALL_PATH+".cia")
    except: pass
    else:
        tooInstalling = True
        os.rename(installPath+_TOOINSTALL_PATH+".cia", installPath+_TOOINSTALL_CIA_PATH+".cia")

    try: os.stat(installPath+_PENDINGUPDATE_PATH)
    except: pass
    else: os.remove(installPath+_PENDINGUPDATE_PATH)

    try: os.stat(installPath+_VERSION_FILE_PATH)
    except: pass
    else: os.remove(installPath+_VERSION_FILE_PATH)
    configBinFD = open(installPath+_VERSION_FILE_PATH,"xb")
    configBinFD.write(versionToUpdateTo.encode("utf8"))
    configBinFD.close()
    print(("The update","The installation")[bool(confidence2Install)]+" was successful.")
    if tooInstalling:
        print("""
Please install the new launcher CIA.
  Open FBI and select SD > CTGP-7 > cia > CTGP-7.cia > Install CIA
""")
    input("Press any key to continue.")
    exit(0)
except (KeyboardInterrupt, EOFError):
    pass
except Exception as e:
    print("An error has occured: %s"%e)

print("\nCleaning up...")
if appProgress>=2:
    # If update failed or user aborted, save the file lists in pendingupdate.bin
    os.makedirs(installPath+"/CTGP-7/config",exist_ok=True)
    a=installPath+"/CTGP-7"
    try: os.stat(a+flist[dlCounter].filePath+".part")
    except: pass
    else: os.remove(a+flist[dlCounter].filePath+".part")
    a=installPath+_PENDINGUPDATE_PATH
    try: os.stat(a+".new")
    except: pass
    else: os.remove(a+".new")
    pendupdf = open(a+".new","xb")
    pendupdf.write(struct.pack("I",dlTotal-dlCounter))
    pendupdf.write(versionToUpdateTo.encode("utf8")+b'\0')
    for i in range(dlCounter, dlTotal):
        pendupdf.write(flist[i].export())
    pendupdf.close()
    try: os.stat(a)
    except: pass
    else: os.remove(a)
    os.rename(a+".new",a)

exit(1)