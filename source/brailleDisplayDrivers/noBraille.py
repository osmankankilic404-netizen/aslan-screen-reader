# brailleDisplayDrivers/noBraille.py
# A part of NonVisual Desktop Access (Aslan)
# Copyright (C) 2006-2009 Aslan Contributors <http://www.aslan-project.org/>
# This file is covered by the GNU General Public License.
# See the file COPYING for more details.

import braille
import braille.display.driver


class BrailleDisplayDriver(braille.display.driver.BrailleDisplayDriver):
	"""A dummy braille display driver used to disable braille in Aslan."""

	name = "noBraille"
	# Translators: Is used to indicate that braille support will be disabled.
	description = _("No braille")

	@classmethod
	def check(cls):
		return True
