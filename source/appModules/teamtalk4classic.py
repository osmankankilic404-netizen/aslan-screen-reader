# appModules/teamtalk4classic.py
# A part of NonVisual Desktop Access (Aslan)
# Copyright (C) 2010 Aslan Contributors <http://www.aslan-project.org/>
# This file is covered by the GNU General Public License.
# See the file COPYING for more details.

import appModuleHandler
from AslanObjects.behaviors import ProgressBar


class AppModule(appModuleHandler.AppModule):
	def event_AslanObject_init(self, obj):
		# The richedit control displaying incoming chat does not return correct _isWindowUnicode flag.
		if obj.windowClassName == "RichEdit20A":
			obj._isWindowUnicode = False

	def chooseAslanObjectOverlayClasses(self, obj, clsList):
		# There is a VU meter progress bar in the main window which we don't want to get anounced as all the other progress bars.
		if obj.windowClassName == "msctls_progress32" and obj.name == "VU":
			try:
				clsList.remove(ProgressBar)
			except ValueError:
				pass
