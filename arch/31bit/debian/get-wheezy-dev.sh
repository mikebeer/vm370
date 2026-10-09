#!/bin/sh
# get-wheezy-dev.sh -- the same as get-wheezy-dev.ps1, for Linux/WSL/macOS:
# Debian 7 (wheezy) s390 packages for gcc under Debian on VM/370+.
#   sh get-wheezy-dev.sh [--no-cxx]     -> wheezy-s390-dev.zip
set -e
B=http://archive.debian.org/debian/
P="pool/main/g/gcc-4.6/gcc-4.6-base_4.6.3-14_s390.deb
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
pool/main/l/linux/linux-libc-dev_3.2.78-1_s390.deb"
[ "$1" = "--no-cxx" ] || P="$P
pool/main/g/gcc-defaults/g++_4.6.3-8_s390.deb
pool/main/g/gcc-4.6/g++-4.6_4.6.3-14_s390.deb
pool/main/g/gcc-4.6/libstdc++6-4.6-dev_4.6.3-14_s390.deb
pool/main/g/gcc-4.7/libstdc++6_4.7.2-5_s390.deb"
mkdir -p wheezy-s390-dev
for p in $P; do
  f=wheezy-s390-dev/$(basename $p)
  [ -s "$f" ] || { echo "fetch $(basename $p)"; curl -fsSL --retry 3 -o "$f" "$B$p"; }
done
rm -f wheezy-s390-dev.zip
(cd wheezy-s390-dev && zip -q ../wheezy-s390-dev.zip *.deb)
ls -l wheezy-s390-dev.zip
