$ErrorActionPreference = 'Stop'

Write-Host 'Windows geliştirme araçları kuruluyor...' -ForegroundColor Cyan
if (-not (Get-Command winget -ErrorAction SilentlyContinue)) {
  throw 'winget bulunamadı. Windows App Installer/Windows 10 1809+ veya Windows 11 gerekir.'
}

$apps = @(
  'Git.Git',
  '7zip.7zip',
  'Microsoft.OpenJDK.17',
  'Google.AndroidStudio',
  'Microsoft.VisualStudio.2022.BuildTools',
  'OpenJS.NodeJS.LTS'
)
foreach ($app in $apps) {
  winget install --id $app --exact --accept-source-agreements --accept-package-agreements
}

if (-not (Get-Command flutter -ErrorAction SilentlyContinue)) {
  Write-Host 'Flutter otomatik olarak PATH üzerinde yok. Resmi sayfadan Flutter stable indirin:' -ForegroundColor Yellow
  Write-Host 'https://docs.flutter.dev/get-started/install/windows'
}

Write-Host 'Kurulum tamamlandı. Yeni PowerShell açıp check-windows-build-tools.ps1 çalıştırın.' -ForegroundColor Green
