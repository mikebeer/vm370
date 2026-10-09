VM/370+  --  overlay kit, 9 October 2026 (build 5)
=========================================

VM/370 Community Edition V1 R1.2, with CP converted to ESA/390 (AMODE 31)
and an EC-mode CMS on MAINT 290 that can use storage above 16 MB.
Development checkpoint of the VM/370+ project, not a release.

WHAT YOU NEED
  - A fresh, unmodified extraction of VM370CE_V1_R1_2.zip.
    Do NOT apply this kit to a SixPack you care about.
  - Hercules 4.x (SDL Hyperion, tested 4.9.1) or Hercules 3.13.
    Older Hercules 3.0x is untested in ESA/390 mode.
  - A tn3270 emulator (the WC3270 in the CE package is fine).

INSTALL
  1. Unzip VM370CE_V1_R1_2.zip into a new directory.
  2. Unzip kit parts 1-3 OVER it (part 1: config, shadows, tools;
     part 2: disks/vm50-4.cckd; part 3: the CMSUSER volume's shadow;
     part 4: Linux, vm370plus/linux/ and the VM50-2 shadow (MAINT's
     19D with LINUX EXEC); parts 5-7: the Debian disk, see
     LINUX/390 below),
     so the files below replace or add:
        vm370ce.conf                 ARCHMODE ESA/390, CPUMODEL 3090,
                                     ECPSVM NO (CE's own S/370 settings
                                     will not boot this CP)
        disks/vm50-4.cckd            CE's VM50-4 with the paging-area
                                     allocation record fixed (I-239)
        disks/shadows/*_1.shadow     everything else: the ESA/390 CP
                                     nucleus, the EC-mode CMS on 290,
                                     HIGHSTOR, the patched GCCLIB/BREXX,
                                     the directory (ECMODE, 256M), ...
  3. Start it exactly as CE: vm370ce.cmd (Windows) or vm370ce.sh.
  4. CE's hercules.rc IPLs 6A1 by itself when Hercules starts.
     If CP asks
        Start ((Warm|Force|COLD|CKPT) (DRain) (DIsable) (NOAUTOlo)) or (SHUTDOWN)
     answer  /cold  (the first time there is no warm-start data).
     Once the console shows  DMKCPI966I Initialization complete
     the system is up -- do NOT type ipl 6a1 again (that would reset
     the running system).  Only if nothing has been IPLed (no DMKCPI
     messages at all) type  ipl 6a1  yourself.
  5. Connect the 3270 emulator to localhost:3270.

USE
  logon cmsuser cmsuser noipl
  cp def stor 128m               HIGHSTOR region = 16 MB .. machine size
  cp link maint 290 290 rr
  ipl 290                        the EC-mode CMS
  highstor query                 HIGHSTOR 16384K- 131072K TOTAL ...
  cp d psw                       030E....  = EC mode

  IPL CMS / IPL 190 still give the classic BC-mode CMS.

  cREXX (the 2022 S370 tree, F0041), built natively on this system:
    ipl 290, then  global txtlib gcclib  and on CMSUSER's E disk:
        rxc -v   rxas -v   rxdas -v   rxbvm -v
        rxbvm -l d ascommon        10 tests, Success
        rxbvm -l d asebcdic        12 tests, Success
    The sources are on CMSUSER's D disk; CRXMAKE EXEC rebuilds them
    (RXVMINTP needs GCC380 in AMODE 31 -- GCC370 runs out of storage).
    Known: RXC -L on a REXX program ends in DLMALLOC PANIC, as on
    stock CE.  vm370plus/ has CRXMAKE.EXEC and the cms.h it needs.

  cREXX cross-compiled on the PC for AMODE 31 (GCC 13 -m31, newlib, the
  CMS runtime in vm370plus/m5f/), on CMSUSER's A disk -- these need
  HERCULES 4.x (they use z900-level instructions 3.13 lacks):
        ipl 290
        rxc31 basic                BASIC REXX -> BASIC RXAS
        rxas31 basic               -> BASIC RXBIN
        rxbvm31 basic              runs it; heap above 16 MB
        libctest a b               C library check (printf, malloc,
                                   files, floating point)

  Compiling C with the compiler running above 16 MB:
    GCC EXEC chooses GCC370 here (no S/380); GCC380 is the AMODE 31
    build.  vm370plus/GCC31.EXEC in this kit forces GCC380 (and
    vm370plus/HELLO31.C is the test program).  Get them onto your
    A disk (e.g. via the card reader: devinit 00c with an
    'ID CMSUSER' card, then READCARD), then
        gcc31 hello31
        global txtlib pdpclib
        load hello31 (start
    (needs  cp def stor 128m  -- GCC380 asks for a 60 MB heap).

LINUX/390 ON VM/370+  (milestone M7, 9 October 2026)
  A Linux 4.0 kernel (31-bit, ESA/390) runs in a virtual machine.  Kit b4
  adds a complete DEBIAN 7 (wheezy, s390) system on a 3390 disk:
  sysvinit, udev, rsyslog, cron, OpenSSH, apt/dpkg, 154 packages, root on
  ext2, 128 MB swap file.  The kernel is IPLed from the card reader; its
  initramfs (BusyBox) brings the disk and the network up and then hands
  over to Debian (switch_root).  Without the disk you get the BusyBox
  system in memory as before (prompt  vm370plus:~# ).

  Files (vm370plus/linux/):
      linux48.rdr     ID MAINT card + the kernel with its initramfs
      lxparm.rdr      ID MAINT card + the parameter line
                      no_removal_warning conmode=3215 condev=0x0009
      lxparmram.rdr   the same + vmroot=ram: stay in the BusyBox system
                      even if Debian is on the disk (repairs)
  and disks/lnx190.cckd -- the Debian disk, volume LNX190, a 3390-1
  (parts 5-7 of the kit, see INSTALL THE DEBIAN DISK).

  INSTALL THE DEBIAN DISK
    The disk is 82 MB, shipped split in three pieces.  Unzip parts 5, 6
    and 7 into the CE directory, then in that directory (cmd.exe):
        copy /b disks\lnx190.cckd.001+disks\lnx190.cckd.002+disks\lnx190.cckd.003 disks\lnx190.cckd
        del disks\lnx190.cckd.00?
    (Linux/WSL:  cat disks/lnx190.cckd.00? > disks/lnx190.cckd )
    vm370ce.conf in this kit already has the line
        0190    3390    disks/lnx190.cckd
    KEEP A COPY of lnx190.cckd: it is your Linux system disk, and
    Hercules writes to it.

  THE FULL MANUAL is vm370plus/linux/VM370PLUS-Guide.docx (Word): what
  VM/370+ is, the differences to CE, installation, Linux, cREXX.

  START LINUX FROM CMS (build 5): the kernel, the LINUX EXEC and the
  parameter files are on MAINT's 19D (your U disk).  With 64 MB and the
  devices attached (step 3 below):
        cp def stor 64m
        ipl cms
        linux
  The EXEC punches the kernel into your own reader and IPLs it as an
  ESA/390 machine.  Your IP address comes from  userid LXPARM  on 19D
  (MAINT 10.1.1.2, CMSUSER 10.1.2.2), else DEFAULT LXPARM.
  Two Debian systems at once are too slow until CP uses real storage
  above 16 MB (M4b.3); Debian next to CMS users works.

  BOOT DEBIAN (by hand)
  1. vm370ce.conf has MAINSIZE 256 (CP uses 16 MB as real storage and the
     rest as paging store).  Keep it.  For the network remove the # in
     front of  #0600.2  CTCI ...  (see NETWORK below).
  2. With VM/370+ up (step 4 of INSTALL), at the HERCULES console spool
     the two decks to MAINT's reader, in this order:
        /cp spool 00c class *
        devinit 00c vm370plus/linux/linux48.rdr ebcdic eof
        /cp start 00c
     wait until CP reports the file (RDR FILE ... TO MAINT), then
        devinit 00c vm370plus/linux/lxparm.rdr ebcdic eof
        /cp start 00c
  3. On the 3270:   logon maint cpcms noipl
        cp q rdr all                  two files: the kernel, the parms
        cp def stor 64m               Debian needs the 64 MB
        cp attach 600 to maint as 620 the network (if configured)
        cp attach 601 to maint as 630
        cp attach 190 to maint as 250 the Debian disk
        cp set esa on                 this virtual machine is ESA/390
        cp ipl 00c                    IPL from the reader
     About 4-5 minutes with Hercules: the kernel log, then
        root: the system on /dev/dasda1 -- switch_root
        INIT: version 2.88 booting
        ... Starting OpenBSD Secure Shell server: sshd.
        Debian GNU/Linux 7 vm370plus ttyS0
        vm370plus login:
     Log in as  root , password  vm370plus .
  4. The terminal is a line device: no full-screen programs (use
     nano/vi only if you must; less works as a pager).  CP's MORE...:
     press CLEAR (or PA2).
  5. To leave:  poweroff  (Debian stops its services, then CP shows
     DISABLED WAIT), then  cp logoff  (which releases the adapters and
     the disk).  To run it again, spool the two decks again -- IPL from
     the reader consumes them.

  NETWORK: SSH (PuTTY) INTO LINUX
  Linux talks to the PC over a channel-to-channel adapter that Hercules
  connects to a tun interface on the PC (CTCI).  Linux is 10.1.1.2, the
  PC end is 10.1.1.1.
  a. vm370ce.conf: remove the # in front of
        #0600.2  CTCI    10.1.1.2 10.1.1.1
     Linux PC / WSL2: Hercules needs the tun driver (/dev/net/tun) and
     must run as root (or with hercifc installed setuid).  Windows:
     Hercules needs SDL's CTCI-WIN package (TunTap64.dll, with Npcap)
     next to hercules.exe -- without it the 0600 line fails and the
     rest still works.
  b. Attach the adapters BEFORE  cp ipl 00c  (step 3), each on its own
     virtual control unit (620 and 630, not 620 and 621).
  c. On the PC:  ssh root@10.1.1.2  (PuTTY: host 10.1.1.2, port 22),
     password  vm370plus .  Debian runs OpenSSH (the BusyBox system runs
     Dropbear); the first login may take a minute after boot.
  d. Internet access from Debian needs routing/NAT on the PC;
     /etc/apt/sources.list points at archive.debian.org (wheezy).
  Other IP addresses: add  vmip=a.b.c.d vmpeer=w.x.y.z  to the line in
  lxparm.rdr, change the 0600 line to match, and in Debian edit
  /etc/network/interfaces.

  Notes:
   - SET ESA ON / OFF switches a virtual machine between S/370 and
     ESA/390; CMS needs it OFF (the default).
   - Linux believes it runs "natively" (no SCLP, no z/VM interfaces),
     so it needs conmode=3215 condev=0x0009.
   - Linux 4.0 is the last kernel with 31-bit support; this one carries
     three fixes (vm370plus/linux/*.patch): 2 KB IDALs for buffers above
     16 MB, the PSW alignment of psw_idle, and an endless loop in the
     31-bit I/O-interrupt return path (entry.S).
   - Works with Hercules 3.13 and 4.x.

RULES THAT MATTER
  - Always end with  /shutdown  at the Hercules console, then  exit.
    Killing Hercules leaves the shadows inconsistent.
  - Never run two Hercules instances on these disks.
  - Do not IPL something else after IPL CMS (the shared saved system) in
    the same session: leaving a shared system is not finished yet
    (I-235).  Log off and on, or use IPL 190 / IPL 290 (unshared).
  - CP's own machine is 16 MB; with MAINSIZE above 16 (this kit: 256)
    the rest is CP's paging store (milestone M4b).  Virtual machines
    may be up to 256 MB.
  - CPWATCH is no longer autologged (AUTOLOG1's PROFILE EXEC: the two
    CPWATCH lines start with '*').  It is an S/370 CP monitor that loops
    under this CP at priority 5 and starves everyone else (I-251).
  - CP emulates the S/370 interval timer from the TOD clock (ESA/390 has
    none), so time slices end and virtual interval timers run (I-250).
  - CP Q V STOR shows only 5 digits (131072K appears as 31072K) -- a
    cosmetic CP bug (I-246).  DEF STOR shows the right value.

TO GO BACK TO PLAIN CE
  Delete disks/shadows/*_1.shadow, restore vm370ce.conf and
  disks/vm50-4.cckd from the CE zip.

Everything that produced this kit -- the update decks, the generator,
the build tools and the issue log -- is in the project repository.
