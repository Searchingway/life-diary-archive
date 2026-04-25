@echo off
setlocal
set QT_HOST=D:\tools\qt\6.10.1\mingw_64
set MINGW=D:\tools\qt\Tools\mingw1310_64
set CMAKE=D:\tools\Cmake\bin\cmake.exe

"%CMAKE%" -S . -B build-desktop -G "MinGW Makefiles" ^
  -DCMAKE_PREFIX_PATH="%QT_HOST%" ^
  -DCMAKE_C_COMPILER="%MINGW%\bin\gcc.exe" ^
  -DCMAKE_CXX_COMPILER="%MINGW%\bin\g++.exe" ^
  -DCMAKE_MAKE_PROGRAM="%MINGW%\bin\mingw32-make.exe"

if errorlevel 1 exit /b 1

"%CMAKE%" --build build-desktop
endlocal
