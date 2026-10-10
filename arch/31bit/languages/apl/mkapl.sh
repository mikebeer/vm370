#!/bin/sh
# mkapl.sh OUT -- APL for VM/370plus: OUT/apl (Linux/390 31-bit, static),
# OUT/apl.text (CMS TEXT deck: LOAD APL, GENMOD APL).
set -e
H=$(cd "$(dirname "$0")" && pwd); A=${APLSRC:-/home/claude/mikebeer/apl}; O=$1
mkdir -p "$O"
s390x-linux-gnu-gcc -m31 --sysroot=/home/claude/lx31/sysroot -std=c89 -O2 -static \
  -o "$O/apl" "$A/apl_all.c" -lm
CFLAGS_PRE="-I$H/../../m5f/inc" CFLAGS_EXTRA="-U__linux__ -U__unix__ -U__unix -U__gnu_linux__ -std=c89 -w" \
  sh "$H/../../m5f/crt.sh" "$O/apl.text" "$A/apl_all.c" >/dev/null
echo "mkapl: $O/apl and $O/apl.text"
