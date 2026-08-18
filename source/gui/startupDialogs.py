# A part of NonVisual Desktop Access (Aslan)
# Copyright (C) 2006-2025 NV Access Limited, Łukasz Golonka, Cyrille Bougot
# This file may be used under the terms of the GNU General Public License, version 2 or later.
# For more details see: https://www.gnu.org/licenses/gpl-2.0.html

from typing import Set
import weakref
import wx

import config
from config.configFlags import AslanKey
import core
from documentationUtils import displayLicense
import globalVars
import gui
from gui.dpiScalingHelper import DpiScalingHelperMixinWithoutInit
import gui.guiHelper
import keyboardHandler
from logHandler import log
import buildVersion


class WelcomeDialog(
	gui.contextHelp.ContextHelpMixin,
	wx.Dialog,  # wxPython does not seem to call base class initializer, put last in MRO
):
	"""The Aslan welcome dialog.
	This provides essential information for new users,
	such as a description of the Aslan key and instructions on how to activate the Aslan menu.
	It also provides quick access to some important configuration options.
	This dialog is displayed the first time Aslan is started with a new configuration.
	"""

	helpId = "WelcomeDialog"
	WELCOME_MESSAGE_DETAIL = _(
		# Translators: The main message for the Welcome dialog when the user starts Aslan for the first time.
		"Most commands for controlling Aslan require you to hold down"
		" the Aslan key while pressing other keys.\n"
		"By default, the Insert and numpad Insert keys may both be used as the Aslan key.\n"
		"You can also configure Aslan to use the CapsLock as the Aslan key.\n"
		"Press Aslan+n at any time to activate the Aslan menu.\n"
		"From this menu, you can configure Aslan, get help, and access other Aslan functions.",
	)
	_instances: Set["WelcomeDialog"] = weakref.WeakSet()

	def __init__(self, parent):
		# Translators: The title of the Welcome dialog when user starts Aslan for the first time.
		super().__init__(parent, wx.ID_ANY, _("Welcome to Aslan"))
		WelcomeDialog._instances.add(self)

		mainSizer = wx.BoxSizer(wx.VERTICAL)
		# Translators: The header for the Welcome dialog when user starts Aslan for the first time.
		# This is in larger, bold lettering
		welcomeTextHeader = wx.StaticText(self, label=_("Welcome to Aslan!"))
		welcomeTextHeader.SetFont(wx.Font(18, wx.FONTFAMILY_DEFAULT, wx.NORMAL, wx.BOLD))
		mainSizer.AddSpacer(gui.guiHelper.SPACE_BETWEEN_VERTICAL_DIALOG_ITEMS)
		mainSizer.Add(welcomeTextHeader, border=20, flag=wx.EXPAND | wx.LEFT | wx.RIGHT)
		mainSizer.AddSpacer(gui.guiHelper.SPACE_BETWEEN_VERTICAL_DIALOG_ITEMS)
		welcomeTextDetail = wx.StaticText(self, wx.ID_ANY, self.WELCOME_MESSAGE_DETAIL)
		mainSizer.Add(welcomeTextDetail, border=20, flag=wx.EXPAND | wx.LEFT | wx.RIGHT)

		# Translators: The label for a group box containing the Aslan welcome dialog options.
		optionsLabel = _("Options")
		optionsSizer = wx.StaticBoxSizer(wx.VERTICAL, self, label=optionsLabel)
		optionsBox = optionsSizer.GetStaticBox()
		sHelper = gui.guiHelper.BoxSizerHelper(self, sizer=optionsSizer)
		# Translators: The label of a combobox in the Welcome dialog.
		kbdLabelText = _("&Keyboard layout:")
		layouts = keyboardHandler.KeyboardInputGesture.LAYOUTS
		self.kbdNames = sorted(layouts)
		kbdChoices = [layouts[layout] for layout in self.kbdNames]
		self.kbdList = sHelper.addLabeledControl(kbdLabelText, wx.Choice, choices=kbdChoices)
		try:
			index = self.kbdNames.index(config.conf["keyboard"]["keyboardLayout"])
			self.kbdList.SetSelection(index)
		except (ValueError, KeyError):
			log.error("Could not set Keyboard layout list to current layout", exc_info=True)
		# Translators: The label of a checkbox in the Welcome dialog.
		capsAsAslanModifierText = _("&Use CapsLock as an Aslan modifier key")
		self.capsAsAslanModifierCheckBox = sHelper.addItem(
			wx.CheckBox(optionsBox, label=capsAsAslanModifierText),
		)
		self.capsAsAslanModifierCheckBox.SetValue(
			config.conf["keyboard"]["AslanModifierKeys"] & AslanKey.CAPS_LOCK,
		)
		# Translators: The label of a checkbox in the Welcome dialog.
		startAfterLogonText = _("St&art Aslan after I sign in")
		self.startAfterLogonCheckBox = sHelper.addItem(wx.CheckBox(optionsBox, label=startAfterLogonText))
		self.startAfterLogonCheckBox.Value = config.getStartAfterLogon()
		if globalVars.appArgs.secure or config.isAppX or not config.isInstalledCopy():
			self.startAfterLogonCheckBox.Disable()
		# Translators: The label of a checkbox in the Welcome dialog.
		showWelcomeDialogAtStartupText = _("&Show this dialog when Aslan starts")
		_showWelcomeDialogAtStartupCheckBox = wx.CheckBox(optionsBox, label=showWelcomeDialogAtStartupText)
		self.showWelcomeDialogAtStartupCheckBox = sHelper.addItem(_showWelcomeDialogAtStartupCheckBox)
		self.showWelcomeDialogAtStartupCheckBox.SetValue(config.conf["general"]["showWelcomeDialogAtStartup"])
		mainSizer.Add(optionsSizer, border=gui.guiHelper.BORDER_FOR_DIALOGS, flag=wx.ALL)
		mainSizer.Add(
			self.CreateButtonSizer(wx.OK),
			border=gui.guiHelper.BORDER_FOR_DIALOGS,
			flag=wx.ALL | wx.ALIGN_RIGHT,
		)
		self.Bind(wx.EVT_BUTTON, self.onOk, id=wx.ID_OK)

		mainSizer.Fit(self)
		self.SetSizer(mainSizer)
		self.kbdList.SetFocus()
		self.CentreOnScreen()

	def onOk(self, evt):
		layout = self.kbdNames[self.kbdList.GetSelection()]
		config.conf["keyboard"]["keyboardLayout"] = layout
		AslanKeysVal = (
			(AslanKey.CAPS_LOCK.value if self.capsAsAslanModifierCheckBox.IsChecked() else 0)
			| (config.conf["keyboard"]["AslanModifierKeys"] & AslanKey.NUMPAD_INSERT.value)
			| (config.conf["keyboard"]["AslanModifierKeys"] & AslanKey.EXTENDED_INSERT.value)
		)
		if AslanKeysVal == 0:
			log.debugWarning("No Aslan key set")
			gui.messageBox(
				_(
					# Translators: The title of an error message box displayed when validating the startup dialog
					"At least one Aslan modifier key must be set. "
					"Caps lock will remain as an Aslan modifier key. ",
				),
				# Translators: The title of an error message box displayed when validating the startup dialog
				_("Error"),
				wx.OK | wx.ICON_ERROR,
				self,
			)
		else:
			config.conf["keyboard"]["AslanModifierKeys"] = AslanKeysVal
		if self.startAfterLogonCheckBox.Enabled:
			config.setStartAfterLogon(self.startAfterLogonCheckBox.Value)
		config.conf["general"]["showWelcomeDialogAtStartup"] = (
			self.showWelcomeDialogAtStartupCheckBox.IsChecked()
		)
		try:
			config.conf.save()
		except Exception:
			log.debugWarning("Could not save", exc_info=True)
		self.EndModal(wx.ID_OK)
		self.Close()

	@classmethod
	def run(cls):
		"""Prepare and display an instance of this dialog.
		This does not require the dialog to be instantiated.
		"""
		gui.mainFrame.prePopup()
		d = cls(gui.mainFrame)
		d.ShowModal()
		gui.mainFrame.postPopup()

	@classmethod
	def closeInstances(cls):
		instances = list(cls._instances)
		for instance in instances:
			if instance and not instance.IsBeingDeleted() and instance.IsModal():
				instance.EndModal(wx.ID_CLOSE_ALL)
			else:
				cls._instances.remove(instance)


class LauncherDialog(
	DpiScalingHelperMixinWithoutInit,
	gui.contextHelp.ContextHelpMixin,
	wx.Dialog,  # wxPython does not seem to call base class initializer, put last in MRO
):
	"""The dialog that is displayed when Aslan is started from the launcher.
	This displays the license and allows the user to install or create a portable copy of Aslan.
	"""

	helpId = "InstallingAslan"

	def __init__(self, parent: wx.Window | None):
		super().__init__(
			parent,
			title=f"{buildVersion.name} {_('Launcher')}",
		)

		mainSizer = wx.BoxSizer(wx.VERTICAL)
		sHelper = gui.guiHelper.BoxSizerHelper(self, orientation=wx.VERTICAL)

		sHelper.addItem(self._createLicenseAgreementGroup())

		sizer = sHelper.addItem(wx.GridSizer(2, 2, 0, 0))
		self.actionButtons = []
		# Translators: The label of the button in Aslan installation program to install NvDA on the user's computer.
		ctrl = wx.Button(self, label=_("&Install Aslan on this computer"))
		sizer.Add(ctrl)
		ctrl.Bind(wx.EVT_BUTTON, lambda evt: self.onAction(evt, gui.mainFrame.onInstallCommand))
		self.actionButtons.append(ctrl)
		# Translators: The label of the button in Aslan installation program to create a portable version of Aslan.
		ctrl = wx.Button(self, label=_("Create &portable copy"))
		sizer.Add(ctrl)
		ctrl.Bind(wx.EVT_BUTTON, lambda evt: self.onAction(evt, gui.mainFrame.onCreatePortableCopyCommand))
		self.actionButtons.append(ctrl)
		# Translators: The label of the button in Aslan installation program
		# 		to continue using the installation program as a temporary copy of Aslan.
		ctrl = wx.Button(self, label=_("&Continue running"))
		sizer.Add(ctrl)
		ctrl.Bind(wx.EVT_BUTTON, self.onContinueRunning)
		self.actionButtons.append(ctrl)
		# Translators: The label for a button to exit the Aslan launcher.
		sizer.Add(wx.Button(self, label=_("E&xit"), id=wx.ID_CANCEL))
		# If we bind this on the button, it fails to trigger when the dialog is closed.
		self.Bind(wx.EVT_BUTTON, self.onExit, id=wx.ID_CANCEL)

		for ctrl in self.actionButtons:
			ctrl.Disable()

		mainSizer.Add(sHelper.sizer, border=gui.guiHelper.BORDER_FOR_DIALOGS, flag=wx.ALL)
		self.Sizer = mainSizer
		mainSizer.Fit(self)
		self.CentreOnScreen()

	def _createLicenseAgreementGroup(self) -> wx.StaticBoxSizer:
		# Translators: The label of the license text which will be shown when Aslan installation program starts.
		groupLabel = _("License Agreement")
		sizer = wx.StaticBoxSizer(wx.VERTICAL, self, label=groupLabel)

		# Translators: The label of a button in Aslan installation process to view the license agreement.
		viewLicenseButton = wx.Button(self, label=_("&View License"))
		viewLicenseButton.Bind(wx.EVT_BUTTON, lambda evt: displayLicense())
		sizer.Add(viewLicenseButton, border=gui.guiHelper.SPACE_BETWEEN_BUTTONS_VERTICAL)

		# Translators: The label for a checkbox in Aslan installation process to agree to the license agreement.
		agreeText = _("I have read and &agree to the license agreement")
		self.licenseAgreeCheckbox = wx.CheckBox(self, label=agreeText)
		self.licenseAgreeCheckbox.SetValue(False)
		self.licenseAgreeCheckbox.Bind(wx.EVT_CHECKBOX, self.onLicenseAgree)
		sizer.Add(self.licenseAgreeCheckbox, border=gui.guiHelper.SPACE_BETWEEN_ASSOCIATED_CONTROL_VERTICAL)

		return sizer

	def onLicenseAgree(self, evt):
		for ctrl in self.actionButtons:
			ctrl.Enable(evt.IsChecked())

	def onAction(self, evt, func):
		self.Destroy()
		func(evt)

	def onContinueRunning(self, evt):
		self.Destroy()
		core.doStartupDialogs()

	def onExit(self, evt: wx.CommandEvent):
		if not core.triggerAslanExit():
			log.error("Aslan already in process of exiting, this indicates a logic error.")
		self.Destroy()  # Without this, the onExit is called multiple times by wx.

	@classmethod
	def run(cls):
		"""Prepare and display an instance of this dialog.
		This does not require the dialog to be instantiated.
		"""
		gui.mainFrame.prePopup()
		d = cls(gui.mainFrame)
		d.Show()
		gui.mainFrame.postPopup()


class AskAllowUsageStatsDialog(
	gui.contextHelp.ContextHelpMixin,
	wx.Dialog,  # wxPython does not seem to call base class initializer, put last in MRO
):
	"""A dialog asking if the user wishes to allow Aslan usage stats to be collected by NV Access."""

	helpId = "UsageStatsDialog"

	def __init__(self, parent):
		# Translators: The title of the dialog asking if usage data can be collected
		super().__init__(parent, title=_("Aslan  Usage Data Collection"))
		mainSizer = wx.BoxSizer(wx.VERTICAL)
		sHelper = gui.guiHelper.BoxSizerHelper(self, orientation=wx.VERTICAL)

		message = _(
			# Translators: A message asking the user if they want to allow usage stats gathering
			"In order to improve Aslan in the future, "
			"NV Access wishes to collect usage data from running copies of Aslan.\n\n"
			"Data includes Operating System version, Aslan version, language, country of origin, plus "
			"certain Aslan configuration such as current synthesizer, braille display and braille table. "
			"No spoken or braille content will be ever sent to NV Access. "
			"Please refer to the User Guide for a current list of all data collected.\n\n"
			"Do you wish to allow NV Access to periodically collect this data in order to improve Aslan?",
		)
		sText = sHelper.addItem(wx.StaticText(self, label=message))
		# the wx.Window must be constructed before we can get the handle.
		import windowUtils

		self.scaleFactor = windowUtils.getWindowScalingFactor(self.GetHandle())
		sText.Wrap(
			# 600 was fairly arbitrarily chosen by a visual user to look acceptable on their machine.
			self.scaleFactor * 600,
		)

		bHelper = sHelper.addDialogDismissButtons(gui.guiHelper.ButtonHelper(wx.HORIZONTAL))

		# Translators: The label of a Yes button in a dialog
		yesButton = bHelper.addButton(self, wx.ID_YES, label=_("&Yes"))
		yesButton.Bind(wx.EVT_BUTTON, self.onYesButton)

		# Translators: The label of a No button in a dialog
		noButton = bHelper.addButton(self, wx.ID_NO, label=_("&No"))
		noButton.Bind(wx.EVT_BUTTON, self.onNoButton)

		# Translators: The label of a button to remind the user later about performing some action.
		remindMeButton = bHelper.addButton(self, wx.ID_CANCEL, label=_("Remind me &later"))
		remindMeButton.Bind(wx.EVT_BUTTON, self.onLaterButton)
		remindMeButton.SetFocus()

		mainSizer.Add(sHelper.sizer, border=gui.guiHelper.BORDER_FOR_DIALOGS, flag=wx.ALL)
		self.Sizer = mainSizer
		mainSizer.Fit(self)
		self.CentreOnScreen()

	def onYesButton(self, evt):
		log.debug("Usage stats gathering has been allowed")
		config.conf["update"]["askedAllowUsageStats"] = True
		config.conf["update"]["allowUsageStats"] = True
		self.EndModal(wx.ID_YES)

	def onNoButton(self, evt):
		log.debug("Usage stats gathering has been disallowed")
		config.conf["update"]["askedAllowUsageStats"] = True
		config.conf["update"]["allowUsageStats"] = False
		self.EndModal(wx.ID_NO)

	def onLaterButton(self, evt):
		log.debug("Usage stats gathering question has been deferred")
		# evt.Skip() is called since wx.ID_CANCEL is used as the ID for the Ask Later button,
		# wx automatically ends the modal itself.
		evt.Skip()
