#!/bin/bash
# M8: compile every source of a current-cREXX CMake target with the M5f
# cross flags (GCC 13 -m31, newlib, cmsrt) and report which ones fail.
#   trycc.sh TARGETDIR  (e.g. compiler/CMakeFiles/rxclib.dir)
H=/home/claude/crexx-host; C=/home/claude/adesutherland/crexx
X=s390x-linux-gnu; NEWLIB=/home/claude/nlbuild; NLSRC=/home/claude/nlsrc/newlib-4.4.0.20231231/newlib
GI=$($X-gcc -m31 -print-file-name=include)
CF="-m31 -mesa -march=z900 -msoft-float -mlong-double-64 -O2 -std=gnu90 -fno-pic -fno-pie -fno-stack-protector -nostdinc -I/home/claude/vm370/arch/31bit/m8/inc -isystem $GI -I$NEWLIB/targ-include -I$NLSRC/libc/include -D_POSIX_THREADS -D_POSIX_MONOTONIC_CLOCK -D_POSIX_TIMERS -D_UNIX98_THREAD_MUTEX_ATTRIBUTES -Dtimezone=_timezone -I/home/claude/vm370/arch/31bit/m8/inc -include /home/claude/vm370/arch/31bit/m8/inc/cmscompat.h"
T=$1; OUT=${2:-/tmp/m8try}; mkdir -p $OUT
INC=$(sed -n 's/^C_INCLUDES = //p' $H/$T/flags.make)
DEF=$(sed -n 's/^C_DEFINES = //p' $H/$T/flags.make)
ok=0; bad=0
for o in $(grep -ho "[^ ]*\.c\.o:" $H/$T/build.make | sort -u); do
  rel=${o#*.dir/}; rel=${rel%.o:}; rel=${rel//__\//..\/}
  src=$(cd $C/$(dirname ${T%%/CMakeFiles*}) 2>/dev/null; true)
  base=$(dirname ${T%%/CMakeFiles*})/${T%%/CMakeFiles*}
  f=$(realpath -m $C/${T%%/CMakeFiles*}/$rel); [ -f "$f" ] || f=$(realpath -m $H/${T%%/CMakeFiles*}/$rel)
  if $X-gcc $CF $DEF $INC -c "$f" -o $OUT/$(basename $f .c).o 2> $OUT/$(basename $f .c).err; then ok=$((ok+1)); else bad=$((bad+1)); echo "FAIL $f: $(grep -m1 error $OUT/$(basename $f .c).err)"; fi
done
echo "$T: $ok ok, $bad failed"
