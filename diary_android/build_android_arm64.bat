@echo off
setlocal
set QT_ANDROID=D:\tools\qt\6.10.1\android_arm64_v8a
set ANDROID_SDK_ROOT=C:\Users\hp\AppData\Local\Android\Sdk
set ANDROID_NDK_ROOT=C:\Users\hp\AppData\Local\Android\Sdk\ndk\25.2.9519653
set JAVA_HOME=C:\Program Files\Java\latest
set CMAKE=D:\tools\Cmake\bin\cmake.exe

if not exist "%QT_ANDROID%\lib\cmake\Qt6\Qt6Config.cmake" (
  echo Qt Android ARM64-v8a kit not found: %QT_ANDROID%
  echo Please install it with D:\tools\qt\MaintenanceTool.exe first.
  exit /b 1
)

"%CMAKE%" -S . -B build-android-arm64 -G Ninja ^
  -DCMAKE_PREFIX_PATH="%QT_ANDROID%" ^
  -DANDROID_SDK_ROOT="%ANDROID_SDK_ROOT%" ^
  -DANDROID_NDK_ROOT="%ANDROID_NDK_ROOT%" ^
  -DANDROID_ABI=arm64-v8a ^
  -DANDROID_PLATFORM=android-31

if errorlevel 1 exit /b 1

"%CMAKE%" --build build-android-arm64 --target apk
endlocal
