#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VENDOR="${VENDOR_DIR:-$ROOT/vendor}"
ANDROID_HOME="${ANDROID_HOME:-$HOME/Android/Sdk}"
FLUTTER_DIR="${FLUTTER_DIR:-$HOME/flutter}"

fail() { echo "OFFLINE KURULUM DURDU: $*" >&2; exit 1; }

command -v unzip >/dev/null || fail 'unzip eksik; Ubuntu paket yöneticisi veya önceden hazırlanmış sistem imajı gerekir.'
command -v java >/dev/null || fail 'Java/JDK eksik; vendor/jdk-17 veya sistem JDK 17 sağlayın.'

if [ -d "$VENDOR/flutter-sdk" ]; then
  mkdir -p "$(dirname "$FLUTTER_DIR")"
  rm -rf "$FLUTTER_DIR"
  cp -a "$VENDOR/flutter-sdk" "$FLUTTER_DIR"
elif [ ! -x "$FLUTTER_DIR/bin/flutter" ]; then
  fail "Flutter bulunamadı. Yalnızca GitHub'dan indirilmiş/lisanslı SDK'yı $VENDOR/flutter-sdk içine koyun."
fi

if [ -f "$VENDOR/android-sdk-tools.zip" ]; then
  mkdir -p "$ANDROID_HOME/cmdline-tools"
  rm -rf "$ANDROID_HOME/cmdline-tools/latest" "$ROOT/.offline-tools"
  mkdir -p "$ROOT/.offline-tools"
  unzip -q "$VENDOR/android-sdk-tools.zip" -d "$ROOT/.offline-tools"
  mv "$ROOT/.offline-tools/cmdline-tools" "$ANDROID_HOME/cmdline-tools/latest"
fi

if [ ! -x "$ANDROID_HOME/cmdline-tools/latest/bin/sdkmanager" ]; then
  fail "Android sdkmanager bulunamadı. Lisanslı tools zip'ini $VENDOR/android-sdk-tools.zip olarak sağlayın."
fi

export ANDROID_HOME ANDROID_SDK_ROOT="$ANDROID_HOME"
export PATH="$FLUTTER_DIR/bin:$ANDROID_HOME/platform-tools:$ANDROID_HOME/cmdline-tools/latest/bin:$PATH"
flutter config --android-sdk "$ANDROID_HOME"
flutter config --enable-linux-desktop
flutter doctor -v

echo 'GitHub-only/offline Ubuntu kurulumu doğrulandı; ağ çağrısı yapılmadı.'
