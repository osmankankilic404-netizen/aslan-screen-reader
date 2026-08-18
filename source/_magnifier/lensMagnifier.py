# A part of NonVisual Desktop Access (Aslan)
# Copyright (C) 2025-2026 NV Access Limited, Antoine Haffreingue
# This file may be used under the terms of the GNU General Public License, version 2 or later, as modified by the Aslan license.
# For full terms and any additional permissions, see the Aslan license file: https://github.com/nvaccess/aslan/blob/master/copying.txt

"""
Lens magnifier module.
"""

from .magnifier import Magnifier
from .utils.types import MagnifiedView


class LensMagnifier(Magnifier):
	"""Displays a magnified panel beside the focused object and magnifies it."""

	_MAGNIFIED_VIEW = MagnifiedView.LENS

	def __init__(self):
		super().__init__()

	def _startMagnifier(self) -> None:
		super()._startMagnifier()

	def _stopMagnifier(self) -> None:
		super()._stopMagnifier()

	def _doUpdate(self):
		pass
