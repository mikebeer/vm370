@echo off
rem get-wheezy-the.bat -- VM/370+: download THE (The Hessling Editor) and
rem Regina REXX for Debian 7 (wheezy) s390, with the packages they need,
rem from archive.debian.org.  Windows 10 or later (PowerShell 5).
rem   get-wheezy-the.bat            -> .\wheezy-the\*.deb
rem Then attach the .deb files (or the wheezy-the.zip it makes) to the chat.
setlocal
set "DEST=%~dp0wheezy-the"
powershell -NoProfile -ExecutionPolicy Bypass -Command "$s=Get-Content -Raw -LiteralPath '%~f0'; iex (($s -split ('#'+'PSSTART'))[1])"
if errorlevel 1 (echo FAILED & exit /b 1)
echo.
echo Done: the files are in %DEST% and in %~dp0wheezy-the.zip
exit /b 0
#PSSTART
$ErrorActionPreference = 'Stop'
[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
$base = 'https://archive.debian.org/debian/'
$dest = $env:DEST
New-Item -ItemType Directory -Force -Path $dest | Out-Null
# what we want, and what the VM/370+ Debian disk already has (not fetched)
$want = @('the', 'the-doc', 'regina-rexx', 'libregina3')
$have = @('libc6', 'libc-bin', 'libgcc1', 'multiarch-support', 'libtinfo5', 'libncurses5',
          'libncursesw5', 'ncurses-base', 'ncurses-bin', 'debconf', 'dpkg', 'perl-base',
          'zlib1g', 'install-info', 'libselinux1', 'tzdata', 'gcc-4.7-base', 'dpkg-dev',
          'debconf-2.0', 'awk', 'mawk')
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
$zip = Join-Path (Split-Path $dest -Parent) 'wheezy-the.zip'
if (Test-Path $zip) { Remove-Item $zip }
Compress-Archive -Path (Join-Path $dest '*.deb') -DestinationPath $zip
Write-Host ("{0} packages downloaded" -f $got.Count)
