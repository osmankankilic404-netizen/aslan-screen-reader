#!/usr/bin/env bash
set -euo pipefail
export ANDROID_HOME="${ANDROID_HOME:-$HOME/Android/Sdk}"
export ANDROID_SDK_ROOT="${ANDROID_SDK_ROOT:-$ANDROID_HOME}"
export PATH="$PATH:$ANDROID_HOME/platform-tools:$ANDROID_HOME/cmdline-tools/latest/bin:$HOME/flutter/bin"

echo '--- versions ---'
java -version
flutter --version
sdkmanager --version
adb version

echo '--- flutter doctor ---'
flutter doctor -v

echo '--- Android packages ---'
sdkmanager --list_installed | sed -n '1,100p'
