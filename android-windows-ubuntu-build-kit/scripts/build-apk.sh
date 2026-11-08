#!/usr/bin/env bash
set -euo pipefail

if [ ! -f pubspec.yaml ]; then
  echo 'Bu script Flutter proje kökünde çalıştırılmalı: pubspec.yaml bulunamadı.' >&2
  exit 1
fi
flutter clean
flutter pub get
flutter analyze
flutter build apk --release
flutter build appbundle --release

echo 'APK: build/app/outputs/flutter-apk/app-release.apk'
echo 'AAB: build/app/outputs/bundle/release/app-release.aab'
