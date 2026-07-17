@echo off
setlocal

set "APP_VERSION_NAME=1.6.1"
set "APP_VERSION_CODE=3"
set "APP_PACKAGE=com.localfirst.lifediary"
for %%I in ("%~dp0.") do set "SCRIPT_DIR=%%~fI"
set "BUILD_DIR=%SCRIPT_DIR%\build-android-arm64-release"
set "APK_OUTPUT_DIR=%BUILD_DIR%\android-build\build\outputs\apk\release"
set "APK_BASENAME=LifeDiaryMobile-%APP_VERSION_NAME%-arm64-v8a"
set "ALIGNED_APK=%APK_OUTPUT_DIR%\%APK_BASENAME%-aligned.apk"
set "SIGNED_APK=%APK_OUTPUT_DIR%\%APK_BASENAME%-signed.apk"

if not defined QT_ANDROID goto :missing_QT_ANDROID
if not defined ANDROID_SDK_ROOT goto :missing_ANDROID_SDK_ROOT
if not defined ANDROID_NDK_ROOT goto :missing_ANDROID_NDK_ROOT
if not defined CMAKE goto :missing_CMAKE
if not defined LIFE_DIARY_KEYSTORE goto :missing_LIFE_DIARY_KEYSTORE
if not defined LIFE_DIARY_KEY_ALIAS goto :missing_LIFE_DIARY_KEY_ALIAS
if not defined LIFE_DIARY_STOREPASS goto :missing_LIFE_DIARY_STOREPASS
if not defined LIFE_DIARY_KEYPASS goto :missing_LIFE_DIARY_KEYPASS

set "ANDROID_BUILD_TOOLS=%ANDROID_SDK_ROOT%\build-tools\36.0.0"
set "ADB=%ANDROID_SDK_ROOT%\platform-tools\adb.exe"
set "NINJA="
for /f "delims=" %%I in ('where ninja.exe 2^>nul') do if not defined NINJA set "NINJA=%%I"
if not defined NINJA (
  for %%I in ("%CMAKE%") do set "CMAKE_BIN=%%~dpI"
  if exist "%CMAKE_BIN%ninja.exe" set "NINJA=%CMAKE_BIN%ninja.exe"
)

if not exist "%QT_ANDROID%\bin\qt-cmake.bat" goto :missing_qt_cmake
if not exist "%ANDROID_NDK_ROOT%\source.properties" goto :missing_ndk
if not exist "%CMAKE%" goto :missing_cmake_exe
if not exist "%NINJA%" goto :missing_ninja
if not exist "%ANDROID_BUILD_TOOLS%\zipalign.exe" goto :missing_build_tools
if not exist "%ANDROID_BUILD_TOOLS%\apksigner.bat" goto :missing_build_tools
if not exist "%ADB%" goto :missing_adb
if not exist "%LIFE_DIARY_KEYSTORE%" goto :missing_keystore

cd /d "%SCRIPT_DIR%"
if exist "%BUILD_DIR%" rmdir /s /q "%BUILD_DIR%"
if exist "%BUILD_DIR%" (
  echo Failed to remove old build directory: %BUILD_DIR%
  exit /b 1
)

call "%QT_ANDROID%\bin\qt-cmake.bat" -S "%SCRIPT_DIR%" -B "%BUILD_DIR%" -G Ninja ^
  -DCMAKE_MAKE_PROGRAM="%NINJA%" ^
  -DANDROID_SDK_ROOT="%ANDROID_SDK_ROOT%" ^
  -DANDROID_NDK_ROOT="%ANDROID_NDK_ROOT%" ^
  -DANDROID_ABI=arm64-v8a ^
  -DANDROID_PLATFORM=android-27 ^
  -DCMAKE_BUILD_TYPE=Release
if errorlevel 1 exit /b 1

"%CMAKE%" --build "%BUILD_DIR%" --target apk
if errorlevel 1 exit /b 1

set "UNSIGNED_APK="
for %%I in ("%APK_OUTPUT_DIR%\*-unsigned.apk") do if exist "%%~fI" set "UNSIGNED_APK=%%~fI"
if not defined UNSIGNED_APK (
  echo Unsigned release APK not found in: %APK_OUTPUT_DIR%
  exit /b 1
)

"%ANDROID_BUILD_TOOLS%\zipalign.exe" -f -p 4 "%UNSIGNED_APK%" "%ALIGNED_APK%"
if errorlevel 1 exit /b 1

"%ANDROID_BUILD_TOOLS%\apksigner.bat" sign ^
  --ks "%LIFE_DIARY_KEYSTORE%" ^
  --ks-key-alias "%LIFE_DIARY_KEY_ALIAS%" ^
  --ks-pass env:LIFE_DIARY_STOREPASS ^
  --key-pass env:LIFE_DIARY_KEYPASS ^
  --out "%SIGNED_APK%" ^
  "%ALIGNED_APK%"
if errorlevel 1 exit /b 1

del /q "%ALIGNED_APK%" >nul 2>nul

"%ANDROID_BUILD_TOOLS%\apksigner.bat" verify --print-certs "%SIGNED_APK%"
if errorlevel 1 exit /b 1

"%ANDROID_BUILD_TOOLS%\aapt.exe" dump badging "%SIGNED_APK%"
if errorlevel 1 exit /b 1

"%ADB%" install -r "%SIGNED_APK%"
if errorlevel 1 (
  echo ADB install failed. The complete ADB error is shown above.
  exit /b 1
)

"%ADB%" shell monkey -p %APP_PACKAGE% 1
if errorlevel 1 (
  echo ADB launch failed. The complete ADB error is shown above.
  exit /b 1
)

echo Signed APK: %SIGNED_APK%
exit /b 0

:missing_QT_ANDROID
echo Missing required environment variable: QT_ANDROID
exit /b 1
:missing_ANDROID_SDK_ROOT
echo Missing required environment variable: ANDROID_SDK_ROOT
exit /b 1
:missing_ANDROID_NDK_ROOT
echo Missing required environment variable: ANDROID_NDK_ROOT
exit /b 1
:missing_CMAKE
echo Missing required environment variable: CMAKE
exit /b 1
:missing_LIFE_DIARY_KEYSTORE
echo Missing required environment variable: LIFE_DIARY_KEYSTORE
exit /b 1
:missing_LIFE_DIARY_KEY_ALIAS
echo Missing required environment variable: LIFE_DIARY_KEY_ALIAS
exit /b 1
:missing_LIFE_DIARY_STOREPASS
echo Missing required environment variable: LIFE_DIARY_STOREPASS
exit /b 1
:missing_LIFE_DIARY_KEYPASS
echo Missing required environment variable: LIFE_DIARY_KEYPASS
exit /b 1
:missing_qt_cmake
echo qt-cmake.bat not found under QT_ANDROID.
exit /b 1
:missing_ndk
echo Android NDK source.properties not found under ANDROID_NDK_ROOT.
exit /b 1
:missing_cmake_exe
echo CMAKE does not point to cmake.exe.
exit /b 1
:missing_ninja
echo ninja.exe was not found on PATH or next to CMAKE.
exit /b 1
:missing_build_tools
echo Android build-tools 36.0.0, zipalign.exe, or apksigner.bat was not found.
exit /b 1
:missing_adb
echo adb.exe was not found under ANDROID_SDK_ROOT.
exit /b 1
:missing_keystore
echo LIFE_DIARY_KEYSTORE does not point to an existing keystore.
exit /b 1
