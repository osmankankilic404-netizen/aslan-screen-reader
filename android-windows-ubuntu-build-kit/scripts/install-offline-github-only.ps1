$ErrorActionPreference = 'Stop'
$Root = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
$Vendor = if ($env:VENDOR_DIR) { $env:VENDOR_DIR } else { Join-Path $Root 'vendor' }

function Fail($Message) { throw "OFFLINE KURULUM DURDU: $Message" }

$flutterVendor = Join-Path $Vendor 'flutter-sdk'
$flutter = Get-Command flutter -ErrorAction SilentlyContinue
if (-not $flutter -and -not (Test-Path (Join-Path $flutterVendor 'bin\flutter.bat'))) {
  Fail "Flutter bulunamadı. GitHub'dan edinilmiş SDK'yı vendor\flutter-sdk içine koyun."
}

$androidZip = Join-Path $Vendor 'android-sdk-tools.zip'
if (-not (Test-Path $androidZip) -and -not $env:ANDROID_HOME) {
  Fail "Android SDK bulunamadı. vendor\android-sdk-tools.zip veya ANDROID_HOME sağlayın."
}

if (Test-Path (Join-Path $Vendor 'jdk-17')) {
  $env:JAVA_HOME = Join-Path $Vendor 'jdk-17'
}

if (Test-Path (Join-Path $Vendor 'flutter-sdk\bin\flutter.bat')) {
  $env:Path = (Join-Path $Vendor 'flutter-sdk\bin') + ';' + $env:Path
}

flutter doctor -v
flutter config --enable-windows-desktop
Write-Host 'GitHub-only/offline Windows kurulumu doğrulandı; ağ çağrısı yapılmadı.' -ForegroundColor Green
