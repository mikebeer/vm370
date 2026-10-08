# M7 — ESA/390 guests, target Linux/390 (scoped 7 October 2026)

VM/370+ runs every guest as a System/370 virtual machine: BC or EC mode,
S/370 I/O (`SIO`/`TIO`/`HIO`, CAW and CSW in page 0), S/370-format DAT.
M7 adds a second kind of virtual machine, an **ESA/390 virtual machine**,
good enough to IPL a 31-bit Linux/390 kernel from the virtual reader and
reach a shell on the virtual console. This is what VM/XA SF did for XA
guests beside its S/370 guests (Gum 1983, docs/IO-ROUTE): one CP, a machine
mode per user, every guest I/O instruction intercepted and simulated.

## What already works for free

The real machine is ESA/390, and an EC-mode S/370 guest already *runs* on
it with its own PSW copied into the real one (docs/34, M2 step 3). An
ESA/390 PSW has the same layout as a S/370 EC PSW with bit 12 on, so an
ESA/390 guest's PSW, AMODE 31, SVC, program, external and timer
interruptions need little more than CP agreeing that this is the guest's
architecture. The new-PSW and old-PSW slots, the program, SVC and external
interruption codes are at the same addresses in both lowcores.

## What an ESA/390 guest needs that a S/370 guest does not

| | Area | ESA/390 guest | Where in CP |
|---|---|---|---|
| 1 | Machine mode | a per-user flag set before IPL (`SET MACHINE ESA`; later a directory option); system reset loads ESA/390 CR defaults | DMKCFM/DMKCFS (command), VMBLOK flag, DMKCFG/DMKVMI (reset, IPL) |
| 2 | IPL | virtual IPL stores the IPL **subchannel id** at X'B8' (X'0001' + subchannel number) and the IPL parameters at X'BC', not the device address at X'02' | DMKCFG |
| 3 | I/O instructions | `STSCH MSCH SSCH TSCH TPI CSCH HSCH RSCH STCRW`; `CHSC`, `SERVC` answered "not available" | DMKPRV decode (opcodes B230–B23B, B239), a new virtual channel-subsystem module |
| 4 | Subchannels | one virtual subchannel per virtual device, number = position in the VDEVBLOK table; SCHIB from the VDEVBLOK (device number, enabled, ISC, interruption parameter) | VDEVBLOK extension or a parallel table |
| 5 | Channel programs | ORB: key, format-1 CCWs (31-bit data addresses), IDAWs; translated to what DMKCCW/DMKVIO already run (format-0 CCWs with real IDAWs, which reach any real frame) | DMKCCW front end |
| 6 | Completion | IRB (SCSW from the virtual CSW — Hercules `scsw2csw` in reverse; ESW zero), pending status until `TSCH`; I/O interruption reflected with subchannel id at X'B8' and parameter at X'BC', enabled by ISC mask in virtual CR6 | DMKVIO/DMKDSP reflection |
| 7 | DAT | guest tables in ESA/390 format (CR0 bits 8-12 = B'10110', CR1 STD, 4-byte PTEs) shadowed into CP's real ESA/390 tables | DMKVAT |
| 8 | Address spaces | Linux 31-bit copies user data with `MVCP`/`MVCS` (secondary space = user): secondary STD (CR7), `SAC`, `IAC`, `LASP` | DMKVAT, DMKPRV |
| 9 | Misc privileged ops | `STIDP` (version X'FF' = under VM), `STAP`, `SIGP` (one CPU: sense/stop/restart), `PTLB`, `IPTE`, `ISKE/SSKE/RRBE` (I-46), `TPROT`, `LRA` 31-bit, `DIAG X'10'/X'44'` | DMKPRV, DMKHVC |

The heavy items are 3–6 (a virtual channel subsystem) and 7–8 (shadowing a
second table format, with a second address space). The rest is decoding.

## Increments and observables

| | Increment | Observable |
|---|---|---|
| **M7.0** | Baseline: a tape-IPLed ESA/390 test guest (in the `guest31` style, GNU `as -m31`) records what CP does today with `STSCH`, `SSCH`, an ESA PSW and X'B8' | the guest's result area, displayed from CP: which instructions reflect operation exceptions |
| **M7.1** | Machine mode + ESA IPL | `SET MACHINE ESA`, `IPL 181`: X'B8' holds `0001 nnnn`; a S/370 user beside it unchanged (regression) |
| **M7.2** | Virtual channel subsystem, synchronous subset: `STSCH`/`MSCH`/`SSCH`/`TSCH`/`TPI`, format-0 and format-1 CCWs, console and reader | test guest writes a line to its console with `SSCH`, reads cards from the reader, takes an I/O interruption |
| **M7.3** | ESA/390 guest DAT, primary space | test guest enables DAT with a remapped page (docs/GOTCHAS: identity mapping proves nothing) |
| **M7.4** | What Linux uses besides: secondary space and `MVCP`/`MVCS`, `STIDP`/`STAP`/`SIGP`, timers, `DIAG X'10'` | Linux's early boot gets past `setup_arch` |
| **M7.5** | Linux/390 31-bit IPLed from the reader (kernel + parm + initrd), shell on the 3215 console | `uname -a` on the console |
| later | ECKD DASD for the guest (3380/3390 minidisks), CTC/networking | Linux root file system on a minidisk |

Linux's own reader IPL code reads the rest of the kernel with `SSCH` on the
subchannel at X'B8', so M7.2 is on the critical path before any kernel code
runs. A 31-bit kernel image (2.4 or 2.6, the last series with 31-bit
support) has to come from outside: the workspace reaches package registries
and GitHub only, so either a prebuilt image from there or a kernel
cross-built with `s390x-linux-gnu-gcc -m31` (present here).

## Decisions taken

- **Simulate, don't pass through.** As VM/XA did: every guest I/O
  instruction intercepts (in ESA/390 they are privileged-operation
  exceptions from a problem-state guest), and CP builds the real channel
  program as it does today. The S/370 path stays as it is.
- **Reuse DMKCCW.** A guest ORB and its CCWs are converted at `SSCH` into
  the virtual-CAW form DMKVSI/DMKCCW already accept; format-1 data
  addresses above 16 MB become IDAWs, which DMKCCW already builds for
  page-crossing areas and which are 31-bit in ESA/390.
- **One subchannel per virtual device**, numbered by VDEVBLOK index, so
  `STSCH` loops (Linux probes subchannels 0..n until cc 3) see exactly
  the user's devices.

## M7.0 result (g390a1, 7 October 11:06)

`IPL 181` of `tests/guest390/g390a` under today's CP, MAINSIZE 16:

| Test | Result |
|---|---|
| lowcore after IPL | X'00' = the IPL PSW `00080000`; X'B8' = `00000181` (S/370: device address at X'BA'). An ESA/390 guest expects `0001 nnnn` |
| `STIDP` | cc 0, `FF098052 30900000` -- version X'FF', "running under VM", already right |
| `STSCH`, `TPI`, `SSCH` | operation exception (ILC 4, code 1) reflected to the guest |
| `STAP` | operation exception too: CP does not simulate it (S/370 guests never asked) |

The ESA/390 PSW survives intact (program old PSW `00080000 80000456`), as
expected from M2 step 3. So M7.1 is the lowcore/IPL and machine-mode
question, and M7.2 the four I/O instructions, plus `STAP`.

## M7.2 result: reader IPL the Linux way (g390d17, 7 October 14:30)

`tests/guest390/g390d` is IPLed from the reader with Linux 4.0's own
`iplstart` protocol: the IPL record's CCWs fill X'18'-X'B7', the
program reads the IPL subchannel id from X'B8', runs `SSCH` on it with
format-1 chains of 20 card reads, and handles the I/O interruption with
`TSCH` until unit exception. Under `SET ESA ON` it now prints
`LOADED BY SSCH FROM THE READER (M7.2)` on its console with `SSCH`. The
final IRB is `00804007 ... 0D`: start function, primary + secondary
status, CE+DE+UE (end of file).

Three CP defects were in the way:

| Run | Symptom | Cause | Fix |
|---|---|---|---|
| g390d5-12 | IPL UNIT ERROR, CCW at X'48' destroyed | DMKVMI (the IPL simulator) keeps its CAW at X'48' and gets its CSW at X'40'; Linux's IPL record keeps CCWs there | DMKVMI saves and restores X'48', sends a read into X'40'-X'4F' to a buffer, and copies it home after the I/O |
| g390d14 | code overlaid, operation exception at X'366' | CP updates the S/370 interval timer at location 80 (X'50') for every guest. That word holds the IPL record's CCW for card 11, so the card landed on the wrong address | DMKDSP skips the location-80 update at both UPVIRT sites when VMESA390 is set (ESA/390 has no interval timer) |
| g390d15-16 | second `SSCH` cc 2 | VM/370's virtual reader reflects channel end and device end as two interruptions. The subchannel stayed busy after the CE-only IRB | DMKDSP merges a queued DE into the CE status for ESA/390 guests, so there is one status, as a channel subsystem presents it |

## M7.4/M7.5 progress: Linux 4.0 31-bit from the reader (7 October, lx1-lx12)

The Linux 4.0 kernel (31-bit, `allnoconfig` plus 3215 console and initramfs,
built with gcc 13 `-march=z900`) is punched as a 33,672-card reader deck
(the image as built is already card-laid-out; an ID card in front) and
IPLed with `SET ESA ON`, `DEF STOR 64M`, `IPL 00C`. It now loads completely
and runs through early setup to `paging_init`, where it enables DAT with
ESA/390-format tables. That is M7.3, the next increment.

What CP had to learn on the way, each found as the next program check
(`TRACE PROG TERM` set before the IPL stops at the first one):

| Run | Stop | Change |
|---|---|---|
| lx2 | iplstart crash after the kernel: SSCH for the parameter file "failed" | DMKVSP answers an empty-reader SIO with cc 1 itself, bypassing DMKVCS. For an ESA/390 guest it now posts the unit check as an I/O interruption (SSCH cc 0), and TSCLEAR ends a unit check alone |
| lx3 | `STFL` operation exception | DMKVCS stores X'80000000' (N3) at X'C8'; Hercules provides the N3 instructions in ESA/390 mode |
| lx6 | `STSI` | cc 3 (no system information) |
| (ahead) | `SERVC` | cc 3 (no SCLP); Linux falls back to `TPROT` sizing |
| lx9 | `STPX` loop (in `memcpy_absolute` and the early program-check handler) | prefix 0 |
| lx10 | `TPROT` loop over 2 GB | cc 0 below VMSIZE, cc 3 above; new DMKPRV route for opcode X'E5' |
| lx11 | `SPX` in `setup_lowcore` | see the limitation below |
| lx12 | translation specification at `paging_init` (`SSM` turning DAT on) | **M7.3** |

`DIAG X'308'`, `EFPC` and `CSP` program-check too, but Linux probes them
under exception-table fixups, as it would on hardware without them.
`CHANGE RDR ALL KEEP NOHOLD` (Linux's DIAG 8 after the IPL) gets "INVALID
OPTION - KEEP" from VM/370: harmless.

**Limitation: `SPX` without virtual prefixing.** VM/370 has none. The
kernel is uniprocessor and addresses its lowcore at real 0 (`S390_lowcore`),
so `SPX P` copies page P to page 0, which stays the lowcore; `STPX` keeps
answering 0, so `memcpy_absolute` takes its plain path. Writes through
`lowcore_ptr[0]` after the `SPX` are not seen at real 0. Real prefixing
(swapping the two page-table entries, with the CORTABLE back pointers and
swap-table entries) is left for when an SMP or a kernel that relies on it
needs it.

Also noted: DMKVSIEX clears the condition code with `NI VMPSW+4,X'CF'` as
well as `VMPSW+2` (BC-mode PSW). For a 31-bit EC/ESA PSW that clears
address bits 2-3, so a guest instruction address from X'10000000' to
X'3FFFFFFF' doing I/O would be damaged. Linux at 64 MB is far below that;
to fix with M7.3.

## M7.5 — Linux reaches user space (8 October 2026)

**Result (lx78):** Linux 4.0, 31-bit, IPLed from MAINT's reader, boots with
its 3215 console on MAINT's terminal and runs `/init` from its initramfs:

```
*** 400098 PROG  0010 ==> 213D98     /init's first segment fault, Linux's
*** 4000A6 SVC   0004 ==> 213B78     write()
*** 4000AC SVC   001D ==> 213B78     pause()
Freeing unused kernel memory: 104K (0027a000 - 00294000)

HELLO FROM LINUX/390 ON VM/370+ (M7)
```

Kernel parameters (parameter file in the reader, or built in):
`no_removal_warning conmode=3215 condev=0x0009`. Kernel and patches:
`arch/31bit/linux390/`.

### The steps from lx40 to lx78

| Run | Symptom | Cause and fix |
|---|---|---|
| lx40–47 | oopses in kfree/kmalloc during cio probing, "memory corruption" | the 3215 console was never enabled, and Linux took an error path in `device_add` for the unnamed console device. Native Hercules with the same kernel and `conmode=3215` showed `console [ttyS0] enabled`, so the cause was in CP |
| lx47 | `cio_commit_config` fails | MSCH kept only ISC and enable; Linux reads back MM/MP, concurrent sense, XMWME, MBFC and MBI with STSCH. Now kept per subchannel |
| lx48–52 | SENSE ID (X'E4') never answered | VM/370's virtual devices don't know it. DMKVCS answers a lone SENSE ID itself from the device type (`SIDTAB`: 3215, 2501/2540/3505, 2540P/3525, 1403/3211, 3330/3340/3350, 2314, 3420), unaligned buffers included |
| lx51 | `ccw_device_wait_idle` loops on TSCH cc 1 | an immediate completion (SIO cc 1, CSW stored) left SSCH at cc 1. Now SSCH cc 0 and the status queued as an interruption. CSCH leaves a clear-function status pending |
| lx57 | status with device status 0 | DMKDSP builds a device-only interrupt (`VDEVPEND`) from `VDEVINTS`, not `VDEVCSW`: the status is queued on the channel-end path (`VDEVCHAN`, `VCHCEPND`, `VCUCEPND`) |
| lx66–67 | path-verification NOP never ends, Linux retries SENSE ID | the console's NOP (X'03') does not come back through DMKVSJ's TESTEC. DMKVCS ends a lone NOP itself. A zero-count CCW is converted as count 1 + SLI |
| lx67 | CP abend **DSP001** | a status queued on a selector channel needs `VCHCEDEV` |
| lx68–69 | `Failed to execute /init (error -14)` | a page-protection exception (a clean user stack page) was reflected with a stale TEID without bit 29, so Linux took it for low-address protection. DMKPRG now passes the real TEID for code 4 |
| lx70–77 | `PROGRAM INTERRUPT LOOP` (specification exception after `STPT`) | CP fetched the privileged instruction through the *primary*-space shadow (RUNCR1). After the first exec, primary is the user's space, so the user's bytes at the kernel's address were read and `STPT` was decoded as `ISK`. DMKPRV now fetches from the home-space shadow in home mode, and EXTSHCR1 (CP's quick LRA paths) is the home shadow in home mode |

### Tools built for it

- `drive.py` **gdump**: after CP shutdown, a guest's real storage is read
  through its segment table (from LOCATE's VMBLOK) and saved as
  `<run>.gdump`. Used to read the kernel log (`__log_buf`), lowcore and cio
  structures while Linux owns the console.
- `drive.py` **capture**: follow a value CP printed (a VMBLOK address) in a
  later step.
- **CP PER** (`PER STORE range RUN`) and **CP TRACE PROG SVC EXT RUN** on the
  test terminal, both working for ESA/390 guests.
- DMKVCS ring (`DMKVCSRG`): subchannel instructions only, repeats counted.
- DMKPRG capture `PRGSM6`: registers at a simulated specification exception.
