# Ortam, imzalama ve güvenlik

## Ubuntu

Önerilen değişkenler:

```bash
export ANDROID_HOME="$HOME/Android/Sdk"
export ANDROID_SDK_ROOT="$ANDROID_HOME"
export PATH="$PATH:$ANDROID_HOME/platform-tools:$ANDROID_HOME/cmdline-tools/latest/bin:$HOME/flutter/bin"
```

## Windows

Android Studio veya sdkmanager kurulumundan sonra `ANDROID_HOME` ve `ANDROID_SDK_ROOT` değerlerini Android SDK klasörüne ayarlayın. Flutter `flutter doctor -v` ile doğrulayın.

## Release imzası

Keystore ve `key.properties` repoya konulmamalıdır. GitHub Actions Secrets kullanın:

- `ANDROID_KEYSTORE_BASE64`
- `ANDROID_KEYSTORE_PASSWORD`
- `ANDROID_KEY_ALIAS`
- `ANDROID_KEY_PASSWORD`

Debug APK test içindir. Google Play dağıtımı için release imzalama, package/application ID, versionCode/versionName ve Play App Signing ayarları gerekir.

## Güvenlik

- GitHub tokenını sohbete, script içine, `.env` dosyasına veya Git geçmişine yazmayın.
- Token yalnızca korumalı secret/connector alanında tutulmalıdır.
- Paylaşılmış bir tokenı GitHub ayarlarından iptal edip yenileyin.
- Keystore, sertifika, Windows signing certificate ve parolaları repoya commit etmeyin.
- Resmi olmayan APK/SDK mirror'larından indirme yapmayın.
- Installer scriptlerini çalıştırmadan önce diff ile inceleyin.
