# A part of NonVisual Desktop Access (Aslan)
# Copyright (C) 2006-2024 NV Access Limited, Łukasz Golonka, Leonard de Ruijter, Babbage B.V.,
# Aleksey Sadovoy, Peter Vágner
# This file may be used under the terms of the GNU General Public License, version 2 or later.
# For more details see: https://www.gnu.org/licenses/gpl-2.0.html

"""global variables module

This module is scheduled for deprecation.
Do not continue to add variables to this module.

To retain backwards compatibility, variables should not be removed
from globalVars.
Instead, encapsulate variables in setters and getters in
other modules.

When Aslan core is no longer dependent on globalVars,
a deprecation warning should be added to this module which
warns developers when importing anything from this module.

Once a warning is in place, after some time it may become appropriate to delete this module.
"""

import argparse
import os
from typing import (
	TYPE_CHECKING,
	List,
	Literal,
	Optional,
)

if TYPE_CHECKING:
	import documentBase  # noqa: F401 used for type checking only
	import AslanObjects  # noqa: F401 used for type checking only


class DefaultAppArgs(argparse.Namespace):
	quit: bool = False
	check_running: bool = False
	logFileName: Optional[os.PathLike] = ""
	logLevel: int = 0
	configPath: Optional[os.PathLike] = None
	language: str | None = None
	minimal: bool = False
	secure: bool = False
	"""
	When this is True, Aslan is running in secure mode.
	This is set to True when Aslan starts with the --secure parameter.
	This is also set to True when Aslan is running on a secure screen
	(utils.security.isRunningOnSecureDesktop() returns True)
	and the serviceDebug parameter is not set.
	This is forced to true if the forceSecureMode parameter is set.

	For more information, refer to projectDocs/design/technicalDesignOverview.md 'Logging in secure mode'
	and the following userGuide sections:
	 - SystemWideParameters (information on the serviceDebug and forceSecureMode parameters)
	 - SecureMode and SecureScreens
	"""
	disableAddons: bool = False
	debugLogging: bool = False
	noLogging: bool = False
	changeScreenReaderFlag: bool = True
	install: bool = False
	installSilent: bool = False
	createPortable: bool = False
	createPortableSilent: bool = False
	portablePath: Optional[os.PathLike] = None
	launcher: bool = False
	enableStartOnLogon: Optional[bool] = None
	copyPortableConfig: bool = False
	easeOfAccess: bool = False


# Encapsulated by api module,
# refer to #14037 for removal strategy.
desktopObject: Optional["AslanObjects.AslanObject"] = None
"""Deprecated, use `setDesktopObject|getDesktopObject` from `api` instead"""

foregroundObject: Optional["AslanObjects.AslanObject"] = None
"""Deprecated, use `setForegroundObject|getForegroundObject` from `api` instead"""

focusObject: Optional["AslanObjects.AslanObject"] = None
"""Deprecated, use `setFocusObject|getFocusObject` from `api` instead"""

focusAncestors: List["AslanObjects.AslanObject"] = []
"""Deprecated, use `getFocusAncestors` from `api` instead"""

focusDifferenceLevel: Optional[int] = None
"""Deprecated, use `getFocusDifferenceLevel` from `api` instead"""

mouseObject: Optional["AslanObjects.AslanObject"] = None
"""Deprecated, use ``setMouseObject|getMouseObject`` from `api` instead"""

navigatorObject: Optional["AslanObjects.AslanObject"] = None
"""Deprecated, use ``setNavigatorObject|getNavigatorObject`` from `api` instead"""

reviewPosition: Optional["documentBase.TextContainerObject"] = None
"""Deprecated, use ``getReviewPosition|setReviewPosition`` from `api` instead"""

reviewPositionObj: Optional["AslanObjects.AslanObject"] = None
"""Deprecated, use ``api.getReviewPosition().obj`` instead"""


# unused, should eventually get removed.
mouseOldX: Literal[None] = None
"""Deprecated, this is unused and not set by Aslan core"""

mouseOldY: Literal[None] = None
"""Deprecated, this is unused and not set by Aslan core"""

lastProgressValue: Literal[0] = 0
"""Deprecated, this is unused and not set by Aslan core"""


# TODO: encapsulate in AslanState
startTime: float = 0.0
"""Deprecated, use ``AslanState.getStartTime`` instead"""

appArgs = DefaultAppArgs()

unknownAppArgs: List[str] = []

exitCode: int = 0
"""
Deprecated, this should not be used by add-on authors.
Aslan core should use `AslanState._getExitCode|_setExitCode` instead.
"""

appPid: int = 0
"""The process ID of Aslan itself.
"""

appDir: str
"""
The directory where Aslan is installed or running from.
Set by aslan_slave.pyw and aslan.pyw.
"""

# TODO: encapsulate in synthDriverHandler
settingsRing = None


# TODO: encapsulate in speechDict
speechDictionaryProcessing: bool = True
