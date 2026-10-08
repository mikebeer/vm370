#!/bin/sh
# VM/370+: finish a Debian wheezy s390 system after debootstrap's second
# stage (run inside the chroot).  Console: the 3215 is ttyS0, line mode.
set -e
echo vm370plus > /etc/hostname
cat > /etc/hosts <<H
127.0.0.1 localhost
10.1.1.2  vm370plus
H
cat > /etc/fstab <<F
# VM/370+: the root is mounted by the initramfs before switch_root
/dev/dasda1  /      ext2   defaults,errors=remount-ro  0  0
proc         /proc  proc   defaults                    0  0
F
cat > /etc/network/interfaces <<N
auto lo
iface lo inet loopback

# the CTC pair to the PC (Hercules CTCI); the initramfs groups and
# activates the adapters before switch_root
auto ctc0
iface ctc0 inet static
    address 10.1.1.2
    netmask 255.255.255.255
    pointopoint 10.1.1.1
    gateway 10.1.1.1
    mtu 1500
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
echo "VM/370+ post-install done"
