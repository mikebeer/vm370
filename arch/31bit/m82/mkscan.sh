#!/bin/sh
# M8.2: the EBCDIC scanners.  re2c -e with upstream's S370/encoding.re.
# re2c's EBCDIC table makes "\n" X'25' (LF); GCC380 and GCCLIB31 use '\n'
# = X'15' (NL), which is what a CMS text record ends with -- so every
# "case 0x25:" gets a "case 0x15:" beside it.
set -e
cd "$(dirname "$0")"
C=/home/claude/adesutherland/crexx; H=/home/claude/crexx-host; R=$H/re2c/re2c; G=$PWD/gen
(cd $H/compiler && $R -I $C/S370 -e -o $G/rxcposcn.c $C/compiler/rxcposcn.re)
(cd $H/compiler && $R -I $C/S370 -e -o $G/rexbscan.c $C/compiler/rxcpbscn.re)
(cd $H/compiler && $R -I $C/S370 -e -o $G/rexcscan.c $C/compiler/rxcpcscn.re)
(cd $H/assembler && $R -I $C/S370 -e -o $G/rxasscan.c $C/assembler/rxasscan.re)
sed -i 's/case 0x25:/case 0x15: case 0x25:/' $G/*.c
grep -c "case 0x15: case 0x25:" $G/*.c
