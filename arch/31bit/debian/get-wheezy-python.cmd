@echo off
rem get-wheezy-python.cmd -- VM/370+, Windows 11: download the Debian 7
rem (wheezy) s390 packages for Python 2.7 and 3.2 under Debian and pack them into ONE zip to upload.
rem Double-click it, or run it from cmd.exe.  Uses curl.exe and tar.exe,
rem which Windows 11 has built in.  Result: wheezy-s390-python.zip (about 9 MB)
rem next to this file.  

setlocal
cd /d "%~dp0"
set B=http://archive.debian.org/debian/
if not exist wheezy-s390-python mkdir wheezy-s390-python

for %%P in (
  pool/main/p/python2.7/python2.7-minimal_2.7.3-6+deb7u2_s390.deb
  pool/main/m/mime-support/mime-support_3.52-1+deb7u1_all.deb
  pool/main/e/expat/libexpat1_2.1.0-1+deb7u2_s390.deb
  pool/main/p/python2.7/python2.7_2.7.3-6+deb7u2_s390.deb
  pool/main/p/python-defaults/python-minimal_2.7.3-4+deb7u1_all.deb
  pool/main/p/python-defaults/python_2.7.3-4+deb7u1_all.deb
  pool/main/p/python3.2/python3.2-minimal_3.2.3-7_s390.deb
  pool/main/libf/libffi/libffi5_3.0.10-3_s390.deb
  pool/main/p/python3.2/python3.2_3.2.3-7_s390.deb
  pool/main/p/python3-defaults/python3-minimal_3.2.3-6_all.deb
  pool/main/p/python3-defaults/python3_3.2.3-6_all.deb
) do call :get %%P

:pack
if exist wheezy-s390-python.zip del wheezy-s390-python.zip
pushd wheezy-s390-python
tar -a -c -f ..\wheezy-s390-python.zip *.deb
popd
if errorlevel 1 (echo *** packing failed & pause & exit /b 1)
echo.
echo done: %CD%\wheezy-s390-python.zip -- upload this one file
dir wheezy-s390-python.zip | find "wheezy"
pause
exit /b 0

:get
set F=wheezy-s390-python\%~nx1
if exist "%F%" (echo have  %~nx1 & exit /b 0)
echo fetch %~nx1
curl.exe -fsSL --retry 3 -o "%F%" "%B%%1"
if errorlevel 1 (echo *** cannot download %1 & del "%F%" 2>nul & pause & exit 1)
exit /b 0
