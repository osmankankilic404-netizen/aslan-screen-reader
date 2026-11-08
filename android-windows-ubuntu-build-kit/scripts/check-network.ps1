$ErrorActionPreference = 'Continue'
$targets = @(
  @{ Name = 'GitHub'; Url = 'https://github.com' },
  @{ Name = 'GitHub raw'; Url = 'https://raw.githubusercontent.com' },
  @{ Name = 'Android resmi'; Url = 'https://developer.android.com' },
  @{ Name = 'Flutter docs'; Url = 'https://docs.flutter.dev' },
  @{ Name = 'Microsoft'; Url = 'https://visualstudio.microsoft.com' },
  @{ Name = 'npm registry'; Url = 'https://registry.npmjs.org' }
)
foreach ($target in $targets) {
  try {
    Invoke-WebRequest -Uri $target.Url -Method Head -TimeoutSec 12 -UseBasicParsing | Out-Null
    Write-Host "[OK]   $($target.Name) — $($target.Url)" -ForegroundColor Green
  } catch {
    Write-Host "[MISS] $($target.Name) — $($target.Url)" -ForegroundColor Yellow
  }
}
Write-Host 'Erişilemeyen adres varsa GitHub-only/offline vendor akışını kullanın.'
