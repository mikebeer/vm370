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
  printf '#!/bin/sh\nsync\nexec /bin/busybox %s -f\n' $c > /sbin/$c; chmod 755 /sbin/$c; done
hostname vm370plus
mkdir -p /dev/pts /etc/dropbear; mount -t devpts devpts /dev/pts
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
echo
echo "HELLO FROM LINUX/390 ON VM/370+ (M7)"
cat /etc/motd
uname -a
echo "BusyBox userland (in memory): ls /bin  ps  free  top -n1  vi  dmesg  poweroff"
export TERM=dumb HOME=/root PS1='\h:\w# ' PATH=/bin:/sbin:/usr/bin:/usr/sbin
cd /root
while true; do /bin/sh; echo "(shell ended -- restarting; 'poweroff' stops Linux)"; done
