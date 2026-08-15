# LifeDiary Mobile 1.6 Android Release Build

This historical procedure builds, signs, installs, and launches the Qt Android arm64-v8a release APK for `legacy/mobile-qt/LifeDiaryMobile`. The current mobile app is `mobile/`; see `docs/CURRENT.md`.

## Required Environment Variables

Set these variables in the PowerShell session before building. Do not place real passwords or local keystore paths in source files.

```powershell
$env:QT_ANDROID = '<Qt Android arm64-v8a kit root>'
$env:ANDROID_SDK_ROOT = '<Android SDK root>'
$env:ANDROID_NDK_ROOT = '<Android NDK root>'
$env:CMAKE = '<full path to cmake.exe>'
$env:LIFE_DIARY_KEYSTORE = '<full path to release keystore>'
$env:LIFE_DIARY_KEY_ALIAS = '<keystore alias>'
$env:LIFE_DIARY_STOREPASS = '<keystore password>'
$env:LIFE_DIARY_KEYPASS = '<key password>'
```

The batch file finds `ninja.exe` from `PATH` or from the directory containing `CMAKE`.

## Build, Sign, Install, and Launch

```powershell
cd legacy/mobile-qt/LifeDiaryMobile
.\build_android_arm64.bat
```

The script removes the old `build-android-arm64-release` directory, configures a Release arm64-v8a build, creates a signed APK, and runs these checks in order:

```text
apksigner verify --print-certs <signed apk>
aapt dump badging <signed apk>
adb install -r <signed apk>
adb shell monkey -p com.localfirst.lifediary 1
```

The deliverable is:

```text
legacy/mobile-qt/LifeDiaryMobile/build-android-arm64-release/android-build/build/outputs/apk/release/LifeDiaryMobile-1.6.1-arm64-v8a-signed.apk
```

Version values are `versionName 1.6.1` and `versionCode 3` in both CMake and the Android manifest.

If `adb install` fails, stop there and retain the complete terminal error. Do not treat any `*-unsigned.apk` file as a deliverable.
