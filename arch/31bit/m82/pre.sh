#!/bin/bash
# M8.2 prepass on the PC: compile the staged tree (prep.py) the way GCC380
# sees it on CMS -- GCCLIB31 headers, staged shims, GCC 3 predefines -- with
# s390x gcc -m31, to find missing headers, declarations and symbols before
# the slow native run.   pre.sh [name ...]  -> $OUT/*.o, *.err
cd "$(dirname "$0")"
S=${SP:-/tmp/claude-0/-home-claude-vm370/0e789c93-0fd6-50d9-9e2c-c5456a7467b9/scratchpad}
ST=${STAGE:-$S/m82stage}; OUT=${OUT:-$S/m82pre}; mkdir -p $OUT
DEFS="$(cat defs.txt)"
CF="-m31 -std=gnu99 -O0 -undef -nostdinc -fno-builtin -fno-stack-protector -D__CMS__ -D__GNUC__=3 -D__GNUC_MINOR__=2 -D__i370__ -D__CHAR_UNSIGNED__ -Wimplicit-function-declaration -Wno-int-conversion -I$ST -I../gcclib31/src"
FILES="$@"; [ -z "$FILES" ] && FILES=$(cat $ST/units.txt)
ok=0; bad=0
for b in $FILES; do
  if s390x-linux-gnu-gcc $CF $DEFS -c $ST/$b.c -o $OUT/$b.o 2> $OUT/$b.err; then ok=$((ok+1)); else bad=$((bad+1)); echo "FAIL $b: $(grep -m1 'error' $OUT/$b.err | cut -c1-200)"; fi
done
echo "$ok ok, $bad failed"
