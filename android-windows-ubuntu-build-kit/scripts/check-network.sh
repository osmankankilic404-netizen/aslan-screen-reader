#!/usr/bin/env bash
set -u

check_url() {
  name="$1"; url="$2"
  if curl -fsSI --connect-timeout 5 --max-time 12 "$url" >/dev/null 2>&1; then
    printf '[OK]   %s — %s\n' "$name" "$url"
    return 0
  fi
  printf '[MISS] %s — %s\n' "$name" "$url"
  return 1
}

command -v curl >/dev/null || { echo 'curl bulunamadı.'; exit 1; }
status=0
check_url 'GitHub' 'https://github.com' || status=1
check_url 'GitHub raw' 'https://raw.githubusercontent.com' || status=1
check_url 'Android resmi' 'https://developer.android.com' || status=1
check_url 'Flutter docs' 'https://docs.flutter.dev' || status=1
check_url 'Microsoft' 'https://visualstudio.microsoft.com' || status=1
check_url 'npm registry' 'https://registry.npmjs.org' || status=1

if [ "$status" -eq 0 ]; then
  echo 'Normal internet modu kullanılabilir.'
else
  echo 'Bazı adresler erişilemiyor. GitHub-only/offline mod için vendor klasörünü kullanın.'
fi
exit 0
