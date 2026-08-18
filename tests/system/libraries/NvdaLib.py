# A part of NonVisual Desktop Access (Aslan)
# Copyright (C) 2020 NV Access Limited
# This file may be used under the terms of the GNU General Public License, version 2 or later.
# For more details see: https://www.gnu.org/licenses/gpl-2.0.html

"""This file provides robot library functions for Aslan system tests.
It contains helper methods for system tests, most specifically related to Aslan
- setup config,
- starting
- quiting
- config cleanup
This is in contrast with the `SystemTestSpy/speechSpy*.py files,
which provide library functions related to monitoring Aslan and asserting Aslan output.
"""

# imported methods start with underscore (_) so they don't get imported into robot files as keywords
from datetime import datetime as _datetime
from os.path import (
	join as _pJoin,
	abspath as _abspath,
	expandvars as _expandvars,
	exists as _exists,
	splitext as _splitext,
	dirname as _dirname,
)
import tempfile as _tempFile
from typing import (
	Optional as _Optional,
	Tuple as _Tuple,
)
from urllib.parse import quote as _quoteStr

import typing
from robotremoteserver import (
	test_remote_server as _testRemoteServer,
	stop_remote_server as _stopRemoteServer,
)
from SystemTestSpy import (
	_blockUntilConditionMet,
	DEFAULT_INTERVAL_BETWEEN_EVAL_SECONDS,
	_getLib,
	_aslanSpyAlias,
	configManager,
)

if typing.TYPE_CHECKING:
	from SystemTestSpy.speechSpyGlobalPlugin import AslanSpyLib

# Imported for type information
from robot.libraries.BuiltIn import BuiltIn
from robot.libraries.OperatingSystem import OperatingSystem as _OpSysLib
from robot.libraries.Process import Process as _Process
from robot.libraries.Remote import Remote as _Remote

builtIn: BuiltIn = BuiltIn()
opSys: _OpSysLib = _getLib("OperatingSystem")
process: _Process = _getLib("Process")


class _NvdaLocationData:
	def __init__(self):
		# robot is expected to be run from the Aslan repo root directory. We want all repo specific
		# paths to be relative to this. This would allow us to change where it is run from if we decided to.
		self.repoRoot = _abspath("./")
		self.stagingDir = _tempFile.gettempdir()
		opSys.directory_should_exist(self.stagingDir)

		self.whichAslan = builtIn.get_variable_value("${whichAslan}", "source")
		self._installFilePath = builtIn.get_variable_value("${installDir}", None)
		self.AslanInstallerCommandline = None
		if self.whichAslan == "source":
			self._runAslanFilePath = _pJoin(self.repoRoot, "runaslan.bat")
			self.baseAslanCommandline = self._runAslanFilePath
		elif self.whichAslan == "installed":
			self._runAslanFilePath = self.findInstalledAslanPath()
			self.baseAslanCommandline = f'"{str(self._runAslanFilePath)}"'
			if self._installFilePath is not None:
				self.AslanInstallerCommandline = f'"{str(self._installFilePath)}"'
		else:
			raise AssertionError(
				"RobotFramework should be run with argument: '-v whichAslan:[source|installed]'",
			)

		self.profileDir = _pJoin(self.stagingDir, "aslanProfile")
		self.logPath = _pJoin(self.profileDir, "aslan.log")
		self.preservedLogsDir = _pJoin(
			builtIn.get_variable_value("${OUTPUT DIR}"),
			"aslanTestRunLogs",
		)

	def getPy2exeBootLogPath(self) -> _Optional[str]:
		if self.whichAslan == "installed":
			executablePath = _locations.findInstalledAslanPath()
			# py2exe names this log file after the executable, see py2exe/boot_common.py
			return _splitext(executablePath)[0] + ".log"
		elif self.whichAslan == "source":
			return None  # Py2exe not used for source.

	def findInstalledAslanPath(self) -> _Optional[str]:
		AslanFilePath = _pJoin(_expandvars("%PROGRAMFILES%"), "aslan", "aslan.exe")
		legacyAslanFilePath = _pJoin(_expandvars("%PROGRAMFILES%"), "Aslan", "aslan.exe")
		exeErrorMsg = f"Unable to find installed Aslan exe. Paths tried: {AslanFilePath}, {legacyAslanFilePath}"
		try:
			opSys.file_should_exist(AslanFilePath)
			return AslanFilePath
		except AssertionError:
			# Older versions of Aslan (<=2020.4) install the exe in Aslan\aslan.exe
			opSys.file_should_exist(legacyAslanFilePath, exeErrorMsg)
			return legacyAslanFilePath

	def ensureInstallerPathsExist(self):
		fileWarnMsg = f"Unable to run Aslan installer unless path exists. Path given: {self._installFilePath}"
		opSys.file_should_exist(self._installFilePath, fileWarnMsg)
		opSys.create_directory(self.profileDir)
		opSys.create_directory(self.preservedLogsDir)

	def ensurePathsExist(self):
		fileWarnMsg = f"Unable to run Aslan installer unless path exists. Path given: {self._runAslanFilePath}"
		opSys.file_should_exist(self._runAslanFilePath, fileWarnMsg)
		opSys.create_directory(self.profileDir)
		opSys.create_directory(self.preservedLogsDir)


_locations = _NvdaLocationData()


class NvdaLib:
	"""Robot Framework library for interacting with Aslan.
	Notable:
	- NvdaLib.aslanSpy is a library instance for getting speech and other information out of Aslan
	"""

	def __init__(self):
		self.aslanSpy: _Optional["AslanSpyLib"] = None
		self.aslanHandle: _Optional[int] = None
		self.lastAslanStart: _Optional[_datetime] = None

	@staticmethod
	def _createTestIdFileName(name):
		suiteName = builtIn.get_variable_value("${SUITE NAME}")
		testName = builtIn.get_variable_value("${TEST NAME}")
		outputFileName = f"{suiteName}-{testName}-{name}".replace(" ", "_")
		outputFileName = _quoteStr(outputFileName)
		return outputFileName

	@staticmethod
	def setup_aslan_profile(configFileName, gesturesFileName: _Optional[str] = None):
		configManager.setupProfile(
			_locations.repoRoot,
			configFileName,
			_locations.stagingDir,
			gesturesFileName,
		)

	@staticmethod
	def teardown_aslan_profile():
		configManager.teardownProfile(
			_locations.stagingDir,
		)

	aslanProcessAlias = "aslanAlias"
	_spyServerPort = 8270  # is `registered by IANA` for remote server usage. Two ASCII values:'RF'
	_spyServerURI = f"http://127.0.0.1:{_spyServerPort}"
	_spyAlias = _aslanSpyAlias

	def _startAslanProcess(self):
		"""Start Aslan.
		Use debug logging, replacing any current instance, using the system test profile directory
		"""
		_locations.ensurePathsExist()
		command = (
			f"{_locations.baseAslanCommandline}"
			f" --debug-logging"
			f" -r"
			f' -c "{_locations.profileDir}"'
			f' --log-file "{_locations.logPath}"'
		)
		self.aslanHandle = handle = process.start_process(
			command,
			shell=True,
			alias=self.aslanProcessAlias,
			stdout=_pJoin(_locations.preservedLogsDir, self._createTestIdFileName("stdout.txt")),
			stderr=_pJoin(_locations.preservedLogsDir, self._createTestIdFileName("stderr.txt")),
		)
		return handle

	def _startAslanInstallerProcess(self):
		"""Start Aslan Installer.
		Use debug logging, replacing any current instance, using the system test profile directory
		"""
		_locations.ensureInstallerPathsExist()
		command = (
			f"{_locations.AslanInstallerCommandline}"
			f" --debug-logging"
			f" -r"
			f' -c "{_locations.profileDir}"'
			f' --log-file "{_locations.logPath}"'
		)
		self.aslanHandle = handle = process.start_process(
			command,
			shell=True,
			alias=self.aslanProcessAlias,
			stdout=_pJoin(_locations.preservedLogsDir, self._createTestIdFileName("stdout.txt")),
			stderr=_pJoin(_locations.preservedLogsDir, self._createTestIdFileName("stderr.txt")),
		)
		return handle

	def _connectToRemoteServer(self, connectionTimeoutSecs: int = 15) -> None:
		"""Connects to the aslanSpyServer
		Because we do not know how far through the startup Aslan is, we have to poll
		to check that the server is available. Importing the library immediately seems
		to succeed, but then calling a keyword later fails with RuntimeError:
			"Connection to remote server broken: [Errno 10061]
				No connection could be made because the target machine actively refused it"
		Instead we wait until the remote server is available before importing the library and continuing.
		"""

		builtIn.log(f"Waiting for {self._spyAlias} to be available at: {self._spyServerURI}", level="DEBUG")
		# Importing the 'Remote' library always succeeds, even when a connection can not be made.
		# If that happens, then some 'Remote' keyword will fail at some later point.
		# therefore we use '_testRemoteServer' to ensure that we can in fact connect before proceeding.
		_blockUntilConditionMet(
			getValue=lambda: _testRemoteServer(self._spyServerURI, log=False),
			giveUpAfterSeconds=connectionTimeoutSecs,
			intervalBetweenSeconds=DEFAULT_INTERVAL_BETWEEN_EVAL_SECONDS,
			errorMessage=f"Unable to connect to {self._spyAlias}",
		)
		builtIn.log(f"Connecting to {self._spyAlias}", level="DEBUG")
		# If any remote call takes longer than this, the connection will be closed!
		maxRemoteKeywordDurationSeconds = 30
		builtIn.import_library(
			"Remote",  # name of library to import
			# Arguments to construct the library instance:
			f"uri={self._spyServerURI}",
			f"timeout={maxRemoteKeywordDurationSeconds}",
			# Set an alias for the imported library instance
			"WITH NAME",
			self._spyAlias,
		)
		builtIn.log(f"Getting {self._spyAlias} library instance", level="DEBUG")
		self.aslanSpy = self._addMethodsToSpy(builtIn.get_library_instance(self._spyAlias))
		# Ensure that keywords timeout before `timeout` given to `Remote` library,
		# otherwise we lose control over Aslan.
		self.aslanSpy.init_max_keyword_duration(maxSeconds=maxRemoteKeywordDurationSeconds)

	@staticmethod
	def _addMethodsToSpy(remoteLib: _Remote):
		"""Adds a method for each keywords on the remote library.
		@param remoteLib: the library to augment with methods.
		@rtype: SystemTestSpy.speechSpyGlobalPlugin.AslanSpyLib
		@return: The library augmented with methods for all keywords.
		"""

		# Add methods back onto the lib so they can be called directly rather than manually calling run_keyword
		def _makeKeywordCaller(lib, keyword):
			def runKeyword(*args, **kwargs):
				builtIn.log(
					f"{keyword}{f' {args}' if args else ''}{f' {kwargs}' if kwargs else ''}",
				)
				return lib.run_keyword(keyword, args, kwargs)

			return runKeyword

		for name in remoteLib.get_keyword_names():
			setattr(
				remoteLib,
				name,
				_makeKeywordCaller(remoteLib, name),
			)
		return remoteLib

	def start_AslanInstaller(self, settingsFileName):
		self.lastAslanStart = _datetime.utcnow()
		builtIn.log(f"Starting Aslan with config: {settingsFileName}")
		self.setup_aslan_profile(settingsFileName)
		aslanProcessHandle = self._startAslanInstallerProcess()
		process.process_should_be_running(aslanProcessHandle)
		# Timeout is increased due to the installer load time and start up splash sound
		self._connectToRemoteServer(connectionTimeoutSecs=30)
		self.aslanSpy.wait_for_Aslan_startup_to_complete()
		return aslanProcessHandle

	def enable_verbose_debug_logging_if_requested(self):
		builtIn.should_be_true(self.aslanSpy is not None)
		shouldEnableVerboseDebugLogging = bool(
			builtIn.get_variable_value("${verboseDebugLogging}", ""),
		)
		if shouldEnableVerboseDebugLogging:
			self.aslanSpy.modifyAslanConfig(
				[
					(["debugLog", "MSAA"], True),
					(["debugLog", "UIA"], True),
					(["debugLog", "timeSinceInput"], True),
				],
			)

	def start_Aslan(self, settingsFileName: str, gesturesFileName: _Optional[str] = None):
		self.lastAslanStart = _datetime.utcnow()
		builtIn.log(f"Starting Aslan with config: {settingsFileName}")
		self.setup_aslan_profile(settingsFileName, gesturesFileName)
		builtIn.log("Config copied", level="DEBUG")  # observe timing of the startup
		aslanProcessHandle = self._startAslanProcess()
		builtIn.log("Started Aslan process", level="DEBUG")  # observe timing of the startup
		process.process_should_be_running(aslanProcessHandle)
		self._connectToRemoteServer()
		builtIn.log("Connected to RF remote server", level="DEBUG")  # observe timing of the startup
		self.aslanSpy.wait_for_Aslan_startup_to_complete()
		builtIn.log("Startup complete", level="DEBUG")  # observe timing of the startup
		return aslanProcessHandle

	def save_Aslan_log(self):
		"""Aslan logs are saved to the ${OUTPUT DIR}/aslanTestRunLogs/${SUITE NAME}-${TEST NAME}-aslan.log"""
		builtIn.log("Saving Aslan log")
		saveToPath = self.create_preserved_test_output_filename("aslan.log")
		opSys.copy_file(
			_locations.logPath,
			saveToPath,
		)
		builtIn.log(f"Log saved to: {saveToPath}", level="DEBUG")

	def save_py2exe_boot_log(self):
		"""If a dialog shows: Errors in "aslan.exe", see the logfile at <path> for details.
		This orginates from
		py2exe boot logs are saved to
		${OUTPUT DIR}/aslanTestRunLogs/${SUITE NAME}-${TEST NAME}-py2exe-aslan.log
		"""
		copyFrom = _locations.getPy2exeBootLogPath()
		if not copyFrom or not _exists(copyFrom):
			builtIn.log("No py2exe log")
			return
		builtIn.log("Saving py2exe log")
		saveToPath = self.create_preserved_test_output_filename("py2exe-aslan.log")
		opSys.copy_file(
			copyFrom,
			saveToPath,
		)
		builtIn.log(f"py2exe log saved to: {saveToPath}", level="DEBUG")

	def create_preserved_test_output_filename(self, fileName):
		"""EG for aslan.log path will become:
		${OUTPUT DIR}/aslanTestRunLogs/${SUITE NAME}-${TEST NAME}-aslan.log
		"""
		return _pJoin(_locations.preservedLogsDir, self._createTestIdFileName(fileName))

	def _quitAslanProcessCleanup(self):
		self.save_Aslan_log()
		self.save_py2exe_boot_log()
		crashDmpPath = self.save_crash_dump_if_exists()
		# remove the spy so that if aslan is run manually against this config it does not interfere.
		self.teardown_aslan_profile()
		if crashDmpPath is not None:
			raise AssertionError(f"Aslan crashed during this test. Crash dump saved to: {crashDmpPath}")

	def quit_Aslan(self):
		builtIn.log("Stopping aslanSpy server: {}".format(self._spyServerURI))
		try:
			_stopRemoteServer(self._spyServerURI, log=False)
			process.run_process(
				f"{_locations.baseAslanCommandline} -q --disable-addons",
				shell=True,
			)
			process.wait_for_process(self.aslanHandle)
		except Exception:
			raise
		finally:
			self._quitAslanProcessCleanup()

	def quit_AslanInstaller(self):
		builtIn.log("Stopping aslanSpy server: {}".format(self._spyServerURI))
		self.aslanSpy.emulateKeyPress("insert+q")
		self.aslanSpy.wait_for_specific_speech("Exit Aslan")
		self.aslanSpy.emulateKeyPress("enter", blockUntilProcessed=False)
		builtIn.sleep(1)
		try:
			_stopRemoteServer(self._spyServerURI, log=False)
		except Exception:
			raise
		finally:
			self._quitAslanProcessCleanup()

	@staticmethod
	def check_for_crash_dump(
		since: _Optional[_datetime],
		overridePath: _Optional[str] = None,
	) -> _Optional[str]:
		"""
		Checks if a crash.dmp exits and returns the crash dmp path if so
		"""
		crashPath = overridePath or _pJoin(_dirname(_locations.logPath), "aslan_crash.dmp")
		try:
			opSys.file_should_not_exist(crashPath)
		except Exception:
			crashTime = opSys.get_modified_time(crashPath, format="epoch")
			crashTime = _datetime.fromtimestamp(crashTime)
			since = since.replace(microsecond=0)  # get_modified_time only reports seconds, not microseconds
			if crashTime >= since:
				return crashPath

	def save_crash_dump_if_exists(self, deleteCachedAfter: bool = True) -> _Optional[str]:
		crashPath = self.check_for_crash_dump(self.lastAslanStart)
		if crashPath is None:
			return None
		saveToPath = self.create_preserved_test_output_filename("aslan_crash.dmp")
		opSys.copy_file(
			crashPath,
			saveToPath,
		)
		if deleteCachedAfter:
			opSys.remove_file(crashPath)
			opSys.wait_until_removed(crashPath)
		return saveToPath


def getSpyLib() -> "AslanSpyLib":
	"""Gets the spy library instance. This has been augmented with methods for all supported keywords.
	Requires NvdaLib and aslanSpy (remote library - see speechSpyGlobalPlugin) to be initialised.
	On failure check order of keywords in Robot log and Aslan log for failures.
	@return: Remote Aslan spy Robot Framework library.
	"""
	aslanLib = _getLib("NvdaLib")
	spy = aslanLib.aslanSpy
	if spy is None:
		raise AssertionError("Spy not yet available, check order of keywords and Aslan log for errors.")
	return spy


def getSpeechAfterKey(key) -> str:
	"""Ensure speech has stopped, press key, and get speech until it stops.
	@return: The speech after key press.
	"""
	spy = getSpyLib()
	spy.wait_for_speech_to_finish()
	nextSpeechIndex = spy.get_next_speech_index()
	spy.emulateKeyPress(key)
	spy.wait_for_speech_to_finish(speechStartedIndex=nextSpeechIndex)
	speech = spy.get_speech_at_index_until_now(nextSpeechIndex)
	return speech


def getSpeechAndBrailleAfterKey(key) -> _Tuple[str, str]:
	"""Ensure speech has stopped, press key, and get speech until it stops, report the status of the
	braille display.
	@return: Tuple of Speech then Braille.
	"""
	spy = getSpyLib()
	spy.wait_for_speech_to_finish()

	nextSpeechIndex = spy.get_next_speech_index()
	nextBrailleIndex = spy.get_next_braille_index()

	spy.emulateKeyPress(key)

	spy.wait_for_speech_to_finish(speechStartedIndex=nextSpeechIndex)
	speech = spy.get_speech_at_index_until_now(nextSpeechIndex)

	spy.wait_for_braille_update(nextBrailleIndex)
	braille = spy.get_last_braille()

	return speech, braille
