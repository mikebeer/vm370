#!/bin/bash
# Current cREXX (rxc, rxas, rxvm, rxlink) cross-built for Linux on
# VM/370+: s390 31-bit, static, glibc sysroot from lx31.
#   build.sh vm|rxas|rxc|rxlink|all   -> out/<tool>
set -e
cd "$(dirname "$0")"
C=${CREXX:-/home/claude/adesutherland/crexx}
G=${CREXXGEN:-/home/claude/crexx-host/generated}
H=${CREXXHOST:-/home/claude/crexx-host}
CC="s390x-linux-gnu-gcc -m31 --sysroot=/home/claude/lx31/sysroot"
DEFS="-DCREXX_VM_SINGLE_THREADED=1 -DNTHREADED=1 -DMANUAL_PLUGIN_LINK=1 -DCREXX_VM_STATIC_ONLY=1 -DCREXX_VM_NO_SOCKETS=1"
INC="-I$G -I$C/interpreter -I$C/interpreter/rxvmplugin -I$C/assembler -I$C/binutils/include -I$C/rxpa -I$C/platform \
 -I$C/avl_tree -I$C/utf8 -I$C/inc -I$C/interpreter/rxvmplugin/rxvmplugins/mc_decimal/decnumber -I$C/compiler -I$H/compiler -I$H/assembler"
CF="-std=gnu99 -O2 -w $DEFS $INC"
source <(sed -n '/^VM="/,/rxgraph.c"/p;/^AS="/,/rxastoke.c"/p' ../../m8/build.sh)
VMF=$(for f in $VM; do echo $C/$f; done)
CP=$(sed -n 's/^ *"\${CREXX_\(SOURCE\|HOST_BUILD\)}\/\(compiler\/[a-z_0-9]*\.c\)"/\1 \2/p' $C/ports/single-threaded/compiler.cmake |
  while read w f; do [ $w = SOURCE ] && echo $C/$f || echo $H/$f; done)
mkdir -p out obj
obj() { local o; for f in "$@"; do o=obj/$(echo $f | md5sum | cut -c1-12)_$(basename $f .c).o
  [ $o -nt $f ] || $CC $CF -c $f -o $o; echo $o; done; }
build() { # name "main sources" "library sources": the library (VM, assembler) is
  # an archive, so a tool takes only what it calls (rxpashim vs rxcpfunc)
  local name=$1 m l
  m=$(obj $2); l=$(obj $3)
  rm -f obj/lib$name.a; s390x-linux-gnu-ar rcs obj/lib$name.a $l
  $CC -static -o out/$name $m obj/lib$name.a -lm
  echo "built out/$name"
}
case "$1" in
vm) build rxvm "$C/interpreter/rxvmmain.c" "$VMF" ;;
rxas) build rxas "$C/assembler/rxasmain.c" "$AS $VMF" ;;
rxc) build rxc "$C/compiler/rxc_main.c $CP $C/interpreter/rxvml.c" "$VMF $AS" ;;
all) $0 vm; $0 rxas; $0 rxc ;;
*) echo "usage: build.sh vm|rxas|rxc|all"; exit 2 ;;
esac
