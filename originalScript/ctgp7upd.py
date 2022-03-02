#!/usr/bin/python3

import os, requests, time#, locale, glob
from sys import argv
import util.display as display

SCRIPT_FOR_CONSOLE = False # False if you run in a wrapper

_UPDTEMPDL_EXTENSION = ".updpt"
_DL_ATTEMPT_TOTALCNT = 30
_UPDATE_BASE_URL = "https://raw.githubusercontent.com/PabloMK7/CTGP-7updates/master"
_UPDATE_BASE_URL2= "https://github.com/PabloMK7/CTGP-7updates/releases/download/v"
_UPDATE_URL_EXTPART = "/updates/data"
_TOOINSTALL_FNAME = "tooInstall"
_TARGET_NAME = "CTGP-7"
_VERSION_FILE_PATH = "/config/version.bin"
_UPDATE_FILEFLAGMD_COLOR = ["\x1b[0;92m","\x1b[0;91m","\x1b[0;94m","\x1b[0;34m"]

_UPDATE_FILEFLAGMD = ["M","D","T","F"] # F is not treated like a method, just as a reminder for T. F in the chat bois indeed.

def mkfolders(fol:str):
	import os
	g=fol[0:fol.rfind("/")]
	s=""; j=fol.find("/")+1
	while True:
		j=fol.find("/",j)+1
		if j==-1: break
		s=fol[0:j-1]
		try: os.mkdir(s)
		except OSError as error: pass
		if s==g: break


# size is byte count, fmt follows printf scheme
def mkSzFmt(size:int, fmts:str):
	szstr=["bytes", "KiB", "MiB", "GiB"]; szpow:int=0
	nsz:float=size
	while abs(nsz)>=1024: nsz=nsz/1024; szpow += 1
	return fmts%nsz + " %s"%szstr[szpow]

# Output: zero: ok | non-zero: invalid
def ctgpververify(s:str):
	p="0123456789." # decimal + dot
	for i in range(len(s)):
		if p.find(s[i])<0: return 1
	l=p.split(".") # maj.min / maj.min.mic (Pablo, correct me when you change)
	if len(l)<2 or len(l)>3: return 1
	return 0

def iff(x,i,o):
	if x: return i
	return o

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

# "F" is dealt with here
def parseAndSortDlList(dll:list):
	global dlCounter
	fileN=[]; fileM=[]; fileO=[]; newDl=[]; oldf=""
	dlCounter=0; filemode=_UPDATE_FILEFLAGMD

	for i in range(len(dll)):
		ms=dll[i][0]; mf=dll[i][1]

		if ms=="F":
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
			if fileM[i]=="M": dlCounter += 1
			newDl.append((filemode.index(fileM[i]), fileN[i], fileO[i]))

	return newDl

def findCVerInCList(lst:list,ver:str):
	for idx in range(len(lst)):
		if lst[idx][0]==ver: break
	else: return 0 # Break out, you're too outdated, mate.
	return idx

#sysloc:str = locale.getlocale()[0] # No idea how to deal with encodings

# Useful link, helped me with the ANSI codes:
# https://gist.github.com/fnky/458719343aabd01cfb17a3a4f7296797

def fatErr(idx:int, fn:str="", fo:str=""):
	strl=["""
File {} couldn't be downloaded.

Please make sure you're able to connect to GitHub and try again later.
""".format(fn),"""
Failed relocating a file.

From: {}
To: {}

This may stem from SD Card corruption or a heavily outdated build.
It's recommended to reinstall CTGP-7 at this point.
""".format(fo, fn),"""
The file method for {}
is unknown.

Is the file list corrupted, or did I miss a method?
Please contact CyberYoshi64 about this.

By the way, the update therefore fails.
""".format(fn),"""
The folder specified does not contain a valid CTGP-7 installation.

The version is invalid or the folder is not a CTGP-7 installation.

Have you specified the correct folder? Have you even installed CTGP-7?
I will not guess; the update is aborted.
""".format(fn, fo)]
	try:
		display.clog(strl[idx])
	except: display.clog("An unknown error occured. Please try again.")
	appexit(1)

def appexit(r:int):
	global mainfolder
	if SCRIPT_FOR_CONSOLE: input("Press any key to continue... ")
	try: os.remove(mainfolder+"/changelog.txt")
	except: pass
	display.cexit(); exit(r)

def dlErrDesc(): global rep; return "Attempt "+str(rep+1)+"/"+str(_DL_ATTEMPT_TOTALCNT)

def ScreenDisplay():
	global dlList, dlCounter, i, dlObtainedCnt, verf
	lastver=verf[len(verf)-1][0]
	fnm:str=dlList[i][1]
	# Version: from → to
	display.clog("""\
Updating to {}
({}/{}) {}

{}""".format(lastver, dlObtainedCnt, dlCounter, fnm, dlErrDesc()))

def main():
	global mainfolder, ses, dlList, dlCounter, dlObtainedCnt
	global verf, vers, veri, rep, tooInstalled, fSizeOverall
	global fSizeAdd, fSizeRmv
	
	try: os.mkdir(mainfolder)
	except: pass

	try: verf=open(mainfolder+_VERSION_FILE_PATH)
	except: fatErr(3)
	else:
		vers=verf.read(); verf.close()
		if len(vers)<3 or len(vers)>7: fatErr(3)
		if ctgpververify(vers): fatErr(3)
		display.clog("CTGP-7 version detected: "+vers)

	display.clog("Searching for updates...")

	url=_UPDATE_BASE_URL+"/updates/changeloglist"

	dl=ses.get(url)
	if not dl.ok:
		display.clog("\x1b[2KFailed getting changelog. Cannot update.")
		display.clog("Please try again later.")
		exit(1)

	verf=splitChangelogData(dl.text)
	veri=findCVerInCList(verf,vers)
	
	if SCRIPT_FOR_CONSOLE:
		try: os.stat(mainfolder+"/changelog.txt")
		except: pass
		else: os.remove(mainfolder+"/changelog.txt")
		of=open(mainfolder+"/changelog.txt","xb")
	
		for i in range(veri+1,len(verf)):
			of.write(bytes(""" --- Changelog for {} :
	
	{}
	
	""".format(verf[i][0],verf[i][1]),"utf8"))
			of.flush()
	
	percv0=len(verf)-veri-1
	for i in range(veri+1,len(verf)):
		url=_UPDATE_BASE_URL2+verf[i][0]+"/filelist.txt"
		display.clog((" (%5.1f%%)  Obtaining file list for v" % ((i-veri)/percv0*100))+verf[i][0])
		for rep in range(_DL_ATTEMPT_TOTALCNT):
			try: dl=ses.get(url, timeout=5)
			except: display.clog("Fail getting list for {} ({}/{}): timeout/bad connection?".format(verf[i][0], rep + 1, _DL_ATTEMPT_TOTALCNT))
			else:
				if dl.ok: break
				display.clog("Fail getting list for {} ({}/{}): got statcode {}".format(verf[i][0], rep + 1, _DL_ATTEMPT_TOTALCNT, dl.status_code))
			time.sleep(2.0)
		else:
			fatErr(0)
		dl=dl.text.split("\n")
		for i in dl:
			if i=="": break
			dlList.append((i[0],i[1:]))
	dlList=parseAndSortDlList(dlList)
	if len(dlList) or veri<len(verf)-1:
		if SCRIPT_FOR_CONSOLE:
			display.clog("\nGot file lists!\n\nDo you want to update to "+verf[len(verf)-1][0]+" now?")
			of.close(); os.system(iff(os.name!="nt","less "+mainfolder+"/changelog.txt", "notepad "+mainfolder.replace("/","\\")+"\\changelog.txt"))
			input("Press ^C to abort the update, otherwise press Return")
	else:
		display.clog("No updates were found. Please try again later.")
		return 2

	try: ses.get(_UPDATE_BASE_URL)
	except: pass


def doUpdate():
	global dlObtainedCnt, fSizeAdd, fSizeRmv, fSizeOverall
	global dlList, mainfolder, tooInstalled, verf, i
	display.clog("Starting update!")
	for i in range(len(dlList)):
		fmode=dlList[i][0]; fname=dlList[i][1]; fmvo=dlList[i][2]
		f=fname; f1=fmvo; rep=0
		if fmode==_UPDATE_FILEFLAGMD.index("M"):
			dlObtainedCnt += 1
			ScreenDisplay()
		url=_UPDATE_BASE_URL+_UPDATE_URL_EXTPART+fname
		if fmode==0:
			
			mkfolders(mainfolder+f)
			
			while True:
				try: dl=ses.get(url, timeout=5, allow_redirects=0)
				except: pass
				else:
					fSizeAdd += len(dl.content)
					if dl.ok: break
				rep += 1
				if rep >= _DL_ATTEMPT_TOTALCNT: fatErr(0,f,f1)
				ScreenDisplay()
				time.sleep(1.0)
			
			try: fsprop=os.stat(mainfolder+f)
			except: fSizeOverall += fsprop.st_size
			else: fSizeOverall += (len(dl.content) - fsprop.st_size)
			try: os.stat(mainfolder+f+_UPDTEMPDL_EXTENSION)
			except: pass
			else: os.remove(mainfolder+f+_UPDTEMPDL_EXTENSION)
			
			of=open(mainfolder+f+_UPDTEMPDL_EXTENSION,"x+b")
			of.write(dl.content)
			of.flush()
			of.close()
			
			try: os.stat(mainfolder+f)
			except: pass
			else: os.remove(mainfolder+f)
			os.rename(mainfolder+f+_UPDTEMPDL_EXTENSION,mainfolder+f)
		
		elif fmode==1:
			try: fsprop=os.stat(mainfolder+f)
			except: pass
			else:
				fSizeRmv += fsprop.st_size
				fSizeOverall -= fsprop.st_size
				os.remove(mainfolder+f)
		elif fmode==2:
			try: os.stat(mainfolder+f1)
			except: fatErr(1,f,f1)
			else:
				try: os.rename(src=mainfolder+f1, dst=mainfolder+f)
				except: fatErr(1,f,f1)
		else:
			fatErr(2,f,f1)

	try: os.stat(mainfolder+"/cia/"+_TOOINSTALL_FNAME+".cia")
	except: pass
	else:
		# That breaks the fSizeOverall, will add correction later
		tooInstalled=True
		if _TOOINSTALL_FNAME != _TARGET_NAME:
			try: os.stat(mainfolder+"/cia/"+_TARGET_NAME+".cia")
			except: pass
			else: os.remove(mainfolder+"/cia/"+_TARGET_NAME+".cia")
			os.rename(src=mainfolder+"/cia/"+_TOOINSTALL_FNAME+".cia",dst=mainfolder+"/cia/"+_TARGET_NAME+".cia")
			try: os.stat(mainfolder+"/cia/"+_TARGET_NAME+".3dsx")
			except: pass
			else: os.remove(mainfolder+"/cia/"+_TARGET_NAME+".3dsx")
			os.rename(src=mainfolder+"/cia/"+_TOOINSTALL_FNAME+".3dsx",dst=mainfolder+"/cia/"+_TARGET_NAME+".3dsx")

	# Update config/version.bin
	if len(dlList):
		try: os.stat(mainfolder+_VERSION_FILE_PATH)
		except: pass
		else: os.remove(mainfolder+_VERSION_FILE_PATH)
		of=open(mainfolder+_VERSION_FILE_PATH,"x+b")
		of.write(verf[len(verf)-1][0].encode("ascii")); of.flush(); of.close()
	return 0

tmpv:int=0
try: tmpv=argv.index("-h")
except: pass

if tmpv>0:
	display.clog("""CTGP-7 Updater script 1.1

Usage: {} [CTGP7fol] [-h]

CTGP-7fol – Path to CTGP-7 folder
-h - Show this help

This can refer to the CTGP-7 folder on your 3DS's SD Card or
a backup folder on your PC.

If not specified, you'll get a prompt to drag'n'drop the CTGP-7 folder.

This tool acts as close to the official updater, so you have to make
sure, you specify the correct folder, otherwise, no updates will be
performed.""".format(argv[0]))
	exit()

mainfolder:str=""; tmpv=2
if len(argv)>1: mainfolder=argv[1].replace("\\","/") # Windows may use \, but I'm / gang (Python is OK with it)
if len(mainfolder)<5: tmpv=1
ses=requests.session()
dlList=[]; verf=0; vers=0; veri=0; i=0; rep=0; tooInstalled=False
dlCounter=0; oldtermw=0; oldtermh=0; dlObtainedCnt=0
fSizeAdd:int=0; fSizeRmv:int=0; fSizeOverall:int=0

display.cinit()
if tmpv==1 and SCRIPT_FOR_CONSOLE:
	display.clog("The CTGP-7 folder was not specified.\n\nPlease specify the folder to continue.\nOtherwise, press ^C")
	while True:
		try: mainfolder=input("Name > ").strip()
		except (KeyboardInterrupt, EOFError): exit()
		except: pass
		if len(mainfolder)>1 and "'\"".find(mainfolder[0])>=0 and "'\"".find(mainfolder[-1])>=0: mainfolder=mainfolder[1:-1]
		if os.path.exists(mainfolder): break
		display.clog("\nThis folder does not exist. Please make sure you drag'n'drop or otherwise specify the folder correctly")
try:
	display.clog("\x1b[0;0m\x1b[?25h"*(os.name!="nt"))
	if not main():
		if not doUpdate():
			display.clog("Update successful!\n\n{} updated\n{} removed\n{} difference overall".format(mkSzFmt(fSizeAdd,"%9.1f"), mkSzFmt(fSizeRmv,"%9.1f"), mkSzFmt(fSizeOverall,"%+9.1f")))
			if tooInstalled:
				display.clog("""
The launcher was updated.
Please install the new CTGP-7 CIA manually through FBI.

Open FBI and navigate SD > CTGP-7 > cia > {}.cia, then "Install".""".format(_TARGET_NAME))
			if SCRIPT_FOR_CONSOLE: input("\nPress Return to exit.")
except (KeyboardInterrupt, EOFError): # Do not show a weird error for this simple action
	display.clog("The program was interrupted. Update aborted.\nThe installation may be in an inconsistent state,\nif not updated properly.")
	appexit(5)
except (OSError, FileExistsError, FileNotFoundError) as err: # Did I corrupt the SD Card by accident or was it corrupted already?
	display.clog("""An error has occured while dealing with the storage device.

Reason: {}
Context: {}, {}, {}

This could stem from a bad installation or the storage device is corrupted.
Please backup all content on said device to another location.
It's recommended to reformat the device and try again.

If problems persist, please obtain a new storage device or update in the CTGP-7 launcher.
""".format(err.strerror, err.args, err.filename, err.filename2))
	appexit(6)
except (ConnectionError,ConnectionResetError,ConnectionAbortedError,ConnectionRefusedError):
	display.clog("An uncatched connection error has occured. Update aborted.\nIf problems persist, try updating in the CTGP-7 launcher instead.")
	appexit(7)
#except (ValueError, TypeError, IndexError, NotImplementedError):
#	display.clog("Something unexpected has happened. Update aborted.\nIf problems persist, try updating in the CTGP-7 launcher instead.")
#	appexit(8)
#except: fatErr(0xDEADBEEF)

appexit(0)
