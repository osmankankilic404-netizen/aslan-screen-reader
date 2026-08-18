# virtualBuffers/lotusNotes.py
# A part of NonVisual Desktop Access (Aslan)
# This file is covered by the GNU General Public License.
# See the file COPYING for more details.
# Copyright (C) 2010-2012 NV Access Limited

from . import VirtualBuffer, VirtualBufferTextInfo
import controlTypes
import AslanObjects.IAccessible
import winUser
import mouseHandler
import IAccessibleHandler
import oleacc
from logHandler import log
from virtualBuffers import VirtualBufferTextInfo  # noqa: F811


class LotusNotesRichText_TextInfo(VirtualBufferTextInfo):
	def _normalizeControlField(self, attrs):
		role = controlTypes.Role.STATICTEXT
		states = IAccessibleHandler.getStatesSetFromIAccessibleAttrs(attrs)
		if controlTypes.State.LINKED in states:
			role = controlTypes.Role.LINK
		attrs["role"] = role
		attrs["states"] = states
		return super(LotusNotesRichText_TextInfo, self)._normalizeControlField(attrs)


class LotusNotesRichText(VirtualBuffer):
	TextInfo = LotusNotesRichText_TextInfo

	def __init__(self, rootAslanObject):
		super(LotusNotesRichText, self).__init__(rootAslanObject, backendName="lotusNotesRichText")

	def __contains__(self, obj):
		return winUser.isDescendantWindow(self.rootAslanObject.windowHandle, obj.windowHandle)

	def _get_isAlive(self):
		if self.isLoading:
			return True
		root = self.rootAslanObject
		if not root:
			return False
		if not winUser.isWindow(root.windowHandle) or root.role == controlTypes.Role.UNKNOWN:
			return False
		return True

	def getAslanObjectFromIdentifier(self, docHandle, ID):
		return AslanObjects.IAccessible.getAslanObjectFromEvent(docHandle, winUser.OBJID_CLIENT, ID)

	def getIdentifierFromAslanObject(self, obj):
		return obj.windowHandle, obj.event_childID

	# Older implementation of this function, overriden later in this file by a second definition of the same
	# function. This first definition is kept in case one wants to migrate some functionalities from it to the
	# second definition.
	def _searchableAttribsForNodeType(self, nodeType):
		if nodeType == "formField":
			attrs = {
				"IAccessible::role": [
					oleacc.ROLE_SYSTEM_PUSHBUTTON,
					oleacc.ROLE_SYSTEM_RADIOBUTTON,
					oleacc.ROLE_SYSTEM_CHECKBUTTON,
					oleacc.ROLE_SYSTEM_COMBOBOX,
					oleacc.ROLE_SYSTEM_LIST,
					oleacc.ROLE_SYSTEM_TEXT,
				],
			}
		elif nodeType == "list":
			attrs = {"IAccessible::role": [oleacc.ROLE_SYSTEM_LIST]}
		elif nodeType == "listItem":
			attrs = {"IAccessible::role": [oleacc.ROLE_SYSTEM_LISTITEM]}
		elif nodeType == "button":
			attrs = {"IAccessible::role": [oleacc.ROLE_SYSTEM_PUSHBUTTON]}
		elif nodeType == "edit":
			attrs = {"IAccessible::role": [oleacc.ROLE_SYSTEM_TEXT]}
		elif nodeType == "radioButton":
			attrs = {"IAccessible::role": [oleacc.ROLE_SYSTEM_RADIOBUTTON]}
		elif nodeType == "comboBox":
			attrs = {"IAccessible::role": [oleacc.ROLE_SYSTEM_COMBOBOX]}
		elif nodeType == "checkBox":
			attrs = {"IAccessible::role": [oleacc.ROLE_SYSTEM_CHECKBUTTON]}
		elif nodeType == "graphic":
			attrs = {"IAccessible::role": [oleacc.ROLE_SYSTEM_GRAPHIC]}
		elif nodeType == "focusable":
			attrs = {"IAccessible::state_%s" % oleacc.STATE_SYSTEM_FOCUSABLE: [1]}
		else:
			return None
		return attrs

	def _activateAslanObject(self, obj):
		try:
			obj.doAction()
			return
		except:  # noqa: E722
			pass

		log.debugWarning("could not programmatically activate field, trying mouse")
		l = obj.location  # noqa: E741
		if not l:
			log.debugWarning("no location for field")
			return
		oldX, oldY = winUser.getCursorPos()
		winUser.setCursorPos(*l.center)
		mouseHandler.doPrimaryClick()
		winUser.setCursorPos(oldX, oldY)

	def _shouldSetFocusToObj(self, obj):
		states = obj.states
		return controlTypes.State.FOCUSABLE in states or controlTypes.State.LINKED in states

	def shouldPassThrough(self, obj, reason=None):
		return False

	def _searchableAttribsForNodeType(self, nodeType):
		if nodeType == "link":
			attrs = {"IAccessible::state_%s" % oleacc.STATE_SYSTEM_LINKED: [1]}
		elif nodeType == "graphic":
			attrs = {"IAccessible::role": [oleacc.ROLE_SYSTEM_GRAPHIC]}
		elif nodeType == "focusable":
			attrs = {
				"IAccessible::state_%s" % oleacc.STATE_SYSTEM_FOCUSABLE: [1],
				"IAccessible::state_%s" % oleacc.STATE_SYSTEM_LINKED: [1],
			}
		else:
			return None
		return attrs
