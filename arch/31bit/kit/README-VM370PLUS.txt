VM/370+  --  overlay kit, 8 October 2026
=========================================

VM/370 Community Edition V1 R1.2, with CP converted to ESA/390 (AMODE 31)
and an EC-mode CMS on MAINT 290 that can use storage above 16 MB.
Development checkpoint of the CREXX/370 project, not a release.

WHAT YOU NEED
  - A fresh, unmodified extraction of VM370CE_V1_R1_2.zip.
    Do NOT apply this kit to a SixPack you care about.
  - Hercules 4.x (SDL Hyperion, tested 4.9.1) or Hercules 3.13.
    Older Hercules 3.0x is untested in ESA/390 mode.
  - A tn3270 emulator (the WC3270 in the CE package is fine).

INSTALL
  1. Unzip VM370CE_V1_R1_2.zip into a new directory.
  2. Unzip ALL THREE kit parts OVER it (part 1: config, shadows, tools;
     part 2: disks/vm50-4.cckd; part 3: the CMSUSER volume's shadow),
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
  4. At the Hercules console type:   ipl 6a1
     CP says
        Start ((Warm|Force|COLD|CKPT) (DRain) (DIsable) (NOAUTOlo)) or (SHUTDOWN)
     Answer:  /cold
     (There is no warm-start data in the kit, so COLD is correct.)
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

LINUX/390 ON VM/370+  (milestone M7, 8 October 2026)
  A Linux 4.0 kernel (31-bit, ESA/390) runs in a virtual machine:
  console on your terminal (3215 mode), its own initramfs, /init prints
      HELLO FROM LINUX/390 ON VM/370+ (M7)
  /init is m7sh, a tiny shell (no C library, no disk yet): after the
  HELLO line it prompts  / #  and knows
      help  ls [dir]  cat file  mem  ps  uname  uptime  mount  cpu
      dmesg  echo  mkdir  cd  pwd  write file text  halt
  (/proc, /sys and a tmpfs on /tmp are mounted; files you write live
  in memory only).  vm370plus/linux/ has the two reader decks:
      linux45.rdr   ID MAINT card + the kernel (initramfs with m7sh)
      lxparm.rdr    ID MAINT card + the parameter line
                    no_removal_warning conmode=3215 condev=0x0009

  1. vm370ce.conf in this kit has MAINSIZE 64 (CP uses 16 MB as real
     storage and the rest as paging store).  Keep it.
  2. IPL as above (ipl 6a1, /cold).  Then at the HERCULES console,
     spool the two decks to MAINT's reader, in this order:
        /cp spool 00c class *
        devinit 00c vm370plus/linux/linux45.rdr ebcdic eof
        /cp start 00c
     wait until CP reports the file (a few seconds; RDR FILE ... TO MAINT)
        devinit 00c vm370plus/linux/lxparm.rdr ebcdic eof
        /cp start 00c
  3. On the 3270:   logon maint cpcms noipl
        cp q rdr all             two files: the kernel, then the parms
        cp def stor 16m
        cp set esa on            this virtual machine is ESA/390
        cp ipl 00c               IPL from the reader
     Linux reads the kernel and the parameter file, then prints its
     boot log on your terminal ("Linux version 4.0.0+ ...", "console
     [ttyS0] enabled", ... "Freeing unused kernel memory") and the
     HELLO line and the  / #  prompt.  About 1-2 minutes with Hercules.
     Type commands as on any terminal, e.g.  ps  or  mem .
  4. The terminal fills: CP shows MORE... -- press CLEAR (or PA2).
  5. To leave Linux:  halt  (Linux stops; CP shows a disabled wait),
     or PA1 (CP mode); then  cp logoff  (or  ipl cms).
     To run it again, spool the two decks again (step 2) -- IPL from
     the reader consumes them.
  Notes:
   - SET ESA ON / OFF switches a virtual machine between S/370 and
     ESA/390; CMS needs it OFF (the default).
   - Linux believes it runs "natively" (no SCLP, no z/VM interfaces),
     so it needs conmode=3215 condev=0x0009.  The deviations of the
     ESA/390 virtual machine are listed in docs/40-M7.3-GUEST-DAT.md.
   - Works with Hercules 3.13 and 4.x.

RULES THAT MATTER
  - Always end with  /shutdown  at the Hercules console, then  exit.
    Killing Hercules leaves the shadows inconsistent.
  - Never run two Hercules instances on these disks.
  - Do not IPL something else after IPL CMS (the shared saved system) in
    the same session: leaving a shared system is not finished yet
    (I-235).  Log off and on, or use IPL 190 / IPL 290 (unshared).
  - CP's own machine is 16 MB; with MAINSIZE above 16 (this kit: 64)
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
