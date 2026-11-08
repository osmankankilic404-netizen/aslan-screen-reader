# Android / Windows / Ubuntu uygulama değerlendirme listesi

## Ortak kalite

`flutter pub get`, `flutter analyze` ve `flutter test` hatasız çalışmalıdır. Uygulama açılışta çökmemeli, temel ekranlar gerçek cihaz veya masaüstü hedefinde denenmelidir. Debug loglarında gizli anahtar, parola veya kişisel veri bulunmamalıdır.

## Android APK/AAB

APK release olarak üretilmeli, Android manifest ve application ID doğru olmalı, minimum/target SDK kararı belgelenmeli, izinler gereksiz yere geniş olmamalıdır. Gerçek Android cihazda kurulum, açılış, yönlendirme, ağ bağlantısı, ekran döndürme ve geri düğmesi kontrol edilmelidir. AAB Play Console yükleme doğrulamasından geçmelidir. Release keystore repoda bulunmamalıdır.

## Windows

Windows release klasörü başka bir temiz Windows makinede çalıştırılmalıdır. Visual C++ runtime gereksinimi belgelenmeli, uygulama açılışı ve dosya yolları kontrol edilmeli, Defender/SmartScreen imza durumu açıklanmalıdır. Kurulum paketi gerekiyorsa MSIX, Inno Setup veya WiX ayrıca seçilmelidir; bu kit Flutter release klasörünü üretir.

## Ubuntu/Linux

Linux release bundle temiz Ubuntu üzerinde çalıştırılmalıdır. GTK, GLib, OpenGL ve ses bağımlılıkları belgelenmeli, uygulama pencere açılışı, dosya erişimi, ağ, ekran ölçekleme ve AppImage/deb paketleme kararı kontrol edilmelidir. Bu kit Flutter Linux bundle üretir; AppImage/deb paketleme ayrı dağıtım adımıdır.

## Güvenlik ve yayın

API anahtarları, keystore, sertifika, imza parolaları, `.env` ve kullanıcı verileri kaynak repoya konulmamalıdır. GitHub Actions Secrets kullanılmalıdır. Her yayın için sürüm, commit SHA, build tarihi, hedef platform ve artifact hash'i kaydedilmelidir.
