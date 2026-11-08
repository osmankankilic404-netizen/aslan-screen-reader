$ErrorActionPreference = 'Stop'
if (-not (Test-Path 'pubspec.yaml')) { throw 'Bu script Flutter proje kökünde çalıştırılmalı: pubspec.yaml bulunamadı.' }
flutter clean
flutter pub get
flutter analyze
flutter config --enable-windows-desktop
flutter build windows --release
Write-Host 'Windows çıktısı: build\windows\x64\runner\Release\' -ForegroundColor Green
