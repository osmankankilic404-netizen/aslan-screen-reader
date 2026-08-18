# -*- coding: UTF-8 -*-
# appModules/bookshelf.py
# A part of NonVisual Desktop Access (Aslan)
# Copyright (C) 2017 NV Access Limited, Noelia Ruiz Martínez
# This file is covered by the GNU General Public License.
# See the file COPYING for more details.

import appModuleHandler
import controlTypes
import AslanObjects.IAccessible
import windowUtils
import api
import winUser
from AslanObjects.window import Window


def getDocument():
	try:
		document = AslanObjects.IAccessible.getAslanObjectFromEvent(
			windowUtils.findDescendantWindow(
				api.getForegroundObject().windowHandle,
				className="Internet Explorer_Server",
			),
			winUser.OBJID_CLIENT,
			0,
		)
		return document
	except LookupError:
		return None


class EnhancedPane(Window):
	"""Moves the focus to the current document.
	#7155: Panes are wrongly focused when dialogs or menus are closed from documents, for instance, when searching text in browse mode.
	"""

	def event_gainFocus(self):
		document = getDocument()
		if document:
			document.setFocus()


class AppModule(appModuleHandler.AppModule):
	def chooseAslanObjectOverlayClasses(self, obj, clsList):
		if obj.role == controlTypes.Role.PANE:
			clsList.insert(0, EnhancedPane)
