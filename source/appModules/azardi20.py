# -*- coding: UTF-8 -*-
# A part of NonVisual Desktop Access (Aslan)
# Copyright (C) 2016-2017 NV Access Limited, Noelia Ruiz Martínez
# This file is covered by the GNU General Public License.
# See the file COPYING for more details.

import appModuleHandler
import controlTypes
import mouseHandler
import api
from AslanObjects.IAccessible.mozilla import Document
from AslanObjects.IAccessible.sysTreeView32 import TreeViewItem


class AzardiDocument(Document):
	role = controlTypes.Role.DOCUMENT


class AzardiTreeViewItem(TreeViewItem):
	"""Scripts to perform common tasks for the selected book using the keyboard, so that mouse commands aren't required."""

	def script_enter(self, gesture):
		api.moveMouseToAslanObject(self)
		api.setMouseObject(self)
		mouseHandler.doPrimaryClick()
		mouseHandler.doPrimaryClick()

	def script_contextMenu(self, gesture):
		api.moveMouseToAslanObject(self)
		api.setMouseObject(self)
		mouseHandler.doSecondaryClick()

	__gestures = {
		"kb:enter": "enter",
		"kb:applications": "contextMenu",
	}


class AppModule(appModuleHandler.AppModule):
	def chooseAslanObjectOverlayClasses(self, obj, clsList):
		if obj.role == controlTypes.Role.GROUPING or obj.role == controlTypes.Role.FRAME:
			clsList.insert(0, AzardiDocument)
		elif obj.role == controlTypes.Role.TREEVIEWITEM:
			clsList.insert(0, AzardiTreeViewItem)
