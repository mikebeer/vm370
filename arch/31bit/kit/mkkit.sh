#!/bin/bash
# mkkit.sh -- build the VM/370plus overlay kit from the working pack.
# Run only with Hercules DOWN after a clean /shutdown.  Three parts, each
# under 30 MB: part 1 = config + shadows + tools + README, part 2 = the
# I-239-patched vm50-4.cckd, part 3 = the user volume's shadow (CMSUSER).  gccbrx.cckd is byte-identical to CE's and is
# not shipped.  Verified 6 Oct on a fresh CE extraction (kt1).
set -e
R=/home/claude/vm370; C=$R/scratchpad/VM370CE.V1.R1.2
D=${1:-$R/dist}; STAMP=$(date -u +%Y%m%d)-b${KITBUILD:?set KITBUILD, the build number of this kit}
pgrep -x hercules >/dev/null && { echo "### Hercules is running"; exit 1; }
for f in $C/disks/shadows/*_1.shadow; do cckdcdsk -3 -ro $f >/dev/null || { echo "### bad $f"; exit 1; }; done
W=$(mktemp -d); K=$W/VM370CE.V1.R1.2; mkdir -p $K/disks/shadows $K/vm370plus
python3 - "$C/vm370ce.conf" "$K/vm370ce.conf" <<'PY'
import sys
s=open(sys.argv[1]).read()
i=s.find('# A SECOND 3215, added 3 October')
if i>0: s=s[:i].rstrip()+'\n'
s=s.replace('MAINSIZE        16','MAINSIZE        256')
s=s.replace('#0500 CTCE 30882 127.0.0.1 30880','0500 CTCE 30882 127.0.0.1 30880')
s=s.replace('0600.2  CTCI    10.1.1.2 10.1.1.1','# Remove the # on the next line for Linux networking (README):\n#0600.2  CTCI    10.1.1.2 10.1.1.1')
s=s.replace('PANTITLE        "VM370CE 1.1.2"','PANTITLE        "VM/370plus (VM370CE 1.1.2 ESA/390)"')
open(sys.argv[2],'w').write(s)
PY
cp $C/disks/vm50-4.cckd $K/disks/; cp $C/disks/shadows/*_1.shadow $K/disks/shadows/
for f in $K/disks/shadows/*_1.shadow; do cckdcomp $f >/dev/null; cckdcdsk -3 -ro $f >/dev/null; done   # free space out
# VM50-3 carries spool and TEMP paging: test runs leave tens of MB of dead
# tracks there that cckdcomp cannot reclaim.  SHADOW3=<a clean vm50-3_1.shadow>
# ships that one instead (the kit is IPLed COLD, so no spool file survives).
test -n "$SHADOW3" && cp "$SHADOW3" $K/disks/shadows/vm50-3_1.shadow
cp $R/arch/31bit/kit/README-VM370PLUS.txt $K/
cp $R/arch/31bit/cms/{GCC31.EXEC,HELLO31.C,HIGHSTOR.ASSEMBLE,HSTEST.ASSEMBLE} $R/arch/31bit/crexx/{CRXMAKE.EXEC,cms.h} $K/vm370plus/
mkdir -p $K/vm370plus/m5f; cp $R/arch/31bit/m5f/{README.md,cmsrt.c,cp1047.h,entry31.s,crt.sh,image.ld,hello31.c,libctest.c,elf_to_cms-pcrel.patch} $K/vm370plus/m5f/
mkdir -p $K/vm370plus/linux; cp -r $R/arch/31bit/linux390/decks/{linux48.rdr,lxparm.rdr,lxparmram.rdr} $R/arch/31bit/linux390/{README.md,config-4.0-31bit,busybox-1.36.1.config,psw_idle-align.patch,dma16m-idal.patch,entry-mcck-loop.patch,initramfs} $K/vm370plus/linux/
cp $R/arch/31bit/debian/vm370plus-post.sh $K/vm370plus/linux/
cp -r $R/arch/31bit/linux390/cms $K/vm370plus/linux/   # LINUX EXEC and LXPARM files (also on MAINT 19D)
test -n "$GUIDE" && cp "$GUIDE" $K/vm370plus/linux/VM370PLUS-Guide.docx
mkdir -p $D; cd $W
zip -qr $D/VM370PLUS-kit-$STAMP-part1.zip VM370CE.V1.R1.2 -x "VM370CE.V1.R1.2/disks/vm50-4.cckd" "VM370CE.V1.R1.2/disks/shadows/vm50u0_1.shadow" "VM370CE.V1.R1.2/vm370plus/linux/*" "VM370CE.V1.R1.2/disks/shadows/vm50-2_1.shadow"
zip -qr $D/VM370PLUS-kit-$STAMP-part4.zip VM370CE.V1.R1.2/vm370plus/linux VM370CE.V1.R1.2/disks/shadows/vm50-2_1.shadow
zip -q  $D/VM370PLUS-kit-$STAMP-part2.zip VM370CE.V1.R1.2/disks/vm50-4.cckd
zip -q  $D/VM370PLUS-kit-$STAMP-part3.zip VM370CE.V1.R1.2/disks/shadows/vm50u0_1.shadow
# parts 5-7: the Debian disk (LNX190), compacted, split in three pieces
# that copy /b joins (README: INSTALL THE DEBIAN DISK)
if [ -n "$DEBDISK" ]; then
  mkdir -p $W/deb/VM370CE.V1.R1.2/disks; cp $DEBDISK $W/deb/lnx190.cckd
  cckdcomp $W/deb/lnx190.cckd >/dev/null
  n=$(stat -c %s $W/deb/lnx190.cckd); p=$(( (n+2)/3 ))
  split -b $p -d -a 3 --numeric-suffixes=1 $W/deb/lnx190.cckd $W/deb/VM370CE.V1.R1.2/disks/lnx190.cckd.
  sha256sum $W/deb/lnx190.cckd | sed 's#  .*#  lnx190.cckd#' > $W/deb/VM370CE.V1.R1.2/disks/lnx190.sha256
  (cd $W/deb; zip -q $D/VM370PLUS-kit-$STAMP-part5.zip VM370CE.V1.R1.2/disks/lnx190.cckd.001 VM370CE.V1.R1.2/disks/lnx190.sha256
   zip -q $D/VM370PLUS-kit-$STAMP-part6.zip VM370CE.V1.R1.2/disks/lnx190.cckd.002
   zip -q $D/VM370PLUS-kit-$STAMP-part7.zip VM370CE.V1.R1.2/disks/lnx190.cckd.003)
fi
rm -rf $W; ls -la $D
