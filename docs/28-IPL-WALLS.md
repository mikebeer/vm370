# The walls between a converted CP and a clean IPL

Started 28 September 2026, rewritten 1 October, re-measured 1 October (midday),
re-measured again 1 October 18:45 UTC,
again 2 October 12:10 UTC when wall 11 fell,
**and again 2 October 18:55 UTC, when walls 14 and 15 fell, wall 13 was
downgraded, and a Status column was added.** Every
section that has been superseded says so where it stands rather than being
deleted, because the diff is the point of this file.
Extends **STATE.md** and **BUILD-CYCLE.md**. Read after GOTCHAS.md.

**This file is the version-controlled original; the project's copy is published
from it.** It answers one standing question — *what is between the current status
and an IPL without errors?* — and that answer has now been given three times with
three different numbers, so it belongs somewhere with a diff.

Sixteen walls so far, thirteen of them closed, one downgraded to "never was a
wall", one not CP's, and one open. Every one was located to a specific
instruction at a specific address rather than inferred, and **each was only
visible once the previous one fell** — which is the single most useful thing
this document records, because it is also why no estimate of "how much is left"
has ever survived contact.

The count itself is evidence for that last point: this file said "eleven walls"
for two days while walls 14 and 15 were already in the nucleus, waiting to be
reached.

## The walls, in the order CP hit them

The **Status** column is the one to read first. It is deliberately not a
percentage: a wall is `closed` only when the failure it names is gone *and* the
run that proves it is in the build journal.

| # | Wall | How it presented | Found by | Status |
|---|---|---|---|---|
| 1 | The conversion executes, and S/370 rejects it | disabled wait `X'111111'`, `B234` = `STSCH` under `ARCHMODE S/370` | reading the PSW | **closed** |
| 2 | **BC-mode PSW is a third axis, never counted** | `Invalid IPL PSW: 00040000 00004470` — bit 12 zero | Hercules refused the IPL | **closed** |
| 3 | The standalone loader is itself S/370 I/O | `9D00 8000` = `TIO 0(R8)` in `DMKLD00E` | PSW at `X'44C2'` | **closed** |
| 4 | `XAIO` borrowed R15, a `USING` base in 54 modules | interruption code `X'15'`, operand exception | PoP + the trace | **closed** |
| 5 | Subchannels resolved but never enabled | `MSCH` count 0; cc 3 from every `SSCH` | counting MSCHs in the artifact | **closed** |
| 6 | The architecture probe clobbered R1 | exactly one device per module failed | register dump | **closed** |
| 7 | `DMKDMP` took the dump with `ISK` | `DMKDMP905W SYSTEM DUMP FAILURE` | `0934` at the failing address | **closed** |
| 8 | `SSK` sized storage at **zero**, and FRELOOP ate the nucleus | `C6D9C5C5` (`"FREE"`) every 16 bytes, incl. lowcore | breakpoint + arithmetic | **closed** |
| 9 | CP executes an ECPS:VM assist *before* probing for assists | `SCNRU` / `STEVL`, operation exception | `pgmtrace`, one run | **closed** |
| 10 | Our own DSECT grew; the block generator did not | `CPI001` — SYSRES not found | `dumpscan.py` on the dump | **closed** |
| 11 | **`CR0`'s translation format says 64 KB segments** — NOT the STDs, see the retraction below | `PRG018` = translation specification | Hercules's `dat.c`, a day late | **closed** 2 Oct 12:02 UTC |
| 12 | **Not a CP wall: the build environment is reclaimed mid-run** | Hercules, the driver and the watcher vanish together; the log ends on a normal `Ready;` | `uptime`, two hours late | **not CP's** — mitigated by sliced builds |
| 13 | ~~Privileged-operation exception on `SSM`, DAT on, in problem state~~ | `PSW=040D0000 0006D130`, `INST=8000D129` | SDL 4.9.1 + `pgmtrace` | **NOT A WALL — downgraded 2 Oct** |
| 14 | **A half-converted geometry group in `DMKPTR` `GETENTRY`** — one of five instructions converted, four left at 64 KB | silent hang: CP alive, in supervisor state, taking I/O interrupts, printing nothing, for five days | `abendmap.py` + arithmetic checked against a `savecore` | **closed** 2 Oct — `I-162` |
| 15 | **`N R7,=A(X'FFF0')` did two jobs on a halfword PTE** — strip flags *and* leave page×16 for `ACORETBL` | `ABEND PTR020`, "DMKPTRUC IS NEGATIVE", with a 30,669-line dump | `DMKPTRUC`/`DMKPTRP2` read out of the nucleus | **closed** 2 Oct — `I-163` |
| 16 | **CP writes a one-byte blank to the console from an `X'EE'`-filled buffer** — not silent, empty | `CCW=09056360 60000001`, buffer `40EEEEEE…`, `Stat=0C00`; no read CCW anywhere; dispatcher enabled wait `PSW=030E0000` | CCW trace armed **before** the ipl | **OPEN — where CP stops now** — `I-165` |

**Walls 1–11, 14 and 15 are closed.** Wall 11 fell on 2 October at 12:02 UTC:
`PRG018` is gone after five days. Wall 12 is not CP's. **Wall 16 is where CP
stops now.**

### Wall 13 is downgraded, not closed

It was recorded as a wall on the strength of a privileged-operation exception on
`SSM`. The PSW that was quoted for it says otherwise and always did:
`040D0000` has `cmwp=D`, i.e. **bit 15 set — problem state** — and Hercules
printed the operand as `V:0006D131`, a *virtual* address. That is a virtual
machine executing `SSM`, which CP is supposed to intercept and virtualise in
`DMKPRV`; the exception is the mechanism, not a fault. On 2 October CP ran
**past** it to the dispatcher's wait in every run, which settles it. The entry
stays in the table with its original wording struck through, because a wall that
was never a wall is exactly the kind of thing this file exists to keep visible.

### Walls 14 and 15 are the same defect class, and it is ours

Both are groups of instructions that encode page geometry and must change
together — and in both, an earlier pass converted **one** member and left the
rest. That is worse than converting none: the arithmetic stays internally
consistent enough to produce a plausible address, so it fails as a hang or a
counter underflow rather than as an assembly error. Wall 14 cost five days for
three cards. `tools/geomchk.py` now sweeps for the class and reports a site only
where no deck of ours replaces its sequence number; it currently lists **15
PROVEN** unconverted sites, including the identical `16*2+8` swap-table
expression in `DMKCDB`, `DMKCDM` and `DMKPGS`. The class is not confined to
`DMKPTR` and wall 16 may well be another member of it.

A caution on reading the next section, **superseded 2 October 18:55 UTC and kept
for the diff**. It read: *"by the measure of what CP visibly does, it currently
does less than on 30 September — it prints nothing at all, where it used to
initialise fully and dump itself."* That held while wall 14 stood. With walls 14
and 15 closed, CP talks again: the wall-15 build printed
`DMKDMP908I SYSTEM FAILURE; CODE PTR020` and a complete 30,669-line dump ending
in `*** END OF DUMP ***`, so DMKDMP's whole path — abend, message, formatted
dump, converted printer — works end to end.

What has **not** been shown at any point is CP printing a *normal*
initialisation message. Every console line this project has ever seen came from
DMKDMP on the abend path. So in wall 16, silence is **not** evidence that
initialisation failed, and that asymmetry is the trap to avoid repeating: the
ordinary message path (`DMKQCNWT` → `DMKCNS`) has never been exercised
successfully, and until it has, "prints nothing" and "did nothing" are different
claims.

Walls 1–10 are closed, and for the record: Detail for each in `docs/13-ISSUES.md`; the entries
worth reading are **I-77**, **I-102**, **I-104**, **I-108**, **I-110**,
**I-114**, **I-116**, **I-162** and **I-163**.

## Wall 16 — every fact measured so far, and the two readings it allows

Measured 2 October, three runs, identical each time:

| | |
|---|---|
| PSW | `030E0000 00000000` — `sm=03`, `cmwp=E`, `am=24`, `ia=0` |
| state | **enabled** wait (W=1), supervisor, interrupts not masked |
| `GR12` / `GR13` | `00032BC0` / `00033BC0` — `DMKDSPCH`'s base pair, from `ADSPCH` in the PSA |
| `GR14` | `50034C98` — return address `X'34C98'`, just past DMKDSP's two-base range |
| `X'86'` | external interruption code `X'1004'` — clock comparator |
| varies run to run | `GR03` (a TOD value), `GR09` (`50`→`54`) |
| constant run to run | `GR04=9`, `GR05=5`, `GR07=165` |
| console output | **none** |
| `cold` sent to `0009` | delivered (`/(0009) cold`) and **ignored** — same wait, same registers |

### RESOLVED 2 October 19:08 UTC — CP is not silent, it writes one blank byte

Two readings were open: CP idle with undrained messages, or CP stuck before
console I/O existed. **Neither.** With CCW tracing armed *before* the IPL — which
`build.sh test` could not express until the `--` marker was added — the entire
console conversation is six CCWs (`I-165`):

```
0009: Halt subchannel
0009:CCW=0406DA80 20000020 => all zeros      sense, 32 bytes; Stat=0C00 Count=001F
0009:CCW=09056360 60000001 => 40EEEEEE EE..  WRITE, count 1; Stat=0C00
0009:CCW=03000000 20000001                   NOP;   Stat=0C00
```

Every CCW completes with `Stat=0C00` — CE+DE, no error. So the channel program
is right, the device is right, and the one byte CP writes is `X'40'`, an EBCDIC
blank. **The lone blank line in every run's output is CP's message.** The buffer
at `X'056360'` is still full of `X'EE'`, DMKFRE's `&FRETRAP` fill for allocated
storage that has never been written, so the text was never moved in and the
count was never set.

There is **no read CCW anywhere** — opcodes `04`, `09`, `03` only. CP never posts
a console read, so the `cold` typed at `0009` was discarded by the 3215 with no
error and no trace. That half is settled too.

So wall 16 is not "CP prints nothing". It is **CP writes an empty message**: a
correct channel program pointed at an unfilled buffer with a length of 1. A
length that collapses to 1 next to a buffer that is never filled is the
signature of a length read from the wrong place — `I-128`'s structural law, and
therefore the same class as walls 14 and 15.

**What the harness cost here.** Three runs armed `t+009` *after* `herc:ipl`,
recorded an empty trace, and that emptiness was read as "CP issues no I/O". It
was not evidence of anything. Two limitations, now fixed or written down:
`build.sh test` appended every caller spec after the ipl, so a trace could never
cover the IPL (fixed — specs before a literal `--` now precede it); and `test`
passes `--bare` to `mkrun`, which **omits the whole `BOOT` dialogue** — the null
line, `cold`, `cp disc`, `logon maint`. `--bare` is correct for its original
purpose, a standalone loader IPL with no operating system underneath, and wrong
for testing a CP nucleus.

## What CP does today

IPL 6A1 under `ARCHMODE ESA/390`, on a nucleus 32 update decks deep, built by
CE's own 1970s assembler:

- restores its nucleus page image, **sizes real storage correctly at 16 MB**,
  builds its CORTABLE, enumerates **and enables** its 949 subchannels,
- reads volume labels from its DASD and **resolves SYSRES by volume serial**,
- disables the ECPS:VM assists it cannot have and carries on,
- **prints on the operator console**, and
- **writes a complete formatted dump of itself** — registers, control
  registers, TOD clock, 3.4 MB of storage — through a converted printer path.

Confirmed from inside the machine: `GR01 = 01000000` (the storage size),
`CR6 = FF000000` (the I/O-interruption subclass mask), and the RDEVBLOK array
striding `X'60'` and abutting the RCUBLOKs exactly. Since 1 October the same
facts are confirmed on **two engines**, Hercules 3.13 and SDL 4.9.1, which agree
on all six compared values (`claude/HERCULES-4.md`).

## Wall 11, in detail — RETRACTED CAUSE, and what it actually was

**The diagnosis below is kept verbatim because it is wrong in an instructive
way.** It attributes `PRG018` to the segment table being in System/370 format.
The tables were genuinely wrong and converting them was genuinely necessary —
but they were **not the cause of the exception**, and converting them did not
clear it.

Hercules checks `CR0` at `[3.11.3.2]`, **before fetching a single table entry**:

    if ((regs->CR(0) & CR0_TRAN_FMT) != CR0_TRAN_ESA390)
        goto tran_spec_excp;

    CR0_TRAN_FMT    0x00F80000   bits 8-12, the translation format
    CR0_TRAN_ESA390 0x00B00000   1 MB segments, 4 KB pages

CE sets `CPCREG0 DC X'81800CC0'`, and `X'81800CC0' & X'00F80000'` is
**`X'00800000'`** — System/370 for 4 KB pages and **64 KB segments**. Two bits.

The proof is a converted nucleus whose tables were verified correct *first*, read
out of the stopped machine on 2 October: `CR1 = X'00FFC005'` (bit 0 clear, origin
`X'FFC000'` 4096-aligned), `STE 0 = X'00FFAC0F'` (bit 0 clear, PTO 64-aligned,
PTL 15), a page table of `00000000 00001000 00002000 00003000 …` — textbook
ESA/390 PTEs — **and the identical `PRG018` at the identical `LRA`.** One card,
`CPCREG0 DC X'81B00CC0'`, cleared it. `I-152`.

The lesson is about diagnosis rather than about `CR0`: a dump showed a wrong
value, the wrong value was real, and nobody asked whether it was the value the
hardware complains about **first**. The emulator's own source answers that in
four lines.

## Wall 11 as originally diagnosed — kept for the diff

`DMKDMP908I SYSTEM FAILURE; CODE PRG018`. The code is literal: **018 decimal is
`X'12'`, a translation-specification exception.**

    r 8C     00040012              ILC 2, code X'12'
    r 28     000C1000 0003D9F6     program old PSW -- DAT OFF

The failing instruction is four bytes back, and its two predecessors give it
away:

    03D9EE   B711 2010    LCTL  C1,C1,16(R2)    load the segment-table designation
    03D9F2   B170 1000    LRA   R7,0(,R1)       and translate
    03D9F6   4770 C05E    BNZ   ...

That is **`TRANS.MACRO`'s expansion**, verbatim, and `CR1 = 05FFC840` points at
CP's segment table, which reads

    FFC840   F00561D0  F00562A8  F0056380  F0056458  ...

System/370 STEs. The high nibble `F` is `SEGPLEN` — a page-table length of 16
pages for a 64 KB segment. Under ESA/390 those bits are part of the page-table
origin, the length lives in bits 28–31, and **bit 0 is unassigned and must be
zero.** It is 1 in every entry.

### Why this lands in M1 and not M2

M1's premise is *"DAT off, no paging"*, and the premise is **true** — the
program old PSW shows DAT disabled. It does not help. **`LRA` translates
explicitly, whatever the PSW says**, so the tables are consulted during
initialisation regardless.

`06-LEDGER.md`'s test 8 predicted this from the other direction a week earlier:
it found `LRA`'s *operand* truncated in 24-bit mode and used that to move
AMODE 31 into M2. The same property of the same instruction now pulls the
segment-table format into M1. **No site count changed — only the sequencing.**

---

## What is between here and `DMKCPI966I` — re-measured 18:45 UTC

The three earlier answers to this question were a guess, a sweep, and the
assembler's first verdict. This one is the assembler's **second** verdict, after
the conversion was written.

`CORE.XA0033DK` renames every DAT field with no alias, so an unconverted site
cannot assemble. The midday build raised **176 undefined-symbol diagnostics**
across 16 modules — one per site needing work. The build of 13:15 UTC, with the
conversion written, raised **none**:

```
CONFIRMED    0  flagged and predicted
MISSED       0  flagged but NOT predicted -- the sweep has a hole
COLLIDED     0  a symbol this conversion introduced, already defined
SILENT     176  predicted but NOT flagged -- no diagnostic exists
```

The modules did assemble, so every deck applied and every renamed site was
converted. **~700 cards across 23 modules in 53 update decks.**

That build's module accounting, which took three attempts to state correctly
(`I-147` — I reported the denominator as 198, then 192, and it is 186):

| | |
|---|---|
| modules assembled | **186** |
| OK — clean *and* an object deck | **180** |
| DEFECT — a diagnostic that is not an MNOTE | **5** |
| MISSING — no `TEXT`/`TXTLCL`/`TXTHRC` | **0** |
| MNOTE-only — `DMKRIO`, `I-34`'s 3375/3390 notes | **1** |

The five defects had nothing to do with ESA/390, and all four causes are now
asserted statically by `tools/replchk.py` before a build starts: a replacement
must carry forward any label it covers (`PURCONT`), must not define one that
survives on an unreplaced record (`CKSEG`), must take continuation cards with it
(`DMKCPP` 62000000 carried an `X` in **column 72**), and must only name symbols
the module can see (seven diagnostics from putting nine architecture constants in
`CORE COPY`, copied by 42 modules, instead of `EQU COPY`, copied by 179 of 192).
`I-143`. All four are fixed and the confirming build is in progress.

**So wall 11 is converted and assembles. It is not yet proven at run time**, and
nothing below should be read as claiming otherwise. The measurement that decides
it is the nucleus write and the IPL on both engines.

### Group 1 — RETRACTED: not 10 cards, 95 sites

**The figure in the previous version of this section was wrong, and the way it
was wrong matters more than the number.** It read:

> `DMKCPI` 1, `DMKPSA` 4, `DMKSAV` 5 — unchanged, and still a day.

Ten or eleven sites, specific enough to be believed, and quoted across several
sessions. It was three modules someone had looked at, written down as a total.
`22-S370-ONLY.md`, **in this same directory**, has held the real measurement all
along — 200 nucleus sites across 28 modules, taken from Hercules's own opcode
table. Two documents in one directory disagreeing by a factor of twenty, neither
mentioning the other. The tell was available: `DMKPSA` has **five** `ISK`s, not
four, and a count taken by reading is not off by one in a list of five. `I-141`.

`tools/privchk.py` now reports the **remainder** where `s370only.py` reports the
total, and the two were reconciled before either was trusted: with the deck
subtraction disabled they agree **199 against 200**, the single difference being
`STIDC`, missing from `privchk`'s opcode list until the check found it. Every
other opcode matches site for site — TIO 71, SIO 48, ISK 38, SSK 16, RRB 13,
HIO 5, HDV 4, TCH 3, CLRIO 1 — and both put the same four standalone utilities
outside the nucleus.

**95 sites remain, and the split matters more than the total.**

| | sites | where | on the IPL path? |
|---|---|---|---|
| **storage keys** | **62** | 14 modules, `DMKPTR` holding 23 | not for CP coming up; `DMKPSA`'s five are in the fetch/storage-protection checks, reached when a virtual machine touches storage, and `DMKPTR`'s 23 when paging starts |
| **synchronous channel** | **33** | `DMKLD00E` 19, `DMKVMI` 7, `DMKSAV` 5, `DMKCPI` 1, `DMKENT` 1 | **partly yes** |

`ISK`, `SSK` and `RRB` are `GENx370x___x___` in Hercules's opcode table — they do
not exist in ESA/390 at all, so each one executed is an operation exception.
Walls 7 and 8 were exactly this.

**The channel group cannot ride with the deferred multi-channel work, which is
what the previous version assumed.** `DMKLD00E` is the standalone loader that
loads the nucleus; it runs before CP exists. Its 19 sites are on the
*nucleus-write* path, which runs under `ARCHMODE S/370`, so they do not block
this IPL — they block ever loading a nucleus under ESA/390. `DMKSAV`'s five are
in `QDISK`, `SCPZCAW` and the sense-retry path, which is consistent with CP
already restoring its nucleus image successfully; its main restore path is
converted. `DMKCPI`'s is the sense to the IPL device.

### The storage-key family is cheaper than it looked, and provable first

CE sets `CPCREG0 DC X'81800CC0'` where base `PSA MACRO` has `X'80800CC0'`. The
added bit is `CR0_STORKEY_4K`, and Hercules tests it in exactly three places —
`insert_storage_key`, `reset_reference_bit` and `set_storage_key`, the **2 KB**
instructions — raising a special-operation exception when it is **off**, which is
the S/370 rule for models with the 4 KB-key feature. **CE therefore already runs
with 4 KB keys, and both halves of every paired operation already reach one key.**

That turns what looked like a design decision into an observation. CP keeps a key
per 2 KB half of its own accord (`SWPKEY1`, `SWPKEY2`) and packs both hardware
keys into one register against a two-byte mask, because `ISK` only loads bits
24-31. Reading replicates the one 4 KB key into both halves and yields the
*identical* register value; writing takes `SWPKEY1`, because the second `SSK`
already wins and already carries it. `DMKPRV` answers a guest `ISK` from
`SWPTABLE` rather than from hardware, so the guest keeps seeing its two distinct
keys either way. **No deviation to document — only register pressure per site.**
And because `ISKE`/`SSKE`/`RRBE` are valid in S/370 too, all 67 sites can be
converted and tested on CE **as it runs today**, before anything else moves.
`23-STORAGE-KEYS.md` has the detail; `I-142` records that I twice generalised one
site's answer into a rule before checking.

### Group 2 — the DAT tables: WRITTEN. 176 flagged sites converted, ~90 silent read

**Status as of 18:45 UTC: all 176 flagged sites are converted and the modules
assemble.** The text below is the midday analysis, kept because the measurements
and the reasoning still hold; where it describes work as outstanding, read it as
describing what was done. The one item in it that is **still open** is the `VMSEG`
readers, and that is now the largest known remaining item on the path to CP
coming up — see the estimate at the end.

| module | flagged | module | flagged |
|---|---|---|---|
| `DMKBLD` | 37 **converted** | `DMKCPP` | 6 |
| `DMKPGS` | 31 | `DMKRPA` | 6 |
| `DMKPTR` | 31 | `DMKCPI` | 5 **converted** |
| `DMKATS` | 23 | `DMKMCH` | 4 |
| `DMKCFG` | 16 | `DMKCDS` | 2 |
| `DMKVMA` | 13 | `DMKCFH`, `DMKVMD` | 1 each |

`DMKBLD` and `DMKCPI` are the two modules on CP's own initialisation path — the
ones that must be right before `LRA` can succeed. Both are converted (256 and 29
cards), and **both are awaiting their first assembly as this is written**, so
nothing here claims they work.

**What `DMKBLD` taught, and it is the number that matters:** 37 sites the
assembler named, **46 it could not**. The rename-without-aliases discipline
covers 45% of the work in that module; the rest is arithmetic and idiom around
the flagged sites, which has no diagnostic of any kind (`I-124`). Measured across
the 14 unconverted modules the silent work is about **90 candidates**, so the
remainder is roughly **229 changes** (`I-133`). The naive extrapolation from
`DMKBLD`'s ratio gives 310 and overstates, because `DMKBLD` is the *builder* and
carries allocation arithmetic the others only consume.

**The undesigned ABI item is settled, and the source settled it.** The old
version of this document said `DMKBLDRT`'s packed-address interface *"is reached
by SVC, so widening it is an ABI change across 24 callers"*, and made that the
question deciding whether group 2 was days or weeks. Sequence 00523000 documents
the field:

    *        BYTE 0-1 = FIRST ADDRESS TO RELEASE
    *             FIRST 4 BITS = 0, NEXT 8 BITS = SEGMENT, NEXT 4 = PAGE

Twelve bits of page number, split 8+4 for 64 KB segments and **4+8 for 1 MB
ones**. The field keeps its width and its meaning; only the split moves. **No
widening, and no ABI change** — seven shift and mask literals in two routines.

**A group-2 item that did not exist in the previous answer: the `VMSEG`
readers.** `I-128` is the structural law behind most of the silent work —
System/370 packs lengths and flags into the **high** byte of a pointer, which
24-bit address formation ignores, so a packed word is usable as an address with
nothing to strip; ESA/390 moves them to the **low** bits, which address formation
never ignores. Measured:

| | |
|---|---|
| `L`/`LCTL` of `VMSEG` | **92 sites, 40 modules** |
| of 30 classified: unmasked, needing a mask added | **16** |
| masked with a constant that must change | **14** |
| `IC Rn,VMSEG` reading the length from byte 0 | **9** |
| `LCTL C1,C1,VMSEG` — correct as written | the only safe form |

**None of these is flagged, because `VMSEG` is not renamed**, and unlike the
AMODE items below they are **live in M1**: the bits that stop being ignored are
the low ones, so AMODE 24 does not help. The remedy is the one that worked for
the DAT fields — rename `VMSEG` with no alias and let the assembler enumerate all
105 references — and it is a second rename pass, not a reading exercise.

### Group 3 — open, and genuinely not blocking a clean IPL

| Item | Why it does not block | Lands at |
|---|---|---|
| `I-94` `DMKOPRWT` vector nothing fills | blinds bootstrap errors; does not cause them | open, deliberately |
| TSCH polling deviation | works; deviates from PoP notes 4 and 5 | deferred, with multi-controller work |
| `XAIOFIND`'s one-entry device cache | ~507 full subchannel scans per IPL | performance only |
| `DMKAPI`'s `E612` assist | not in `CPLOAD` under AP=NO | if AP returns |
| **`I-126`: `LA Rn,0(,Rn)` — 215 sites, 79 modules** | AMODE 24 still truncates, so all 215 behave as today | **M2**, simultaneously |
| **`I-132`: three-byte address fields — 278 sites, 81 modules** | 24 bits is adequate below 16 MB | **M5**, as structure changes |

The last two are new, and they are the reason this section was re-measured rather
than edited. Both are invisible through a clean IPL and both are large:

* `I-126` is 215 instances of an **idiom**, documented in `DMKPGS` as
  `LA R3,0(,R3)  24 BIT ADDRESSING`. In AMODE 31 `LA` clears only bit 0, so
  every one of them stops stripping anything — not gradually, but at the
  instant the PSW changes, across 79 modules.
* `I-132` is 278 `ICM`/`STCM`/`CLM` with a three-byte mask. **Only 12 of the
  fields are declared `AL3`/`XL3`**; the rest are three bytes of a wider field
  reached by displacement, so no DSECT sweep finds them. A three-byte field has
  nowhere to put a 31-bit address, so unlike `I-126` these cannot be fixed by
  changing an instruction: all 278 are structure changes, each carrying
  `I-116`'s declaration-versus-generator hazard.

Neither belongs in M1 and neither was in anyone's count. They belong in
`WHAT-31BIT-NEEDS.md`.

## Wall 13 — where CP stops now

Measured 2 October 12:02 UTC, on a nucleus built from 59 modules all assembling
clean (59 OK, 0 DEFECT, each run verified complete), written successfully
(`SYSTEM LOAD DECK COMPLETE`, `Nucleus loaded on VM50-1`, wait state `12`), and
IPLed under ESA/390 on SDL Hercules 4.9.1:

    HHC00801I Processor CP00: Privileged-operation exception interruption
    HHC02324I PSW=040D0000 0006D130  INST=8000D129  SSM  297(13)
    CR00=81B00CC0  CR01=00FFC005
    GR03=00FFC000  GR12=0006C008  GR13=0006D008

What this says:

* **`CR00 = 81B00CC0`** — wall 11's fix is live.
* **`CR01 = 00FFC005`** — the designation is in ESA/390 form and the hardware
  accepted it, along with the segment table and the page tables. CP is past the
  translation that used to fault.
* **`PSW = 040D0000`** — byte 0 `04` sets **bit 5: DAT ON**. Byte 1 `0D` sets
  bit 12 (ESA/390 mode, which is `wall 2`'s requirement met) and **bit 15:
  problem state.**
* **`SSM` is privileged**, so problem state alone explains the exception.

The open question is whose instruction it is, and it has exactly two answers:
CP's own code running with the problem-state bit wrongly set, or a virtual
machine's `SSM` that CP failed to intercept. Two facts bear on it and they point
different ways. `GR03 = 00FFC000` is the segment-table address, which is CP's own
table-walking idiom. But **CP emits no console messages at all** in this run — no
`DMKCPI957I`, no `DMKCPI966I` — so it has not finished initialising, and running
a virtual machine before announcing initialisation would be surprising.

`X'6D130'` is 436 KB in. The pre-conversion nucleus was 336 KB, but the
conversion grew CP's tables substantially — page tables from 32 bytes to 1024,
`PAGBMP` from 1048 to 3136 — so the address being past the old nucleus end is not
evidence either way until the new nucleus size is read from this build rather
than remembered from the last one.

## Wall 12 — not CP's: the build environment is reclaimed mid-run

Recorded here because it is what stopped progress on 1 October afternoon, and
because mistaking an environmental failure for a CP one is how a day goes.

Three verification builds died at 13 minutes, 4 minutes and 9 minutes, each
taking Hercules, the `nohup`'d driver and (the third time) the liveness watcher
together, each leaving a log that ends on a normal `Ready;` with no error. Memory
was 7.5 GB of 8 GB free, disk had 22 GB, the kernel log showed no kill, and the
Hercules script was complete. I added `setsid`, wrote a watcher, and reasoned
from three deaths and one 70-minute success that background work does not outlive
a foreground call.

**One command settled it, two hours late: `uptime` reported 39 minutes against
five hours of work.** The container is reclaimed and restarted. Files on disk
survive; processes do not. Nothing done to a background job survives that.

Two consequences, both now in the driver:

* **A long build is not a thing to protect, it is a thing to avoid.** `full`
  stages 104 files and assembles 186 modules in about seventy minutes. But the
  staleness report already names exactly what changed since the snapshot — 45
  inputs — and the snapshot holds the rest, so `build.sh spec` stages 49 files and
  assembles the 58 affected modules. `I-146`.
* **A reaped run must not be mistaken for a finished one.** `w()` waits for
  Hercules to *disappear* and returns success when it does, so a reaped run
  reached `chk` and `asmchk` looking healthy — 15 card files of 104, no
  assemblies, and therefore no diagnostics to find. That is a **false pass on the
  verification build for the whole conversion**, not merely lost time.
  `mkrun.incomplete()` now compares the log against `hercules.rc` — the script is
  what the run was *asked* to do — and `chk()` calls it first. `I-144`.

The reclaim is also why the 13:15 build's output no longer exists: each `full`
begins by restoring `SNAP-2`, and three restarts discarded 180 good modules to
redo four one-line fixes. `I-111`'s property, invoked carelessly.

## The estimate, stated honestly

**Revised 18:45 UTC.**

**Group 2 is written and now partly proven.** ~700 cards, 23 modules, 53 decks,
zero undefined-symbol diagnostics where there were 176, 59 modules assembling
clean, and — as of 2 October — **the DAT structures it produces are accepted by
the hardware**: the designation, the segment table and the page tables all pass
ESA/390 translation. What remains unproven is everything that happens after
translation succeeds, which is now where CP fails.

**Group 1 is not a day; it is 95 sites.** 62 storage-key, 33 channel. The
storage-key family is the one piece of this project that can be written **and
tested** before anything else moves, because `ISKE`/`SSKE`/`RRBE` are valid in
S/370 and CE already runs with 4 KB keys. That makes it the obvious next
substantial piece of work, not because it is small but because it is *provable*.

**The largest known item still blocking CP coming up is the `VMSEG` readers** —
92 `L`/`LCTL` sites in 40 modules, of 30 classified 16 needing a mask added and 14
carrying a constant that must change. None is flagged, because `VMSEG` is not
renamed; the remedy is the one that worked for the DAT fields, a second rename
pass with no alias so the assembler enumerates all 105 references.

**And the honest part: expect a wall 13 that is not on this list.** Eleven walls
have been found and every one was invisible until the previous one fell. Three
answers to "how much is left" have now been given and all three were wrong — the
first two by guessing, the third by quoting a document that disagreed with
another document in the same folder. Group 3 is not on the path to a clean IPL,
but two of its items are now sized for the milestones that own them.

**Group 2 is about 229 remaining changes**, and that figure deserves its
caveats. It is the assembler's 139 remaining flagged sites plus ~90 measured
silent candidates; the candidates each need reading, and the scan only knows the
patterns already learned. `DMKBLD` produced two that no rule would have predicted
— `S R9,F4` reaching `PAGSWP` through an assumed four-byte gap, and one
`SRL R1,8` serving both a CORTABLE index and a page-table entry because the two
strides happened to agree at 16. **The estimate is a floor on the reading, not a
ceiling on the work.**

What can be said without inventing a figure: **ten walls have fallen in four
days, nine of them in one day**, and every one was closed by a mechanical sweep
plus one build cycle. Wall 11 is the first that requires a **data-structure
change** rather than an instruction substitution, so it is the first that cannot
be closed by a sweep alone — and that, not the site count, is why it is
different. What replaces the sweep is a rename that makes the assembler the
checklist, and the measured answer is that this covers **45%** of the work. The
other 55% is read, with `block.py` narrowing the reading to one page per module.
