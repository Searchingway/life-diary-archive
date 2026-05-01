@echo off
setlocal
set QT_ANDROID=D:\tools\qt\6.10.1\android_arm64_v8a
set ANDROID_SDK_ROOT=C:\Users\hp\AppData\Local\Android\Sdk
set ANDROID_NDK_ROOT=C:\Users\hp\AppData\Local\Android\Sdk\ndk\27.2.12479018
set ANDROID_BUILD_TOOLS=%ANDROID_SDK_ROOT%\build-tools\36.0.0
set NINJA=%ANDROID_SDK_ROOT%\cmake\3.22.1\bin\ninja.exe
set CMAKE=D:\tools\Cmake\bin\cmake.exe
set BUILD_DIR=build-android-arm64-release
set UNSIGNED_APK=%BUILD_DIR%\android-build\build\outputs\apk\release\android-build-release-unsigned.apk
set ALIGNED_APK=%BUILD_DIR%\android-build\build\outputs\apk\release\LifeDiaryMobile-release-aligned.apk
set SIGNED_APK=%BUILD_DIR%\android-build\build\outputs\apk\release\LifeDiaryMobile-release-signed.apk
set SIGNING_KEYSTORE=signing\life_diary_release.keystore
set SIGNING_ALIAS=life_diary
set SIGNING_STOREPASS=LifeDiary@2026
set SIGNING_KEYPASS=LifeDiary@2026

if not exist "%QT_ANDROID%\bin\qt-cmake.bat" (
  echo Qt Android ARM64-v8a kit not found: %QT_ANDROID%
  echo Please install it with D:\tools\qt\MaintenanceTool.exe first.
  exit /b 1
)

if not exist "%NINJA%" (
  echo Ninja not found: %NINJA%
  exit /b 1
)

if not exist "%SIGNING_KEYSTORE%" (
  echo signing keystore not found: %SIGNING_KEYSTORE%
  exit /b 1
)

"%QT_ANDROID%\bin\qt-cmake.bat" -S . -B "%BUILD_DIR%" -G Ninja ^
  -DCMAKE_MAKE_PROGRAM="%NINJA%" ^
  -DANDROID_SDK_ROOT="%ANDROID_SDK_ROOT%" ^
  -DANDROID_NDK_ROOT="%ANDROID_NDK_ROOT%" ^
  -DANDROID_ABI=arm64-v8a ^
  -DANDROID_PLATFORM=android-27 ^
  -DCMAKE_BUILD_TYPE=Release

if errorlevel 1 exit /b 1

"%CMAKE%" --build "%BUILD_DIR%" --target apk
if errorlevel 1 exit /b 1

if not exist "%UNSIGNED_APK%" (
  echo unsigned release apk not found: %UNSIGNED_APK%
  exit /b 1
)

"%ANDROID_BUILD_TOOLS%\zipalign.exe" -f -p 4 "%UNSIGNED_APK%" "%ALIGNED_APK%"
if errorlevel 1 exit /b 1

"%ANDROID_BUILD_TOOLS%\apksigner.bat" sign ^
  --ks "%SIGNING_KEYSTORE%" ^
  --ks-key-alias "%SIGNING_ALIAS%" ^
  --ks-pass pass:%SIGNING_STOREPASS% ^
  --key-pass pass:%SIGNING_KEYPASS% ^
  --out "%SIGNED_APK%" ^
  "%ALIGNED_APK%"
if errorlevel 1 exit /b 1

"%ANDROID_BUILD_TOOLS%\apksigner.bat" verify --print-certs "%SIGNED_APK%"
if errorlevel 1 exit /b 1

if not exist "..\..\手机直装版" mkdir "..\..\手机直装版"
copy /Y "%SIGNED_APK%" "..\..\手机直装版\LifeDiaryMobile-Mobile15-release-signed.apk" > nul
echo Signed APK: %SIGNED_APK%
echo Copy: ..\..\手机直装版\LifeDiaryMobile-Mobile15-release-signed.apk
endlocal
