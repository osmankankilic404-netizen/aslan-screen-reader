#!/usr/bin/env bash
set -euo pipefail

ANDROID_HOME="${ANDROID_HOME:-$HOME/Android/Sdk}"
ANDROID_CMDLINE_TOOLS_URL="${ANDROID_CMDLINE_TOOLS_URL:-https://dl.google.com/android/repository/commandlinetools-linux-11076708_latest.zip}"
FLUTTER_DIR="${FLUTTER_DIR:-$HOME/flutter}"

sudo apt-get update
sudo apt-get install -y curl unzip git xz-utils zip libglu1-mesa openjdk-17-jdk clang cmake ninja-build pkg-config libgtk-3-dev libstdc++-12-dev

mkdir -p "$ANDROID_HOME/cmdline-tools" "$HOME/.cache/android-kit"
curl -fL "$ANDROID_CMDLINE_TOOLS_URL" -o "$HOME/.cache/android-kit/commandlinetools.zip"
rm -rf "$ANDROID_HOME/cmdline-tools/latest" "$HOME/.cache/android-kit/cmdline-tools"
unzip -q "$HOME/.cache/android-kit/commandlinetools.zip" -d "$HOME/.cache/android-kit"
mv "$HOME/.cache/android-kit/cmdline-tools" "$ANDROID_HOME/cmdline-tools/latest"

mkdir -p "$HOME/.config/flutter"
if [ ! -d "$FLUTTER_DIR" ]; then
  git clone --depth 1 --branch stable https://github.com/flutter/flutter.git "$FLUTTER_DIR"
else
  git -C "$FLUTTER_DIR" pull --ff-only
fi

cat >> "$HOME/.bashrc" <<EOF
export ANDROID_HOME="$ANDROID_HOME"
export ANDROID_SDK_ROOT="$ANDROID_HOME"
export PATH="\$PATH:$ANDROID_HOME/platform-tools:$ANDROID_HOME/cmdline-tools/latest/bin:$FLUTTER_DIR/bin"
EOF
export ANDROID_HOME ANDROID_SDK_ROOT
export PATH="$PATH:$ANDROID_HOME/platform-tools:$ANDROID_HOME/cmdline-tools/latest/bin:$FLUTTER_DIR/bin"

yes | sdkmanager --licenses >/dev/null || true
sdkmanager "platform-tools" "platforms;android-35" "build-tools;35.0.0" "cmdline-tools;latest"
flutter config --android-sdk "$ANDROID_HOME"
flutter precache --android
flutter doctor -v

echo "Ubuntu Android/Flutter ortamı hazır. Yeni terminal açın veya source ~/.bashrc çalıştırın."
