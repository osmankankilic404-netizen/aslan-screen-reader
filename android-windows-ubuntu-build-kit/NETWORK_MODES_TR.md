# Ağ çalışma modları

## Online mod

Makine genel internete erişebiliyorsa normal kurulum scriptleri kullanılabilir. Ubuntu scripti Google Android command-line tools adresinden, Flutter'ı GitHub'dan ve Ubuntu bağımlılıklarını apt kaynaklarından edinir. Windows scripti winget, Android Studio ve Visual Studio kurulum kaynaklarını kullanabilir.

## GitHub-only/offline mod

Makine yalnızca GitHub'a erişebiliyorsa `install-offline-github-only.sh` veya `install-offline-github-only.ps1` kullanılmalıdır. Bu scriptler Google, Microsoft veya başka bir CDN'ye bağlanmaz. Gerekli JDK, Flutter, Android SDK ve Windows SDK dosyaları önceden GitHub release/repository üzerinden alınıp `vendor/` klasörüne konmalıdır.

## Gerçek internet kontrolü

`scripts/check-network.sh` GitHub, Google Android, Flutter, Microsoft ve npm adreslerine erişimi ayrı ayrı test eder. Bir adres erişilemiyorsa bu durum açıkça raporlanır; script güvenlik nedeniyle proxy veya DNS kısıtlamasını aşmaya çalışmaz.

## Uygulama internet bağlantısı

Flutter uygulamasının ağ kullanması için Android manifestinde INTERNET izni, Windows/Linux tarafında ise işletim sistemi güvenlik duvarı/proxy ayarları gerekebilir. API anahtarları uygulama içine gömülmemeli, sunucu tarafında tutulmalıdır. Ağ yokken uygulama, önbellekli veya offline hata ekranı göstermelidir.
