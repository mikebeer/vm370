# The walls between a converted CP and a clean IPL

Started 28 September 2026, rewritten 1 October, **re-measured 1 October (later)**.
Extends **STATE.md** and **BUILD-CYCLE.md**. Read after GOTCHAS.md.

**This file is the version-controlled original; the project's copy is published
from it.** It answers one standing question — *what is between the current status
and an IPL without errors?* — and that answer has now been given three times with
three different numbers, so it belongs somewhere with a diff.

Eleven walls so far. Every one was located to a specific instruction at a
specific address rather than inferred, and **each was only visible once the
previous one fell** — which is the single most useful thing this document
records, because it is also why no estimate of "how much is left" has ever
survived contact.

## The walls, in the order CP hit them

| # | Wall | How it presented | Found by |
|---|---|---|---|
| 1 | The conversion executes, and S/370 rejects it | disabled wait `X'111111'`, `B234` = `STSCH` under `ARCHMODE S/370` | reading the PSW |
| 2 | **BC-mode PSW is a third axis, never counted** | `Invalid IPL PSW: 00040000 00004470` — bit 12 zero | Hercules refused the IPL |
| 3 | The standalone loader is itself S/370 I/O | `9D00 8000` = `TIO 0(R8)` in `DMKLD00E` | PSW at `X'44C2'` |
| 4 | `XAIO` borrowed R15, a `USING` base in 54 modules | interruption code `X'15'`, operand exception | PoP + the trace |
| 5 | Subchannels resolved but never enabled | `MSCH` count 0; cc 3 from every `SSCH` | counting MSCHs in the artifact |
| 6 | The architecture probe clobbered R1 | exactly one device per module failed | register dump |
| 7 | `DMKDMP` took the dump with `ISK` | `DMKDMP905W SYSTEM DUMP FAILURE` | `0934` at the failing address |
| 8 | `SSK` sized storage at **zero**, and FRELOOP ate the nucleus | `C6D9C5C5` (`"FREE"`) every 16 bytes, incl. lowcore | breakpoint + arithmetic |
| 9 | CP executes an ECPS:VM assist *before* probing for assists | `SCNRU` / `STEVL`, operation exception | `pgmtrace`, one run |
| 10 | Our own DSECT grew; the block generator did not | `CPI001` — SYSRES not found | `dumpscan.py` on the dump |
| 11 | **`TRANS` loads an S/370 STD and `LRA` rejects it** | `PRG018` = translation specification | the dump, below |

Walls 1–10 are closed. Detail for each in `docs/13-ISSUES.md`; the entries
worth reading are **I-77**, **I-102**, **I-104**, **I-108**, **I-110**,
**I-114** and **I-116**.

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

## Wall 11, in detail — where CP stops now

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

## What is between here and `DMKCPI966I` — re-measured

The two earlier answers to this question were a guess and a sweep. This one is
the **assembler's**, which is the first version of it that cannot be argued with:
`CORE.XA0033DK` renames every DAT field with no alias, so an unconverted site
fails to assemble. The build of 1 October reported **190 statements flagged
across 186 modules, 176 of them naming a renamed symbol**, and `asmerr.py`
reconciled them against `dattab.py`'s independent sweep:

```
CONFIRMED  176  flagged and predicted
MISSED       0  flagged but NOT predicted -- the sweep has a hole
SILENT      67  predicted but NOT flagged -- no diagnostic exists
```

### Group 1 — known, small, and mechanical: 10 cards

| Module | Sites | What | Fix |
|---|---|---|---|
| `DMKCPI` | 1 | `SIO 0(R15)` at 00485480, a sense to the IPL device | 1 card |
| `DMKPSA` | 4 | `ISK R15,R15` — storage keys in the interrupt handlers | `ISKE`, 4 cards |
| `DMKSAV` | 5 | `SIO`/`TIO` in `QDISK` and the sense path | 5 cards |

Unchanged, and still a day.

### Group 2 — the DAT tables: 176 flagged sites in 16 modules, plus ~90 silent

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

## The estimate, stated honestly

**Group 1 is a day.** Group 3 is not on the path to a clean IPL, but two of its
items are now sized for the milestones that own them.

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
