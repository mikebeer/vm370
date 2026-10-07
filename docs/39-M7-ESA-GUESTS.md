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
