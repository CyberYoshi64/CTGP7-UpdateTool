#!/usr/bin/python3
from CTGP7UpdaterApp.CTGP7Updater import CTGP7Updater
import os, argparse

def logger(data:dict):
    if "m" in data:
        if len(data["m"])<2:
            print("")
        else:
            print(data["m"],end=os.linesep*(data["m"][-1]!="\r"))
    elif "p" in data:
        pass # Ignore it, no progress bar needed for console

def ConsoleConfirmed(message:str):
    print(message)
    try:    return input("[yN]").upper()=="Y"
    except: return False

argprs = argparse.ArgumentParser()
argprs.add_argument("-i", "--install", action="store_true", help="Force a re-install, even is updates are viable.")
argprs.add_argument("-p", dest="path", help="Specify a path to a 3DS SD Card instead of auto-detecting.")
arg = argprs.parse_args()
try:
    _INSTALLER_VERB = {True: "install", False: "update"}
    makeNewInstall = False
    
    print("CTGP-7 Update Tool v1.2")
    if arg.path != None:
        sdPath = arg.path
        print("Using path from argument")
    else:
        sdPath = CTGP7Updater.findNintendo3DSRoot()
        if sdPath == None:
            raise Exception("Cannot determine a suitable SD Card.")
        print("Using path: \"{}\"".format(sdPath))
    
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
    if installPathFlag & 3:
        if not ConsoleConfirmed("""\
There was no valid CTGP-7 installation detected.
If there is one, it appears to be corrupted.
Proceeding will wipe the installation and make a new one.

Do you wish to continue anyway?"""):
            raise Exception("User refused to reinstall the modpack.")
        makeNewInstall = True; installPathFlag &= 3
    updater = CTGP7Updater(makeNewInstall)
    updater.fetchDefaultCDNURL()
    updater.setLogFunction(logger)
    updater.setBaseDirectory(sdPath)
    updater.getLatestVersion()
    updater.loadUpdateInfo()
    updater.verifySpaceAvailable()

    # This question is only for console; for GUI, take the value
    # of installPathFlag and check to verfiy entered path.
    # Console is one-shot.
    if installPathFlag & 4:
        if not ConsoleConfirmed("""\
Proceeding to {}ing to version '{}'.
Do you want to proceed?""".format(_INSTALLER_VERB[updater.isInstaller], updater.latestVersion)):
            raise Exception("User cancelled the installation.")
    else:
        if not ConsoleConfirmed("""\
A pending update to version '{}' was detected.
You must finish this update before starting a new one.
Do you want to proceed?""".format(updater.latestVersion)):
            raise Exception("User cancelled the installation.")

    updater.cleanInstallFolder()
    updater.startUpdate()

    print("""
The installation of version {} was successful.

Make sure to install the following CIA using FBI:
SD > CTGP-7 > cia > CTGP-7.cia
""".format(updater.latestVersion))
except Exception as e:
    print("""
An error has occured:
{}

Should issues persist, ask for help in the
CTGP-7 Discord Server.
Invite: https://discord.com/invite/0uTPwYv3SPQww54l
""".format(e))

try:    input("Press Return to exit the application.")
except: pass