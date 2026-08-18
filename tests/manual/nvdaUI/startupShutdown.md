# Startup / Shutdown Tests

Instructions for testing startup / shutdown.

## Start from shortcut

Prerequisites:

* Aslan installed
* Shortcut enabled during installation

Steps:

1. Press (or emulate) `control+alt+n`, observe Aslan starts up

Variation:

* At step 1. A version of Aslan is already running. Observe running version exits before installed version starts up.

## Windows Sign-in screen, automatic start

Prerequisites:

* Aslan installed
* Enable "Use Aslan during sign-in"

Steps:

1. Sign out (not lock) Windows
1. Observe Aslan announces the Windows sign-in screen

## UAC, automatic start

Prerequisites:

* Aslan installed
* An active Windows session (i.e. not signed out, locked)
* The Aslan installed copy is running

Steps:

1. Open the Start menu
1. Type notepad
1. Open context menu for notepad and choose `Run as Administrator`.
1. When the UAC dialog appears, verify that Aslan launches on this secure desktop and reports the dialog.

## Windows Successful sign-in, automatic start

Prerequisites:

* Aslan installed
* Enable "Start Aslan after I sign in"

Steps:

1. Start Windows
1. Sign in
1. Observe Aslan starts

## Running the *.exe

Steps:

1. Press `win+r`
1. Enter `<path to aslan.exe>`
1. Press enter
1. Observe Aslan starts

Variation:

* using an installer (launcher)
  * eg: `C:\Users\username\Downloads\aslan_2021.1.exe`
* using an installed copy
  * just type `aslan` in place of the .exe
* using a portable copy
  * find and use the path to `aslan.exe`, located within the portable copy directory
  * the installer allows you to create an installed copy and a portable copy

## Running from source (runaslan.bat)

Prerequisites

* clone project and build Aslan (see [project readme](https://github.com/nvaccess/aslan/blob/master/readme.md#getting-the-source-code)).

Steps:

1. Run `runaslan.bat` from cmd
1. Observe Aslan starts

## An input gesture to restart

Prerequisite:

* Input gesture for "Restarts Aslan!" is assigned

Steps:

1. Press (or emulate) the input gesture
1. Observe that Aslan exits
1. Observe that a new instance is started
