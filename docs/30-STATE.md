# cREXX on VM/370 CE — where things stand

Last updated **1 October 2026**. **Read this first in a new session.**

---

## Current position, 1 October — the DAT conversion is written and verified

**The segment- and page-table conversion is done and it assembles.** On
30 September CP reached `DMKDMP908I SYSTEM FAILURE; CODE PRG018` — a
translation-specification exception — because `CR1 = 05FFC840` pointed at a
segment table of System/370 STEs, `F00561D0 F00562A8 F0056380 …`, with `SEGPLEN`
in the high nibble where ESA/390 requires bit 0 to be zero. That is now
converted: roughly **700 cards across 23 modules in 53 update decks**, covering
the STE, the PTE, the segment-table designation in `VMSEG`, the table sizes, the
shifts, the masks and the alignment.

### What the verification build said

The first build of the whole conversion came back **180 of 192 modules clean**,
and the number that matters is from `tools/asmerr.py`:

    CONFIRMED    0  flagged and predicted
    MISSED       0  flagged but NOT predicted
    COLLIDED     0  a symbol this conversion introduced, already defined
    SILENT     176  predicted but NOT flagged -- no diagnostic exists

Every DAT field was renamed with **no alias** precisely so that an unconverted
site would fail with `IFO188 UNDEFINED SYMBOL` rather than quietly read the
wrong bytes. The previous build raised 176 such diagnostics. This one raises
none, in modules that did assemble — so every deck applied and every site was
converted.

The twelve diagnostics that remained had nothing to do with ESA/390. All four
causes are now asserted mechanically by `tools/replchk.py`, which reproduces all
twelve in under a second and which `mk()` refuses to build past:

| | | |
|---|---|---|
| `SCOPE` | 7 | nine architecture constants put in `CORE COPY` (42 modules) instead of `EQU COPY` (179 of 192) |
| `LABEL-LOST` | 1 | a replacement dropped `PURCONT`, dangling three branches |
| `LABEL-DUP` | 1 | a deck emitted `CKSEG EQU *` that survives on an unreplaced record |
| `CONT-ORPHAN` | 1 | a replaced card carried an `X` in **column 72**; its continuation became a standalone statement |

The last is `R-04` from the other side — not a continuation marker written where
it should not be, but one *removed* where it was load-bearing. `mkdeck.card()`
asserts column 72 on cards it **writes**, which is why the failure had to arrive
through a record it does not write.

All four are fixed; the confirming build is running.

### Group 1 re-measured, and it is not ten sites

`IPL-WALLS.md` said group 1 had "10 cards left". `22-S370-ONLY.md`, in the same
directory, has held **200 nucleus sites across 28 modules** all along. Both were
written here and neither mentioned the other; the quoted figure had been the
wrong one for several sessions. `I-141`.

`tools/privchk.py` now reports the **remainder** where `s370only.py` reports the
total, and the two were reconciled before either was trusted: with the deck
subtraction disabled they agree **199 against 200**, the one difference being
`STIDC`, missing from `privchk`'s opcode list until the check found it.

**95 sites remain**, and the split matters more than the total:

- **62 storage-key sites** (`ISK`/`SSK`/`RRB`), `DMKPTR` holding 23.
- **33 synchronous channel sites** — `DMKLD00E` (19), `DMKVMI` (7), `DMKSAV` (5),
  `DMKCPI`, `DMKENT` — `SIO`/`TIO` polling loops in code that runs before there
  is an I/O supervisor to call. **`DMKLD00E` is the standalone loader that loads
  the nucleus**, so these cannot ride with the deferred multi-channel work: they
  are the IPL path.

### The storage-key family is cheaper than it looked, and provable first

CE sets `CPCREG0 DC X'81800CC0'` where base `PSA MACRO` has `X'80800CC0'`. The
added bit is `CR0_STORKEY_4K`, and Hercules tests it in exactly three places —
`insert_storage_key`, `reset_reference_bit`, `set_storage_key` — raising a
special-operation exception when it is **off**, which is the S/370 rule for
models with the 4 KB-key feature. **So CE already runs with 4 KB keys and both
halves of every paired operation already reach one key.**

That turns what looked like a design decision into an observation. Reading
replicates the one key into both halves and gives the *identical* register value
against CP's `X'0202'` mask; writing takes `SWPKEY1`, because the second `SSK`
already wins and already carries it. `SWPKEY1`/`SWPKEY2` stay independent guest
state either way, since `DMKPRV` answers a guest `ISK` from `SWPTABLE` and not
from hardware. No deviation to document — only register pressure per site.
And because `ISKE`/`SSKE`/`RRBE` are valid in S/370 too, all 67 sites can be
converted and **tested on CE as it runs today**, before anything else moves.
`23-STORAGE-KEYS.md` has it.

### The milestone plan has moved, in two places

`01-PROPOSAL.md` §6 carries M0–M5. Two corrections made on 30 September:

1. **M5 added** — real storage above 16 MB, the "C" axis of
   `WHAT-31BIT-NEEDS.md`. It had no milestone at all, so a deliberate deferral
   read as an oversight. Two of its 67 storage-key sites turned out to be on
   M1's critical path (`I-104`, `I-109`), which is the generalisable lesson:
   **ask which single site runs earliest, not how large the axis is.**
2. **M1 now requires part of B.** M1's premise "DAT off" is true and does not
   help: `LRA` translates **explicitly**, whatever the PSW says, so CP's 174
   `TRANS` sites consult the tables during initialisation. M1 therefore needs a
   valid ESA/390 segment-table designation and STE format for the tables CP
   builds for itself. `06-LEDGER.md`'s test 8 predicted this from the other
   direction. **No site count changes — only the sequencing.**

Also recorded: **we are running strategy A** (IPL from DASD: 12 modules, 82 DAT
references), not the strategy B the worklist chose (`loadcore`: 9 modules, 12).
Nobody wrote that down, and the worklist's estimate has been quoted since as
though B were still in force.

### The build, and why it is circular

`claude/BUILD-CYCLE.md` is the operational document: **a successful build
replaces the CP that performed it with one that cannot perform the next one.**
Four phases, snapshot before the nucleus write, snapshot with Hercules down.
Restoring a snapshot rewinds every deck that postdates it — `I-111`.

Every test runs on **both Hercules 3.13 and 4.9.1** (`build.sh dual`).

### The instruments, which are now the valuable part

Deck generation and running:

- `tools/mkdeck.py` — UPDATE decks with enforced column discipline, ordering and
  8-digit sequence numbers. It refuses bad cards rather than truncating, and its
  `aux()` **merges** an AUXLCL rather than replacing it (`I-138`).
- `tools/mkrun.py` — generates a whole verification run from specs, plus
  `boot_failed()` and `wrong_arch()`, which read the boot and the architecture
  back **out of the run's own log**.
- `tools/build.sh` — the driver. Archives each log before overwriting it
  (`I-131`), tests diagnostic **severity** rather than whether output exists
  (`I-137`), and refuses to start on stale staged cards or a broken deck
  invariant.

Checks that gate a build:

- `tools/replchk.py` — the four `./ R` invariants above.
- `tools/iochk.py` — every staged card-reader file still matches its deck.
  `mk` snapshots the decks before Hercules starts, so a deck edited mid-build is
  silently absent from it (`I-140`).
- `tools/symchk.py` — scope-aware symbol collisions: a deck on a module reaches
  that module, a deck on a member reaches every module that copies it.
- `mkdeck.auxcheck()` — every generated deck is listed in its member's AUXLCL.

Measurement:

- `tools/asmerr.py` — reconciles the assembler's diagnostics against the
  predicted sweep. CONFIRMED / MISSED / COLLIDED / SILENT, with a hard
  cross-check against the count the log states about itself.
- `tools/deckchk.py` — every flagged site is covered by a deck anchor.
- `tools/block.py` — prints the basic block around each flagged site with its
  silent neighbours marked, because a converted field's *neighbours* have no
  diagnostic.
- `tools/idiom.py` — fourteen idiom classes with per-class scope tests.
- `tools/privchk.py` — the S/370-only remainder, reconciled against
  `s370only.py`.
- `tools/dumpscan.py` — reads a printed CP dump back into a byte image and
  measures it. This is what proved `I-116`.
- `tools/s370only.py`, `selfrel.py`, `shifts.py`, `dattab.py` — the sweeps.
- `tools/tally.py` — regenerates `13-ISSUES.md`'s status counts from the table.
- `herc:pgmtrace +1` — Hercules traces program interrupts and **disassembles and
  names** them, including the ECPS:VM assists.

### The one lesson worth carrying, stated plainly

On 30 September, five separate times, work was based on **a check that could not
fail**. On 1 October the shape changed: five times, work was based on **an
artefact that read as current and was not.**

A build log overwritten by the build that depended on it (`I-131`). An AUXLCL
entry overwritten by a later generator, so a verified deck would never have been
applied (`I-138`). A card-reader file snapshotted before a deck was corrected
(`I-140`). A site count written down from three modules and quoted as a total for
several sessions (`I-141`). A status tally that had drifted from its own table by
24 entries. Four of the five were my own record of a measurement rather than the
measurement.

The fix was the same every time: **stop storing the answer, store the thing that
derives it.** `iochk` derives the card file from the deck. `privchk` derives the
count from the source. `tally` derives the summary from the table. None of them
can go stale, because none of them remember anything.

Two further habits earned their place the same day. A tool's green light means
only what it claims — `deckchk` reported zero uncovered for `DMKVMA` while two
sites were unconverted, because it checks anchors and not semantics. And **a
check whose output is mostly noise is not a check**: `replchk` first reported 411
candidates, the three real failures invisible among them.

### Issue register

`13-ISSUES.md`: **139 entries, 79 fixed, 13 open.** Closed entries are kept
deliberately, including the retracted claims — six of the twenty-three, and
three more added on 1 October. The counts are generated by `tools/tally.py`
rather than maintained, after the hand-written ones drifted by 24 entries.

That retraction count is the number to watch. A review that only ever finds good
news is not reviewing.

---

## The documents, and the order to read them

| Doc | What it is |
|---|---|
| **STATE.md** | this file — current position, what is on which machine |
| **BUILD-CYCLE.md** | why each build destroys the machine that performs it. Read before building |
| **WHAT-31BIT-NEEDS.md** | the A/B/C distinction, populations, the four undesigned items |
| **GOTCHAS.md** | the expensive knowledge. Read before touching anything |
| **STE-DESIGN.md** | the ESA/390 table formats, the alignment decision, the order of work |
| **DAT-CONVERSION.md** | how the conversion was made and measured: four instruments, fourteen idiom classes, seven checks |
| **IPL-WALLS.md** | what stands between the current state and an IPL without errors |
| **VM370CE31-PROPOSAL.md** | the 31-bit plan, written for Adrian |
| **CP-VERIFIED.md** | two design hypotheses checked against CP source |
| **CP-INVENTORY.md** | the architecture-dependency counts |
| **IO-ROUTE.md** | channel subsystem: traps, references, revised estimate |
| **FINDINGS.md** | the measurement record, including retractions |
| **ROUTES.md** | the three routes sized against each other |
| **RECONSTRUCT.md** | how to rebuild the cc370 toolchain |
| **REPO-PLAN.md** | repository layout, not yet acted on |

In the repository, `docs/01-PROPOSAL.md` §6 holds the live M0–M5 plan,
`docs/13-ISSUES.md` the issue register, and `docs/22-S370-ONLY.md`,
`23-STORAGE-KEYS.md` and `25-BOOTSTRAP-IO.md` the group-1 inventory — read those
three before planning any S/370-only work, because they already hold the
measurement.

## Two projects now, and they are separate

**1. cREXX on VM/370 CE** — build 92 ships and runs. This was the original
work and it is paused rather than finished.

**2. A 31-bit VM/370 CE** — Mike's stated priority as of 26 September:
"a compatible VM/370 CE first on 31 bit, and ideally later 64". cREXX is
explicitly set aside for this. Mike confirmed on 30 September that **virtual
31-bit addressing is mandatory, not optional** — "otherwise the whole migration
does not make much sense".

The connection: cREXX's compiler needs about 18 MB and CMS gives it 16.
But note that **31-bit CP alone does not fix that** — see the proposal §5.

---

## Project 2: the 31-bit conversion — the 26 September picture

Everything in this section predates any change to CP. It is kept because the
measurements are still good; where it disagrees with **Current position** above,
the later text wins.

### Hardware question: ANSWERED

Eight standalone tests passed on **stock, unpatched Hercules**, ARCHMODE
ESA/390, no operating system:

| Test | Question | Answer |
|---|---|---|
| 1 | hand-built DAT tables accepted, DAT runs | yes |
| 2 | the page table is actually walked | walked |
| 3 | AMODE 31 switch works, DAT survives it | yes |
| 4a | above-the-line **virtual** address translates | yes |
| 4b | …to an above-the-line **real** frame | yes |
| 5 | MSCH/SSCH/TSCH drives a real device | yes |
| 6 | `ORB5_I` gives `SCSW1_Z` and deferred cc 0 | yes |
| 7 | an I/O **interruption** arrives and identifies its subchannel | yes |
| 8 | `LRA` behaves as `TRANS` assumes, in both modes | **no, in 24-bit** |

Test 4b is load-bearing: a store at virtual `X'01005000'` in 31-bit mode with
DAT on lands at real `X'01100000'`, and real `X'5000'` stays zero.

**Test 8 is the one that keeps mattering.** In 24-bit mode `LRA`'s *operand*
address is masked before translation, so it answers correctly about the wrong
page — cc=0 and a plausible real address. Its result is not truncated; its
question is. That moved AMODE 31 into M2, and on 30 September the same property
pulled the segment-table format into M1.

### Milestone 0: closed, and used in anger

`XAOPS.MACRO` — the ESA/390 instructions as macros for CE's 1970s assembler —
was read onto MAINT's A-disk, built with `MACLIB GEN XALIB XAOPS`, and all
twelve members assembled by CE's own Assembler XF. `R-17` closed. Since then
the macro set has grown to include `ISKE`, `SSKE`, `RRBE`, `IVSK`, `IPTE` and
`TPROT`, each noted as proven by execution in its own test script.

**This is CP's own idiom** — 21 sites already use `DC X'E6nn',S(...)` for
the ECPS:VM assists. Those 21 sites became `I-114`: they are S/370-only, CP
executes one *before* it probes for them, and all 21 are now no-opped at
assembly time with the same six bytes CP's own recovery writes at run time.

### The source

Adrian's maintained tree is at `/home/claude/vmce` — 201 CP `.ASSEMBLE`,
59 `.MACRO`, 56 `.COPY`, 314 CMS members, plus `kernel-c/`, `network/`,
`wide/`, `changes/`, `maintenance/`. It survives container reclaims because it
sits outside `scratchpad/`; the CE extraction and every built nucleus do not.

`maintenance/files/194/CPLOAD.EXEC` is CP's own nucleus load list — 174 modules.
It is the authority on whether a module is in the nucleus, and therefore on
whether a site is on the IPL path at all. `DMKFMT`, `DMKDDR`, `DMKDIR` and
`DMKSSP` are standalone utilities outside it.

### What the source showed

Detail in CP-VERIFIED.md and CP-INVENTORY.md. The headlines:

**The biggest item is a compatibility decision.** Segment size goes from
64 KB to 1 MB — ESA/390 has no 64 KB option. The consequence is shared
segments: `DMKATS` and named saved systems are built on 64 KB granularity,
and the minimum shareable unit becomes 1 MB. No parameter solves that.
**Running CE settled it**: `USER DIRECT` puts eight machines at 15 MB and
CMS's shared segments at 15.0–15.7 MB, so a 1 MB common segment 15 would
expose private storage. Frame-level sharing never marks a segment common, so
it is now the only viable route rather than a preference.

**`DMKVAT` is probably the least of the DAT work, not the most.** It is
already parameterised by architecture — `GPR 9 = ARCHITECTURE CONTROL
INDEX` indexes `ARCHTECT`, which has `PTEINCR`, `PINVBIT` and `ZEROBIT` as
table entries, and **four of its eight variants already use fullword page
table entries**. `CODE70` has `SEGMASK X'7FF00000'` — 2,048 one-megabyte
segments, a 31-bit address space. `PINVBIT DC X'04'` and `LOADPTE`'s `LH`/`L`
pair are a third independent witness for the ESA/390 PTE layout, arrived at
from CP's own source rather than from the architecture manual.

**I/O is ten instruction sites, not 1,493 references.** Every S/370 I/O
instruction in `DMKIOS` is a single instruction with the same `0(R1)`
operand; the CAW is built in two places. A shim that synthesises a CSW at
`X'40'` after each `TSCH` leaves all 1,917 CAW/CSW references working.

**`TRANS`, invoked 174 times, concentrates the translation interface.**
Converting one macro covers 174 sites.

**Two retractions of my own claims**: `BAL`/`BALR` self-correct in 31-bit
mode, so only mode boundaries matter; and the DAT table work is owned by
`DMKPGS` (96), `DMKATS` (73) and `DMKBLD` (63) more than by `DMKVAT` (55).

### Setup

**CE's own config must be `ARCHMODE S/370` to build** and `ESA/390` to test.
`mkrun.archmode()` flips ARCHMODE, CPUMODEL, ECPSVM and MAINSIZE together,
because `CPUMODEL 4381` is a machine that does not exist in ESA/390 and
`ECPSVM YES` declares assists whose opcodes are S/370-only. A build driver
must reset S/370 on exit, and a diagnostic afterwards must set ESA/390 and
**verify it from the log** — `I-115`.

---

## The /380 route: three measurements outstanding

Closed on 25 September on evidence that turned out invalid — the CR13
reading was of the *virtual* register, and real CR13 measures zero with CP
up. The conclusion may still be right; it is untested. On Mike's machines,
needing nobody else:

1. **Real CR13 with a guest genuinely executing** — `stop` mid-compile on
   the build-92 machine, then `cr`.
2. **The `ECMODE` flag** on that userid's `USER DIRECT` entry. If absent,
   `DMKDSP` never reloads CR4–13 and (1) is a formality.
3. **`MEMTEST` on the VM/380 machine**, capturing `r 8E.2`, the PSW and the
   faulting address rather than inferring the failure.

Why it still matters: S/380 needs neither a DAT nor an I/O rewrite, so it is
far cheaper *if* CR13 cooperates — against which it needs a patched
emulator, a real cost for a community distribution.

---

## Project 1: cREXX on VM/370 CE — paused

### What works

**Build 92 ships and runs.** Compiler, assembler, linker and virtual
machine built on the mainframe, installing from five card decks. Verified
end to end 25 Sept:

    RXCOK -o T T.rexx     compile
    RXASOK T              assemble
    RXVM T                run

    073/MV no XXERc
    3 25 Sep 2026 16:49:54
    255 FF NUM
    padded|

That exercises reverse, words, date, time, x2d, d2x, datatype and strip —
the EBCDIC fixes, the library link, the compiler finding the library
through CMS enumeration, and the VM reading the module.

**Library:** 61 of 146 members, PC-built, linked by MKLIB. 49 were compiled
natively on 24 Sept but that copy went with a temporary disk.

### What is on which machine

Three distinct Hercules installations, easily confused:

  - **build-92 machine** — VM/370 CE, stock Hercules 3.07, `ARCHMODE
    S/370`. 191 disk: PDPCLIB TXTLIB (2011 build), RXVM MODULE, T REXX.
    250 disk (317 MB pack, the A disk): RXCOK / RXASOK / RXLNKOK MODULEs,
    TA01-TA42 TEXT, P1 REXX, T REXX.
  - **VM/380 machine** — the patched Hercules 3.07:380-5.0, `Modes: S/370
    S/380 ESA/390 z/Arch`. For `MEMTEST` only.
  - **the ESA/390 lab** — `herc.conf`, no DASD. For the standalone tests.

Check the Hercules banner every time. Two of the three are version 3.07 and
both offer ESA/390.

### What is not finished

**85 missing library members.** Importing more than about 60 exhausts the
compiler — one parse context per exposed procedure, 554 for the full
library. Reported to Adrian; the fix is lazy parsing on import, upstream.

**Four members blocked on a decision**: datatype, fsayfmt, trace, rxjson
test whether a character is a letter by range. EBCDIC letters come in three
blocks with gaps. Needs a VM instruction or an agreed library helper — with
Adrian.

**format and qscan** exceed PDPCLIB's fixed 256 KB stack in RXAS's flow
analysis.

**_typedformat** wants about 18 MB to assemble. Compiled for the first time
on 26 Sept; never assembled.

### Upstream, reported but unfixed

  - Import memory: one parse context per exposed procedure
  - Storage leak: ~400 KB per RXC or RXAS run, unrecovered until IPL
  - Inline payloads emitted as single .meta records of 36+ KB, which RXAS
    cannot read back

### Patches written, not submitted

  - 18 against mvslovers/cc370 at ba58285
  - 8 against cREXX
  - 2 in GCCLIB (the `&&`-for-`&` stack rounding, and fopen's file id)

Packaged as `cc370-cms-toolchain.zip` with README and PATCHES.md.

---

## Owed to the team

Not sent, and they belong in one note:

  - **The above-the-line retraction.** Three published measurements were
    24-bit truncation artifacts. FINDINGS.md has the detail.
  - **VMARC does not fail on large archives.** Fifteen decks exceeded the
    CMS 65,535-record limit — DEVDK at 122,651. Ross found it and has had
    the correction; the wider team has not.
  - **The 31-bit result.** This is now much more than a hardware claim: a
    converted CP initialises and dumps itself under ESA/390, and the DAT
    table conversion assembles clean across 23 modules. Worth framing
    carefully, with the IPL stated plainly as not yet achieved.

## What Adrian already has, which changes the plan

From three documents supplied 26 September:

  - **CP and CMS build from Git and boot** — 183 CP and 89 CMS TEXT
    members, two clean builds, all 266 decks binary-identical between runs.
    This closes the gate this project would otherwise have listed first.
  - **C is already in the CMS nucleus** — `DMSFRE STAT`'s chain
    calculation, built with the maintained GCC port, qualified with
    differential tests, reboot, reversal and exact restoration.
  - **Networking exists** — CP C switch plus CMS lwIP, whole-frame DIAG
    transfers, a third service VM, external HTTP passing.
  - **`wide/` is z/Architecture**, not 31-bit — freestanding, GCC s390x
    LP64, `z900`, ELF64 via `loadcore`, DAT fixtures in W-02/03. Explicitly
    not an OS or a CMS boot image, so it reads as a 64-bit *application*
    environment. Same method as our eight tests.
  - **Neither kernel is 31-bit yet**, stated explicitly.
  - He is on **Hercules 4.9.1**, so `FEATURE_370_EXTENSION` is available to
    him — useless for addressing but it backports relative branches,
    immediates, MVCLE and CMPSC into S/370 mode.
