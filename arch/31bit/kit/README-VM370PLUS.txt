VM/370+  --  overlay kit, 6 October 2026
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
  2. Unzip BOTH kit parts OVER it (part 1: config, shadows, tools;
     part 2: disks/vm50-4.cckd), so the files below replace or add:
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

RULES THAT MATTER
  - Always end with  /shutdown  at the Hercules console, then  exit.
    Killing Hercules leaves the shadows inconsistent.
  - Never run two Hercules instances on these disks.
  - Do not IPL something else after IPL CMS (the shared saved system) in
    the same session: leaving a shared system is not finished yet
    (I-235).  Log off and on, or use IPL 190 / IPL 290 (unshared).
  - CP itself runs with 16 MB of real storage (MAINSIZE 16).  Virtual
    machines may be up to 256 MB.  Raising CP's real storage is
    milestone M4b.
  - CP Q V STOR shows only 5 digits (131072K appears as 31072K) -- a
    cosmetic CP bug (I-246).  DEF STOR shows the right value.

TO GO BACK TO PLAIN CE
  Delete disks/shadows/*_1.shadow, restore vm370ce.conf and
  disks/vm50-4.cckd from the CE zip.

Everything that produced this kit -- the update decks, the generator,
the build tools and the issue log -- is in the project repository.
