#!/bin/sh
# M8.2: the EBCDIC scanners, re2c -e with upstream's S370/encoding.re.
# re2c's EBCDIC table is code page 037 with "\n" as X'25'; VM/370plus is
# IBM-1047 throughout (Hercules CODEPAGE 819/1047, so the C sources, GCC380
# and every text file), with "\n" as X'15' (NL, what GCC380 and GCCLIB31
# use).  re2c/ebcdic.h is re2c's table for that; this script builds a re2c
# with it (once) and generates the four scanners.
set -e
cd "$(dirname "$0")"
C=/home/claude/adesutherland/crexx; G=$PWD/gen
B=${RE2C1047:-/tmp/re2c1047}
if [ ! -x $B/build/re2c ]; then
  rm -rf $B; mkdir -p $B
  cp -r $C/re2c $B/src
  cp re2c/ebcdic.h $B/src/src/encoding/ebcdic.h
  mkdir -p $B/build
  (cd $B/build && cmake -DCMAKE_BUILD_TYPE=Release $B/src > cmake.log && make -j8 re2c > make.log)
fi
R=$B/build/re2c; H=/home/claude/crexx-host
(cd $H/compiler && $R -I $C/S370 -e -o $G/rxcposcn.c $C/compiler/rxcposcn.re)
(cd $H/compiler && $R -I $C/S370 -e -o $G/rexbscan.c $C/compiler/rxcpbscn.re)
(cd $H/compiler && $R -I $C/S370 -e -o $G/rexcscan.c $C/compiler/rxcpcscn.re)
(cd $H/assembler && $R -I $C/S370 -e -o $G/rxasscan.c $C/assembler/rxasscan.re)
grep -c "0x15" $G/*.c
