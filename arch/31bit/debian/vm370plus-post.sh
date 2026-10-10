#!/bin/sh
# VM/370plus: finish a Debian wheezy s390 system after debootstrap's second
# stage (run inside the chroot).  Console: the 3215 is ttyS0, line mode.
set -e
echo vm370plus > /etc/hostname
cat > /etc/hosts <<H
127.0.0.1 localhost
10.1.1.2  vm370plus
H
cat > /etc/fstab <<F
# VM/370plus: the root is mounted by the initramfs before switch_root
/dev/dasda1  /      ext2   defaults,errors=remount-ro  0  0
proc         /proc  proc   defaults                    0  0
/swapfile    none   swap   sw                          0  0
F
# 64 MB is too little for dpkg's xz on some packages: 128 MB of swap
[ -f /swapfile ] || { dd if=/dev/zero of=/swapfile bs=1M count=128; mkswap /swapfile; }
chmod 600 /swapfile
cat > /etc/network/interfaces <<N
auto lo
iface lo inet loopback

# the CTC pair to the PC (Hercules CTCI).  The initramfs groups the
# adapters and configures ctc0 from the IPL parameters (vmip=, vmpeer=;
# default 10.1.1.2 / 10.1.1.1) before switch_root, so the same disk
# works for every user; Debian leaves it alone.
auto ctc0
iface ctc0 inet manual
N
echo "nameserver 8.8.8.8" > /etc/resolv.conf
cat > /etc/apt/sources.list <<S
deb http://archive.debian.org/debian wheezy main
S
echo 'Acquire::Check-Valid-Until "false";' > /etc/apt/apt.conf.d/10archive
# the console: one getty on the 3215 (line mode, TERM dumb), no VTs
sed -i -e '/^[1-6]:/d' -e '/^T[0-9]:/d' /etc/inittab
echo 'T0:2345:respawn:/sbin/getty -L ttyS0 9600 dumb' >> /etc/inittab
grep -q '^ttyS0$' /etc/securetty || echo ttyS0 >> /etc/securetty
echo 'root:vm370plus' | chpasswd
# sshd: allow the root password login, as on the RAM system
sed -i 's/^PermitRootLogin .*/PermitRootLogin yes/' /etc/ssh/sshd_config
# no hardware clock, no keyboard, no udev settle wait at boot
echo 'HWCLOCKACCESS=no' >> /etc/default/rcS 2>/dev/null || true
# debootstrap's own clean-up, if its second stage did not get that far
[ -x /sbin/start-stop-daemon.REAL ] && mv /sbin/start-stop-daemon.REAL /sbin/start-stop-daemon
rm -f /usr/sbin/policy-rc.d
echo "VM/370plus post-install done"
