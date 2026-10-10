@echo off
rem get-wheezy.bat -- VM/370plus: download Debian 7 (wheezy) s390 packages
rem and every package they need that our Debian disk does not have yet,
rem from archive.debian.org.  Windows 10 or later (PowerShell 5).
rem   get-wheezy.bat                    -> asterisk (the default)
rem   get-wheezy.bat pkg1 pkg2 ...      -> those packages
rem Result: .\wheezy-pkgs\*.deb and wheezy-pkgs.zip -- attach the zip to the chat.
setlocal
set "WANT=%*"
if "%WANT%"=="" set "WANT=asterisk asterisk-core-sounds-en-gsm asterisk-moh-opsound-gsm"
set "DEST=%~dp0wheezy-pkgs"
powershell -NoProfile -ExecutionPolicy Bypass -Command "$s=Get-Content -Raw -LiteralPath '%~f0'; iex (($s -split ('#'+'PSSTART'))[1])"
if errorlevel 1 (echo FAILED & exit /b 1)
echo.
echo Done: the files are in %DEST% and in %~dp0wheezy-pkgs.zip
exit /b 0
#PSSTART
$ErrorActionPreference = 'Stop'
[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
$base = 'https://archive.debian.org/debian/'
$dest = $env:DEST
New-Item -ItemType Directory -Force -Path $dest | Out-Null
# what we want, and what the VM/370plus Debian disk already has (not fetched)
$want = $env:WANT -split '\s+' | Where-Object { $_ }
# every package already on the VM/370plus Debian disk (golden7, dpkg-query)
$have = @('adduser','apt','apt-utils','aptitude','aptitude-common','base-files','base-passwd','bash','binutils','bsdmainutils','bsdutils','ca-certificates','coreutils','cpio','cpp','cpp-4.6','cron','dash','debconf','debconf-i18n','debian-archive-keyring','debianutils','diffutils','dpkg','e2fslibs','e2fsprogs','file','findutils','g++','g++-4.6','gawk','gcc','gcc-4.6','gcc-4.6-base','gcc-4.7-base','gnupg','gpgv','grep','groff-base','gzip','hostname','ifupdown','info','initscripts','insserv','install-info','iproute','iptables','iputils-ping','isc-dhcp-client','isc-dhcp-common','kmod','less','libacl1','libapt-inst1.5','libapt-pkg4.12','libattr1','libblkid1','libboost-iostreams1.49.0','libbsd0','libbz2-1.0','libc-bin','libc-dev-bin','libc6','libc6-dev','libcomerr2','libcwidget3','libdb5.1','libedit2','libept1.4.12','libexpat1','libffi5','libfuse2','libgcc1','libgcrypt11','libgdbm3','libgmp10','libgnutls26','libgomp1','libgpg-error0','libgssapi-krb5-2','libidn11','libk5crypto3','libkeyutils1','libkmod2','libkrb5-3','libkrb5support0','liblocale-gettext-perl','liblzma5','libmagic1','libmount1','libmpc2','libmpfr4','libncurses5','libncursesw5','libnewt0.52','libnfnetlink0','libp11-kit0','libpam-modules','libpam-modules-bin','libpam-runtime','libpam0g','libpipeline1','libpopt0','libprocps0','libreadline6','libregina3','libselinux1','libsemanage-common','libsemanage1','libsepol1','libsigc++-2.0-0c2a','libsigsegv2','libslang2','libsqlite3-0','libss2','libssl1.0.0','libstdc++6','libstdc++6-4.6-dev','libtasn1-3','libtext-charwidth-perl','libtext-iconv-perl','libtext-wrapi18n-perl','libtinfo5','libudev0','libusb-0.1-4','libustr-1.0-1','libuuid1','libwrap0','libxapian22','linux-libc-dev','login','logrotate','lsb-base','make','man-db','manpages','mawk','mime-support','mount','multiarch-support','nano','ncurses-base','ncurses-bin','net-tools','netbase','netcat-traditional','openssh-client','openssh-server','openssl','passwd','perl-base','procps','psmisc','python','python-minimal','python2.7','python2.7-minimal','python3','python3-minimal','python3.2','python3.2-minimal','readline-common','regina-rexx','rsyslog','s390-tools','sed','sensible-utils','sysv-rc','sysvinit','sysvinit-utils','tar','tasksel','tasksel-data','the','the-doc','traceroute','tzdata','udev','util-linux','vim-common','vim-tiny','wget','whiptail','xz-utils','zlib1g')
$idx = Join-Path $dest 'Packages.gz'
Write-Host 'Fetching the wheezy s390 package index ...'
Invoke-WebRequest -UseBasicParsing -Uri ($base + 'dists/wheezy/main/binary-s390/Packages.gz') -OutFile $idx
$fs = [IO.File]::OpenRead($idx)
$gz = New-Object IO.Compression.GzipStream($fs, [IO.Compression.CompressionMode]::Decompress)
$rd = New-Object IO.StreamReader($gz)
$txt = $rd.ReadToEnd(); $rd.Close()
$pk = @{}; $prov = @{}
foreach ($st in ($txt -split "`n`n")) {
  $h = @{}
  foreach ($l in ($st -split "`n")) { if ($l -match '^([A-Za-z-]+):\s*(.*)$') { $h[$matches[1]] = $matches[2] } }
  if ($h['Package']) {
    $pk[$h['Package']] = $h
    if ($h['Provides']) { foreach ($v in ($h['Provides'] -split ',')) { $v = $v.Trim(); if (-not $prov[$v]) { $prov[$v] = $h['Package'] } } }
  }
}
Write-Host ("{0} packages in the index" -f $pk.Count)
$todo = New-Object System.Collections.Queue
$want | ForEach-Object { $todo.Enqueue($_) }
$got = [ordered]@{}
while ($todo.Count -gt 0) {
  $n = $todo.Dequeue()
  if ($have -contains $n -or $got.Contains($n)) { continue }
  if (-not $pk[$n]) {
    if ($prov[$n]) { $n = $prov[$n]; if ($have -contains $n -or $got.Contains($n)) { continue } }
    else { Write-Host "  not in wheezy: $n"; continue }
  }
  $p = $pk[$n]; $got[$n] = $p['Filename']
  foreach ($f in 'Pre-Depends', 'Depends') {
    if ($p[$f]) {
      foreach ($d in ($p[$f] -split ',')) {
        $first = ($d -split '\|')[0].Trim()
        $name = ($first -split '[\s(]')[0]
        if ($name) { $todo.Enqueue($name) }
      }
    }
  }
}
foreach ($n in $got.Keys) {
  $file = $got[$n]; $out = Join-Path $dest (Split-Path $file -Leaf)
  Write-Host "  $n  <- $file"
  Invoke-WebRequest -UseBasicParsing -Uri ($base + $file) -OutFile $out
}
Remove-Item $idx
$zip = Join-Path (Split-Path $dest -Parent) 'wheezy-pkgs.zip'
if (Test-Path $zip) { Remove-Item $zip }
Compress-Archive -Path (Join-Path $dest '*.deb') -DestinationPath $zip
Write-Host ("{0} packages downloaded" -f $got.Count)
