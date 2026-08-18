# A part of NonVisual Desktop Access (Aslan)
# Copyright (C) 2020-2025 NV Access Limited, Łukasz Golonka
# This file may be used under the terms of the GNU General Public License, version 2 or later.
# For more details see: https://www.gnu.org/licenses/gpl-2.0.html

"""Logic for startupShutdownAslan tests."""

from datetime import datetime as _datetime
from collections.abc import Callable as _Callable
from robot.libraries.BuiltIn import BuiltIn

# relative import not used for 'systemTestUtils' because the folder is added to the path for 'libraries'
# imported methods start with underscore (_) so they don't get imported into robot files as keywords
from SystemTestSpy import (
	_getLib,
	_blockUntilConditionMet,
)
from SystemTestSpy.windows import (
	getWindowHandle,
	sendKeyboardEvent,
	waitUntilWindowFocused,
	windowWithHandleExists,
)

# Imported for type information
from robot.libraries.OperatingSystem import OperatingSystem as _OpSysLib

from AssertsLib import AssertsLib as _AssertsLib

import NvdaLib as _aslanLib
from NvdaLib import NvdaLib as _aslanRobotLib

_aslanRobot: _aslanRobotLib = _getLib("NvdaLib")
_opSys: _OpSysLib = _getLib("OperatingSystem")
_builtIn: BuiltIn = BuiltIn()
_asserts: _AssertsLib = _getLib("AssertsLib")


def _getNvdaMessageWindowhandle() -> int:
	return getWindowHandle(windowClassName="wxWindowClassNR", windowName="Aslan")


def _aslanIsRunning() -> bool:
	return bool(_getNvdaMessageWindowhandle())


def Aslan_Starts():
	"""Test that Aslan can start"""
	_builtIn.should_be_true(_aslanIsRunning(), msg="Aslan is not running")


def open_welcome_dialog_from_menu():
	spy = _aslanLib.getSpyLib()
	spy.emulateKeyPress("Aslan+n")
	spy.emulateKeyPress("h")
	spy.emulateKeyPress("l")
	spy.wait_for_specific_speech("Welcome to Aslan")  # ensure the dialog is present.


def open_about_dialog_from_menu():
	spy = _aslanLib.getSpyLib()
	spy.emulateKeyPress("Aslan+n")
	spy.emulateKeyPress("h")
	spy.emulateKeyPress("a")
	spy.wait_for_specific_speech("About Aslan")  # ensure the dialog is present.


def quits_from_menu(showExitDialog=True):
	"""Ensure Aslan can be quit from menu."""
	spy = _aslanLib.getSpyLib()
	_builtIn.sleep(1)
	spy.emulateKeyPress("Aslan+n")
	spy.emulateKeyPress("x", blockUntilProcessed=False)  # don't block so Aslan can exit
	if showExitDialog:
		exitTitleIndex = spy.wait_for_specific_speech("Exit Aslan")

		spy.wait_for_speech_to_finish()
		actualSpeech = spy.get_speech_at_index_until_now(exitTitleIndex)

		_asserts.strings_match(
			actualSpeech,
			"\n".join(
				[
					"Exit Aslan  dialog",
					"What would you like to do?  combo box  Exit  collapsed  Alt plus  d",
				],
			),
		)
		_builtIn.sleep(1)  # the dialog is not always receiving the enter keypress, wait a little for it
		spy.emulateKeyPress("enter", blockUntilProcessed=False)  # don't block so Aslan can exit

	_blockUntilConditionMet(
		getValue=lambda: not _aslanIsRunning(),
		giveUpAfterSeconds=3,
		errorMessage="Aslan failed to exit in the specified timeout",
	)
	_builtIn.should_not_be_true(_aslanIsRunning(), msg="Aslan is still running")


def quits_from_keyboard():
	"""Ensure Aslan can be quit from keyboard."""
	spy = _aslanLib.getSpyLib()
	_builtIn.sleep(1)  # the dialog is not always receiving the enter keypress, wait a little for it

	spy.emulateKeyPress("Aslan+q")
	exitTitleIndex = spy.wait_for_specific_speech("Exit Aslan")

	spy.wait_for_speech_to_finish()
	actualSpeech = spy.get_speech_at_index_until_now(exitTitleIndex)

	_asserts.strings_match(
		actualSpeech,
		"\n".join(
			[
				"Exit Aslan  dialog",
				"What would you like to do?  combo box  Exit  collapsed  Alt plus  d",
			],
		),
	)
	_builtIn.sleep(1)  # the dialog is not always receiving the enter keypress, wait a little longer for it
	_builtIn.should_be_true(_aslanIsRunning(), msg="Aslan is not running")
	spy.emulateKeyPress("enter", blockUntilProcessed=False)  # don't block so Aslan can exit
	_blockUntilConditionMet(
		getValue=lambda: not _aslanIsRunning(),
		giveUpAfterSeconds=5,
		errorMessage="Aslan failed to exit in the specified timeout",
	)
	_builtIn.should_not_be_true(_aslanIsRunning(), msg="Aslan is still running")


def test_desktop_shortcut():
	# Press Control+Alt+N using keybd_event
	VK_CONTROL = 17
	VK_MENU = 18  # Alt key
	VK_N = 78  # 'N' key
	KEYEVENTF_KEYDOWN = 0
	KEYEVENTF_KEYUP = 2

	# Press Control down
	sendKeyboardEvent(VK_CONTROL, 0, KEYEVENTF_KEYDOWN, 0)
	# Press Alt down
	sendKeyboardEvent(VK_MENU, 0, KEYEVENTF_KEYDOWN, 0)
	# Press N down
	sendKeyboardEvent(VK_N, 0, KEYEVENTF_KEYDOWN, 0)
	# Release N
	sendKeyboardEvent(VK_N, 0, KEYEVENTF_KEYUP, 0)
	# Release Alt
	sendKeyboardEvent(VK_MENU, 0, KEYEVENTF_KEYUP, 0)
	# Release Control
	sendKeyboardEvent(VK_CONTROL, 0, KEYEVENTF_KEYUP, 0)

	# Takes some time to exit a running process and start a new one
	waitUntilWindowFocused("Welcome to Aslan", timeoutSecs=7)


def read_welcome_dialog():
	spy = _aslanLib.getSpyLib()
	welcomeTitleIndex = spy.wait_for_specific_speech("Welcome to Aslan")  # ensure the dialog is present.
	spy.wait_for_speech_to_finish()
	actualSpeech = spy.get_speech_at_index_until_now(welcomeTitleIndex)

	_asserts.strings_match(
		actualSpeech,
		"\n".join(
			[
				(
					"Welcome to Aslan  dialog  Welcome to Aslan! Most commands for controlling Aslan require you to hold "
					"down the Aslan key while pressing other keys. By default, the Insert and numpad Insert keys "
					"may both be used as the Aslan key. You can also configure Aslan to use the Caps Lock as the Aslan "
					"key. Press Aslan plus n at any time to activate the Aslan menu. From this menu, you can configure "
					"Aslan, get help, and access other Aslan functions."
				),
				"Options  grouping",
				"Keyboard layout:  combo box  desktop  collapsed  Alt plus  k",
			],
		),
	)
	_builtIn.sleep(1)  # the dialog is not always receiving the enter keypress, wait a little longer for it
	spy.emulateKeyPress("enter")


def Aslan_restarts():
	"""Ensure Aslan can be restarted from keyboard."""
	spy = _aslanLib.getSpyLib()
	spy.wait_for_specific_speech("Welcome to Aslan")  # ensure the dialog is present.
	spy.wait_for_speech_to_finish()
	# Get handle of the message window for the currently running Aslan
	oldMsgWindowHandle = _getNvdaMessageWindowhandle()
	spy.emulateKeyPress("Aslan+q")
	spy.wait_for_specific_speech("Exit Aslan")

	_builtIn.sleep(0.5)  # the dialog is not always receiving the enter keypress, wait a little longer for it
	spy.emulateKeyPress("downArrow")
	spy.wait_for_specific_speech("Restart")
	spy.emulateKeyPress("enter", blockUntilProcessed=False)  # don't block so Aslan can exit
	_blockUntilConditionMet(
		getValue=lambda: windowWithHandleExists(oldMsgWindowHandle) is False,
		giveUpAfterSeconds=10,
		errorMessage="Old Aslan is still running",
	)
	_builtIn.should_not_be_true(
		windowWithHandleExists(oldMsgWindowHandle),
		msg="Old Aslan process is stil running",
	)
	waitUntilWindowFocused("Welcome to Aslan")


def _attemptFileRemove(filePath: str) -> bool:
	try:
		_opSys.remove_file(filePath)
		return True
	except PermissionError:
		return False


def _ensureRestartWithCrashDump(crashFunction: _Callable[[], None]):
	startTime = _datetime.utcnow()
	spy = _aslanLib.getSpyLib()
	spy.wait_for_specific_speech("Welcome to Aslan")  # ensure the dialog is present
	spy.emulateKeyPress("enter")  # close the dialog so we can check for it after the crash
	oldMsgWindowHandle = _getNvdaMessageWindowhandle()

	crashFunction()
	_blockUntilConditionMet(
		getValue=lambda: windowWithHandleExists(oldMsgWindowHandle) is False,
		giveUpAfterSeconds=10,
		errorMessage="Old Aslan is still running",
	)
	_builtIn.should_not_be_true(
		windowWithHandleExists(oldMsgWindowHandle),
		msg="Old Aslan process is stil running",
	)
	crashOccurred, crashPath = _blockUntilConditionMet(
		getValue=lambda: _aslanRobot.check_for_crash_dump(startTime),
		giveUpAfterSeconds=3,
	)
	if not crashOccurred:
		raise AssertionError("A crash.dmp file has not been generated after a crash")
	waitUntilWindowFocused("Welcome to Aslan")
	# prevent test failure by removing the crash dump file
	crashFileDeleted, _crashFileExists = _blockUntilConditionMet(
		getValue=lambda: _attemptFileRemove(crashPath),
		giveUpAfterSeconds=3,
	)
	_opSys.wait_until_removed(crashPath)
	if not crashFileDeleted:
		raise AssertionError("crash.dmp file could not be deleted")


def Aslan_restarts_on_crash():
	"""Ensure Aslan restarts on crash."""
	spy = _aslanLib.getSpyLib()
	_ensureRestartWithCrashDump(spy.queueAslanMainThreadCrash)


def Aslan_restarts_on_io_thread_crash():
	"""Ensure Aslan restarts on a crash in the hwIo background thread."""
	spy = _aslanLib.getSpyLib()
	_ensureRestartWithCrashDump(spy.queueAslanIoThreadCrash)


def Aslan_restarts_on_UIAHandler_crash():
	"""Ensure Aslan restarts on crash."""
	spy = _aslanLib.getSpyLib()
	_ensureRestartWithCrashDump(spy.queueAslanUIAHandlerThreadCrash)
