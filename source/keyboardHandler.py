# A part of NonVisual Desktop Access (Aslan)
# This file is covered by the GNU General Public License.
# See the file COPYING for more details.
# Copyright (C) 2006-2025 NV Access Limited, Peter Vágner, Aleksey Sadovoy, Babbage B.V., Cyrille Bougot

"""Keyboard support"""

import ctypes
import time
import re
import typing
from typing import (
	Tuple,
	List,
	Optional,
	Any,
)

import winVersion
import winUser
import vkCodes
import eventHandler
import speech
import ui
from keyLabels import localizedKeyLabels
from logHandler import log
import config
from config.configFlags import AslanKey
import api
import winInputHook
import inputCore
import tones
import core
import AslanState
from contextlib import contextmanager
import threading
import winBindings.kernel32
import winKernel
from winBindings import user32

if typing.TYPE_CHECKING:
	from AslanObjects import AslanObject  # noqa: F401
	from watchdog import WatchdogObserver

_watchdogObserver: typing.Optional["WatchdogObserver"] = None
ignoreInjected = False
_lastInjectedKeyUp: tuple[int, int] | None = None
_injectionDoneEvent: int | None = None
type _ModifierT = tuple[int, bool]
_TO_UNICODE_EX_FLAG_NO_STATE_CHANGE = 0x04
_TO_UNICODE_EX_BUFFER_LENGTH = 5
_KEY_PRESSED_STATE = 0x80


def _getKeyStates(
	modifierVkCodes: list[int],
	ignoredModifier: int | None = None,
) -> ctypes.Array:
	"""Return keyboard state for ToUnicodeEx while forcing selected modifiers pressed."""
	states: ctypes.Array = (ctypes.c_ubyte * 256)()
	for i in range(256):
		if i in modifierVkCodes and i != ignoredModifier:
			states[i] = _KEY_PRESSED_STATE
		else:
			states[i] = user32.GetKeyState(i)
	return states


def _toUnicodeEx(
	vkCode: int,
	scanCode: int,
	states: ctypes.Array,
	buffer: ctypes.Array,
	keyboardLayout: int,
) -> int:
	"""Call ToUnicodeEx without modifying keyboard state."""
	return user32.ToUnicodeEx(
		vkCode,
		scanCode,
		states,
		buffer,
		len(buffer),
		_TO_UNICODE_EX_FLAG_NO_STATE_CHANGE,
		keyboardLayout,
	)


# Fake vk codes.
# These constants should be assigned to the name that Aslan will use for the key.
VK_WIN = "windows"
VK_Aslan = "Aslan"

#: Keys which have been trapped by Aslan and should not be passed to the OS.
trappedKeys = set()
#: Tracks the number of keys passed through by request of the user.
#: If -1, pass through is disabled.
#: If 0 or higher then key downs and key ups will be passed straight through.
passKeyThroughCount = -1
#: The last key down passed through by request of the user.
lastPassThroughKeyDown = None
#: The last Aslan modifier key that was pressed with no subsequent key presses.
lastAslanModifier = None
#: When the last Aslan modifier key was released.
lastAslanModifierReleaseTime = None
#: Indicates that the Aslan modifier's special functionality should be bypassed until a key is next released.
bypassAslanModifier = False
#: The modifiers currently being pressed.
currentModifiers = set()
#: A counter which is incremented each time a key is pressed.
#: Note that this may be removed in future, so reliance on it should generally be avoided.
#: @type: int
keyCounter = 0
#: The current sticky NVDa modifier key.
stickyAslanModifier = None
#: Whether the sticky Aslan modifier is locked.
stickyAslanModifierLocked = False

_ignoreInjectionLock = threading.Lock()


@contextmanager
def ignoreInjection():
	"""Context manager that allows ignoring injected keys temporarily by using a with statement."""
	global ignoreInjected
	with _ignoreInjectionLock:
		ignoreInjected = True
		yield
		ignoreInjected = False


def passNextKeyThrough():
	global passKeyThroughCount
	if passKeyThroughCount == -1:
		passKeyThroughCount = 0


def isAslanModifierKey(vkCode: int, extended: bool) -> bool:
	if (
		(config.conf["keyboard"]["AslanModifierKeys"] & AslanKey.NUMPAD_INSERT)
		and vkCode == winUser.VK_INSERT
		and not extended
	):
		return True
	elif (
		(config.conf["keyboard"]["AslanModifierKeys"] & AslanKey.EXTENDED_INSERT)
		and vkCode == winUser.VK_INSERT
		and extended
	):
		return True
	elif (config.conf["keyboard"]["AslanModifierKeys"] & AslanKey.CAPS_LOCK) and vkCode == winUser.VK_CAPITAL:
		return True
	else:
		return False


def __getattr__(attrName: str) -> Any:
	"""Module level `__getattr__` used to preserve backward compatibility."""
	if attrName == "SUPPORTED_Aslan_MODIFIER_KEYS" and AslanState._allowDeprecatedAPI():
		log.warning(
			"keyboardHandler.SUPPORTED_Aslan_MODIFIER_KEYS is deprecated with no direct replacement. "
			"Consider using the class config.configFlags.AslanKey instead.",
		)
		return ("capslock", "numpadinsert", "insert")
	raise AttributeError(f"module {repr(__name__)} has no attribute {repr(attrName)}")


def getAslanModifierKeys() -> List[Tuple[int, Optional[bool]]]:
	keys = []
	if config.conf["keyboard"]["AslanModifierKeys"] & AslanKey.EXTENDED_INSERT:
		keys.append(vkCodes.byName["insert"])
	if config.conf["keyboard"]["AslanModifierKeys"] & AslanKey.NUMPAD_INSERT:
		keys.append(vkCodes.byName["numpadinsert"])
	if config.conf["keyboard"]["AslanModifierKeys"] & AslanKey.CAPS_LOCK:
		keys.append(vkCodes.byName["capslock"])
	return keys


def shouldUseToUnicodeEx(focus: Optional["AslanObject"] = None):
	"Returns whether to use ToUnicodeEx to determine typed characters."
	if not focus:
		focus = api.getFocusObject()
	from AslanObjects.window import Window
	from AslanObjects.behaviors import KeyboardHandlerBasedTypedCharSupport

	return (
		# The focused Aslan object should be a real window
		isinstance(focus, Window)
		# This is only possible in Windows 10 1607 and above
		and winVersion.getWinVer() >= winVersion.WIN10_1607
		and (  # Either of
			# The focus is within a UWP app, where WM_CHAR never gets sent
			focus.windowClassName.startswith("Windows.UI.Core")
			# Or we couldn't inject in-process, and its not a legacy console window without keyboard support.
			# console windows have their own specific typed character support.
			or (
				not (focus.appModule and focus.appModule.helperLocalBindingHandle)
				and focus.windowClassName != "ConsoleWindowClass"
			)
			# Or this is a console with keyboard support, where WM_CHAR messages are doubled
			or isinstance(focus, KeyboardHandlerBasedTypedCharSupport)
		)
	)


def internal_keyDownEvent(vkCode, scanCode, extended, injected):
	"""Event called by winInputHook when it receives a keyDown."""
	if not inputCore.decide_handleRawKey.decide(
		vkCode=vkCode,
		scanCode=scanCode,
		extended=extended,
		pressed=True,
	):
		return False
	gestureExecuted = False
	try:
		global \
			lastAslanModifier, \
			lastAslanModifierReleaseTime, \
			bypassAslanModifier, \
			passKeyThroughCount, \
			lastPassThroughKeyDown, \
			currentModifiers, \
			keyCounter, \
			stickyAslanModifier, \
			stickyAslanModifierLocked
		# Injected keys should be ignored in some cases.
		if injected and (ignoreInjected or not config.conf["keyboard"]["handleInjectedKeys"]):
			return True

		keyCode = (vkCode, extended)

		if passKeyThroughCount >= 0:
			# We're passing keys through.
			if lastPassThroughKeyDown != keyCode:
				# Increment the pass key through count.
				# We only do this if this isn't a repeat of the previous key down, as we don't receive key ups for repeated key downs.
				passKeyThroughCount += 1
				lastPassThroughKeyDown = keyCode
			return True

		keyCounter += 1
		stickyKeysFlags = winUser.getSystemStickyKeys().dwFlags
		if stickyAslanModifier and not stickyKeysFlags & winUser.SKF_STICKYKEYSON:
			# Sticky keys has been disabled,
			# so clear the sticky Aslan modifier.
			currentModifiers.discard(stickyAslanModifier)
			stickyAslanModifier = None
			stickyAslanModifierLocked = False
		gesture = KeyboardInputGesture(currentModifiers, vkCode, scanCode, extended)
		if not (stickyKeysFlags & winUser.SKF_STICKYKEYSON) and (
			bypassAslanModifier
			or (
				keyCode == lastAslanModifier
				and lastAslanModifierReleaseTime
				and (
					time.time() - lastAslanModifierReleaseTime
					< config.conf["keyboard"]["multiPressTimeout"] / 1000
				)
			)
		):
			# The user wants the key to serve its normal function instead of acting as an Aslan modifier key.
			# There may be key repeats, so ensure we do this until they stop.
			bypassAslanModifier = True
			gesture.isAslanModifierKey = False
		lastAslanModifierReleaseTime = None
		if gesture.isAslanModifierKey:
			lastAslanModifier = keyCode
			if stickyKeysFlags & winUser.SKF_STICKYKEYSON:
				if keyCode == stickyAslanModifier:
					if stickyKeysFlags & winUser.SKF_TRISTATE and not stickyAslanModifierLocked:
						# The Aslan modifier is being locked.
						stickyAslanModifierLocked = True
						if stickyKeysFlags & winUser.SKF_AUDIBLEFEEDBACK:
							tones.beep(1984, 60)
						return False
					else:
						# The Aslan modifier is being unlatched/unlocked.
						stickyAslanModifier = None
						stickyAslanModifierLocked = False
						if stickyKeysFlags & winUser.SKF_AUDIBLEFEEDBACK:
							tones.beep(496, 60)
						return False
				else:
					# The Aslan modifier is being latched.
					if stickyAslanModifier:
						# Clear the previous sticky Aslan modifier.
						currentModifiers.discard(stickyAslanModifier)
						stickyAslanModifierLocked = False
					stickyAslanModifier = keyCode
					if stickyKeysFlags & winUser.SKF_AUDIBLEFEEDBACK:
						tones.beep(1984, 60)
		else:
			# Another key was pressed after the last Aslan modifier key, so it should not be passed through on the next press.
			lastAslanModifier = None
		if gesture.isModifier:
			if (
				gesture.speechEffectWhenExecuted in (gesture.SPEECHEFFECT_PAUSE, gesture.SPEECHEFFECT_RESUME)
				and keyCode in currentModifiers
			):
				# Ignore key repeats for the pause speech key to avoid speech stuttering as it continually pauses and resumes.
				return True
			currentModifiers.add(keyCode)
		elif stickyAslanModifier and not stickyAslanModifierLocked:
			# A non-modifier was pressed, so unlatch the Aslan modifier.
			currentModifiers.discard(stickyAslanModifier)
			stickyAslanModifier = None

		if _watchdogObserver.isAttemptingRecovery:
			# When attempting recovery only process modifiers, but do not execute gesture.
			return True

		try:
			inputCore.manager.executeGesture(gesture)
			gestureExecuted = True
			trappedKeys.add(keyCode)
			return False
		except inputCore.NoInputGestureAction:
			if gesture.isAslanModifierKey:
				# Never pass the Aslan modifier key to the OS.
				trappedKeys.add(keyCode)
				return False
	except:  # noqa: E722
		log.error("internal_keyDownEvent", exc_info=True)
	finally:
		if _watchdogObserver.isAttemptingRecovery:
			return True
		# #6017: handle typed characters in Win10 RS2 and above where we can't detect typed characters in-process
		# This code must be in the 'finally' block as code above returns in several places yet we still want to execute this particular code.
		focus = api.getFocusObject()
		if (
			shouldUseToUnicodeEx(focus)
			# And we only want to do this if the gesture did not result in an executed action
			and not gestureExecuted
			# and not if this gesture is a modifier key
			and not isAslanModifierKey(vkCode, extended)
			and vkCode not in KeyboardInputGesture.NORMAL_MODIFIER_KEYS
		):
			keyStates = (ctypes.c_ubyte * 256)()
			for k in range(256):
				keyStates[k] = user32.GetKeyState(k)
			charBuf = ctypes.create_unicode_buffer(5)
			hkl = user32.GetKeyboardLayout(focus.windowThreadID)
			# In previous Windows builds, calling ToUnicodeEx would destroy keyboard buffer state and therefore cause the app to not produce the right WM_CHAR message.
			# However, ToUnicodeEx now can take a new flag of 0x4, which stops it from destroying keyboard state, thus allowing us to safely call it here.
			res = user32.ToUnicodeEx(
				vkCode,
				scanCode,
				keyStates,
				charBuf,
				len(charBuf),
				0x4,
				hkl,
			)
			if res > 0:
				for ch in charBuf[:res]:
					eventHandler.queueEvent("typedCharacter", focus, ch=ch)
	return True


def internal_keyUpEvent(vkCode, scanCode, extended, injected):
	"""Event called by winInputHook when it receives a keyUp."""
	if not inputCore.decide_handleRawKey.decide(
		vkCode=vkCode,
		scanCode=scanCode,
		extended=extended,
		pressed=False,
	):
		return False
	try:
		global \
			lastAslanModifier, \
			lastAslanModifierReleaseTime, \
			bypassAslanModifier, \
			passKeyThroughCount, \
			lastPassThroughKeyDown, \
			currentModifiers
		keyCode = (vkCode, extended)
		# Injected keys should be ignored in some cases.
		if injected:
			if not config.conf["keyboard"]["handleInjectedKeys"]:
				return True
			if ignoreInjected:
				if keyCode == _lastInjectedKeyUp:
					winBindings.kernel32.SetEvent(_injectionDoneEvent)
				return True

		if passKeyThroughCount >= 1:
			if lastPassThroughKeyDown == keyCode:
				# This key has been released.
				lastPassThroughKeyDown = None
			passKeyThroughCount -= 1
			if passKeyThroughCount == 0:
				passKeyThroughCount = -1
			return True

		if lastAslanModifier and keyCode == lastAslanModifier:
			# The last pressed Aslan modifier key is being released and there were no key presses in between.
			# The user may want to press it again quickly to pass it through.
			lastAslanModifierReleaseTime = time.time()
		# If we were bypassing the Aslan modifier, stop doing so now, as there will be no more repeats.
		bypassAslanModifier = False

		if keyCode != stickyAslanModifier:
			currentModifiers.discard(keyCode)

		# help inputCore  manage its sayAll state for keyboard modifiers -- inputCore itself has no concept of key releases
		if not currentModifiers:
			inputCore.manager.lastModifierWasInSayAll = False

		if keyCode in trappedKeys:
			trappedKeys.remove(keyCode)
			return False
	except:  # noqa: E722
		log.error("", exc_info=True)
	return True


# Register internal key press event with  operating system


def initialize(watchdogObserver: "WatchdogObserver"):
	"""Initialises keyboard support."""
	global _watchdogObserver
	_watchdogObserver = watchdogObserver
	winInputHook.initialize()
	winInputHook.setCallbacks(keyDown=internal_keyDownEvent, keyUp=internal_keyUpEvent)


def terminate():
	winInputHook.terminate()


def getInputHkl():
	"""Obtain the hkl currently being used for input.
	This retrieves the hkl from the thread of the focused window.
	"""
	focus = api.getFocusObject()
	if focus:
		thread = focus.windowThreadID
	else:
		thread = 0
	return user32.GetKeyboardLayout(thread)


def canModifiersPerformAction(modifiers):
	"""Determine whether given generalized modifiers can perform an action if pressed alone.
	For example, alt activates the menu bar if it isn't modifying another key.
	"""
	if inputCore.manager.isInputHelpActive:
		return False
	control = shift = other = False
	for vk, ext in modifiers:
		if vk in (winUser.VK_MENU, VK_WIN):
			# Alt activates the menu bar.
			# Windows activates the Start Menu.
			return True
		elif vk == winUser.VK_CONTROL:
			control = True
		elif vk == winUser.VK_SHIFT:
			shift = True
		elif (vk, ext) not in trappedKeys:
			# Trapped modifiers aren't relevant.
			other = True
	if control and shift and not other:
		# Shift+control switches keyboard layouts.
		return True
	return False


class KeyboardInputGesture(inputCore.InputGesture):
	"""A key pressed on the traditional system keyboard."""

	#: All normal modifier keys, where modifier vk codes are mapped to a more general modifier vk code
	# or C{None} if not applicable.
	#: @type: dict
	NORMAL_MODIFIER_KEYS = {
		winUser.VK_LCONTROL: winUser.VK_CONTROL,
		winUser.VK_RCONTROL: winUser.VK_CONTROL,
		winUser.VK_CONTROL: None,
		winUser.VK_LSHIFT: winUser.VK_SHIFT,
		winUser.VK_RSHIFT: winUser.VK_SHIFT,
		winUser.VK_SHIFT: None,
		winUser.VK_LMENU: winUser.VK_MENU,
		winUser.VK_RMENU: winUser.VK_MENU,
		winUser.VK_MENU: None,
		winUser.VK_LWIN: VK_WIN,
		winUser.VK_RWIN: VK_WIN,
		VK_WIN: None,
	}

	#: All possible toggle key vk codes.
	#: @type: frozenset
	TOGGLE_KEYS = frozenset((winUser.VK_CAPITAL, winUser.VK_NUMLOCK, winUser.VK_SCROLL))

	#: All possible keyboard layouts, where layout names are mapped to localised layout names.
	#: @type: dict
	LAYOUTS = {
		# Translators: One of the keyboard layouts for Aslan.
		"desktop": _("desktop"),
		# Translators: One of the keyboard layouts for Aslan.
		"laptop": _("laptop"),
	}

	@classmethod
	def getVkName(cls, vkCode, isExtended):
		if isinstance(vkCode, str):
			return vkCode
		name = vkCodes.byCode.get((vkCode, isExtended))
		if not name and isExtended is not None:
			# Whether the key is extended doesn't matter for many keys, so try None.
			name = vkCodes.byCode.get((vkCode, None))
		return name if name else ""

	def __init__(self, modifiers, vkCode, scanCode, isExtended):
		#: The keyboard layout in which this gesture was created.
		#: @type: str
		self.layout = config.conf["keyboard"]["keyboardLayout"]
		self.modifiers = modifiers = set(modifiers)
		# Don't double up if this is a modifier key repeat.
		modifiers.discard((vkCode, isExtended))
		if (
			vkCode in (winUser.VK_DIVIDE, winUser.VK_MULTIPLY, winUser.VK_SUBTRACT, winUser.VK_ADD)
			and winUser.getKeyState(winUser.VK_NUMLOCK) & 1
		):
			# Some numpad keys have the same vkCode regardless of numlock.
			# For these keys, treat numlock as a modifier.
			modifiers.add((winUser.VK_NUMLOCK, False))
		self.generalizedModifiers = self._generalizeModifiers(modifiers)
		self.vkCode = vkCode
		self.scanCode = scanCode
		self.isExtended = isExtended
		super(KeyboardInputGesture, self).__init__()

	@classmethod
	def _generalizeModifiers(cls, modifiers: _ModifierT) -> _ModifierT:
		"""Return the input set, with specific modifiers replaced with their general equivalents.

		Replaces keys like leftAlt or rightCtrl with their generic alternatives (i.e. alt or ctrl).

		:param modifiers: Set of (vkCode, extended) tuples.
		:return: A copy of the input set with the specific modifiers replaced with their general equivalents.
		"""
		return set((cls.NORMAL_MODIFIER_KEYS.get(mod) or mod, extended) for mod, extended in modifiers)

	def _get_bypassInputHelp(self):
		# #4226: Numlock must always be handled normally otherwise the Keyboard controller and Windows can get out of synk wih each other in regard to this key state.
		return self.vkCode == winUser.VK_NUMLOCK

	def _get_isAslanModifierKey(self):
		return isAslanModifierKey(self.vkCode, self.isExtended)

	def _get_isModifier(self):
		return self.vkCode in self.NORMAL_MODIFIER_KEYS or self.isAslanModifierKey

	def _get_mainKeyName(self):
		if self.isAslanModifierKey:
			return "Aslan"

		name = self.getVkName(self.vkCode, self.isExtended)
		if name:
			return name

		if 32 < self.vkCode < 128:
			return chr(self.vkCode).lower()
		if self.vkCode == vkCodes.VK_PACKET:
			# Unicode character from non-keyboard input.
			return chr(self.scanCode)
		vkChar = user32.MapVirtualKeyEx(self.vkCode, winUser.MAPVK_VK_TO_CHAR, getInputHkl())
		# the highest bit of a 32 bit value denotes a dead key
		DEAD_KEY_FLAG = 0x80000000
		if vkChar > 0 and not (vkChar & DEAD_KEY_FLAG):
			if vkChar == 43:  # "+"
				# A gesture identifier can't include "+" except as a separator.
				return "plus"
			return chr(vkChar).lower()

		if self.vkCode == 0xFF:
			# #3468: This key is unknown to Windows.
			# GetKeyNameText often returns something inappropriate in these cases
			# due to disregarding the extended flag.
			return "unknown_%02x" % self.scanCode
		return winUser.getKeyNameText(self.scanCode, self.isExtended)

	def _get_modifierNames(self):
		modTexts = []
		for modVk, modExt in self.generalizedModifiers:
			if isAslanModifierKey(modVk, modExt):
				modTexts.append("Aslan")
			else:
				modTexts.append(self.getVkName(modVk, None))
		return modTexts

	def _get__keyNamesInDisplayOrder(self):
		return tuple(self.modifierNames) + (self.mainKeyName,)

	def _get_displayName(self):
		return "+".join(
			# Translators: Reported for an unknown key press.
			# %s will be replaced with the key code.
			_("unknown %s") % key[8:]
			if key.startswith("unknown_")
			else localizedKeyLabels.get(key.lower(), key)
			for key in self._keyNamesInDisplayOrder
		)

	def _get_character(self) -> str | None:
		"""Get the character this key combination would produce.

		Uses ToUnicodeEx with the no-state-change flag to avoid modifying keyboard state.
		For dead keys, returns the dead key character itself.
		Returns None for unprintable characters or when Windows key is pressed.
		"""
		try:
			threadID = api.getFocusObject().windowThreadID
		except AttributeError:
			return None
		keyboardLayout = user32.GetKeyboardLayout(threadID)
		buffer = ctypes.create_unicode_buffer(_TO_UNICODE_EX_BUFFER_LENGTH)

		modifierVkCodes: list[int] = []
		hasWindowsModifier = False
		for mod, _ in self.modifiers:
			modifier = self.NORMAL_MODIFIER_KEYS.get(mod)
			if modifier is None and mod in self.NORMAL_MODIFIER_KEYS.values():
				modifier = mod
			if modifier == VK_WIN:
				hasWindowsModifier = True
			elif modifier is not None:
				modifierVkCodes.append(modifier)

		# Characters with the Windows key are invalid.
		if hasWindowsModifier:
			return None

		states = _getKeyStates(modifierVkCodes)

		res = _toUnicodeEx(self.vkCode, self.scanCode, states, buffer, keyboardLayout)

		# res < 0 means dead key - return the dead key character
		if res < 0:
			# Dead key: buffer contains the dead key character
			# Call ToUnicodeEx again to get and clear the dead key from buffer
			_toUnicodeEx(self.vkCode, self.scanCode, states, buffer, keyboardLayout)
			return buffer.value[:1] if buffer.value else None

		if res == 0:
			return None

		# Check alt key behavior - alt sometimes gives same character as without alt
		if winUser.VK_MENU in modifierVkCodes:
			altStates = _getKeyStates(modifierVkCodes, ignoredModifier=winUser.VK_MENU)
			newBuffer = ctypes.create_unicode_buffer(_TO_UNICODE_EX_BUFFER_LENGTH)
			_toUnicodeEx(
				self.vkCode,
				self.scanCode,
				altStates,
				newBuffer,
				keyboardLayout,
			)
			# If same character with and without alt, it's not valid
			if buffer.value == newBuffer.value:
				return None

		return buffer.value[:res]

	def _get_inputHelpCharacter(self) -> str | None:
		"""Returns the character this gesture should additionally report in input help mode."""
		# Commands keep original behavior, even if they also produce a printable character.
		if any(isAslanModifierKey(mod, ext) for mod, ext in self.modifiers) or self.script:
			return None

		char = self.character
		if not char:
			return None

		if not char.isprintable():
			return None

		# Avoid duplicating only when the display name already matches the produced character.
		if self.displayName == char:
			return None

		return char

	def _get_identifiers(self):
		keyName = "+".join(self._keyNamesInDisplayOrder)
		return (
			"kb({layout}):{key}".format(layout=self.layout, key=keyName),
			"kb:{key}".format(key=keyName),
		)

	def _get_shouldReportAsCommand(self):
		if self.isExtended and winUser.VK_VOLUME_MUTE <= self.vkCode <= winUser.VK_VOLUME_UP:
			# Don't report volume controlling keys.
			return False
		if self.vkCode == 0xFF:
			# #3468: This key is unknown to Windows.
			# This could be for an event such as gyroscope movement,
			# so don't report it.
			return False
		if self.vkCode in self.TOGGLE_KEYS:
			# #5490: Dont report for keys that toggle on off.
			# This is to avoid them from being reported twice: once by the 'speak command keys' feature,
			# and once to announce that the state has changed.
			return False
		return not self.isCharacter

	def _get_isCharacter(self):
		# Aside from space, a key name of more than 1 character is a potential command and therefore is not a character.
		if self.vkCode != winUser.VK_SPACE and len(self.mainKeyName) > 1:
			return False
		# If this key has modifiers other than shift, it is a command and not a character; e.g. shift+f is a character, but control+f is a command.
		modifiers = self.generalizedModifiers
		if modifiers and (len(modifiers) > 1 or tuple(modifiers)[0][0] != winUser.VK_SHIFT):
			return False
		return True

	def _get_speechEffectWhenExecuted(self):
		if inputCore.manager.isInputHelpActive:
			return self.SPEECHEFFECT_CANCEL
		if self.isExtended and winUser.VK_VOLUME_MUTE <= self.vkCode <= winUser.VK_VOLUME_UP:
			return None
		if self.vkCode == 0xFF:
			# #3468: This key is unknown to Windows.
			# This could be for an event such as gyroscope movement,
			# so don't interrupt speech.
			return None
		if not config.conf["keyboard"]["speechInterruptForCharacters"] and (
			not self.shouldReportAsCommand
			or self.vkCode in (winUser.VK_SHIFT, winUser.VK_LSHIFT, winUser.VK_RSHIFT)
		):
			return None
		if self.vkCode == winUser.VK_RETURN and not config.conf["keyboard"]["speechInterruptForEnter"]:
			return None
		if self.vkCode in (winUser.VK_SHIFT, winUser.VK_LSHIFT, winUser.VK_RSHIFT):
			return self.SPEECHEFFECT_RESUME if speech.getState().isPaused else self.SPEECHEFFECT_PAUSE
		return self.SPEECHEFFECT_CANCEL

	def reportExtra(self):
		if self.vkCode in self.TOGGLE_KEYS:
			core.callLater(30, self._reportToggleKey)

	def _reportToggleKey(self):
		toggleState = winUser.getKeyState(self.vkCode) & 1
		key = self.mainKeyName
		ui.message(
			"{key} {state}".format(
				key=localizedKeyLabels.get(key.lower(), key),
				state=_("on") if toggleState else _("off"),
			),
		)

	def executeScript(self, script):
		if canModifiersPerformAction(self.generalizedModifiers):
			# #3472: These modifiers can perform an action if pressed alone
			# and we've just totally consumed the main key.
			# Send special reserved vkcode VK_NONE (0xff)
			# to at least notify the app's key state that something happened.
			# This allows alt and windows to be bound to scripts and
			# stops control+shift from switching keyboard layouts in cursorManager selection scripts.
			# This must be done before executing the script,
			# As if the script takes a long time and the user releases these modifier keys before the script finishes,
			# it is already too late.
			with ignoreInjection():
				winUser.keybd_event(winUser.VK_NONE, 0, 0, 0)
				winUser.keybd_event(winUser.VK_NONE, 0, user32.KEYEVENTF.KEYUP, 0)
		# Now actually execute the script.
		super().executeScript(script)

	#: The maximum amount of time (in ms) to wait for keys injected by Aslan to be
	#: received by Aslan.
	_INJECTION_WAIT_TIMEOUT: int = 10

	def send(self):
		global _lastInjectedKeyUp, _injectionDoneEvent
		keys = []
		for vk, ext in self.generalizedModifiers:
			if vk == VK_WIN:
				if (
					winUser.getKeyState(winUser.VK_LWIN) & 32768
					or winUser.getKeyState(winUser.VK_RWIN) & 32768
				):
					# Already down.
					continue
				vk = winUser.VK_LWIN
			elif vk == winUser.VK_NUMLOCK:
				# Numlock is considered a modifier by Aslan but never by the OS.
				continue
			elif winUser.getKeyState(vk) & 32768:
				# Already down.
				continue
			keys.append((vk, 0, ext))
		keys.append((self.vkCode, self.scanCode, self.isExtended))

		with ignoreInjection():
			handleInjectedKeys = config.conf["keyboard"]["handleInjectedKeys"]
			if handleInjectedKeys:
				_lastInjectedKeyUp = (keys[0][0], keys[0][2])
				if not _injectionDoneEvent:
					_injectionDoneEvent = winKernel.createEvent()
			if winUser.getKeyState(self.vkCode) & 32768:
				# This key is already down, so send a key up for it first.
				winUser.keybd_event(self.vkCode, self.scanCode, self.isExtended + 2, 0)

			# Send key down events for these keys.
			for vk, scan, ext in keys:
				winUser.keybd_event(vk, scan, ext, 0)
			# Send key up events for the keys in reverse order.
			for vk, scan, ext in reversed(keys):
				winUser.keybd_event(vk, scan, ext + 2, 0)
			if handleInjectedKeys:
				# Wait for the keys to be received by Aslan. We don't do this if
				# handleInjectedKeys is disabled because we just ignore all injected keys
				# in that case.
				winKernel.waitForSingleObject(_injectionDoneEvent, self._INJECTION_WAIT_TIMEOUT)

	@classmethod
	def fromName(cls, name):
		"""Create an instance given a key name.
		@param name: The key name.
		@type name: str
		@return: A gesture for the specified key.
		@rtype: L{KeyboardInputGesture}
		"""
		keyNames = name.split("+")
		keys = []
		for keyName in keyNames:
			if keyName == "plus":
				# A key name can't include "+" except as a separator.
				keyName = "+"
			if keyName == VK_WIN:
				vk = winUser.VK_LWIN
				ext = False
			elif keyName.lower() == VK_Aslan.lower():
				vk, ext = getAslanModifierKeys()[0]
			elif len(keyName) == 1:
				ext = False
				requiredMods, vk = winUser.VkKeyScanEx(keyName, getInputHkl())
				if requiredMods & 1:
					keys.append((winUser.VK_SHIFT, False))
				if requiredMods & 2:
					keys.append((winUser.VK_CONTROL, False))
				if requiredMods & 4:
					keys.append((winUser.VK_MENU, False))
				# Not sure whether we need to support the Hankaku modifier (& 8).
			else:
				vk, ext = vkCodes.byName[keyName.lower()]
				if ext is None:
					ext = False
			keys.append((vk, ext))

		if not keys:
			raise ValueError

		return cls(keys[:-1], vk, 0, ext)

	RE_IDENTIFIER = re.compile(r"^kb(?:\((.+?)\))?:(.*)$")

	@classmethod
	def getDisplayTextForIdentifier(cls, identifier):
		layout, keys = cls.RE_IDENTIFIER.match(identifier).groups()
		dispSource = None
		if layout:
			try:
				# Translators: Used when describing keys on the system keyboard with a particular layout.
				# %s is replaced with the layout name.
				# For example, in English, this might produce "laptop keyboard".
				dispSource = _("%s keyboard") % cls.LAYOUTS[layout]
			except KeyError:
				pass
		if not dispSource:
			# Translators: Used when describing keys on the system keyboard applying to all layouts.
			dispSource = _("keyboard, all layouts")

		keys = set(keys.split("+"))
		names = []
		main = None
		numlock = None
		try:
			# If present, the Aslan key should appear first.
			keys.remove("aslan")
			names.append("Aslan")
		except KeyError:
			pass
		for key in keys:
			try:
				# vkCodes.byName values are (vk, ext)
				vk = vkCodes.byName[key][0]
			except KeyError:
				# This could be a fake vk.
				vk = key
			label = localizedKeyLabels.get(key, key)
			if vk in cls.NORMAL_MODIFIER_KEYS:
				names.append(label)
			elif vk == winUser.VK_NUMLOCK:
				# Numlock can be both modifier or main key so handle it separately and add it at the end after modifiers
				# but before main key
				numlock = label
			else:
				# The main key must be last, so handle that outside the loop.
				main = label
		if numlock is not None:
			names.append(numlock)
		if main is not None:
			# If there is no main key, this gesture identifier only contains modifiers.
			names.append(main)
		return dispSource, "+".join(names)


inputCore.registerGestureSource("kb", KeyboardInputGesture)


def injectRawKeyboardInput(isPress, code, isExtended):
	"""Inject raw input from a system keyboard that is not handled natively by Windows.
	For example, this might be used for input from a QWERTY keyboard on a braille display.
	Aslan will treat the key as if it had been pressed on a normal system keyboard.
	If it is not handled by Aslan, it will be sent to the operating system.
	@param isPress: Whether the key is being pressed.
	@type isPress: bool
	@param code: The scan code (PC set 1) of the key.
	@type code: int
	@param isExtended: Whether this is an extended key.
	@type isExtended: bool
	"""
	mapScan = code
	if isExtended:
		# Change what we pass to MapVirtualKeyEx, but don't change what Aslan gets.
		mapScan |= 0xE000
	vkCode = user32.MapVirtualKeyEx(mapScan, winUser.MAPVK_VSC_TO_VK_EX, getInputHkl())
	flags = 0
	if not isPress:
		flags |= 2
	if isExtended:
		flags |= 1
	winUser.keybd_event(vkCode, code, flags, None)
