#!/usr/bin/env bash
set -euo pipefail

# Android + Flutter Android + Flutter Linux desktop dependencies.
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
"$SCRIPT_DIR/install-ubuntu-android.sh"

sudo apt-get update
sudo apt-get install -y \
  clang cmake ninja-build pkg-config libgtk-3-dev liblzma-dev \
  libstdc++-12-dev libglu1-mesa libasound2-dev libpulse-dev \
  libx11-dev libxcomposite-dev libxdamage-dev libxext-dev \
  libxfixes-dev libxi-dev libxrandr-dev libsecret-1-dev

export PATH="$HOME/flutter/bin:$PATH"
flutter config --enable-linux-desktop
flutter precache --linux
flutter doctor -v

echo "Ubuntu Android + Linux desktop Flutter ortamı hazır."
