#!/bin/bash
# mkkit.sh -- build the VM/370+ overlay kit from the working pack.
# Run only with Hercules DOWN after a clean /shutdown.  Three parts, each
# under 30 MB: part 1 = config + shadows + tools + README, part 2 = the
# I-239-patched vm50-4.cckd, part 3 = the user volume's shadow (CMSUSER).  gccbrx.cckd is byte-identical to CE's and is
# not shipped.  Verified 6 Oct on a fresh CE extraction (kt1).
set -e
R=/home/claude/vm370; C=$R/scratchpad/VM370CE.V1.R1.2
D=${1:-$R/dist}; STAMP=$(date -u +%Y%m%d)
pgrep -x hercules >/dev/null && { echo "### Hercules is running"; exit 1; }
for f in $C/disks/shadows/*_1.shadow; do cckdcdsk -3 -ro $f >/dev/null || { echo "### bad $f"; exit 1; }; done
W=$(mktemp -d); K=$W/VM370CE.V1.R1.2; mkdir -p $K/disks/shadows $K/vm370plus
python3 - "$C/vm370ce.conf" "$K/vm370ce.conf" <<'PY'
import sys
s=open(sys.argv[1]).read()
i=s.find('# A SECOND 3215, added 3 October')
if i>0: s=s[:i].rstrip()+'\n'
s=s.replace('MAINSIZE        16','MAINSIZE        64')
s=s.replace('PANTITLE        "VM370CE 1.1.2"','PANTITLE        "VM/370+ (VM370CE 1.1.2 ESA/390)"')
open(sys.argv[2],'w').write(s)
PY
cp $C/disks/vm50-4.cckd $K/disks/; cp $C/disks/shadows/*_1.shadow $K/disks/shadows/
cp $R/arch/31bit/kit/README-VM370PLUS.txt $K/
cp $R/arch/31bit/cms/{GCC31.EXEC,HELLO31.C,HIGHSTOR.ASSEMBLE,HSTEST.ASSEMBLE} $R/arch/31bit/crexx/{CRXMAKE.EXEC,cms.h} $K/vm370plus/
mkdir -p $K/vm370plus/m5f; cp $R/arch/31bit/m5f/{README.md,cmsrt.c,cp1047.h,entry31.s,crt.sh,image.ld,hello31.c,libctest.c,elf_to_cms-pcrel.patch} $K/vm370plus/m5f/
mkdir -p $K/vm370plus/linux; cp -r $R/arch/31bit/linux390/decks/{linux45.rdr,lxparm.rdr} $R/arch/31bit/linux390/{README.md,config-4.0-31bit,psw_idle-align.patch,initramfs} $K/vm370plus/linux/
mkdir -p $D; cd $W
zip -qr $D/VM370PLUS-kit-$STAMP-part1.zip VM370CE.V1.R1.2 -x "VM370CE.V1.R1.2/disks/vm50-4.cckd" "VM370CE.V1.R1.2/disks/shadows/vm50u0_1.shadow"
zip -q  $D/VM370PLUS-kit-$STAMP-part2.zip VM370CE.V1.R1.2/disks/vm50-4.cckd
zip -q  $D/VM370PLUS-kit-$STAMP-part3.zip VM370CE.V1.R1.2/disks/shadows/vm50u0_1.shadow
rm -rf $W; ls -la $D
