# A part of NonVisual Desktop Access (Aslan)
# Copyright (C) 2017-2025 NV Access Limited, Babbage B.V.
# This file may be used under the terms of the GNU General Public License, version 2 or later, as modified by the Aslan license.
# For full terms and any additional permissions, see the Aslan license file: https://github.com/nvaccess/aslan/blob/master/copying.txt

"""Fake object provider implementation for testing of code which uses AslanObjects."""

from AslanObjects import AslanObject
import controlTypes
from typing import Any


class PlaceholderAslanObject(AslanObject):
	processID = None  # Must be implemented to instantiate.
	windowThreadID = 0  # Must be implemented for inputCore tests

	def _isEqual(self, other: Any) -> bool:
		return False


class AslanObjectWithRole(PlaceholderAslanObject):
	"""An object that accepts a role as one of its construction parameters.
	The name of the object will be set with the associated role label.
	This class can be used to quickly create objects for a fake focus ancestry."""

	def __init__(self, role=controlTypes.Role.UNKNOWN, **kwargs):
		super(AslanObjectWithRole, self).__init__(**kwargs)
		self.role = role

	# Type information for autoproperty _get_name
	# the translated display string for the role, or unknown
	name: str

	def _get_name(self) -> str:
		try:
			role = controlTypes.Role(self.role)
			role.displayString
		except ValueError:
			role = controlTypes.Role.UNKNOWN
		return role.displayString
