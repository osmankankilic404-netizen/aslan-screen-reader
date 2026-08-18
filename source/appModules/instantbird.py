# appModules/instantbird.py
# A part of NonVisual Desktop Access (Aslan)
# This file is covered by the GNU General Public License.
# See the file COPYING for more details.
# Copyright (C) 2013 NV Access Limited

"""App module for Instantbird"""

import appModuleHandler
import AslanObjects.IAccessible.mozilla
import controlTypes


class AppModule(appModuleHandler.AppModule):
	def event_AslanObject_init(self, obj):
		if (
			isinstance(obj, AslanObjects.IAccessible.IAccessible)
			and obj.windowClassName == "MozillaWindowClass"
			and not isinstance(obj, AslanObjects.IAccessible.mozilla.Mozilla)
			and obj.role == controlTypes.Role.UNKNOWN
		):
			# #2667: This is a Mozilla accessible that has already died.
			# Instantbird fires focus on a dead accessible first every time you focus a contact,
			# so block focus on these to eliminate annoyance.
			obj.shouldAllowIAccessibleFocusEvent = False
