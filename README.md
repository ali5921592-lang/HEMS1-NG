# Nurse Guide Pro — Android + iOS Uygulaması (İngilizce Sürüm)

Bu klasör, **Nurse Guide Pro** web uygulamasını (`www/index.html` — Hemşire
Rehberi Pro'nun İngilizce sürümü), hiçbir iç kodu değiştirmeden,
[Capacitor](https://capacitorjs.com/) ile hem **Android** hem **iOS**
uygulamasına dönüştürür. APK, AAB ve IPA dosyaları **GitHub Actions**
üzerinden otomatik olarak derlenir — Android Studio veya Xcode kurmanıza ya
da elle bir işlem yapmanıza gerek yoktur.

> Bu proje, Türkçe "Hemşire Rehberi Pro" mobil projesiyle **birebir aynı
> altyapıyı** kullanır; farkı yalnızca `www/index.html` içeriği (İngilizce
> uygulama) ve uygulama kimliğidir (`appId: com.nurseguidepro.app`). İki dil
> versiyonu Play Store'da **ayrı iki uygulama** olarak yayınlanmak üzere
> tasarlanmıştır (aynı appId ile ikisini birden yayınlamak mümkün değildir).

## Nasıl çalışır?

1. Bu repoyu GitHub'a yüklediğinizde (`main`/`master` dalına push), `.github/workflows/build-android.yml`
   iş akışı otomatik tetiklenir.
2. İş akışı sırasıyla:
   - Node.js ve JDK 17 kurar,
   - `npm install` ile Capacitor bağımlılıklarını indirir,
   - `npx cap add android` ile **native Android projesini o an taze olarak üretir**
     (bu klasör repoya commit edilmez — her zaman güncel ve tutarlı olması için
     CI'da yeniden oluşturulur),
   - `resources/icon.png` ve `resources/splash.png` kaynak görsellerinden tüm
     yoğunluklar için uygulama ikonu ve açılış ekranını otomatik üretir,
   - `scripts/patch-android.py` ile projeyi düzenler: gereksiz izinleri kaldırır,
     bildirim ikonunu yerleştirir, sürüm numarasını artırır, kod/kaynak
     küçültmeyi (R8/ProGuard) açar ve (varsa) release imzalamasını yapılandırır,
   - `./gradlew assembleRelease` ile **APK**, `./gradlew bundleRelease` ile
     **AAB** (Play Store formatı) üretir,
   - İkisini de iş akışının "Artifacts" (çıktılar) bölümüne yükler.
3. Derlenen dosyaları indirmek için: **Actions** sekmesi → ilgili çalıştırma →
   sayfanın altındaki **Artifacts** bölümü → `nurse-guide-pro-apk` /
   `nurse-guide-pro-aab` dosyalarını indirin.

## ⚠️ Play Store'a yüklemeden önce: gerçek imzalama şart

Varsayılan olarak (hiçbir "secret" eklemediyseniz) iş akışı, release build'i
**geçici olarak debug anahtarıyla imzalar**. Bu APK/AAB **telefonunuza kurulup
test edilebilir** ama **Play Store bunu kabul etmez**.

Play Store'a yüklenebilir, gerçek imzalı bir AAB almak için:

### 1) Bir imzalama anahtarı (keystore) oluşturun (bilgisayarınızda, bir kez)

```bash
keytool -genkey -v -keystore release.keystore -alias nurse-guide-pro \
  -keyalg RSA -keysize 2048 -validity 10000
```

Bu, sizden bir şifre ve birkaç bilgi (isim, kuruluş vb.) isteyecek ve
`release.keystore` dosyasını oluşturacaktır. **Bu dosyayı ve şifrelerini asla
kaybetmeyin / paylaşmayın** — Play Store'da uygulamanızı güncelleyebilmek için
her zaman aynı anahtara ihtiyacınız olacak.

> Not: Türkçe versiyon için ayrı bir keystore, İngilizce versiyon için ayrı bir
> keystore kullanmanız gerekir (ikisi farklı Play Store uygulaması olacağı için).
> Aynı keystore'u her ikisi için de kullanabilirsiniz, tek şart alias'ların
> farklı olması değil — her iki uygulamanın appId'si zaten farklı olduğu için
> bu bir sorun teşkil etmez.

### 2) Keystore dosyasını base64'e çevirin

```bash
base64 -w 0 release.keystore > release.keystore.base64.txt
```

(macOS'ta `base64 -w 0` yerine `base64` kullanın.)

### 3) GitHub reponuza 4 "secret" ekleyin

Repo sayfanızda: **Settings → Secrets and variables → Actions → New repository secret**

| Secret adı | Değeri |
|---|---|
| `KEYSTORE_BASE64` | `release.keystore.base64.txt` dosyasının içeriği |
| `KEYSTORE_PASSWORD` | `keytool` sırasında girdiğiniz keystore şifresi |
| `KEY_ALIAS` | `nurse-guide-pro` (yukarıdaki `-alias` değeri) |
| `KEY_PASSWORD` | Anahtar (key) şifresi (genelde keystore şifresiyle aynıdır) |

Bu 4 secret eklendikten sonra yapılan her push'ta iş akışı **otomatik olarak
gerçek imzalı, Play Store'a yüklenebilir bir AAB** üretecektir — başka hiçbir
işlem gerekmez.

### 4) Play Console'a yükleme

Üretilen `.aab` dosyasını [Google Play Console](https://play.google.com/console)
üzerinden yeni bir uygulama olarak yükleyebilirsiniz.

## 🍎 iOS (App Store) — Apple Developer hesabı gerektirir

Bu proje hem Android hem iOS'u **aynı repo, aynı web kodundan** üretir.
iOS derlemesi `.github/workflows/build-ios.yml` ile **macOS runner** üzerinde
(Xcode önceden kurulu gelir) otomatik çalışır.

### Android ile kritik fark: Apple Developer Program zorunlu

Android'de "secret" eklemeseniz bile her zaman kurulabilir bir debug-signed
APK üretilebiliyordu. **iOS'ta bu mümkün değil** — Apple, gerçek bir
`.ipa` üretebilmek için bile geçerli bir Apple Developer Program üyeliği
(yıllık $99) ve o hesaptan üretilmiş bir Distribution sertifikası +
provisioning profile ister. Bu bilgileri sizin için üretemem; yalnızca siz
Apple Developer hesabınızdan alabilirsiniz.

**5 secret tanımlanmadığı sürece** iş akışı, projenin Xcode'da sorunsuz
açıldığını ve derlendiğini doğrulamak için yalnızca bir **simulator duman
testi** yapar (gerçek bir .ipa üretmez). Secret'lar eklendiğinde otomatik
olarak gerçek, imzalı, App Store'a yüklenebilir bir `.ipa` üretir.

### Gerekli 5 GitHub secret'ı nasıl elde edilir

1. **Apple Developer hesabınızla** [developer.apple.com](https://developer.apple.com) → Certificates, Identifiers & Profiles bölümüne gidin.
2. **Distribution sertifikası** oluşturun (Certificates → + → Apple Distribution), indirin, Mac'inizde çift tıklayıp Keychain Access'e ekleyin, sonra Keychain Access'ten sağ tık > Export > `.p12` formatında dışa aktarın (bir şifre belirleyin).
3. **App ID** oluşturun (Identifiers → + → App IDs), `capacitor.config.json` içindeki `appId` (`com.nurseguidepro.app`) ile birebir aynı olmalı.
4. **Provisioning Profile** oluşturun (Profiles → + → App Store → yukarıdaki App ID'yi ve sertifikayı seçin), indirin (`.mobileprovision` dosyası), bir isim verin (bu isim `IOS_PROFILE_NAME` olacak).
5. **Team ID**'nizi bulun: developer.apple.com → Membership sayfasında görünür (10 karakterlik kod).
6. `.p12` ve `.mobileprovision` dosyalarını base64'e çevirin:
   ```bash
   base64 -i Certificates.p12 | pbcopy      # IOS_DIST_CERT_BASE64 icin
   base64 -i profile.mobileprovision | pbcopy  # IOS_PROVISION_PROFILE_BASE64 icin
   ```
7. Repo **Settings → Secrets and variables → Actions** bölümüne şu 5 secret'ı ekleyin:

| Secret adı | Değeri |
|---|---|
| `IOS_DIST_CERT_BASE64` | `.p12` dosyasının base64 hali |
| `IOS_DIST_CERT_PASSWORD` | `.p12` dışa aktarırken belirlediğiniz şifre |
| `IOS_PROVISION_PROFILE_BASE64` | `.mobileprovision` dosyasının base64 hali |
| `IOS_TEAM_ID` | Apple Developer Team ID (10 karakter) |
| `IOS_PROFILE_NAME` | Provisioning profile'a verdiğiniz isim |

Bu 5 secret eklendikten sonra her push'ta otomatik olarak imzalı `.ipa`
üretilir ve iş akışının **Artifacts** bölümünden indirilebilir.

> **Not:** Türkçe ve İngilizce versiyonlar farklı `appId` kullandığı için
> (`com.hemsirerehberi.pro` vs `com.nurseguidepro.app`), Apple Developer
> hesabınızda **iki ayrı App ID, iki ayrı Provisioning Profile** oluşturmanız
> gerekir (aynı Distribution sertifikası ve Team ID her ikisi için de
> kullanılabilir).

### Bundle Identifier, Versiyon ve Build Number özelleştirme

Bu değerleri elle değiştirmeniz gerekmez — **Actions** sekmesinden workflow'u
elle tetiklediğinizde (workflow_dispatch) şu alanları girebilirsiniz:
- **Bundle Identifier** — boş bırakılırsa `capacitor.config.json` değeri kullanılır
- **Versiyon numarası** (örn. `1.2.0`)
- **Build numarası** — boş bırakılırsa GitHub çalıştırma numarası kullanılır (her seferinde otomatik artar, App Store Connect'in gereksinimini karşılar)

### App Store'a yükleme

Üretilen `.ipa` dosyasını **Transporter** uygulaması (Mac App Store'dan
ücretsiz indirilir) veya `xcrun altool`/`xcrun notarytool` ile
App Store Connect'e yükleyebilirsiniz.

### Apple Human Interface Guidelines uyumluluğu

- **Light/Dark Mode:** Uygulamanın kendi `data-theme` mekanizması korunur; mobil köprü scripti StatusBar'ı buna göre senkronize eder.
- **Safe Area (çentik/Dynamic Island):** `capacitor.config.json` içinde `ios.contentInset:"automatic"` ayarlanmıştır (Apple'ın önerdiği standart yöntem); ayrıca üst bar için `env(safe-area-inset-top)` ek güvence olarak enjekte edilir. Alt gezinme çubuğu zaten `env(safe-area-inset-bottom)` kullanıyordu (mevcut kodda).
- **Swipe Back:** Capacitor'ın WKWebView varsayılan `allowsBackForwardNavigationGestures` davranışı korunur; uygulama SPA olduğu için bu jest donanım geri tuşu mantığıyla çakışmaz.
- **iPad desteği:** `patch-ios.py`, iPad için 4 yönü de destekleyecek ve `UIRequiresFullScreen`'i kaldırarak Split View/Slide Over'a izin verecek şekilde `Info.plist`'i düzenler.
- **Privacy Manifest:** `ios-privacy/PrivacyInfo.xcprivacy` dosyası, hem diske kopyalanır hem de `scripts/add_privacy_manifest_to_xcodeproj.rb` ile Xcode projesinin gerçek "Copy Bundle Resources" derleme fazına kaydedilir (yalnızca dosyayı kopyalamak Xcode'un onu `.ipa` içine paketlemesi için yeterli değildir).
- **Gereksiz izin yok:** Varsayılan Capacitor şablonu kamera/konum/mikrofon gibi hiçbir izin açıklaması içermez; `patch-ios.py` bunu her derlemede doğrular.

## Otomatik düzeltilen uyumluluk sorunu: `window.storage`

Web uygulaması, yalnızca Claude.ai artifact ortamında bulunan özel bir
`window.storage` API'si kullanıyordu. Gerçek bir Android WebView'da bu API
mevcut olmadığı için favoriler/notlar/nöbet listesi hiç kaydedilmezdi.

`www/index.html` dosyasının sonuna, **mevcut uygulama kodunu hiç değiştirmeden**,
ayrı bir `<script>` bloğu eklendi (İngilizce yorumlarla). Bu script:
- `window.storage` yoksa, aynı arayüzü `localStorage` üzerinden sağlar,
- Android donanım geri tuşunu SPA içi gezinmeyle eşler,
- Karanlık mod durumuna göre durum çubuğunu (status bar) senkronize eder,
- Açılış ekranını (splash screen) kapatır,
- Nöbet listesindeki vardiyalar için **gerçek native yerel bildirimler**
  zamanlar (uygulama kapalıyken de çalışır).

## İzinler

Uygulama tamamen çevrimdışı çalıştığı için `INTERNET` ve
`ACCESS_NETWORK_STATE` izinleri CI tarafından otomatik kaldırılır. Yalnızca
nöbet bildirimi özelliği için gerekli olan bildirim izni (Android 13+'ta
çalışma zamanında kullanıcıya sorulur) kalır.

## Yerel olarak test etmek isterseniz (opsiyonel)

```bash
npm install
npx cap add android
npx capacitor-assets generate --android
npx cap sync android
cd android
./gradlew assembleDebug
```

Üretilen dosya: `android/app/build/outputs/apk/debug/app-debug.apk`

## Proje yapısı

```
├── .github/workflows/build-android.yml   # Android otomatik derleme iş akışı
├── .github/workflows/build-ios.yml       # iOS otomatik derleme iş akışı
├── capacitor.config.json                 # Capacitor yapılandırması (Android+iOS)
├── package.json                          # Bağımlılıklar (Android+iOS)
├── resources/
│   ├── icon.png                          # Uygulama ikonu kaynağı (1024x1024)
│   ├── splash.png                        # Açılış ekranı kaynağı (2732x2732)
│   └── notification-icon.png             # Bildirim ikonu (beyaz siluet)
├── ios-privacy/PrivacyInfo.xcprivacy      # Apple Privacy Manifest kaynağı
├── scripts/
│   ├── patch-android.py                  # CI'da native Android projesini düzenleyen script
│   ├── patch-ios.py                      # CI'da native iOS projesini düzenleyen script (Info.plist, ekran yönleri)
│   ├── add_privacy_manifest_to_xcodeproj.rb  # Privacy Manifest'i Xcode projesine gerçekten kaydeder
│   └── generate-export-options.py        # App Store export için exportOptions.plist üretir
└── www/index.html                        # Uygulamanın kendisi (DEĞİŞTİRİLMEDİ + ek köprü scripti)
```

## Uygulama kimliği ve sürüm

- **Paket adı (applicationId):** `com.nurseguidepro.app`
- **Uygulama adı:** Nurse Guide Pro
- **versionCode:** Her CI çalıştırmasında otomatik artar.

Paket adını değiştirmek isterseniz `capacitor.config.json` içindeki `appId`
alanını güncelleyin (Play Store'a ilk yüklemeden ÖNCE yapılmalıdır; sonradan
değiştirilemez).
