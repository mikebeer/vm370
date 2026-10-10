// content.js -- the text of the VM/370plus guide.  Helpers from mkmanual.js.
module.exports = function (M) {
const { P, H1, H1plain, H2, H3, B, N, NOTE, ATTN, SCREEN, TABLE, setAppendix } = M;

// ------------------------------------------------------------------ preface
H1plain('Preface');
P('This manual introduces VM/370plus, tells you how to install it over a VM/370 Community Edition system running under the Hercules emulator, and describes how to use the two things it adds to VM/370: virtual machines larger than 16 MB with programs that run in 31-bit addressing mode, and virtual machines that run the ESA/390 architecture, in which Linux/390 and a complete Debian system run.');
P('It is written for the VM/370 user who already knows CP and CMS: how to log on, how to use the CP commands of the general user (class G) and of the system operator (class A and B), how to edit and run an EXEC. Where VM/370plus behaves as VM/370 does, this manual says nothing; where it differs, it says how and why.');
H3('How this manual is organized');
B(['**Chapter 1, Introduction**, says what VM/370plus is and what it is for.',
   '**Chapter 2, Differences from VM/370 Community Edition**, lists every externally visible change.',
   '**Chapter 3, Installing VM/370plus**, takes you from a fresh Community Edition to a running VM/370plus system.',
   '**Chapter 4, Operating VM/370plus**, covers start-up, shutdown and the rules that keep the system healthy.',
   '**Chapter 5, Running Linux/390**, describes ESA/390 virtual machines, the Linux kernel, the Debian system and the network connection to the PC.',
   '**Chapter 6, Service Machines**, describes CHATBOT, the chatbot service machine, and the service machines that are planned.',
   '**Chapter 7, cREXX on VM/370plus**, describes the REXX compiler and virtual machine built for and on VM/370plus, the languages written in cREXX that run on CMS and on Linux, and Turbo CREXX.',
   '**Chapter 8, Restrictions and Known Problems**, lists what does not work yet.',
   '**Appendix A** summarizes the new and changed commands, **Appendix B** lists the files in the installation kit, **Appendix C** gives the ESA/390 deviations of the virtual machine.']);
H3('Conventions');
P('Commands are shown in `monospaced type`. In command descriptions, uppercase letters are typed as shown and lowercase words stand for values you supply. Examples of terminal sessions are shown in framed figures; lines you type are not marked separately because the context makes clear which they are.');
H3('Summary of changes');
P('This edition is kept up to date as VM/370plus grows; each change is listed here, newest first.');
B(['**10 October 2026, evening (kit build 6).** `IPL LINUX` and vmzipl: Debian starts from its own disk; the Debian disk is a 3390-9 (7 GB); no 64-CCW limit for Linux disk I/O; mosquitto (MQTT) and Asterisk under Debian; `QUERY SET` shows ESA; the CHATBOT service machine and `CHAT` (new Chapter 6); RXBVM8 has TIME and DATE; the console banner reads VM/370plus; a fix for memory corruption in Linux guests above 16 MB (location 80).',
   '**10 October 2026.** Regina REXX and THE under Debian; languages written in cREXX for CMS and Linux (BASIC, SNOBOL4, Pascal, Lisp, Smalltalk, PL/M, Prolog, LOGO); Turbo CREXX on both; four more minidisks for CMSUSER (196–199); the native build of the current cREXX (M8.2); Python and GNU C under Debian; milestones brought up to date.',
   '**9 October 2026.** First edition, for kit build 5.']);
P('*PC* means the personal computer on which Hercules runs. *Real* storage and devices are those of the Hercules machine; *virtual* storage and devices are those CP gives a user.');

// ---------------------------------------------------------------- chapter 1
H1('Introduction');
P('VM/370 was written for System/370: 24-bit addresses, 16 MB of storage, S/370 channel I/O. VM/370plus is the VM/370 Community Edition V1 R1.2 with its Control Program (CP) converted to the ESA/390 architecture. It runs on Hercules in `ARCHMODE ESA/390` and gives its users:');
B(['**Virtual machines up to 256 MB.** CP builds ESA/390 segment and page tables, runs in 31-bit addressing mode itself, and gives a virtual machine as much storage as its directory entry allows.',
   '**31-bit programs under CMS.** An EC-mode CMS, IPLed from MAINT’s 290 disk, lets programs obtain storage above 16 MB (the HIGHSTOR facility) and run in 31-bit addressing mode, with a C compiler and library for such programs.',
   '**ESA/390 virtual machines.** `SET ESA ON` makes a virtual machine an ESA/390 machine: channel subsystem I/O (SSCH, TSCH, MSCH, STSCH), the ESA/390 PSW and control registers, home and primary address spaces, IEEE floating point. Linux/390 runs in it.',
   '**Linux and Debian.** A Linux 4.0 kernel (31-bit, the last Linux release that supports 31-bit machines) IPLs from the virtual card reader and runs Debian 7 from a 3390 disk, with SSH access from the PC over a channel-to-channel adapter.',
   '**cREXX.** The cREXX REXX compiler, assembler and virtual machine run on VM/370plus and are built on it.']);
P('Everything else is VM/370: the same CP commands, the same directory, the same CMS for 24-bit work, the same spooling, the same operator. Programs that ran under the Community Edition run unchanged.');
H2('How VM/370plus is built');
P('VM/370plus is a set of UPDATE decks applied to the Community Edition source, assembled on the system itself, and loaded into the CP nucleus with the standard VMFLOAD procedure. The repository of the project holds every deck, the generator that produces them, the build tools, the issue register and the regression runs. Nothing in VM/370plus is a binary patch.');
H2('Milestones');
P('The conversion was done in milestones, each closed by a run that exercises it. Figure 1 shows where they stand.');
TABLE(['Milestone', 'Content', 'Status'], [
  ['M0–M1', 'ESA/390 instructions for the assembler; CP IPLs in ESA/390 mode, console and channel subsystem', 'complete'],
  ['M2', 'ESA/390 DAT tables, CP in 31-bit mode, 31-bit guests', 'complete'],
  ['M3–M4', 'CMS under the new CP, shared CMS by page frame, several users, 4 KB storage keys', 'complete'],
  ['M4b', 'real storage up to 2 GB (above 16 MB as CP\u2019s paging store)', 'complete'],
  ['M4b.3', 'CP uses real frames above 16 MB directly', 'planned'],
  ['M5', 'EC-mode CMS with storage above 16 MB (HIGHSTOR), 31-bit C (cross and native)', 'complete'],
  ['M6', 'a CMS nucleus that is itself 31-bit', 'planned, before M9'],
  ['M7', 'ESA/390 virtual machines, Linux/390, Debian, SSH', 'complete'],
  ['M7.8', 'Linux for several users from a linkable disk (LINUX EXEC); Linux and CMS side by side', 'complete; two Debians at once need M4b.3'],
  ['M7.9', 'channel programs of any length for ESA/390 guests (no 64-CCW limit)', 'complete'],
  ['M7.10', 'IPL of Linux from its disk (vmzipl) and `IPL LINUX`', 'complete'],
  ['M7.11', 'a 3390-9 Debian disk (about 7 GB) as the standard Linux disk', 'complete'],
  ['\u2014', 'service machines: CHATBOT (the MCchat persona bot) with CHAT EXEC', 'complete'],
  ['M8', 'cREXX: the 2022 release built natively (M5); the current release cross-built (M8.1)', 'complete'],
  ['M8.2', 'the current cREXX built natively with GCC380', 'compiler, assembler and VM work; the library does not build yet'],
  ['\u2014', 'languages in cREXX for CMS and Linux; Turbo CREXX', 'complete on both'],
  ['\u2014', 'GNU C 4.6, Python 2.7 and 3.2, Regina REXX and THE under Debian', 'complete'],
  ['M9', 'z/Architecture (64-bit)', 'planned, after all of the above'],
], [1400, 6038, 2200], 'VM/370plus milestones');

// ---------------------------------------------------------------- chapter 2
H1('Differences from VM/370 Community Edition');
H2('The machine');
TABLE(['Item', 'Community Edition', 'VM/370plus'], [
  ['Hercules architecture', '`ARCHMODE S/370`', '`ARCHMODE ESA/390`'],
  ['CPU model', '4381, ECPS:VM available', '3090, ECPS:VM not used (its assists are S/370-only)'],
  ['Hercules main storage', '16 MB', '64 MB in the kit; up to 2048 MB'],
  ['CP’s addressing mode', '24-bit', '31-bit'],
  ['Real storage used by CP', 'up to 16 MB', '16 MB as frames; the rest as a fast paging store'],
  ['I/O', 'S/370 channels (SIO, TIO, HIO)', 'ESA/390 channel subsystem (SSCH, TSCH, HSCH)'],
  ['Storage keys', '2 KB keys', '4 KB keys (ISKE, SSKE, RRBE)'],
  ['Segment size', '64 KB', '1 MB (ESA/390 has no other)'],
], [2400, 3200, 4038], 'The real machine');
H2('Virtual machines');
B(['**Storage.** A virtual machine may have up to 256 MB. The directory’s maximum (the second size on the USER statement) is checked as before; the kit’s directory allows 256 MB for CMSUSER and 64 MB for MAINT.',
   '**Shared CMS.** The CMS saved system is shared by page frame rather than by segment: with 1 MB segments, sharing whole segments would expose private CMS storage to other users. The effect for the user is none.',
   '**31-bit virtual machines.** A virtual machine in EC mode may run with PSW bit 32 on (31-bit addressing); CP translates its addresses in 31 bits.',
   '**ESA/390 virtual machines.** New command `SET ESA ON|OFF`; see Chapter 5 and Appendix A.',
   '**More disk space for CMSUSER.** Besides 191–195 on VM50U0, CMSUSER has four more minidisks, 196–199, of 115 cylinders (about 52 MB) each on VM50-8, in the cylinders the Community Edition leaves free there. They come formatted, labeled CMS196 to CMS199: `ACCESS 196 H` (197 I, 198 J, 199 K). A CMS minidisk on a 3350 holds at most 65,535 blocks of 800 bytes, about 52 MB; larger minidisks come with milestone M6.']);
H2('CP commands');
TABLE(['Command', 'Change'], [
  ['`SET ESA ON|OFF`', 'New (class G). ON makes the next IPL of a device an IPL of an ESA/390 machine; OFF returns to System/370 at once.'],
  ['`IPL cuu`', 'A user who is running a shared named system (CMS) is IPLed with CLEAR, so that no copy of the shared pages stays in the virtual machine.'],
  ['`QUERY SET`', 'A fifth line shows `ESA ON`, `ESA PENDING` (SET ESA ON before the next IPL of a device) or `ESA OFF`.'],
  ['`IPL LINUX`', 'New. IPLs the Debian disk at virtual address 250 as an ESA/390 machine: `SET ESA ON` and `IPL 250` in one command. Works from a directory IPL statement too.'],
  ['`IPL name`', 'Any other name always IPLs a System/370 machine; a pending `SET ESA ON` waits for the next IPL of a device.'],
  ['`DEFINE STORAGE`', 'Up to 256 MB. Leaves the named system the user was running.'],
  ['`DISPLAY`, `STORE`', 'Address storage above 16 MB.'],
  ['`QUERY VIRTUAL STORAGE`', 'Shows five digits only (131072K appears as 31072K); `DEFINE STORAGE` echoes the right value.'],
], [3000, 6638], 'Changed CP commands');
H2('CMS');
B(['The ordinary CMS (`IPL CMS`, `IPL 190`) is unchanged: a System/370 BC-mode CMS with 16 MB of addressable storage.',
   'An EC-mode CMS is on MAINT’s 290 disk (`IPL 290`). With it, the HIGHSTOR nucleus extension (loaded by the system profile) manages storage from 16 MB to the end of the virtual machine; SVC 120 (GETMAIN/FREEMAIN RU) gives programs storage above the line.',
   'GCC380, the AMODE 31 build of the Community Edition’s GCC, runs above 16 MB; GCCLIB31 is a C library for programs that run in 31-bit mode with their heap above 16 MB.',
   'CPWATCH is not autologged: it is an S/370 monitor that loops under this CP. The two lines in AUTOLOG1’s PROFILE EXEC are commented out.']);

// ---------------------------------------------------------------- chapter 3
H1('Installing VM/370plus');
H2('What you need');
B(['A fresh, unmodified extraction of `VM370CE_V1_R1_2.zip`. Do not install VM/370plus over a system you care about.',
   'Hercules 4.x (SDL Hyperion; tested with 4.7 and 4.9.1) or Hercules 3.13. Programs cross-compiled for 31-bit mode need Hercules 4.x, which has the z900-level instructions in ESA/390 mode.',
   'A 3270 terminal emulator; the wc3270 in the Community Edition package is sufficient.',
   'For Linux networking on Windows: the CTCI-WIN package for SDL Hercules (TunTap64.dll, with Npcap). On Linux or WSL2: the tun driver, and Hercules running as root or with hercifc installed setuid.',
   'The VM/370plus kit: seven zip files, each under 30 MB.']);
TABLE(['Part', 'Contents'], [
  ['1', '`vm370ce.conf` (ESA/390), the shadow files of the system volumes (CP nucleus, CMS, directory), README, tools'],
  ['2', '`disks/vm50-4.cckd`: VM50-4 with its paging area record corrected'],
  ['3', 'the shadow file of the CMSUSER volume'],
  ['4', '`vm370plus/linux/`: the Linux kernel and parameter decks, the CMS files for MAINT 19D, kernel configuration and patches'],
  ['5–7', 'the Debian disk, `disks/lnx190.cckd`, in three pieces'],
], [1000, 8638], 'The installation kit');
H2('Installation steps');
N(['Unzip `VM370CE_V1_R1_2.zip` into a new directory.',
   'Unzip kit parts 1 to 7 over it, replacing files when asked.',
   'Join the Debian disk. In the Community Edition directory, at a Windows command prompt:',
]);
SCREEN(['copy /b disks\\lnx190.cckd.001+disks\\lnx190.cckd.002+disks\\lnx190.cckd.003 disks\\lnx190.cckd',
        'del disks\\lnx190.cckd.00?'], 'Joining the Debian disk (Windows)');
P('On Linux or WSL2 use `cat disks/lnx190.cckd.00? > disks/lnx190.cckd`. The file `disks/lnx190.sha256` holds the checksum of the joined file. Keep a copy of `lnx190.cckd`: it is your Linux system disk and Hercules writes to it.');
N(['If you want the Linux network, remove the `#` in front of the line `#0600.2 CTCI 10.1.1.2 10.1.1.1` in `vm370ce.conf`.',
   'Start the system as you start the Community Edition: `vm370ce.cmd` on Windows, `vm370ce.sh` elsewhere.'], true);
H2('The first IPL');
P('The Community Edition’s `hercules.rc` IPLs from 6A1 by itself when Hercules starts. The first time, CP has no warm-start data and asks for the start type; answer `/cold`. When the console shows `DMKCPI966I Initialization complete`, the system is up.');
SCREEN(['HHCCP041I SYSCONS interface active',
        'VM/370plus Online',
        'Start ((Warm|Force|COLD|CKPT) (DRain) (DIsable) (NOAUTOlo)) or (SHUTDOWN)',
        '/cold',
        'NOW 09:51:57 GMT FRIDAY 10/09/26',
        'DMKCPI966I Initialization complete'], 'The first IPL of VM/370plus');
ATTN('Do not type `ipl 6a1` again once CP has initialized: it resets the running system. Type it yourself only if nothing has been IPLed (no DMKCPI messages at all).');
P('Then connect the 3270 emulator to `localhost:3270` and log on as usual.');
H2('Going back to the Community Edition');
P('Delete `disks/shadows/*_1.shadow` and restore `vm370ce.conf` and `disks/vm50-4.cckd` from the Community Edition zip.');

// ---------------------------------------------------------------- chapter 4
H1('Operating VM/370plus');
H2('Start-up and shutdown');
P('Operation is that of VM/370. The operator’s console is 0009; `ENABLE ALL` brings up the 3270 terminals. To stop the system, the operator types `shutdown` on 0009 and then `exit` at the Hercules console.');
ATTN('Always end with `shutdown` at the operator’s console before you leave Hercules. Killing Hercules leaves the shadow files inconsistent. Never run two Hercules instances on the same disks.');
H2('Storage');
P('CP’s own machine is 16 MB. With `MAINSIZE` above 16 in `vm370ce.conf` (the kit has 64), CP uses the storage above 16 MB as a paging store that no channel addresses: a page-out copies a frame there, a page-in copies it back. Up to 2048 MB has been tested. Virtual machines may be up to 256 MB.');
NOTE('Because CP keeps its working frames in the low 16 MB, a 64 MB Linux machine pages heavily, and while one runs, other users’ work is slower. Using frames above 16 MB directly (milestone M4b.3) is planned.');
H2('Rules that matter');
B(['A user who has IPLed the shared CMS may IPL another system; the shared pages are dropped first (the IPL is done with CLEAR). The shared-system models stay in storage until CP is IPLed again.',
   'CP emulates the System/370 interval timer from the TOD clock, since ESA/390 has none; time slices end and virtual interval timers run.',
   'CPWATCH is not autologged (see Chapter 2).']);

// ---------------------------------------------------------------- chapter 5
H1('Running Linux/390');
P('This chapter describes ESA/390 virtual machines and Linux/390 in them. Linux runs in two forms: a small system in storage (BusyBox), which needs no disk, and Debian 7 on a 3390 disk of its own.');
H2('ESA/390 virtual machines');
P('`SET ESA ON` makes a virtual machine an ESA/390 machine at its next IPL of a device. Such a machine has:');
B(['the ESA/390 PSW and control registers, primary, secondary and home address spaces, and ESA/390 DAT, which CP shadows;',
   'the channel subsystem: its devices are subchannels, I/O is started with SSCH and completed with TSCH; channel programs may use format-0 or format-1 CCWs and 31-bit IDAWs;',
   'IEEE binary floating point, the CPU timer, the clock comparator and SIGP for its one processor.']);
P('`IPL CMS` (or any IPL by name) gives a System/370 machine again; the pending `SET ESA ON` then applies to the next IPL of a device. `SET ESA OFF` returns to System/370 at once. Appendix C lists where the virtual machine deviates from the ESA/390 architecture.');
H2('What a Linux user needs');
TABLE(['Resource', 'Virtual address', 'How it is provided'], [
  ['Storage', '64 MB', '`DEFINE STORAGE 64M`, or 64M in the directory'],
  ['Console', '009 (3215)', 'the terminal; Linux uses it in line mode'],
  ['Card reader', '00C', 'the kernel and the parameters are IPLed from it'],
  ['Debian disk', '250 (3390)', 'a real 3390, attached or dedicated to the user'],
  ['Network', '620 and 630 (CTCA)', 'a CTC pair, attached or dedicated to the user'],
], [2000, 2400, 5238], 'Resources of a Linux virtual machine');
P('The operator attaches the devices:');
SCREEN(['attach 600 to maint as 620', 'attach 601 to maint as 630', 'attach 190 to maint as 250'], 'Attaching a Linux user’s devices (operator)');
P('Each device must be on its own virtual control unit (620 and 630, not 620 and 621). For a permanent arrangement put `DEDICATE` statements in the user’s directory entry.');
H2('Starting Linux from its disk: IPL LINUX');
P('The Debian disk carries its own kernel and IPL records, so Linux IPLs straight from it. With 64 MB of storage and the devices attached (the disk at 250), one CP command is enough, from CMS or from CP:');
SCREEN(['logon cmsuser',
        'cp define storage 64m',
        'cp ipl linux',
        'Linux version 4.0.0+ ...',
        '...',
        'Debian GNU/Linux 7 vm370plus ttyS0',
        'vm370plus login:'], 'Starting Linux from its disk');
P('`IPL LINUX` is `SET ESA ON` followed by `IPL 250`. Options of the device IPL may follow (`IPL LINUX CLEAR`). The kernel parameters, including the IP address, were written to the disk with the kernel by `vmzipl` (below); the reader route that follows remains for a different kernel or other parameters.');
H2('Making a disk IPLable: vmzipl');
P('`vmzipl` is the VM/370plus counterpart of `zipl`, for the 31-bit Linux 4.0 kernel. It is installed on the Debian disk as `/usr/local/sbin/vmzipl`. Run it as root after changing the kernel or its parameters:');
SCREEN(['vmzipl',
        'vmzipl: /dev/dasda: kernel 1775 blocks in 151 runs, channel program 2560 CCWs in 5 blocks',
        'vmzipl: parameters: no_removal_warning conmode=3215 condev=0x0009 vmip=10.1.1.2 vmpeer=10.1.1.1',
        'vmzipl: IPL with  CP SET ESA ON  and  CP IPL <address of this disk>'], 'Running vmzipl');
TABLE(['Option', 'Meaning'], [
  ['`-k file`', 'the kernel image (default `/boot/linux48.image`)'],
  ['`-p "parameters"`', 'the kernel parameter line (default: the running system\u2019s `/proc/cmdline`)'],
  ['`-d device`', 'the disk to make IPLable (default `/dev/dasda`)'],
  ['`-r directory`', 'where that disk\u2019s file system is mounted, when it is not the root'],
], [2400, 7238], 'vmzipl options');
P('It writes `/boot/vmipl.bin` (the kernel with the parameters) and `/boot/vmipl.ccw` (the channel program that reads it), then records 1 and 2 of track 0 (IPL1 and IPL2) of the disk.');
H2('Starting Linux with the LINUX EXEC');
P('The `LINUX EXEC` is on MAINT’s 19D disk, which every CMS user accesses as the U disk. `LINUX` alone issues `CP IPL LINUX`. `LINUX READER` takes the older route: the kernel and the IPL parameter files on 19D go through your reader. From CMS, with 64 MB of storage and the devices attached:');
SCREEN(['logon cmsuser',
        'cp define storage 64m',
        'ipl cms',
        'Ready;',
        'linux reader',
        'LINUX: punching the kernel and CMSUSER LXPARM to your reader ...',
        'PUN FILE 0002  TO  CMSUSER  COPY 01 NOHOLD',
        'PUN FILE 0003  TO  CMSUSER  COPY 01 NOHOLD',
        'LINUX: IPL 00C as an ESA/390 machine',
        'Linux version 4.0.0+ ...',
        '...',
        'root: the system on /dev/dasda1 -- switch_root',
        'INIT: version 2.88 booting',
        '...',
        'Debian GNU/Linux 7 vm370plus ttyS0',
        'vm370plus login:'], 'Starting Linux from CMS');
P('The EXEC holds the files already in your reader, punches the two pieces of the kernel into your own reader as one spool file and then your parameter file, sets `ESA ON` and IPLs the reader. The parameter file is `userid LXPARM` on the U disk, or `DEFAULT LXPARM` if there is none; it carries your IP address. Afterwards `CP CHANGE RDR ALL NOHOLD` releases your other reader files.');
TABLE(['File on MAINT 19D', 'Contents'], [
  ['`LINUX48 KERNEL1`, `KERNEL2`', 'the kernel with its initramfs, 91,696 card images in two files (a CMS file holds at most 65,533 records)'],
  ['`LINUX EXEC`', 'the EXEC described above'],
  ['`DEFAULT LXPARM`', '`no_removal_warning conmode=3215 condev=0x0009`'],
  ['`userid LXPARM`', 'the same plus `vmip=` and `vmpeer=`, the user’s address and the PC’s end'],
], [3000, 6638], 'Linux files on MAINT 19D');
H2('Starting Linux by hand');
P('Without the EXEC, the operator spools the two decks from `vm370plus/linux/` to the user’s reader, and the user IPLs it:');
SCREEN(['/cp spool 00c class *',
        'devinit 00c vm370plus/linux/linux48.rdr ebcdic eof',
        '/cp start 00c',
        'devinit 00c vm370plus/linux/lxparm.rdr ebcdic eof',
        '/cp start 00c'], 'Spooling the Linux decks (Hercules console)');
SCREEN(['logon maint cpcms noipl', 'cp define storage 64m', 'cp set esa on', 'cp ipl 00c'], 'IPL of Linux from the reader');
P('The ID card of the two decks names MAINT; for another user change the first card or spool the decks with `/cp spool 00c ...` and `TRANSFER`. IPL from the reader consumes the files: spool them again for the next IPL.');
H2('The Linux system');
H3('Boot sequence');
P('The kernel’s initramfs (BusyBox) brings the 3390 online, creates a partition and a file system on a new disk, groups the CTC pair as `ctc0` and configures it from the IPL parameters (default 10.1.1.2, peer 10.1.1.1). If the disk holds a system (`/sbin/init`), it hands over to it with `switch_root`; otherwise it stays in storage with the prompt `vm370plus:~#`. The parameter `vmroot=ram` (deck `lxparmram.rdr`) keeps the in-storage system even when Debian is on the disk, which is how you repair the disk.');
H3('Debian');
P('The disk is a 3390 model 9 (10,017 cylinders, about 7 GB). It holds Debian 7.11 (wheezy) for s390: sysvinit, udev, rsyslog, cron, OpenSSH, apt and dpkg, root on ext2 (6.8 GB, about 6 GB free), a 128 MB swap file. The disk carries its own kernel and IPL records, so `IPL LINUX` starts it. Log in as `root` with password `vm370plus`, and change the password.');
P('Development tools are installed: GNU C and C++ 4.6.3 with make, Python 2.7.3 (`python`) and Python 3.2.3 (`python3`), Regina REXX 3.6 (`regina` or `rexx`, classic REXX as on CMS) and THE 3.3, The Hessling Editor (`the`, an XEDIT-like editor; use it over SSH, since the 3215 console cannot show a full screen). cREXX and the languages of Chapter 7 are in `/usr/local/bin`.');
P('Servers are installed too. **mosquitto 1.6.15**, an MQTT broker (`/usr/local/sbin/mosquitto`, configuration `/etc/mosquitto/mosquitto.conf`, port 1883), with the clients `mosquitto_pub` and `mosquitto_sub`; start it with `mosquitto -d -c /etc/mosquitto/mosquitto.conf`. **Asterisk 1.8.13**, the telephone exchange, starts at boot and listens for SIP on UDP port 5060; `asterisk -rx "core show uptime"` talks to it. Both are offered as experiments: they work, at the speed of an emulated mainframe.');
SCREEN(['root@vm370plus:~# mosquitto -d -c /etc/mosquitto/mosquitto.conf',
        'root@vm370plus:~# mosquitto_sub -t vm370plus/test -C 1 &',
        'root@vm370plus:~# mosquitto_pub -t vm370plus/test -m "hello MQTT on VM/370plus"',
        'hello MQTT on VM/370plus'], 'MQTT on Debian');
SCREEN(['root@vm370plus:~# cat /etc/debian_version', '7.11',
        'root@vm370plus:~# df -h /', 'Filesystem      Size  Used Avail Use% Mounted on', '/dev/dasda1     6.8G  541M  5.9G   9% /',
        'root@vm370plus:~# free', '             total       used       free     shared    buffers     cached',
        'Mem:         60512      21688      38824          0       2220      13792'], 'Debian on VM/370plus');
H3('The console');
P('The 3215 is a line device. Programs that use the full screen (vi, top without `-n1`) draw poorly; use them only if you must. Ctrl-C cannot be typed: type `^c` and Enter instead (the 3215 driver turns `^c`, `^d` and `^z` into the control characters). When CP shows MORE..., press CLEAR or PA2.');
H3('Network and SSH');
P('Linux talks to the PC over a channel-to-channel adapter that Hercules connects to a tun interface on the PC (CTCI). From the PC: `ssh root@10.1.1.2`, or PuTTY to host 10.1.1.2, port 22. The first login after a boot may take a minute while the SSH server gathers randomness. Internet access from Linux needs routing and NAT on the PC; `/etc/apt/sources.list` points at archive.debian.org.');
H3('Stopping Linux');
P('`poweroff` (or `halt`) stops Debian; CP then shows a disabled wait. `CP LOGOFF` releases the attached devices. `IPL CMS` returns to CMS in the same session.');
H2('Several Linux users');
P('Each Linux user needs his own copy of the Debian disk, his own CTC pair with a CTCI line in `vm370ce.conf` and his own IP address in `userid LXPARM`. The kit’s example: MAINT on 600/601 and 190, address 10.1.1.2; CMSUSER on 602/603 and 191, address 10.1.2.2.');
SCREEN(['0600.2  CTCI    10.1.1.2 10.1.1.1', '0602.2  CTCI    10.1.2.2 10.1.2.1', '0190    3390    disks/lnx190.cckd', '0191    3390    disks/lnx191.cckd'], 'Two Linux users in vm370ce.conf');
P('Make `lnx191.cckd` a copy of the Debian disk. The disks are identical: the address comes from the IPL parameters, not from the disk. Give Hercules enough storage for CP\u2019s paging store: `MAINSIZE 256` (the kit\u2019s value) for two Linux users, more for more. With too little, CP fills its DASD paging space (`DMKPGT400I SYSTEM TEMP SPACE FULL`) and the Linux machines fail.');
ATTN('Today one Debian system at a time is practical. Two Debian systems run correctly side by side, but CP keeps its frames in 16 MB of real storage, and two Debian working sets (about 13 MB and 7 MB) do not fit: the scheduler keeps one machine waiting for storage, and it barely moves. Using frames above 16 MB (milestone M4b.3) removes this limit. A Debian system and small Linux systems in storage, or a Debian system and any number of CMS users, run together without problems.');
H2('Linux and CMS side by side');
P('Linux users and CMS users share the system as any two VM/370 users do. Tested: one user runs Debian and writes and reads files under load, while another user works in CMS (LISTFILE, COPYFILE, TYPE, ERASE), defines 64 MB, starts Linux with `LINUX`, stops it with `poweroff` and goes back to CMS with `IPL CMS`; the Debian system\u2019s files are unchanged throughout.');

// ---------------------------------------------------------------- chapter 6
H1('Service Machines');
P('A service machine is a virtual machine that works for other users: it runs disconnected, takes requests and sends answers. VM/370 has always had them (the operator, RSCS); VM/370plus adds new ones. The first is CHATBOT. Others are planned (see the end of this chapter).');
H2('CHATBOT');
P('CHATBOT is the persona chatbot of MCchat, written by the project owner in cREXX and run by RXBVM8. It has ten personas, each in English and German, and a knowledge base, all as CMS files; every answer is authored text chosen the way the original bot chooses it. There is no language model and no network.');
P('Users talk to it through the spool. `CHAT` punches the question to CHATBOT’s reader. CHATBOT reads its reader, runs the bot once for all waiting questions, and punches each answer to the reader of the user who sent the question (the spool file’s origin, so nobody can read another user’s answers). The bot keeps each user’s conversation (persona, language, topic) in `userid CBSESS` on its 191 disk.');
SCREEN(['chat hello there',
        'Hello.',
        'I’m Tchaika.',
        'So - what brings you here today?',
        'Ready;',
        'chat /LIST',
        'Personas (name/language): amicus/de amicus/en andron/de andron/en ...',
        'chat /npc elena de',
        'Oh - du bist es.',
        'chat wie geht es dir?',
        'Gut genug, um dich dasselbe zu fragen und es ernst zu meinen. Also - wie geht es dir wirklich?',
        'chat /WHO',
        'You are CMSUSER. You are talking to elena (de).'], 'Talking to CHATBOT from CMS');
P('An answer takes up to half a minute: CHATBOT looks at its reader every 30 seconds (INTERVAL in CHATBOT CONFIG). `CHAT` alone starts a conversation that ends with an empty line.');
TABLE(['Command', 'Meaning'], [
  ['`/HELP`', 'the commands'],
  ['`/LIST`', 'the personas and languages installed'],
  ['`/NPC name [en|de]`', 'talk to another persona'],
  ['`/LANG en|de`', 'change the language'],
  ['`/RESET`', 'start the conversation again'],
  ['`/WHO`', 'who you are and whom you talk to'],
  ['`/DEBUG ON|OFF`', 'show how the bot chose its answer'],
], [2600, 7038], 'CHATBOT commands');
H2('Running CHATBOT');
P('The directory entry is in place: 32 MB, `OPTION ECMODE`, `IPL 290`, a 60-cylinder 191 on VM50U1 that holds the bot, its data and the sessions. Start it from the operator console:');
SCREEN(['autolog chatbot chatbot', 'AUTO LOGON   ***   CHATBOT  USERS = 005'], 'Starting CHATBOT');
P('Its PROFILE EXEC starts the bot when the machine is disconnected, as after AUTOLOG. An interactive logon (`logon chatbot`) gets CMS instead, for maintenance: `EXEC CHATBOT (LOUD` then runs the bot on the console, `EXEC CHATBOT (ONCE LOUD` answers what is waiting and stops. To stop the service, create `CHATBOT STOP A` on its 191 (the loop ends at its next look) or `FORCE CHATBOT`. To start it with the system, add `AUTOLOG CHATBOT CHATBOT` to the start-up (AUTOLOG1’s PROFILE EXEC).');
TABLE(['CHATBOT CONFIG key', 'Meaning'], [
  ['`DEFNPC`, `DEFLANG`', 'persona and language for a new user (tchaika, en)'],
  ['`WIDTH`', 'line width of the answers (72)'],
  ['`CRISIS`', 'YES: words from a persona’s crisis list get its care text'],
  ['`BOTCMD`', 'the command that runs the bot: `RXBVM8 CHATBOT -a CMS`'],
  ['`MAXBATCH`, `INTERVAL`', 'questions per run of the bot (20), seconds between looks at the reader (30)'],
  ['`VAR name value`', 'variables the persona scripts may use'],
], [3000, 6638], 'CHATBOT CONFIG');
NOTE('The upstream bot (build 1) runs unchanged. Its EXECs were adapted to VM/370 and BREXX (no WAKEUP, no UPPER, EXECIO with variable records, AUTOLOG instead of XAUTOLOG) and one bug was fixed; the list is in `vm370plus/chatbot/VM370PLUS.TXT`.');
H2('Planned service machines');
TABLE(['Machine', 'Purpose'], [
  ['ASKSERV', 'an AI gateway: a Linux guest that relays questions to a language model on the PC or in the cloud; CMS users ask it through the spool, like CHAT'],
  ['SQLSERV', 'SQLite in a CMS service machine that owns the database disk; requests by spool, later by IUCV or sockets'],
  ['Telephony', 'a gateway from CMS to Asterisk on Debian: place calls, voicemail notices as messages'],
  ['MQ, MQTT', 'a queue manager on CMS; the mosquitto broker on Debian'],
  ['Network pack', 'optional: a firewall guest (BORDER), an HTTP load balancer, and a machine that starts more web guests under load'],
  ['SMAPI', 'a subset of z/VM’s systems management API'],
], [2200, 7438], 'Planned service machines');

// ---------------------------------------------------------------- chapter 7
H1('cREXX on VM/370plus');
P('cREXX is a REXX implementation built as a compiler (RXC), an assembler (RXAS), a disassembler (RXDAS) and a virtual machine (RXBVM, RXVM). It needs more than 16 MB to compile larger programs, which is where VM/370plus came from.');
H2('The 2022 release, built on VM/370plus');
P('CMSUSER’s disks hold the 2022 cREXX tree (F0041). In the EC-mode CMS it is compiled by GCC380 with GCCLIB31 and runs in 31-bit mode with its heap above 16 MB:');
SCREEN(['logon cmsuser', 'cp define storage 256m', 'cp link maint 290 290 rr', 'ipl 290',
        'exec crxmk31', '...', 'rxcn basic', 'rxasn basic', 'rxbvmn basic', '0.1', 'Ready;'], 'Building and running cREXX on VM/370plus');
P('`CRXMK31 EXEC` compiles the tree and links `RXCN`, `RXASN`, `RXBVMN` and `RXDASN` (about 90 seconds of CPU time). `GCLB31 EXEC` builds the GCCLIB31 library itself. The output equals that of the cross-compiled build line for line.');
H2('The 24-bit build');
P('The same tree also builds with GCC370 as a 24-bit program (`rxc`, `rxas`, `rxdas`, `rxbvm` on CMSUSER’s E disk); in the EC-mode CMS with `global txtlib gcclib`, `rxbvm -l d ascommon` and `rxbvm -l d asebcdic` run their test sets.');
H2('Cross-compiled programs');
P('`rxc31`, `rxas31` and `rxbvm31` on CMSUSER’s A disk were compiled on the PC with GCC 13 (`-m31`), newlib and a small CMS runtime (`vm370plus/m5f/`). They need Hercules 4.x.');
SCREEN(['ipl 290', 'rxc31 basic', 'rxas31 basic', 'rxbvm31 basic', 'libctest a b'], 'Cross-compiled cREXX');
H2('The current cREXX release');
P('The current release (1.0.0-beta.3) needs a C99 compiler; GCC380 is GCC 3.2.3. It runs on VM/370plus cross-compiled with GCC 13 (`RXC8`, `RXAS8`, `RXBVM8`, milestone M8.1). `RXC8` needs `LIBRARY RXBIN` and `RXCEXITS RXBIN` on the disk named by `-l`; source files are `fn CREXX`:');
SCREEN(['rxc8 -l a -i a hello', 'rxas8 -l a hello', 'rxbvm8 -l a hello', 'Hello from current cREXX on VM/370plus', 'sum 1..10 = 55', 'Ready;'], 'The current cREXX on CMS');
P('Milestone M8.2 builds the same release natively with GCC380 and GCCLIB31 (`RXC82`, `RXAS82`, `RXBVM82`). The three work for programs that call no library functions; the library itself does not build natively yet (Chapter 7). Until it does, use the M8.1 tools. Native cREXX on CMS runs in EBCDIC (IBM-1047) throughout, as IBM REXX does.');
H2('Languages written in cREXX');
P('Several languages are implemented as cREXX programs. They are compiled once on the PC and run unchanged on CMS (through `RXBVM8`) and on Linux (through `rxvm`). Floating point comes from `rxfloat`, a cREXX version of the cREXX float plugin, so no native plugin is needed.');
TABLE(['Language', 'CMS', 'Linux', 'Notes'], [
  ['BASIC', '`BASIC fn.bas`', '`basic fn.bas`', 'classic, MS and ANSI dialects (`-MS`, `-FB`, `-ANSI`)'],
  ['SNOBOL4', '`SNOBOL fn.sno`', '`snobol fn.sno`', 'patterns, tables, arrays'],
  ['Pascal', '`PASCAL fn`', '`pasc fn.pas`', 'compiles Pascal to cREXX, then runs it'],
  ['Lisp', '`LISP fn.lisp`', '`lisp fn.lisp`', 'a Common Lisp subset; without a file, a read-eval-print loop'],
  ['Smalltalk', '`SMALLTLK fn.st`', '`smalltalk fn.st`', 'Smalltalk-80 with GNU Smalltalk bracket syntax; class library in `*.ST`'],
  ['PL/M', '`PLM fn`', '`plmc fn.plm`', 'PL/M-80 compiled to cREXX; `( COMPILE` or `-c` compiles only'],
  ['Prolog', '`PROLOG`', '`prolog`', 'consult files with `consult(\'family.pl\')?`'],
  ['LOGO', '`LOGO fn.logo out`', '`logo fn.logo out.svg`', 'turtle graphics written as SVG'],
], [1400, 2100, 2100, 4038], 'Languages in cREXX');
P('On CMS the languages arrive as one reader deck (`LANGS`); `READCARD *` puts the files on your A disk and `LANGSUP EXEC` rebuilds the modules from their hex form. Use one of CMSUSER’s large disks as A for it (for example `ACCESS 196 A`). CMS cuts a command argument to eight characters, so the EXECs pass file names through the program stack: type the names as usual.');
P('The languages need an EC-mode CMS with a large virtual machine: `CP DEFINE STORAGE 256M` and `IPL 290`. Their storage comes from above 16 MB through HIGHSTOR; Smalltalk alone uses about 100 MB, so it is practical only when Hercules gives VM/370plus real storage to match (the kit’s `MAINSIZE 256`); with 16 MB of real storage CP pages it to a crawl. Programs cross-built for CMS run on an 8 MB stack.');
P('On Debian the languages are part of the cREXX bundle (`lxcrexx.tgz`), unpacked under `/usr/local`; the examples are in `/usr/local/share/`*language*.');
H2('Turbo CREXX');
P('Turbo CREXX is a small Turbo-Pascal-style front end: a menu that creates, edits, compiles and runs one cREXX program at a time. It does not implement REXX; it calls the real cREXX tools.');
TABLE(['Key', 'Action'], [
  ['N', 'new program (from a template), then edit it'],
  ['O / E', 'open an existing program; edit it'],
  ['C', 'compile: compiler and assembler, no run'],
  ['R', 'compile and run'],
  ['L', 'copy an example (hello, fibfact) to your disk or directory'],
  ['D', 'show the versions of the tools'],
  ['Q', 'quit'],
], [1400, 8238], 'Turbo CREXX menu');
P('**On Debian**, type `turbocrexx` (or `turbocrexx` *file*`.crexx`). The editor is `$EDITOR`, else nano or vi. Underneath, `crexx` *file*`.crexx` compiles and runs a program (`crexx -noexec` only compiles): a small driver of VM/370plus for `rxc`, `rxas` and `rxvm`, since the upstream `crexx` driver is not yet built for s390.');
P('**On CMS**, type `TURBO` (or `TURBO fn`). Programs are `fn CREXX A`; the editor is EDIT; compile and run use `RXC8`, `RXAS8` and `RXBVM8` with `LIBRARY RXBIN` on A. Without the menu: `TURBO C fn`, `TURBO R fn`, `TURBO E fn`. The examples are `HELLO TCEXAMPL` and `FIBFACT TCEXAMPL`.');
SCREEN(['turbo', '  T U R B O   C R E X X   ---   VM/370plus CMS', '  Current file: (none)',
        '  N New    O Open    E Edit    C Compile    R Run', '  L Examples         D Versions             Q Quit', 'Command:'], 'Turbo CREXX on CMS');

// ---------------------------------------------------------------- chapter 7
H1('Restrictions and Known Problems');
TABLE(['Area', 'Restriction'], [
  ['Real storage', 'CP’s frames are in the low 16 MB; storage above is a paging store. Large guests page heavily.'],
  ['Linux disk I/O', 'The initramfs still limits disk requests to 128 KB (from the time of the 64-CCW limit, now gone); `echo 760 > /sys/block/dasda/queue/max_sectors_kb` allows larger ones.'],
  ['Shared systems', 'The models of a shared named system are not freed when the last user leaves; they stay until CP is IPLed.'],
  ['CP dump', 'DMKDMP cannot write its dump under ESA/390 (I-201); after an abend the registers must be taken from Hercules.'],
  ['CMS', 'The CMS nucleus is 24-bit; programs above 16 MB use HIGHSTOR and SVC 120 (milestone M6 will change this).'],
  ['CPWATCH', 'Loops under this CP; not autologged.'],
  ['QUERY VIRTUAL STORAGE', 'Shows five digits.'],
  ['Multiprocessing', 'One CPU only.'],
  ['cREXX, native', 'The natively built current cREXX (M8.2) cannot build its library yet; use RXC8, RXAS8 and RXBVM8 (M8.1).'],
  ['CMS file names', 'Programs cross-compiled for CMS cut a file name longer than eight characters to eight (Smalltalk’s `collections.st` is `COLLECTI ST`).'],
  ['Linux', 'Linux 4.0 31-bit is the last kernel with 31-bit support; Debian 7 is the last Debian for s390 (31-bit).'],
], [2400, 7238], 'Restrictions');

// ---------------------------------------------------------------- appendices
setAppendix();
H1('Command Summary');
H2('SET ESA');
SCREEN(['SET ESA ON', 'SET ESA OFF'], 'SET ESA');
P('Class G. **ON**: the next IPL of a device (not an IPL by name) makes the virtual machine an ESA/390 machine; it stays pending across `IPL CMS`. **OFF**: the machine is a System/370 machine at once and nothing is pending. Any operand other than OFF means ON.');
H2('IPL');
P('As in VM/370, with three changes: `IPL LINUX` IPLs the disk at 250 as an ESA/390 machine; any other IPL by name gives a System/370 machine; an IPL of a device by a user who runs a shared named system is done with CLEAR.');
H2('QUERY SET');
P('As in VM/370, with a fifth line: `ESA ON` (an ESA/390 machine), `ESA PENDING` (`SET ESA ON` given, takes effect at the next IPL of a device) or `ESA OFF`.');
SCREEN(['cp query set', 'MSG ON , WNG ON , EMSG TEXT, ACNT ON , RUN OFF', 'LINEDIT ON , TIMER ON  , ISAM OFF, ECMODE ON', 'ASSIST OFF           , PAGEX OFF, AUTOPOLL OFF', 'IMSG ON , SMSG OFF, AFFINITY NONE   , NOTRANS OFF', 'STBYPASS OFF , ESA PENDING'], 'QUERY SET after SET ESA ON');
H2('CHAT EXEC');
SCREEN(['CHAT [question] [(WAIT n BOT name LOUD]'], 'CHAT EXEC');
P('On MAINT 19D. Sends the question to the CHATBOT service machine and types the answer; without a question it asks repeatedly until an empty line. **WAIT** is the time to wait for the answer (default 60 seconds), **BOT** another service machine, **LOUD** shows the steps. Keep your reader empty of other files while you use it. Chapter 6.');
H2('LINUX EXEC');
SCREEN(['LINUX [DISK|READER]'], 'LINUX EXEC');
P('On MAINT 19D. **DISK** (the default) issues `CP IPL LINUX`. **READER** punches `LINUX48 KERNEL1`, `KERNEL2` and `userid LXPARM` (or `DEFAULT LXPARM`) to the user’s reader, holding the other reader files, and IPLs the reader as an ESA/390 machine. Needs 64 MB and, for Debian, the devices listed in Chapter 5 under “What a Linux user needs”.');

H1('Contents of the Kit');
TABLE(['Path', 'Contents'], [
  ['`vm370ce.conf`', 'ESA/390 configuration, MAINSIZE 64, the CTC and 3390 lines for Linux'],
  ['`disks/shadows/*_1.shadow`', 'the VM/370plus system: CP nucleus, CMS, directory, user disks'],
  ['`disks/vm50-4.cckd`', 'VM50-4 with the paging area record corrected'],
  ['`disks/lnx190.cckd`', 'the Debian disk, a 3390-9 (after joining parts 5–7)'],
  ['`README-VM370PLUS.txt`', 'the short form of this manual'],
  ['`vm370plus/linux/`', 'linux48.rdr, lxparm.rdr, lxparmram.rdr, kernel configuration, patches, initramfs sources, the Debian post-install script'],
  ['`vm370plus/m5f/`', 'the CMS runtime for cross-compiled 31-bit C programs'],
  ['`vm370plus/*.EXEC`, `*.C`', 'GCC31 EXEC, CRXMAKE EXEC, examples'],
  ['`vm370plus/chatbot/`', 'the CHATBOT service machine: source, data deck, the VM/370 changes (already installed on the system)'],
], [3200, 6438], 'Kit contents');

H1('ESA/390 Deviations of the Virtual Machine');
P('The ESA/390 virtual machine is complete enough for Linux. Where it deviates from the architecture, the deviation is recorded in the project’s register (documents 39 and 40). The ones a user may notice:');
B(['A format-1 channel program is converted to format 0 in place while it runs (any length; at most 32 TIC targets).',
   'No SCLP and no z/VM interfaces (DIAGNOSE codes of z/VM); Linux must be told `conmode=3215 condev=0x0009`.',
   'One processor; SIGP is answered for that processor only.',
   'Selector channels of an ESA/390 guest behave as block multiplexer channels.',
   'Linux’s machine-check handling is not exercised: CP presents no machine checks to the guest.']);
};
