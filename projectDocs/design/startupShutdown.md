# Aslan Starting and Exiting outline

## Ways to start Aslan:

1. For an installed copy:
    1. Ctrl+Alt+N (Desktop shortcut)
        * test: `startupShutdownAslan.Starts from desktop shortcut`
    1. Automatically via Ease of Access on the Windows sign-in screen (at boot or signing out of a previous session)
    1. Automatically via Ease of Access on User Account Control (UAC) screens
    1. Automatically by Ease of Access after signing in to Windows
1. For an installed copy, portable copy, installer:
    1. An exiting instance of Aslan starting a new process (see shutting down procedures)
    1. By running the exe.
        * This can be triggered by a user or external process such as an existing Aslan instance
        * test: `startupShutdownAslan.Starts`
1. For source: eg runaslan.bat

## Aslan can be shutdown by:

1. UI within Aslan, with and without an ExitDialog prompt (uses `triggerAslanExit`):
    1. Aslan+q
        * test: `startupShutdownAslan.Quits from keyboard, Restarts`
    1. An input gesture to restart
    1. After changing some settings (eg installed add-ons or UI language), user prompted on dialog exit.
    1. Via the Aslan menu -> Exit
        * test: `startupShutdownAslan.Quits from menu`
1. A process sending `WM_QUIT`, eg a new Aslan process starting
1. A handled crash (directly causes a new process to start, terminates unsafely)
    * test: `startupShutdownAslan.Restarts on crash, Restarts on braille crash`
1. An unhandled crash (terminates unsafely)
    * requires manual testing/confirmation
1. An external command which kills the process (terminates unsafely)
1. Windows shutting down (terminates unsafely) (uses `wx.EVT_END_SESSION`)

## Manual testing

Check the [manual test guide](../../tests/manual/aslanUI/startupShutdown.md).

## Technical notes

These notes are aimed at developers, wishing to understand technical aspects of the Aslan start and exit.

1. No more than one Aslan process instance should be running at the same time. Interactions with itself could cause severe issues, some (non-exhaustive list) examples of sub-systems where this would be a problem:
   * Aslan config files
   * Global (OS level) keyboard hook
   * Changed / incompatible in-process code
2. As such, we want to be able to detect running instances, cause them to exit, and confirm they have exited.

### Exit hooks/triggers

There are 3 ways that Aslan receives a request to exit:

* From internally calling [triggerAslanExit](#When-exiting-from-triggerAslanExit)
* Receiving [WM_QUIT](#When-exiting-from-WM_QUIT) Windows message
* Receiving [wx.EVT_END_SESSION](#When-exiting-from-wxEVT_END_SESSION) due to Windows session ending

### When exiting from `triggerAslanExit`

* Called from within Aslan.
* A function in the core module
* Only executes the code once, uses a lock and flag to ensure this
* Uses a queue on the main thread to queue a safe shutdown
* Once the queued shutdown starts:
    1. the updateCheck is terminated
    1. watchdog is terminated
    1. globalPlugins and the brailleViewer are terminated, so we can close all windows safely
    1. All wx windows are closed
    1. Now that windows are closed, a new Aslan instance is started if requested

### When exiting from `WM_QUIT`

* [A Windows Message](https://docs.microsoft.com/en-us/windows/win32/winmsg/wm-quit) received from an external process, such as another Aslan process.
* Aslan accepts `WM_QUIT` messages from other processes and creates a [named window](https://docs.microsoft.com/en-us/windows/win32/learnwin32/creating-a-window#creating-the-window) that can be discovered.
* `WM_QUIT` is handled by `wx`, which force closes all wx windows (other UI features like the systray icon are not windows, and remain) and then exits the main loop.
`triggerAslanExit` is a more expansive check than how wxWidgets handles `WM_QUIT`
* We subsequently run `triggerAslanExit` to ensure that clean up code isn't missed, and pump the queue to execute it.
* Using a custom message has been considered:
  * Would allow custom handling (eg just `triggerAslanExit`)
  * Unfortunately, older Aslan versions will only be aware of `WM_QUIT`, so we'd need to send `WM_QUIT` to these versions.
  * Sending the custom message, waiting for a timeout, then sending `WM_QUIT` adds a significant wait time
  * Identifying the running version (to selectively send the message) requires maintaining 2 message windows in Aslan (one for legacy behaviour) and adds complexity

### When exiting from `wx.EVT_END_SESSION`

* This is a [wxCloseEvent](https://docs.wxwidgets.org/3.0/classwx_close_event.html) triggered by a Windows session ending.
* On `wx.EVT_END_SESSION`, we save the config and play the exit sound.
* Other actions are not performed as we have limited time to perform an action for this event.
  * Aslan is expected to run as long as possible during the sign out process.
  * This is achieved through the [Windows API](https://docs.microsoft.com/en-us/windows/win32/api/processthreadsapi/nf-processthreadsapi-setprocessshutdownparameters), by setting the shutdown priority to the lowest reserved value for non-system applications, `0x100`.
  * [SHUTDOWN_NORETRY](https://docs.microsoft.com/en-us/windows/win32/api/processthreadsapi/nf-processthreadsapi-setprocessshutdownparameters) ensures that Aslan does not show up in the blocked shutdown list dialog.
    If it were, the user would have no way of reading the dialog and fixing the issue.

### Replacing an existing Aslan instance

With the requirement to only allow a single instance of Aslan, a new Aslan process must be able to replace an existing Aslan process.
Aslan will exit correctly in response to a [`WM_QUIT`](#When-exiting-from-WM_QUIT) Windows message, but the process must first be detected / identified in order to send the message.
For new Aslan process to detect an existing Aslan process, a named [message window](https://docs.microsoft.com/en-us/windows/win32/learnwin32/creating-a-window#creating-the-window) is used.
A new Aslan process searches for an existing Aslan window, and if it is detected, sends `WM_QUIT`.
The message window is created late during the start up, and destroyed early in exit and is not perfectly indicative of whether or not an Aslan process is running.
As such, we have a [MutEx](#MutEx) that ensures a newly started process blocks until any previous Aslan has finished exiting.

### MutEx

To confirm that another Aslan process is not running,
a [MutEx](https://docs.microsoft.com/en-us/windows/win32/sync/mutex-objects) is owned by the Aslan process.
Aslan will be blocked from starting until it can acquire the MutEx.
If it can not acquire the MutEx within a timeout, startup is aborted.
This is acquired as soon as possible and released by Aslan as late as possible.
When the Aslan process exits abnormally, Windows will release the MutEx.

### Unsafe restart

Called in the event of a crash. Exiting Aslan safely in the event of a crash could be improved, but it is limited as we cannot rely on other threads running or the state of Aslan.
