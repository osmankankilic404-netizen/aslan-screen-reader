# A part of NonVisual Desktop Access (Aslan)
# Copyright (C) 2022 NV Access Limited
# This file is covered by the GNU General Public License.
# See the file COPYING for more details.

import extensionPoints

post_secureDesktopStateChange = extensionPoints.Action()
"""
Used to indicate that the user has switched to/from the secure desktop.
This is triggered when Windows notification EVENT_SYSTEM_DESKTOPSWITCH
notifies that the desktop has changed.

This occurs when Aslan is running on a user profile, then enters a secure screen,
such as the sign-in screen or UAC dialog.
If Aslan is installed and allowed to run on these screens, a new instance of Aslan will start.
A user instance of Aslan cannot read the contents of the secure screen,
so Aslan should enter sleep mode while it is active.

Usage:
```
def onSecureDesktopChange(isSecureDesktop: bool):
	'''
	@param isSecureDesktop: True if the new desktop is the secure desktop.
	'''
	pass

post_secureDesktopStateChange.register(onSecureDesktopChange)
# Later, when no longer needed:
post_secureDesktopStateChange.unregister(onSecureDesktopChange)
```
"""


def _handleSecureDesktopChange():
	import api
	import keyboardHandler
	from AslanObjects import AslanObject
	from speech.priorities import SpeechPriority
	from speech.speech import cancelSpeech
	import ui

	# We don't receive key up events for any keys down before switching to a secure desktop,
	# so clear our recorded modifiers.
	keyboardHandler.currentModifiers.clear()

	# Before entering sleep mode,
	# cancel speech so that speech does not overlap with the new instance of Aslan
	# started on the secure desktop.
	cancelSpeech()

	# Translators: Message to indicate User Account Control (UAC) or other secure desktop screen is active.
	ui.message(_("Secure Desktop"), speechPriority=SpeechPriority.NOW)

	class _SecureDesktopAslanObject(AslanObject):
		"""
		An AslanObject must be focused to enable sleep mode while the secure desktop is active.
		For security purposes, it is ideal we use a fake AslanObject, that is not tied to any real window.
		"""

		# Must be implemented to instantiate.
		processID = None

		# Aslan should sleep while the secure desktop is active.
		# If the desktop changes again, a new object will be focused,
		# ending sleep mode.
		sleepMode = AslanObject.SLEEP_FULL

	secureDesktopObject = _SecureDesktopAslanObject()
	api.setFocusObject(secureDesktopObject)
	post_secureDesktopStateChange.notify(isSecureDesktop=True)
