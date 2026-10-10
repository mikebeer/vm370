@echo off
rem get-wheezy-dev.cmd -- VM/370plus, Windows 11: download the Debian 7 (wheezy)
rem s390 packages for gcc under Debian and pack them into ONE zip to upload.
rem Double-click it, or run it from cmd.exe.  Uses curl.exe and tar.exe,
rem which Windows 11 has built in.  Result: wheezy-s390-dev.zip (about 24 MB)
rem next to this file.  "get-wheezy-dev.cmd nocxx" leaves out g++.

setlocal
cd /d "%~dp0"
set B=http://archive.debian.org/debian/
if not exist wheezy-s390-dev mkdir wheezy-s390-dev

for %%P in (
  pool/main/g/gcc-4.6/gcc-4.6-base_4.6.3-14_s390.deb
  pool/main/g/gcc-4.6/cpp-4.6_4.6.3-14_s390.deb
  pool/main/g/gcc-4.6/gcc-4.6_4.6.3-14_s390.deb
  pool/main/g/gcc-defaults/cpp_4.6.3-8_s390.deb
  pool/main/g/gcc-defaults/gcc_4.6.3-8_s390.deb
  pool/main/g/gmp/libgmp10_5.0.5+dfsg-2_s390.deb
  pool/main/m/mpfr4/libmpfr4_3.1.0-5_s390.deb
  pool/main/m/mpclib/libmpc2_0.9-4_s390.deb
  pool/main/g/gcc-4.7/libgomp1_4.7.2-5_s390.deb
  pool/main/b/binutils/binutils_2.22-8+deb7u2_s390.deb
  pool/main/m/make-dfsg/make_3.81-8.2_s390.deb
  pool/main/e/eglibc/libc-dev-bin_2.13-38+deb7u10_s390.deb
  pool/main/e/eglibc/libc6-dev_2.13-38+deb7u10_s390.deb
  pool/main/l/linux/linux-libc-dev_3.2.78-1_s390.deb
) do call :get %%P

if /i "%1"=="nocxx" goto pack
for %%P in (
  pool/main/g/gcc-defaults/g++_4.6.3-8_s390.deb
  pool/main/g/gcc-4.6/g++-4.6_4.6.3-14_s390.deb
  pool/main/g/gcc-4.6/libstdc++6-4.6-dev_4.6.3-14_s390.deb
  pool/main/g/gcc-4.7/libstdc++6_4.7.2-5_s390.deb
) do call :get %%P

:pack
if exist wheezy-s390-dev.zip del wheezy-s390-dev.zip
pushd wheezy-s390-dev
tar -a -c -f ..\wheezy-s390-dev.zip *.deb
popd
if errorlevel 1 (echo *** packing failed & pause & exit /b 1)
echo.
echo done: %CD%\wheezy-s390-dev.zip -- upload this one file
dir wheezy-s390-dev.zip | find "wheezy"
pause
exit /b 0

:get
set F=wheezy-s390-dev\%~nx1
if exist "%F%" (echo have  %~nx1 & exit /b 0)
echo fetch %~nx1
curl.exe -fsSL --retry 3 -o "%F%" "%B%%1"
if errorlevel 1 (echo *** cannot download %1 & del "%F%" 2>nul & pause & exit 1)
exit /b 0
