# Android APK + Windows Uygulaması Geliştirme Paketi

Bu paket Ubuntu/Linux üzerinde Android APK/AAB üretmek ve Windows üzerinde aynı projeyi masaüstü uygulamasına derlemek için gereken kurulum scriptlerini, kontrol komutlarını ve resmi indirme adreslerini içerir.

## Önemli lisans notu

Android SDK, Android platform paketleri, Windows SDK, Visual Studio Build Tools, Flutter, Node.js ve benzeri büyük araçların tamamını arşivin içine kopyalamadım. Bunlar gigabaytlarca yer kaplayabilir, sürümleri hızla değişir ve bazıları kendi lisanslarıyla dağıtılır. Bunun yerine scriptler resmi kaynaklardan indirip kurar. Bu daha güvenli ve güncel yöntemdir.

## Klasörler

- `scripts/install-ubuntu-android.sh`: Ubuntu üzerinde JDK, Android command-line tools, platform-tools, build-tools, platform ve Flutter kurulumu.
- `scripts/check-ubuntu-android.sh`: Linux ortamı ve SDK doğrulama komutları.
- `scripts/install-windows-build-tools.ps1`: Windows üzerinde winget ile Git, 7-Zip, Flutter, Android Studio/SDK, Visual Studio Build Tools ve Node kurulumu için yardımcı script.
- `scripts/check-windows-build-tools.ps1`: Windows/Flutter/Android/Visual Studio doğrulaması.
- `scripts/build-apk.sh`: Flutter projesini temizleyip APK ve AAB üretir.
- `scripts/build-windows.ps1`: Flutter Windows masaüstü uygulaması üretir.
- `scripts/ci-android.yml`: GitHub Actions üzerinde Android APK/AAB üretimi için örnek workflow.
- `DOWNLOADS.md`: Resmi indirme adresleri ve hangi aracın ne için kullanıldığı.
- `ENVIRONMENT.md`: Ortam değişkenleri, lisans, imza ve güvenlik notları.

## Linux hızlı başlangıç

```bash
chmod +x scripts/*.sh
./scripts/install-ubuntu-android.sh
source "$HOME/.bashrc"
./scripts/check-ubuntu-android.sh
```

Flutter projenin bulunduğu klasörde:

```bash
../apk-windows-build-kit-2026-11-08/scripts/build-apk.sh
```

Üretilecek dosyalar:

- `build/app/outputs/flutter-apk/app-release.apk`
- `build/app/outputs/bundle/release/app-release.aab`

## Windows hızlı başlangıç

PowerShell'i mümkünse yönetici olarak aç:

```powershell
Set-ExecutionPolicy -Scope Process Bypass
.\scripts\install-windows-build-tools.ps1
.\scripts\check-windows-build-tools.ps1
```

Flutter projesinin kökünde:

```powershell
..\apk-windows-build-kit-2026-11-08\scripts\build-windows.ps1
```

Üretim klasörü:

- `build\windows\x64\runner\Release\`

## APK imzalama

Debug APK ile yayın APK'sı aynı değildir. Google Play için release keystore gerekir. Keystore'u Git'e koymayın, parolasını GitHub Secret olarak saklayın ve `key.properties` dosyasını `.gitignore` içine ekleyin. Bu kit otomatik olarak gizli keystore üretip repoya commit etmez.

## Repo durumu

Bu arşiv henüz bir GitHub reposuna push edilmedi; repo URL'si bekleniyor. Token korumalı Git secret alanına alındı ve kaynak dosyalara yazılmadı.
