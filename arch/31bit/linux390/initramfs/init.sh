#!/bin/sh
# /init for Linux/390 on VM/370+ (BusyBox userland, in memory)
/bin/busybox mkdir -p /proc /sys /tmp /dev /root /var/log /usr/bin /usr/sbin /sbin
/bin/busybox mount -t proc proc /proc
/bin/busybox mount -t sysfs sysfs /sys
/bin/busybox mount -t tmpfs tmpfs /tmp 2>/dev/null
/bin/busybox --install -s
# PID 1 is this script, which ignores the signals busybox poweroff/halt/reboot
# send to init, so each acts at once (Linux stops in a disabled wait)
for c in poweroff halt reboot; do rm -f /sbin/$c
  printf '#!/bin/sh\nsync\numount -a -r 2>/dev/null\nexec /bin/busybox %s -f\n' $c > /sbin/$c; chmod 755 /sbin/$c; done
hostname vm370plus
mount -t devtmpfs devtmpfs /dev 2>/dev/null
mkdir -p /dev/pts /etc/dropbear; mount -t devpts devpts /dev/pts
# Disk: every 3390 (or 3380) attached to this virtual machine goes
# online; the first one becomes /data, an ext2 file system that keeps
# its files across IPLs (made on first use -- e.g. a Hercules volume
# from  dasdinit -z -linux file.cckd 3390-1 LNX001 ,  CP ATTACH'ed).
for d in /sys/bus/ccw/devices/*; do
  case "$(cat $d/devtype 2>/dev/null)" in
    3390/*|3380/*) echo 1 > $d/online 2>/dev/null;; esac; done
sleep 1
# VM/370+ converts a format-1 channel program of at most 64 CCWs (D-21):
# 128 KB per request is 32 records of 4 KB, plus Define Extent and
# Locate Record -- well inside.
for q in /sys/block/dasd*/queue/max_sectors_kb; do [ -e $q ] && echo 128 > $q; done
# a volume without a Linux partition gets one over all of it (mkdasdpart)
for d in /dev/dasd?; do
  [ -b $d ] && [ ! -b ${d}1 ] || continue
  mkdasdpart $d && blockdev --rereadpt $d && sleep 1
done
for b in /dev/dasd?1; do
  [ -b $b ] || continue
  mkdir -p /data
  mount -t ext2 $b /data 2>/dev/null || {
    echo "disk: $b has no file system yet -- making one (once)"
    mke2fs -q -b 4096 $b && mount -t ext2 $b /data; }
  if mountpoint -q /data; then echo "disk: $b on /data (persistent)"; break; fi
done
ifconfig lo 127.0.0.1 up
# Network: a CTC pair (Hercules CTCI) attached to this virtual machine, e.g.
#   CP ATTACH 600 * 620  and  CP ATTACH 601 * 621  (the lower one reads).
# Addresses from the IPL parameters vmip= vmpeer= (default 10.1.1.2, and
# the PC at the other end of the CTC, 10.1.1.1).
VMIP=10.1.1.2; VMPEER=10.1.1.1
for a in $(cat /proc/cmdline); do case $a in
  vmip=*) VMIP=${a#vmip=};; vmpeer=*) VMPEER=${a#vmpeer=};; esac; done
CTC=""
for d in /sys/bus/ccw/devices/*; do
  [ "$(cat $d/cutype 2>/dev/null)" = 3088/08 ] && CTC="$CTC ${d##*/}"; done
set -- $CTC
if [ $# -ge 2 ]; then
  echo $1,$2 > /sys/bus/ccwgroup/drivers/ctcm/group
  echo 1 > /sys/bus/ccwgroup/drivers/ctcm/$1/online
  ifconfig ctc0 $VMIP pointopoint $VMPEER mtu 1500 up && route add default gw $VMPEER
  dropbear -R -p 22 && echo "network: ctc0 $VMIP (peer $VMPEER), ssh: root / vm370plus"
else
  echo "network: none (attach a CTC pair, e.g. CP ATTACH 600 * 620, 601 * 621)"
fi
# A Linux system installed on the disk (Debian, see debian-install): boot
# it, unless the IPL parameters say vmroot=ram.  The CTC group and the
# disk stay as set up here; the system on the disk configures the rest.
if [ -x /data/sbin/init ] && [ ! -d /data/debootstrap ] && ! grep -q vmroot=ram /proc/cmdline; then
  echo "root: the system on $(mount | awk '$3=="/data"{print $1}') -- switch_root (vmroot=ram stays here)"
  killall dropbear 2>/dev/null
  # the disk system's ifup sets the address itself ("File exists" if
  # it is still there); the line console wants no colours
  ip addr flush dev ctc0 2>/dev/null   # (not down: a CTC restart hangs)
  export TERM=dumb
  umount /dev/pts /tmp /proc /sys 2>/dev/null
  mount --move /dev /data/dev 2>/dev/null || umount /dev 2>/dev/null
  exec switch_root /data /sbin/init
fi
echo
echo "HELLO FROM LINUX/390 ON VM/370+ (M7)"
cat /etc/motd
uname -a
echo "BusyBox userland (in memory): ls /bin  ps  free  top -n1  vi  dmesg  poweroff"
export TERM=dumb HOME=/root PS1='\h:\w# ' PATH=/bin:/sbin:/usr/bin:/usr/sbin
cd /root
while true; do /bin/sh; echo "(shell ended -- restarting; 'poweroff' stops Linux)"; done
