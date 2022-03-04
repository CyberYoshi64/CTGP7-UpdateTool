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

**Warning:** The console version currently is only for updating an existing CTGP-7 installation.

Modules needed: `requests`

(Should you not have this module, install them with `pip install requests`)

The script is located in the `originalScript` folder. Use the `-h` switch for help on the script syntax.
