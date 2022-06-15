# CTGP-7 Update Tool

This is a work-in-progress Python script mimicking CTGP-7's official updater, based on own observations, analysis of the [archived launcher's source code](https://github.com/PabloMK7/CTGP-7_Launcher) and lots of help from PabloMK7 himself.

Supported platforms: Linux, Windows

## GUI version

**Warning:** The GUI version currently is only for (re-)installing CTGP-7.

Modules needed: `pyside2`, `psutil`

(Should you not have these modules, install them with `pip install pyside2 psutil`)

Simply launch `main.py`.
On Linux, you might need to call it in a terminal using `python main.py`.

## Console version

The console version allows updating an existing CTGP-7 installation and also performing a fresh installation.

Modules needed: `psutil`

(Should you not have this module, install it with `pip install psutil`)

The script is named `ctgp7ConsoleUpdater.py`.

The script will automatically check for the SD Card to install/update on. Make sure you inserted the SD Card before running this tool.
(On Linux, you might have to manually mount the SD Card, if your desktop environment isn't doing it automatically.)

Should there be multiple Nintendo 3DS SD Cards mounted, or your SD Card is not detected, please specify the path to the SD Card (such as `E:` (Windows) or `/media/user/SDCARD` (Linux)) as an argument. (Drag'n'dropped folders are also supported)

Specify `install` as an argument to ignore checking for updates and (re)install the mod.
