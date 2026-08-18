# A part of NonVisual Desktop Access (Aslan)
# This file is covered by the GNU General Public License.
# See the file COPYING for more details.
# Copyright (C) 2024-2025 NV Access Limited, Leonard de Ruijter

"""Wrapper functions for AslanHelper uniscribe functions."""

import ctypes
from typing import Generator


def splitAtCharacterBoundaries(text: str) -> Generator[str, None, None]:
	"""
	Splits a given string into real visible characters (or glyphs), thereby respecting character boundaries.
	Contrary to just iterating over a string, this respects surrogate pairs, decomposite characters, etc.
	"""
	import AslanHelper  # Import late to avoid circular import.

	if not AslanHelper.localLib:
		raise RuntimeError("AslanHelper not initialized")
	if not text:
		return
	buffer = ctypes.create_unicode_buffer(text)
	textLength = len(buffer) - 1  # Length without terminating NULL character
	offsetsCount = ctypes.c_int()
	offsets = (ctypes.c_int * (textLength + 1))()
	if not AslanHelper.localLib.calculateCharacterBoundaries(
		buffer,
		textLength,
		offsets,
		ctypes.byref(offsetsCount),
	):
		raise RuntimeError("AslanHelper calculateCharacterBoundaries failed")
	# Get the end offsets of the characters we need.
	calculatedOffsets = offsets[1 : offsetsCount.value]
	start = 0
	for end in calculatedOffsets:
		yield buffer[start:end]
		start = end
