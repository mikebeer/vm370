#!/bin/bash
# M8: current cREXX (adesutherland/crexx, ports/single-threaded) cross-built
# for CMS on VM/370plus with the M5f toolchain (GCC 13 -m31, newlib, cmsrt).
#   build.sh vm|rxc|rxas   -> rxbvm.text / rxc.text / rxas.text here
set -e
export E2C=${E2C:-/home/claude/m5f/elf_to_cms8}   # RXC is 2.8 MB: the 8 MB image limit
cd "$(dirname "$0")"
C=${CREXX:-/home/claude/adesutherland/crexx}
G=${CREXXGEN:-/home/claude/crexx-host/generated}
DEFS="-DCREXX_CMS_ELF=1 -DCREXX_CMS_TEXT_IO=1 -DCREXX_CMS_DIRENT=1 -DCREXX_VM_SINGLE_THREADED=1 -DNTHREADED=1 -DCREXX_VM_HANDLER_PANEL=20 -DMANUAL_PLUGIN_LINK=1 \
 -DCREXX_VM_STATIC_ONLY=1 -DCREXX_VM_NO_SOCKETS=1 -DCREXX_VM_PORTABLE_ALLOC=1 -DCREXX_VM_COMPACT=1 \
 -DRXVM_MEMORY_SLAB_SIZE=4096 -DRXVM_MEMORY_MAX_STANDARD_SIZE=2048"
INC="-I/home/claude/vm370/arch/31bit/m8/inc/cms -I$G -I$C/interpreter -I$C/interpreter/rxvmplugin -I$C/assembler -I$C/binutils/include -I$C/rxpa -I$C/platform \
 -I$C/avl_tree -I$C/utf8 -I$C/inc -I$C/interpreter/rxvmplugin/rxvmplugins/mc_decimal/decnumber -I$C/compiler"
VM="interpreter/rxvmintp.c interpreter/rxvmworker.c interpreter/rxvmprogram.c interpreter/rxvmactive.c interpreter/rxvmload.c
 interpreter/interrupt_single.c interpreter/rxenv.c interpreter/exitfunc.c interpreter/rxpacallmethod.c interpreter/rxpafuncs.c
 interpreter/rxvml/rxvm_run.c interpreter/rxvmref.c interpreter/rxpacompat.c interpreter/rxvmmemory.c interpreter/rxpashim.c
 interpreter/rxvmplugin/rxvmplugin_framework.c interpreter/rxvmplugin/rxvmplugins/mc_decimal/mc_decimal.c
 interpreter/rxvmplugin/rxvmplugins/mc_decimal/decnumber/decNumber.c interpreter/rxvmplugin/rxvmplugins/mc_decimal/decnumber/decContext.c
 platform/platform.c platform/platform_tso.c platform/platform_native.c platform/text_codec.c platform/oom.c platform/rxinteger.c
 avl_tree/avl_tree.c rxpa/rxpa.c binutils/rxbin.c binutils/rxbin007.c binutils/rxsignature.c binutils/rxsha256.c binutils/rxgraph.c"
export CFLAGS_PRE="-I/home/claude/vm370/arch/31bit/m8/inc/cms"
export CFLAGS_EXTRA="-std=gnu99 -Os $DEFS $INC -w -include cmstz.h ${M8EXTRA}"
H=${CREXXHOST:-/home/claude/crexx-host}
AS="$C/binutils/rxopmeta.c $C/assembler/rxas_dsl.c $C/assembler/rxas_flow.c $C/assembler/rxas_flow_analysis.c
 $C/assembler/rxas_flow_batch.c $C/assembler/rxas_flow_graph.c $C/assembler/rxas_flow_pass.c $C/assembler/rxas_flow_proof.c
 $C/assembler/rxas_flow_rewrite.c $C/assembler/rxas_flow_signal.c $C/assembler/rxas_flow_ssa.c $C/assembler/rxas_flow_use.c
 $C/assembler/rxas_opt.c $C/assembler/rxasassm.c $C/assembler/rxaseror.c $H/assembler/rxasgrmr.c $C/assembler/rxaslib.c
 $H/assembler/rxasscan.c $C/assembler/rxastoke.c"
CP=$(sed -n 's/^ *"\${CREXX_\(SOURCE\|HOST_BUILD\)}\/\(compiler\/[a-z_0-9]*\.c\)"/\1 \2/p' $C/ports/single-threaded/compiler.cmake |
  while read w f; do [ $w = SOURCE ] && echo $C/$f || echo $H/$f; done)
VMF=$(for f in $VM; do echo $C/$f; done)
case "$1" in
vm) ../m5f/crt.sh rxbvm.text $C/interpreter/rxvmmain.c $VMF ;;
rxc) LIBSRC="$VMF $AS" CFLAGS_EXTRA="$CFLAGS_EXTRA -I$H/compiler -I$H/assembler" ../m5f/crt.sh rxc.text $C/compiler/rxc_main.c $CP $C/interpreter/rxvml.c ;;
rxas) CFLAGS_EXTRA="$CFLAGS_EXTRA -I$H/assembler" ../m5f/crt.sh rxas.text $C/assembler/rxasmain.c $AS $VMF ;;
*) echo "usage: build.sh vm"; exit 2 ;;
esac
