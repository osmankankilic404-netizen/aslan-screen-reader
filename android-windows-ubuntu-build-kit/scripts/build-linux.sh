#!/usr/bin/env bash
set -euo pipefail

if [ ! -f pubspec.yaml ]; then
  echo 'Bu script Flutter proje kökünde çalıştırılmalı: pubspec.yaml bulunamadı.' >&2
  exit 1
fi
export PATH="$HOME/flutter/bin:$PATH"
flutter config --enable-linux-desktop
flutter clean
flutter pub get
flutter analyze
flutter test
flutter build linux --release

echo 'Linux çıktısı: build/linux/x64/release/bundle/'
