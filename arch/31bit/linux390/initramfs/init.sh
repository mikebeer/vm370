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
echo
echo "HELLO FROM LINUX/390 ON VM/370+ (M7)"
cat /etc/motd
uname -a
echo "BusyBox userland (in memory): ls /bin  ps  free  top -n1  vi  dmesg  poweroff"
export TERM=dumb HOME=/root PS1='\h:\w# ' PATH=/bin:/sbin:/usr/bin:/usr/sbin
cd /root
while true; do /bin/sh; echo "(shell ended -- restarting; 'poweroff' stops Linux)"; done
