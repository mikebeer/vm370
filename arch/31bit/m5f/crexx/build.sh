#!/bin/sh
# Cross-build the cREXX 2022 tree (F0041) for VM/370+ AMODE 31.
# Scanners/parsers from a host cmake build (ASCII re2c output) in $C/hbuild.
set -e
cd "$(dirname "$0")"
C=${CREXX:-/home/claude/crexx2022}
INC="-I$C/compiler -I$C/platform -I$C/machine -I$C/avl_tree -I$C/utf8 -I$C/interpreter -I$C/assembler"
COMMON="$C/platform/platform.c $C/machine/rxvminst.c $C/avl_tree/avl_tree.c"
export CFLAGS_EXTRA="$INC -w"
../crt.sh rxc.text $C/compiler/rxcpmain.c $C/compiler/rxcpast.c $C/hbuild/compiler/rxcposcn.c \
  $C/compiler/rxcpopgr.c $C/compiler/rxcpopar.c $C/hbuild/compiler/rexbscan.c $C/compiler/rxcpbgmr.c \
  $C/compiler/rxcpbpar.c $C/compiler/rxcpbval.c $C/compiler/rxcpsymb.c $C/compiler/rxcpemit.c \
  $C/compiler/rxcp_opt.c $COMMON
../crt.sh rxas.text $C/assembler/rxasmain.c $C/assembler/rxastoke.c $C/assembler/rxaseror.c \
  $C/hbuild/assembler/rxasscan.c $C/assembler/rxas_opt.c $C/assembler/rxasgrmr.c $C/assembler/rxasassm.c $COMMON
../crt.sh rxdas.text $C/disassembler/rxdamain.c $C/disassembler/rxdadism.c $COMMON
CFLAGS_EXTRA="$INC -w -DNTHREADED=1 -Dtimezone=_timezone" ../crt.sh rxbvm.text \
  $C/interpreter/rxvmmain.c $C/interpreter/rxvmintp.c $C/interpreter/rxvmload.c $COMMON
