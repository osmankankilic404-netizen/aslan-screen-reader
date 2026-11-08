$ErrorActionPreference = 'Continue'
Write-Host '--- versions ---' -ForegroundColor Cyan
where.exe flutter
flutter --version
flutter doctor -v
where.exe adb
adb version
where.exe java
java -version
where.exe git
git --version
Write-Host '--- Visual Studio / Windows desktop ---' -ForegroundColor Cyan
flutter config --list
flutter devices
