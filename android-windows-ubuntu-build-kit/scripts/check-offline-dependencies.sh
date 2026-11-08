#!/usr/bin/env bash
set -u
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VENDOR="$ROOT/vendor"
status=0
for item in flutter-sdk jdk-17 android-sdk-tools.zip android-platforms windows-build-tools windows-sdk; do
  if [ -e "$VENDOR/$item" ]; then
    printf '[OK]   %s\n' "$item"
  else
    printf '[MISS] %s\n' "$item"
    status=1
  fi
done
if [ "$status" -ne 0 ]; then
  echo 'Eksik vendor dosyaları var. Scriptler uydurma paket indirmez; lisanslı dosyaları vendor/ içine koyun.'
  exit 1
fi
echo 'Tüm offline vendor bağımlılıkları mevcut.'
