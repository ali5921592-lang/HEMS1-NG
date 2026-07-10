#!/usr/bin/env python3
"""
patch-android.py
-----------------
Capacitor `npx cap add android` ile tazece uretilen native Android
projesini, GitHub Actions icinde asagidaki sekilde otomatik duzenler:

  1) Gereksiz izinleri kaldirir (uygulama tamamen cevrimdisi calisir,
     INTERNET / ACCESS_NETWORK_STATE izinlerine ihtiyac yoktur).
  2) Bildirim ikonunu (drawable/ic_stat_notify.png) projeye kopyalar.
  3) versionCode degerini CI build numarasina gore artirir (Play Store
     her yuklemede daha yuksek bir versionCode ister).
  4) Release build icin kod kucultme + kaynak kucultmeyi (R8/ProGuard,
     shrinkResources) etkinlestirir -> daha kucuk APK/AAB boyutu.
  5) GEREKLI ortam degiskenleri (KEYSTORE_PATH, KEYSTORE_PASSWORD,
     KEY_ALIAS, KEY_PASSWORD) sagliandiginda, release build icin gercek
     imzalama yapilandirmasi ekler (Play Store'a yuklenebilir AAB/APK).
     Saglanmadiginda, release build gecici olarak debug anahtari ile
     imzalanir (test amacli calisir/kurulabilir ama Play Store'a
     YUKLENEMEZ - bu durum is akisi loglarinda acikca belirtilir).

Bu script yalnizca CI/CD tarafindan native android/ klasoru uzerinde
calisir; projenin www/ icindeki asil web uygulama kodunu HICBIR sekilde
etkilemez.
"""
import os
import re
import shutil
import sys

ANDROID_DIR = "android"
MANIFEST_PATH = os.path.join(ANDROID_DIR, "app", "src", "main", "AndroidManifest.xml")
BUILD_GRADLE_PATH = os.path.join(ANDROID_DIR, "app", "build.gradle")
DRAWABLE_DIR = os.path.join(ANDROID_DIR, "app", "src", "main", "res", "drawable")


def log(msg):
    print(f"[patch-android] {msg}")


def strip_unnecessary_permissions():
    if not os.path.exists(MANIFEST_PATH):
        log(f"UYARI: {MANIFEST_PATH} bulunamadi, izin temizleme atlaniyor.")
        return
    with open(MANIFEST_PATH, "r", encoding="utf-8") as f:
        content = f.read()

    removable = [
        r'\s*<uses-permission android:name="android\.permission\.INTERNET"\s*/>\n?',
        r'\s*<uses-permission android:name="android\.permission\.ACCESS_NETWORK_STATE"\s*/>\n?',
    ]
    original_len = len(content)
    for pattern in removable:
        content = re.sub(pattern, "\n", content)

    with open(MANIFEST_PATH, "w", encoding="utf-8") as f:
        f.write(content)

    if len(content) != original_len:
        log("Gereksiz izinler (INTERNET, ACCESS_NETWORK_STATE) kaldirildi.")
    else:
        log("Kaldirilacak gereksiz izin bulunamadi (zaten yok).")


def copy_notification_icon():
    src = os.path.join("resources", "notification-icon.png")
    if not os.path.exists(src):
        log("UYARI: resources/notification-icon.png bulunamadi, atlaniyor.")
        return
    os.makedirs(DRAWABLE_DIR, exist_ok=True)
    dst = os.path.join(DRAWABLE_DIR, "ic_stat_notify.png")
    shutil.copyfile(src, dst)
    log(f"Bildirim ikonu kopyalandi: {dst}")


def bump_version_code(version_code):
    if not os.path.exists(BUILD_GRADLE_PATH):
        log(f"HATA: {BUILD_GRADLE_PATH} bulunamadi.")
        return
    with open(BUILD_GRADLE_PATH, "r", encoding="utf-8") as f:
        content = f.read()

    new_content, n = re.subn(r"versionCode\s+\d+", f"versionCode {version_code}", content, count=1)
    if n == 0:
        log("UYARI: versionCode satiri bulunamadi, degistirilemedi.")
    else:
        content = new_content
        log(f"versionCode -> {version_code} olarak guncellendi.")

    with open(BUILD_GRADLE_PATH, "w", encoding="utf-8") as f:
        f.write(content)


def enable_minify_and_shrink():
    with open(BUILD_GRADLE_PATH, "r", encoding="utf-8") as f:
        content = f.read()

    def release_block_sub(match):
        block = match.group(0)
        block = re.sub(r"minifyEnabled\s+false", "minifyEnabled true", block)
        if "shrinkResources" not in block:
            block = block.replace(
                "minifyEnabled true",
                "minifyEnabled true\n            shrinkResources true",
                1,
            )
        return block

    new_content, n = re.subn(
        r"release\s*\{[^}]*\}",
        release_block_sub,
        content,
        count=1,
        flags=re.DOTALL,
    )
    if n == 0:
        log("UYARI: release{} bloğu bulunamadi, minify/shrink ayarlanamadi.")
    else:
        content = new_content
        log("Release build icin minifyEnabled=true, shrinkResources=true ayarlandi (kucuk APK/AAB).")

    with open(BUILD_GRADLE_PATH, "w", encoding="utf-8") as f:
        f.write(content)


def add_signing_config(keystore_path, keystore_password, key_alias, key_password):
    with open(BUILD_GRADLE_PATH, "r", encoding="utf-8") as f:
        content = f.read()

    if "signingConfigs" in content:
        log("signingConfigs zaten mevcut, tekrar eklenmiyor.")
        return

    signing_block = f"""
    signingConfigs {{
        release {{
            storeFile file(System.getenv("CI_KEYSTORE_PATH") ?: "{keystore_path}")
            storePassword System.getenv("CI_KEYSTORE_PASSWORD") ?: "{keystore_password}"
            keyAlias System.getenv("CI_KEY_ALIAS") ?: "{key_alias}"
            keyPassword System.getenv("CI_KEY_PASSWORD") ?: "{key_password}"
        }}
    }}
"""

    new_content, n = re.subn(r"(android\s*\{)", r"\1" + signing_block, content, count=1)
    if n == 0:
        log("HATA: 'android {' bloğu bulunamadi, imzalama eklenemedi.")
        return
    content = new_content

    new_content, n = re.subn(
        r"(release\s*\{)",
        r"\1\n            signingConfig signingConfigs.release",
        content,
        count=1,
    )
    if n == 0:
        log("UYARI: release{} bloğu bulunamadi, signingConfig atanamadi.")
    else:
        content = new_content
        log("Gercek release imzalama yapilandirmasi eklendi (Play Store'a hazir).")

    with open(BUILD_GRADLE_PATH, "w", encoding="utf-8") as f:
        f.write(content)


def add_debug_signing_fallback():
    """Imzalama sirlari (secrets) saglanmadiysa, release build'in en azindan
    calisir/kurulabilir olmasi icin debug anahtarini kullan. NOT: Bu durumda
    uretilen AAB/APK Play Store'a YUKLENEMEZ, yalnizca test amaclidir."""
    with open(BUILD_GRADLE_PATH, "r", encoding="utf-8") as f:
        content = f.read()

    if "signingConfigs" in content:
        return

    new_content, n = re.subn(
        r"(release\s*\{)",
        r"\1\n            signingConfig signingConfigs.debug",
        content,
        count=1,
    )
    if n:
        content = new_content
        log("UYARI: Imzalama sirlari (secrets) bulunamadi -> release build GECICI olarak "
            "debug anahtariyla imzalandi. Bu APK/AAB test icin calisir ama Play Store'a "
            "YUKLENEMEZ. Gercek imzalama icin repo Settings > Secrets bolumune "
            "KEYSTORE_BASE64, KEYSTORE_PASSWORD, KEY_ALIAS, KEY_PASSWORD ekleyin.")
    with open(BUILD_GRADLE_PATH, "w", encoding="utf-8") as f:
        f.write(content)


def main():
    version_code = os.environ.get("CI_VERSION_CODE", "1")
    has_signing = os.environ.get("HAS_SIGNING_SECRETS", "false").lower() == "true"

    strip_unnecessary_permissions()
    copy_notification_icon()
    bump_version_code(version_code)
    enable_minify_and_shrink()

    if has_signing:
        add_signing_config(
            keystore_path=os.environ.get("CI_KEYSTORE_PATH", "release.keystore"),
            keystore_password=os.environ.get("CI_KEYSTORE_PASSWORD", ""),
            key_alias=os.environ.get("CI_KEY_ALIAS", ""),
            key_password=os.environ.get("CI_KEY_PASSWORD", ""),
        )
    else:
        add_debug_signing_fallback()

    log("Android proje duzenlemeleri tamamlandi.")


if __name__ == "__main__":
    sys.exit(main())
