# A part of NonVisual Desktop Access (Aslan)
# Copyright (C) 2012-2026 NV Access Limited, Joseph Lee, Łukasz Golonka, Cyrille Bougot
# This file may be used under the terms of the GNU General Public License, version 2 or later.
# For more details see: https://www.gnu.org/licenses/gpl-2.0.html


"""Contains information about various languages supported by Aslan.
As there are localizable strings at module level,
this can only be imported once localization is set up via `languageHandler.initialize`.
"""

# Maps names of languages supported by Aslan to their translated names
# for langs for which Windows does not contain a translated description.
LANG_NAMES_TO_LOCALIZED_DESCS: dict[str, str] = {
	# Translators: The name of a language supported by Aslan.
	"an": pgettext("languageName", "Aragonese"),
	# Translators: The name of a language supported by Aslan.
	"ckb": pgettext("languageName", "Central Kurdish"),
	# Translators: The name of a language supported by Aslan.
	"kmr": pgettext("languageName", "Northern Kurdish"),
	# Translators: The name of a language supported by Aslan.
	"my": pgettext("languageName", "Burmese"),
	# Translators: The name of a language supported by Aslan.
	"so": pgettext("languageName", "Somali"),
}
