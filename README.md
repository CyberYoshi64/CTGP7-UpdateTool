# CTGP-7 Updater Script

This is a work-in-progress Python script mimicking CTGP-7's official updater, based on own observations, analysis of the [archived launcher's source code](https://github.com/PabloMK7/CTGP-7_Launcher) and a bit of help from PabloMK7 himself.

Supported platforms: Linux, Windows

Modules needed: `requests`, `time`

Syntax: `python ctgp7upd.py [folder] [-h] [-p] [-s] [-a]`

- `folder` — Path to a valid CTGP-7 folder to update in
- `-h` — Show this help
- `-p` — Show full path of downloaded file
- `-s` — Show files removed/renamed (Name will change color appropriately)
- `-a` — Same behaviour as `-p -s`

If specifying `folder`, it can be relative, but it was intended to be absolute through drag'n'dropping the CTGP-7 folder.

If `folder` isn't specified as an argument, the script will ask for a valid path, which can also be used to drag'n'drop the CTGP-7 folder in the prompt or enter the path to the CTGP-7 folder, inclusive.

If it doesn't work and you can help with the script, please file an issue. **Pull requests could be used, but cannot be merged, due to the way my Git setup works**

## Author notes

### Where's my progress bar?

Standard Python `requests` do not make use of callback/intermediary functions while they're processing. Unless I move to another module and learn its command set, this is the best I can do.

### How updates exactly work in this script

The script first downloads the changelog, reads all the version numbers and dedicated info into a tuple list, to then check the local version against the list.

From there, if the version is outdated, I read all file lists up to the latest version to then download and insert in the main loop.

After that's done, I edit the version file to reflect the changes appropriately. (Don't confuse the official launcher to redownload the update.)

However, if the update includes a new launcher package, the user is told to install the new launcher themself. ***This script is not capable to install the CIA for the user. Only the 3DSX is able to be copied over, which this tool isn't doing either, at the moment.***

### Why is its output so confined and clean?

While I originally wanted this to be more duck-taped, PabloMK7 kicked my motivation to make this updater as true to the official updater as I can, this also includes the console output looking clean.

### What on earth is this code looking like?

The way I coded it, is quite rubbish, but I'll refine the codeflow over time.
