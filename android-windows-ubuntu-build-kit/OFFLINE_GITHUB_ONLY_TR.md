# GitHub-only offline kurulum raporu

Bu paket yalnızca GitHub adreslerine erişebilen makineler için düzenlenmiştir. Kurulum scriptleri Google, Microsoft veya başka bir CDN'ye sessizce bağlanmaz; eksik bağımlılığı bildirip durur.

## Gerçek sınır

Android SDK command-line tools/platform/build-tools, Visual Studio Build Tools ve Windows SDK gibi ürünlerin dağıtım lisansları ve boyutları vardır. Public GitHub deposuna lisans kontrolü olmadan gömülmeleri doğru değildir. Bu nedenle bu dosyalar sahte veya bozuk ikililerle doldurulmadı. Repo; kurulum scriptlerini, kontrol komutlarını, manifesti ve kullanıcı lisanslı paketleri `vendor/` içine koyduğunda bunları kullanacak offline akışı içerir.

## Offline klasör düzeni

```text
vendor/
  jdk-17/                 # lisanslı veya kurum içi edinilmiş JDK
  android-sdk-tools.zip   # kullanıcı tarafından sağlanan Android tools
  android-platforms/      # sdkmanager cache veya kurum içi paket
  flutter-sdk/            # Flutter SDK arşivi veya klonu
  windows-build-tools/    # yalnızca lisanslı Windows offline layout
```

Public GitHub repo içine yalnızca dağıtım hakkınız olan dosyaları koyun. Ticari/kapalı ikililer için private repo ve ilgili lisans şartları gerekir.

## GitHub-only kullanım

1. GitHub repo'yu veya release asset'lerini makineye indirin.
2. `vendor/` içine lisanslı bağımlılıkları yerleştirin.
3. Ubuntu'da `scripts/install-offline-github-only.sh` çalıştırın.
4. Windows'ta `scripts/install-offline-github-only.ps1` çalıştırın.
5. `scripts/evaluate-project.sh`, `scripts/build-apk.sh`, `scripts/build-linux.sh` veya `scripts/build-windows.ps1` çalıştırın.

Scriptler internet erişimi denemez; eksik dosyayı ve beklenen konumu söyler.

## Gerekli GitHub asset türleri

GitHub repository source, GitHub release asset ve GitHub raw dosya erişimi yeterlidir. GitHub dışındaki indirme adresleri bu offline akışta kullanılmaz. Android ve Windows kapalı dağıtımlarının tamamını public GitHub'a koymak için kullanıcı lisansı ve boyut uygunluğu ayrıca doğrulanmalıdır.
