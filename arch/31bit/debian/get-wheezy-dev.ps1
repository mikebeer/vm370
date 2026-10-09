# get-wheezy-dev.ps1 -- VM/370+: download the Debian 7 (wheezy) s390 packages
# for a C compiler under Debian (gcc 4.6, binutils, make, libc6-dev, and
# optionally g++), and pack them into one zip to upload.
#
#   powershell -ExecutionPolicy Bypass -File get-wheezy-dev.ps1
#   powershell -ExecutionPolicy Bypass -File get-wheezy-dev.ps1 -NoCxx
#
# Result: wheezy-s390-dev.zip (about 16 MB, 24 MB with g++) in this folder.

param([switch]$NoCxx)

$ErrorActionPreference = 'Stop'
$ProgressPreference = 'SilentlyContinue'      # Invoke-WebRequest is slow with it
$base = 'http://archive.debian.org/debian/'

$pkgs = @(
  'pool/main/g/gcc-4.6/gcc-4.6-base_4.6.3-14_s390.deb',
  'pool/main/g/gcc-4.6/cpp-4.6_4.6.3-14_s390.deb',
  'pool/main/g/gcc-4.6/gcc-4.6_4.6.3-14_s390.deb',
  'pool/main/g/gcc-defaults/cpp_4.6.3-8_s390.deb',
  'pool/main/g/gcc-defaults/gcc_4.6.3-8_s390.deb',
  'pool/main/g/gmp/libgmp10_5.0.5+dfsg-2_s390.deb',
  'pool/main/m/mpfr4/libmpfr4_3.1.0-5_s390.deb',
  'pool/main/m/mpclib/libmpc2_0.9-4_s390.deb',
  'pool/main/g/gcc-4.7/libgomp1_4.7.2-5_s390.deb',
  'pool/main/b/binutils/binutils_2.22-8+deb7u2_s390.deb',
  'pool/main/m/make-dfsg/make_3.81-8.2_s390.deb',
  'pool/main/e/eglibc/libc-dev-bin_2.13-38+deb7u10_s390.deb',
  'pool/main/e/eglibc/libc6-dev_2.13-38+deb7u10_s390.deb',
  'pool/main/l/linux/linux-libc-dev_3.2.78-1_s390.deb'
)
if (-not $NoCxx) {
  $pkgs += @(
    'pool/main/g/gcc-defaults/g++_4.6.3-8_s390.deb',
    'pool/main/g/gcc-4.6/g++-4.6_4.6.3-14_s390.deb',
    'pool/main/g/gcc-4.6/libstdc++6-4.6-dev_4.6.3-14_s390.deb',
    'pool/main/g/gcc-4.7/libstdc++6_4.7.2-5_s390.deb'
  )
}

$dir = Join-Path $PSScriptRoot 'wheezy-s390-dev'
New-Item -ItemType Directory -Force -Path $dir | Out-Null

foreach ($p in $pkgs) {
  $name = Split-Path $p -Leaf
  $out = Join-Path $dir $name
  if (Test-Path $out) { Write-Host "have  $name"; continue }
  Write-Host "fetch $name"
  for ($try = 1; $try -le 3; $try++) {
    try {
      Invoke-WebRequest -Uri ($base + $p) -OutFile $out -UseBasicParsing
      break
    } catch {
      if ($try -eq 3) { throw "cannot download $p : $_" }
      Start-Sleep -Seconds 3
    }
  }
}

$zip = Join-Path $PSScriptRoot 'wheezy-s390-dev.zip'
if (Test-Path $zip) { Remove-Item $zip }
Compress-Archive -Path (Join-Path $dir '*.deb') -DestinationPath $zip
$mb = [math]::Round((Get-Item $zip).Length / 1MB, 1)
Write-Host "done: $zip ($mb MB, $($pkgs.Count) packages) -- upload this one file"
