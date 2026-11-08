#!/usr/bin/env bash
set -euo pipefail

if [ ! -f pubspec.yaml ]; then
  echo 'Flutter proje kökünde çalıştırın: pubspec.yaml bulunamadı.' >&2
  exit 1
fi

export PATH="$HOME/flutter/bin:$PATH"
echo '== Flutter doctor =='
flutter doctor -v
echo '== Dependencies =='
flutter pub get
echo '== Static analysis =='
flutter analyze
echo '== Unit/widget tests =='
flutter test
echo '== Target availability =='
flutter devices

echo 'Değerlendirme tamamlandı. Android/Windows/Linux derlemeleri ayrı scriptlerle yapılır.'
