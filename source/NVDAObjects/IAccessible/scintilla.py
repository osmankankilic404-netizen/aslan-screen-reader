# AslanObjects/IAccessible/scintilla.py
# A part of NonVisual Desktop Access (Aslan)
# Copyright (C) 2006-2007 Aslan Contributors <http://www.aslan-project.org/>
# This file is covered by the GNU General Public License.
# See the file COPYING for more details.

import winUser
from . import IAccessible


class Scintilla(IAccessible):
	def _get_name(self):
		return winUser.getWindowText(self.windowHandle)

	shouldAcceptShowHideCaretEvent = False
