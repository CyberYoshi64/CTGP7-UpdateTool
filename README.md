# CTGP-7 Installer

This is a Python application mimicking CTGP-7's official updater, based on own observations, analysis of the [archived launcher's source code](https://github.com/PabloMK7/CTGP-7_Launcher) and lots of help from PabloMK7 himself.

Supported platforms: Linux, Windows

This tool will automatically check for the SD Card to install/update on. Make sure you inserted the SD Card before running this tool.
(On Linux, you might have to manually mount the SD Card, if your desktop environment isn't doing it for you.)

## GUI version

Modules needed: `pyside2`, `psutil`, `urllib3`

(Should you not have these modules, install them with `pip install pyside2 psutil urllib3`)

Simply run `main.py`.
On Linux, you might need to call it in a terminal using `python main.py`.

## Terminal version

Modules needed: `psutil`, `urllib3`

(Should you not have this module, install it with `pip install psutil urllib3`)

Run `terminalMain.py` in a terminal. (duh)

Should there be multiple Nintendo 3DS SD Cards mounted, or your SD Card is not detected, please specify the path to the SD Card (such as `E:` (Windows) or `/media/<user>/SDCARD` (Linux)) with the `-p` argument. (Drag'n'dropped folders are also supported)

To see optional arguments, specify `-h` as an argument.
