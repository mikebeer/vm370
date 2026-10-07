#!/bin/sh
# crt.sh -- VM/370+ M5f: compile and link a C program for CMS (AMODE 31).
#   crt.sh OUT.text file.c ...   -> OUT.text (CMS TEXT deck: LOAD, GENMOD)
# Needs: s390x-linux-gnu-gcc (13, with lib32gcc-13-dev-s390x-cross), the
# newlib build in $NEWLIB (libc.a, libm.a, headers), softfp/libsoftfp.a,
# and elf_to_cms (Adrian Sutherland's, patched: elf_to_cms-pcrel.patch).
set -e
H=$(cd "$(dirname "$0")" && pwd)
X=s390x-linux-gnu
NEWLIB=${NEWLIB:-/home/claude/nlbuild}
NLSRC=${NLSRC:-/home/claude/nlsrc/newlib-4.4.0.20231231/newlib}
E2C=${E2C:-/home/claude/m5f/elf_to_cms}
GI=$($X-gcc -m31 -print-file-name=include)
LIBGCC=$($X-gcc -m31 -print-libgcc-file-name)
OUT=$1; shift
W=$(mktemp -d)
CF="-m31 -mesa -march=z900 -msoft-float -mlong-double-64 -O2 -fno-pic -fno-pie -fno-asynchronous-unwind-tables -fno-unwind-tables -fno-stack-protector -ffunction-sections -fdata-sections -nostdinc -isystem $GI -I$NEWLIB/targ-include -I$NLSRC/libc/include"
objs=""
for c in "$@"; do
  o=$W/$(basename "$c" .c).o
  $X-gcc $CF ${CFLAGS_EXTRA} -c "$c" -o "$o"; objs="$objs $o"
done
$X-gcc $CF -c "$H/cmsrt.c" -o $W/cmsrt.o
$X-as -m31 -mesa "$H/entry31.s" -o $W/entry31.o
$X-ld -m elf_s390 -static --emit-relocs --gc-sections -T "$H/image.ld" \
   -Map "${OUT%.*}.map" -o "${OUT%.*}.elf" $W/entry31.o $objs $W/cmsrt.o \
   --start-group $NEWLIB/libc.a $NEWLIB/libm.a "$H/softfp/libsoftfp.a" $LIBGCC --end-group
$E2C "${OUT%.*}.elf" "$OUT"
rm -rf $W
