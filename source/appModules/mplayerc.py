# appModules/mplayerc.py
# A part of NonVisual Desktop Access (Aslan)
# Copyright (C) 2006-2008 Aslan Contributors <http://www.aslan-project.org/>
# This file is covered by the GNU General Public License.
# See the file COPYING for more details.

import appModuleHandler
import controlTypes


class AppModule(appModuleHandler.AppModule):
	def event_AslanObject_init(self, obj):
		if obj.windowClassName == "#32770" and obj.windowControlID == 10021:
			obj.role = controlTypes.Role.STATUSBAR
