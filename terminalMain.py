#!/usr/bin/python3
from CTGP7UpdaterApp.CTGP7Updater import CTGP7Updater
import os, shutil, argparse

argprs = argparse.ArgumentParser()
argprs.add_argument("-i", "--install", action="store_true", help="Force a re-install, even is updating is viable.")
argprs.add_argument("-p", dest="path", help="Specify a path to a 3DS SD Card instead of trying to auto-detect one.")
argprs.add_argument("-y", "--yes", action="store_true", help="Always answer 'yes'. Use this, only if you know what you're up for.")
arg = argprs.parse_args()

def logger(data:dict):
    if "m" in data:
        if len(data["m"])<2:
            print("")
        else:
            print(data["m"],end=os.linesep*(data["m"][-1]!="\r"))
    elif "p" in data:
        pass # Ignore it, no progress bar needed for console

def ConsoleConfirmed(message:str):
    global arg
    print(message)
    if arg.yes: return True
    try:    return input("[y/N]").upper()=="Y"
    except: return False


try:
    _INSTALLER_VERB = {True: "install", False: "update"}
    makeNewInstall = False; madeSaveBackup = False
    didProcessSucceed = False
    
    print("CTGP-7 Update Tool (Terminal) v1.2")
    if arg.path != None:
        sdPath = arg.path
        print("Using path from argument")
    else:
        sdPath = CTGP7Updater.findNintendo3DSRoot()
        if sdPath == None:
            raise Exception("Cannot determine a suitable SD Card.")
        print("Detected SD Card: \"{}\"".format(sdPath))
    
    if not os.path.exists(sdPath):
        raise Exception("The path '{}' does not exist. Make sure you entered the path correctly.".format(sdPath))
    if not CTGP7Updater._isValidNintendo3DSSDCard(sdPath) and\
    not ConsoleConfirmed("""\
This path does not appear to be that of a SD Card
from a Nintendo 3DS system.
Path chosen: {}

Continue anyway?""".format(sdPath)):
        raise Exception("User cancelled installation.")

    installPathFlag = CTGP7Updater.checkForInstallOfPath(sdPath)
    savefsPath = os.path.join(sdPath, "CTGP-7", "savefs")
    savefsCopy = os.path.join(sdPath, "CTGP-7savebak")

    if not arg.install and (installPathFlag & 3):
        if not ConsoleConfirmed("""\
There was no valid CTGP-7 installation detected.
If there is one, it appears to be corrupted.
Proceeding will wipe the installation and make a new one.

Do you wish to continue anyway?"""):
            raise Exception("User refused to reinstall the modpack.")
        makeNewInstall = True
    
    if arg.install:
        print("!! WARNING: -i/--install specified, forcing a re-install.")
        makeNewInstall = True

    # Console-only; GUI will warn immediately and not take a hold
    # of this value
    if makeNewInstall: installPathFlag &= 3

    updater = CTGP7Updater(makeNewInstall)
    updater.fetchDefaultCDNURL()
    updater.setLogFunction(logger)
    updater.setBaseDirectory(sdPath)
    updater.getLatestVersion()
    updater.loadUpdateInfo()
    updater.verifySpaceAvailable()

    # This question is only for console; for GUI, take the value
    # of installPathFlag and check to verify the entered path.
    # Console is one-shot.
    if (installPathFlag & 4):
        if not ConsoleConfirmed("""\
A pending update to version '{}' was detected.
You must finish this update before starting a new one.
Do you want to proceed?""".format(updater.latestVersion)):
            raise Exception("User cancelled the installation.")
    else:
        if not ConsoleConfirmed("""\
Proceeding to {} to version '{}'.
Do you want to proceed?""".format(_INSTALLER_VERB[updater.isInstaller], updater.latestVersion)):
            raise Exception("User cancelled the installation.")

    if makeNewInstall:
        if os.path.exists(savefsPath):
            try:
                shutil.copytree(savefsPath, savefsCopy)
                madeSaveBackup = True
                print("Your current CTGP-7 save data was backed up in this directory:\n{}".format(savefsCopy))
            except Exception as e:
                if not ConsoleConfirmed("""\
Failed making backup of the save data:
{}

Proceeding will wipe your save data. Continue?""".format(e)):
                    raise Exception("User cancelled installation: save backup failed")

    updater.cleanInstallFolder()
    updater.startUpdate()

    if madeSaveBackup:
        if ConsoleConfirmed("Do you want to restore the save backup done previously?"):
            try:
                shutil.copytree(savefsCopy,savefsPath)
            except:
                print("""\
Failed restoring the backup.
You need to do it manually. Copy from:
{}
To:
{}
""".format(savefsCopy, savefsPath))

    print("""
The installation of version {} was successful.

Make sure to install the following file using FBI on your 3DS:
  SD > CTGP-7 > cia > CTGP-7.cia""".format(updater.latestVersion))
    didProcessSucceed = True
except Exception as e:
    print("""
An error has occured:
{}

Should issues persist, ask for help in the CTGP-7
Discord Server: https://discord.com/invite/0uTPwYv3SPQww54l""".format(e))

if not arg.yes:
    try:    input("Press Return to exit the application.")
    except: pass

exit(not didProcessSucceed)