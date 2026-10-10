# Linux 4.0 31-bit for M7 (ESA/390 guest under VM/370plus)

Built in the workspace from the v4.0 tag with `s390x-linux-gnu-gcc` 13:

    make ARCH=s390 CROSS_COMPILE=s390x-linux-gnu- O=kbuild \
         KCFLAGS="-fcommon -fno-pie -fno-stack-protector -fno-PIE -Wno-error" image

- `config-4.0-31bit`: allnoconfig + PRINTK, TN3215(_CONSOLE), BLK_DEV_INITRD,
  INITRAMFS_SOURCE (a tiny `/init`), BINFMT_ELF, EARLY_PRINTK, MARCH_Z900
  (gcc 13 has no g5); `compiler-gcc13.h` added as a copy of `compiler-gcc5.h`.
- `psw_idle-align.patch`: Linux 4.0's 31-bit `psw_idle` builds its wait PSW at
  `__SF_EMPTY(%r15)` = 4(%r15), which is not doubleword aligned; `LPSW`
  takes a specification exception (lx28). The PSW goes to `__SF_EMPTY+4`.
- The reader deck is `arch/s390/boot/image` cut into 80-byte cards (the image
  is already laid out for a VM reader IPL), an `ID MAINT` card in front.
