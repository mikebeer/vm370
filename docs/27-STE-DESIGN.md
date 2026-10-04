# The DAT table conversion for a clean IPL — design

> **Status, 4 October 2026.** Built, and past wall 11 by a long way: the tables designed here (CORE XA0033DK, EQU XA0037DK, DMKBLD XA0034DK, the XA0036DK sweep) carry CP through IPL from DASD and CMS to `Ready;`, with named systems shared at frame granularity (M3c, [33-FRAME-SHARING.md](33-FRAME-SHARING.md)); walls 11–29 are closed in [28-IPL-WALLS.md](28-IPL-WALLS.md). Three things the design did not have: `DMKBLDRT`'s packed R1 is two 16-bit page numbers, so the ceiling is 256 MB and `DEF STOR 32M`/`64M` now work (`I-185`, `I-203`); `DMKPTR SEGEXA` and `DMKPGS CKSEG` still carried 64 KB arithmetic after the sweep (`I-196`, `I-206`); and `DMKCFG`'s shared-segment path indexed the new table with 64 KB segment numbers (`I-195`). §1's "milestone B" is M2's open half: ledger test 8 has now been measured — a store at `s1ff0000` lands at `ff0000` because CP runs AMODE 24 (`I-208`, [13-ISSUES.md](13-ISSUES.md)) — and §6's 215 strip sites (`I-126`) are that work. The bit layouts, the flag analysis, the alignment idiom and the order of work stand; [30-STATE.md](30-STATE.md) has the position.

1 October 2026. This is **wall 11** of `IPL-WALLS.md`, where CP stops today:
`PRG018`, a translation-specification exception, raised by `TRANS`'s `LRA`
against a System/370 segment table. *(superseded — see status note)*

Every bit position below is quoted from **SA22-7201-08**, not recalled. That
matters more here than anywhere else in the conversion, because a wrong bit
position produces a translation-specification exception that looks exactly like
the one we already have.

**This file is the version-controlled original; the project's copy is published
from it.** It lived only as a project doc for its first half-day, which meant its
corrections had no diff and no history — and this is a document that has been
wrong three times. Three sections were wrong when first written and are corrected
in place, each marked: **§4a** (the alignment work has no precedent — it does),
**§5 step 1** (changing the DSECT first is safe — it is not), and **§4c**'s swap
header arithmetic. They are kept visible because the pattern — a confident claim
about the source that the source contradicts — is the most expensive recurring
mistake in this project.

---

## 1. The scope question, answered: days, not weeks

`WHAT-31BIT-NEEDS.md` names `DMKBLDRT`'s interface the largest undesigned item,
and `IPL-WALLS.md` made the first job finding out whether a clean IPL needs it
**widened** — an ABI change across 24 callers — or only **reinterpreted**. It
needs neither. DMKCPI's own call site settles it:

    CL    R1,=A(X'FFF000') STORAGE OVER 16M VIRTUAL?      @VA11813
    BNH   VBUFFOK        NO WE ARE OK
    L     R1,=A(X'FFF000') SET VIRTUAL STOR TO 16M        @VA11813
    ...
    ST    R1,VMSIZE           SAVE SIZE IN SYSTEM'S VMBLOK.
    SRL   R1,12          BEGIN/ENDING VALUE FOR TABLES    @V304635
    BCTR  R1,R0          MINUS 1 PAGE (BLD WILL COMPENSATE)
    CALL  DMKBLDRT,PARM=NEWSEGS+NEWPAGES

**CP caps its own virtual size at 16 MB** and passes `(size >> 12) - 1` — a page
number, 0…4094, which fits the twelve bits `DMKBLDRT` masks with `N R5,F4095`.
A 12-bit page number expresses 16 MB whatever the segment size is, so the packed
fullword is unchanged. **The ABI widening belongs to milestone B, where a guest
exceeds 16 MB — not to a clean IPL.**

Two further simplifications fall out, and both cut the work down:

* **`TRANS.MACRO` itself needs no change.** Its expansion is
  `LCTL C1,C1,VMSEG` / `LRA` / condition-code branches, and `LRA` is valid in
  ESA/390. It fails today because the *data* is System/370, not because the
  instruction is. So the **174 `TRANS` sites across 66 modules are not in
  scope.** What eventually breaks `TRANS` is AMODE 24 against an above-the-line
  address — ledger test 8 — and that is milestone B.
* **The 358 format-sensitive references are not all in scope either.** Only the
  code that *writes* the tables CP builds for itself during initialisation has
  to change now: `DMKBLDRT`, and the field definitions in `CORE.COPY`.

The estimate in this heading — *days, not weeks* — was withdrawn in `I-121` once
the sweep ran. 176 sites in 16 modules is not a day's work.

---

## 2. The three formats, from the Principles of Operation

### Segment-table designation — what `VMSEG` holds and `LCTL C1,C1` loads

    ┌─┬────────────────────┬───┬─┬─┬───────┐
    │ │Segment-Table Origin│   │P│S│  STL  │
    └─┴────────────────────┴───┴─┴─┴───────┘
     0 1                 19      23 24 25 31

* **STO: bits 1-19**, twelve zeros appended — the segment table sits on a
  **4096-byte boundary**.
* P bit 23 (private space), S bit 24 (storage-alteration event).
* **STL: bits 25-31**, in units of 64 bytes.

System/370 put the length in **bits 0-7** and the origin in bits 8-25, and CP
writes exactly that, in two instructions:

    SKIPFRET ST    R6,VMSEG       STORE NEW SEGTABLE POINTER
             STC   R15,VMSEG      AND STORE IN LEFTMOST BYTE OF VMSEG.

So **both halves move**, and the alignment requirement is new.

### Segment-table entry

    ┌─┬─────────────────────────┬─┬─┬────┐
    │ │    Page-Table Origin    │I│C│PTL │
    └─┴─────────────────────────┴─┴─┴────┘
     0 1                      25 26 27 28 31

* **Bit 0 must be zero**; *"if it is not zero, a translation-specification
  exception is recognized."* **This is precisely our current failure** — CP's
  entries read `F00561D0`, and that `F` is `SEGPLEN`.
* **PTO: bits 1-25**, six zeros appended — page tables on a **64-byte boundary**.
* **I: bit 26** (segment invalid), **C: bit 27** (common segment),
  **PTL: bits 28-31**.

### Page-table entry — and it becomes a fullword

    ┌─┬───────────────────┬─┬─┬─┬─┬────────┐
    │ │       PFRA        │ │I│P│ │        │
    └─┴───────────────────┴─┴─┴─┴─┴────────┘
     0 1                19 20 21 22 23 24 31

* **PFRA: bits 1-19**; **I: bit 21**; **P: bit 22**.
* **Bits 0, 20 and 23 must be zero**; bits 24-31 are ignored.

Two consequences of the PFRA's position that make the conversion easier than it
looks. A page-table entry's value masked with `X'7FFFF000'` **is the real
address of the page frame** — not a page number to be shifted — and the same is
true of an STE: masked with `X'7FFFFFC0'` it is the real address of the page
table. So `ST` of an aligned address is the whole job on both, where System/370
needed the address pre-shifted into a narrower field.

### Sizes, for the 16 MB space CP gives itself

| | System/370 | ESA/390 |
|---|---|---|
| segment size | 64 KB, 16 pages | **1 MB, 256 pages** |
| segments in 16 MB | 256 | **16** |
| segment table | 1024 bytes, 64-byte aligned | **64 bytes, 4096-byte aligned** |
| page table | 16 halfwords = 32 bytes, 8-byte aligned | **256 fullwords = 1024 bytes, 64-byte aligned** |
| tables for 16 MB | ~9 KB | **~16 KB** |

One pleasing accident: a full page table's length code is **15 in both
architectures** — `SEGPLEN` is "no. pages − 1" = 15 for 16 pages, and ESA/390's
`PTL` for 256 pages is also 15, because `PTL` counts in units of 16 entries. The
*value* survives; only its bit position moves, from bits 0-3 to 28-31.

---

## 3. The flag collision, and why it is already solved

`CORE.COPY` defines three CP-private flags inside the fullword `SEGPAGE`:

| Flag | Value in `SEGPAGE+3` | Bit | ESA/390 meaning |
|---|---|---|---|
| `SEGINV` | `X'01'` | 31 | part of `PTL` |
| `SEGMIG` | `X'10'` | 27 | **C — common segment** |
| `SEGENQ` | `X'40'` | 25 | **lowest bit of `PTO`** |

All three collide, which is undesigned item 2 of `WHAT-31BIT-NEEDS.md`. But the
project already holds the measurement that resolves it: with the invalid bit set,
`X'00000070'` *is* correctly segment-invalid, while without it `X'00000050'` is a
valid common segment with page-table origin `X'40'`, and the hardware walks a
page table on top of the CSW.

And `CORE.COPY` says when the flags are meaningful: *"(IF POINTER = 0)"*. They
are read only when there is no page table — that is, when the segment is
**invalid anyway**. So:

> **Set `I` (bit 26, `X'20'` in byte 3) on every entry that is not present, and
> leave `SEGMIG` and `SEGENQ` where they are.** With `I` on, the hardware does
> not interpret `PTO`, `C` or `PTL`, so the two CP flags keep their bit positions
> and their meanings.

The one flag that must move is **`SEGINV`**: `X'01'` lies inside `PTL`, and the
bit the hardware now reads is 26. `SEGINV` becomes `X'20'`.

**Bit 0 must still be vacated**, which is what forces `SEGPLEN` out of bits 0-3
regardless of everything above.

`SEGMIG` turns out not to be part of the problem at all: `dattab.py` found it
**defined in `CORE.COPY` and referenced nowhere else in the tree** — not in a
module, not in a `COPY`, not in a `MACRO`. It is a dead symbol, and half of
undesigned item 2 does not exist.

---

## 4. What has to change

| Where | Change |
|---|---|
| `CORE.COPY` `SEGTABLE` | `SEGPLEN` bits 0-3 → `PTL` bits 28-31; `SEGINV` `X'01'` → `X'20'`; document `SEGMIG`/`SEGENQ` as valid only with `I` set |
| `CORE.COPY` `PAGTABLE` | `PAGCORE` halfword → fullword; `PAGINVAL` → bit 21; `PAGTSWP` 16 entries → 256; a new `PAGFREE` holding the `DMKFREE` address |
| `PAGTBL.MACRO` | `DC &NP.H'8'` → a fullword invalid PTE — the generator half, `I-125` |
| `DMKBLDRT` | the segment-table **length** arithmetic (`SRDL R0,8`), pages-per-segment, `STC R15,VMSEG` → `STL` in bits 25-31, and the new alignments |
| `DMKBLD` elsewhere | `ICM R0,B'0110',SEGPAGE+1`, `TM SEGPAGE+3,…`, `SLL R3,2` index arithmetic |

`R01-SHIFT-SITES.md` already enumerates the shift constants with module, line and
sequence number: **4 → 8** (16 pages/segment → 256), **16 → 20** (64 KB → 1 MB
segment), **6 → 10** (×64-byte page table). Those three apply here. Shift 12
stays 12, because pages remain 4 KB.

---

## 4a. Alignment — corrected: the precedent is in the same routine pair

This section first read: *"no existing site expresses it, so it is the part of
this work with no precedent in the source."* **Both halves of that were wrong.**
`DMKBLDRT` already over-allocates, rounds up, and records the displacement, and
`DMKBLDRL` already undoes it:

    COMPPAGE SLL   R0,3        8 DBL-WORDS NEEDED FOR EACH 64-BYTE SEG.
             AL    R0,F7       PLUS 7 TO ENSURE 64-BYTE ALIGNMENT
             CALL  DMKFREE     GET SPACE FOR REAL SEGMENT TABLES
             LA    R6,63(,R1)  ROUND UP TO NEXT 64-BYTE BOUNDARY
             N     R6,=A(X'FFFFC0')
             ST    R1,SAVEWRK1 SAVE REAL BEGINING OF NEW
             ...
             S     R15,SAVEWRK1
             STH   R15,VMSEGDSP   SAVE IN VMBLOK      <-- the displacement is KEPT

    (DMKBLDRL)
             LA    R1,0(,R1)   STRIP OFF HIGH-ORDER BYTE
             SH    R1,VMSEGDSP GET THE REAL BEGINNING OF IT
             SRL   R0,24       OBTAIN NO. OF SEGMENT TABLES (LESS 1)
             SLL   R0,3        TIMES 8, FOR 8 DBL-WORDS EACH
             AL    R0,F15      PLUS 8, PLUS 7 FOR ALIGNMENT
             CALL  DMKFRET

So the mechanism to design was already designed in 1979, for the same table, by
the same pair of routines. The segment table's conversion is a **generalization
of a working idiom from 64 to 4096**, not a new invention:

| | today | ESA/390 |
|---|---|---|
| pages → table units | `SRDL R0,8` (1 MB per 64-byte unit) | `SRDL R0,12` (**16 MB** per 64-byte unit) |
| units → doublewords | `SLL R0,3` | unchanged — still 8 doublewords per unit |
| alignment slack | `AL R0,F7` (56 bytes) | `AL R0,F511` (**4088 bytes**) |
| round up | `LA R6,63(,R1)` / `N R6,=A(X'FFFFC0')` | `LA R6,4095(,R1)` / `N R6,=A(X'FFF000')` |
| release size | `AL R0,F15` (8 + 7) | `AL R0,F519` (8 + 511) |
| displacement store | `STH R15,VMSEGDSP` | unchanged — 4088 fits a halfword, **the VMBLOK does not change** |

`LA R6,4095(,R1)` is legal: 4095 is the largest displacement the instruction
can encode, and the requirement happens to be exactly that. `=A(X'FFF000')`
already exists as a literal in `DMKCPI`.

**`STC R15,VMSEG` needs no change at all.** ESA/390's STL is "length in units of
64 bytes, minus one" — the same units and the same encoding CP already writes.
Only the *meaning* of a unit changes, 1 MB → 16 MB. For a 16 MB CP the segment
table is 64 bytes and **STL = 0**.

### The page table is the part with no precedent

`DMKBLDRT`'s page-table allocation has **no** alignment logic, and correctly so:

    BLDRP16  LA    R0,PAGBMP   LOAD SIZE OF PAGE AND SWPTABLES
             SRL   R0,3        OBTAIN NUMBER OF DOUBLEWORDS
             CALL  DMKFREE     PAGE AND SWAP TABLE
             LR    R7,R1       PAGETABLE HEADER

A System/370 page table needs 8-byte alignment (its `PTO` is bits 8-28, three
zeros appended) and `DMKFREE` gives doublewords. `DMKFRE`'s documented contract
is *"number of double words desired"* → *"address of the free space obtained"*
and promises nothing more; `MAXSPSIZ` is 30 doublewords, so an ESA/390 page+swap
block takes the general path, where the address is first-fit and doubleword
aligned. **ESA/390 needs 64, so this allocation needs rounding that has never
existed here.**

`DMKBLDRL` recovers the block by arithmetic:

    L     R1,SEGPAGE     GET PAGETABLE POINTER
    N     R1,=A(X'FFFFFE') CLEAR POSSIBLE INVALID BIT
    S     R1,F16         BACK-UP TO START OF CORE FOR TABLES

That works only because the gap between the `DMKFREE` address and `PAGCORE` is
the constant 16. Rounding makes it vary from 0 to 56, so the arithmetic breaks.
Rather than add a second displacement field, **add a header fullword holding the
`DMKFREE` address itself**, so the release becomes `L R1,PAGFREE` with no
arithmetic at all. Three reasons it is the better of the two:

1. It is exact rather than derived, so it cannot drift out of step with the
   allocation the way `F7`/`F15` must be kept in step.
2. It removes `N R1,=A(X'FFFFFE')`, which is **a 24-bit assumption disguised as a
   flag mask** — it clears the System/370 invalid bit *and* truncates a
   page-table address to 24 bits (`I-122`).
3. Every use of the literal 16 becomes `PAGCORE-PAGSTMP`, which the assembler
   checks.

### The STE is better built in a register than patched in storage

Today `DMKBLDRT` writes the entry in three steps:

    ST    R2,SEGPAGE     STORE IN SEGTABLE
    STC   R15,SEGPLEN    AND SAVE IN SEGTABLE   (length into bits 0-3)
    OI    SEGPAGE+3,SEGINV

In ESA/390 byte 3 of the entry holds **two `PTO` bits** (24-25) as well as I, C
and `PTL`, so a `STC` into it would destroy part of the page-table address
whenever that address exceeds 64 × 2²⁴. Building the whole word in a register
and storing it once is both shorter and immune to that:

    OR    R2,R15         ADDRESS, PTL AND I IN ONE WORD
    ST    R2,SEGPTO      ONE STORE, NO READ-MODIFY-WRITE

---

## 4b. What the assembler said: 176 flagged, 176 predicted, 0 holes

`CORE.XA0033DK` renames the fields **without aliases** so that the assembler
becomes the checklist (`I-121`). The build of 1 October ran expecting about 154
errors and reported **190 statements flagged across 186 modules**, of which
**176 name a renamed symbol**. `asmerr.py` reconciled them against the sweep:

```
CONFIRMED  176  flagged and predicted
MISSED       0  flagged but NOT predicted -- the sweep has a hole
SILENT      67  predicted but NOT flagged -- no diagnostic exists
```

The sweep had no holes, and the per-module distribution is the work plan:

| module | flagged | module | flagged |
|---|---|---|---|
| `DMKBLD` | 37 | `DMKCPP` | 6 |
| `DMKPGS` | 31 | `DMKRPA` | 6 |
| `DMKPTR` | 31 | `DMKCPI` | 5 |
| `DMKATS` | 23 | `DMKMCH` | 4 |
| `DMKCFG` | 16 | `DMKCDS` | 2 |
| `DMKVMA` | 13 | `DMKCFH`, `DMKVMD` | 1 each |

Two behaviours of the assembler were learned from this and are worth carrying:

* **A redefined `EQU` is not entirely silent.** `PAGBMP` grows from 192 to 3104
  bytes, so `MVC PAGTABLE(PAGBMP),0(R10)` exceeds `MVC`'s 256-byte length and
  `LA R0,PAGBMP+PAGBMP` exceeds the 4095-byte displacement — `IFO224` and
  `IFO208`. The *consequences* of the new value are reportable even though the
  value itself is not.
* **A symbol used only inside a literal is reported against the literal pool.**
  `DMKCFG`'s `N R10,=AL4(X'FFFFFFFF'-SEGINV)` produces exactly one diagnostic,
  on a generated statement with a **blank sequence number**. The assembler flags
  a site it can give you no line for; the sweep has the line and not the symbol.
  Neither list alone is sufficient, which is the argument for having both.

---

## 4c. What the coarser granularity costs: 3%

A page+swap block is `PAGBMP` bytes, and `PAGBMP` is a computed `EQU`:

    PAGTSWP EQU (PAGCORE-PAGSTMP+16*L'PAGCORE)
    PAGBMP  EQU (PAGTSWP+(SWPFLAG-SWPVM)+16*(SWPCODE-SWPFLAG+1)+8)

**Corrected (`I-127`): the `SWPTABLE` header is 8 bytes, not 12.** The field list
reads `SWPVM DS 1F` / `SWPFLAG2 DS 1X` / `SWPPAG DS 1F`, from which
`SWPFLAG-SWPVM` looks like 12 — but the line between them is `ORG SWPFLAG2`,
which returns the location counter to 4. `DMKBLDRT`'s own
`LA R9,PAGCORE+16*2+8  ADDRESS OF 1ST SWAPTABLE` states the header size plainly
and was read without being believed. **A list of declarations is not a DSECT**:
`ORG`, `CNOP` and alignment all move fields, and only the generated offset is
authoritative.

| | today, per 64 KB segment | ESA/390, per 1 MB segment |
|---|---|---|
| `PAGTABLE` header | 16 | 16 |
| page table | 16 × 2 = 32 | 256 × 4 = **1024** |
| `SWPTABLE` header | 8 | 8 |
| swap table | 16 × 8 = 128 | 256 × 8 = **2048** |
| spare doubleword | 8 | 8 |
| **`PAGBMP`** | **192** = 24 doublewords exactly | **3104** = 388 doublewords exactly |
| + alignment slack | — | + 7 → **395** |
| **bytes per megabyte** | 16 × 192 = **3072** | **3160** |

**A 2.9% increase.** The allocation granularity gets coarser — the smallest
virtual machine's tables grow from 192 bytes to 3160 — but the total for a real
virtual machine is essentially unchanged. The existing "fewer than 16 pages →
short table" path (`FORCE16`, `CLI SEGPLEN,X'F0'`) generalizes to 256 and would
recover the small-machine case later; it is not needed for a clean IPL.

A second claim retracted with the header size: the trailing `+8` in `PAGBMP` was
described as slack absorbing a truncating `SRL R0,3`. `PAGBMP` is an exact
multiple of 8 in **both** architectures, so there is no truncation to absorb and
the `+8` is simply one spare doubleword.

---

## 5. Order of work — corrected: step 1 was not a safe first step

This section first read: *"`CORE.COPY`'s `SEGTABLE` and `PAGTABLE`, with `SEGINV`
moved. **Nothing executes differently yet**; this makes the symbols mean the
right thing."* The second clause was wrong, and it was the dangerous kind of
wrong. `PAGCORE` goes from a halfword to a fullword and CP reaches it with 13
`LH` and 5 `STH` instructions. Change the DSECT alone and each of those silently
accesses the wrong two bytes of a fullword — **and assembles clean**, because
`LH` on a fullword field is legal assembler. That is `I-116`'s shape with two
orders of magnitude more places to hide.

1. **Sweep first** (`dattab.py`), then **rename without aliases**
   (`CORE.XA0033DK`) so the assembler itself reports every site that reads a
   renamed field. `asmerr.py` reconciles the two lists. **Done — §4b.**
2. The alignment design — **§4a**, now that the precedent is known. **Done.**
3. `DMKBLDRT`'s arithmetic and the entries it writes, including
   `MVC PAGCORE+2(15*2),PAGCORE`, which becomes 255 × 4 = 1020 bytes and
   **cannot be one `MVC`**. Then the other 15 modules, in flagged-count order.
4. Rebuild, then IPL **on both engines**. The expected next result is *not* a
   clean IPL — it is a **different** failure, because the first `LRA` will
   succeed and CP will get further. Each wall has hidden the next one, and
   budgeting for that has been more accurate than any estimate of what remains.

### The 67 sites no diagnostic can reach

The rename makes the assembler the checklist for 109 of the 176 sites. It is
blind to the rest **by construction**, and naming them is the difference between
a gap and a surprise:

| field | sites | why no diagnostic fires |
|---|---|---|
| `SHRPAGE` | 31 | a separate declaration in `SHRTABLE.COPY`; renaming `SEGPAGE` does not reach it |
| `PAGBMP` / `PAGTSWP` | 26 | `EQU` arithmetic changed underneath every use |
| `PAGCORE`, `SEGINV`, others | 10 | in a module the rename reached only partly |

A fourth class has no field name at all and so appears in neither list:
arithmetic adjacent to a flagged site (`I-124`). `DMKBLDRT`'s quiesce loop is the
specimen —

    A     R1,=A(X'10000') NEXT VIRTUAL SEGMENT ADDRESS   <-- becomes X'100000'
    LA    R8,4(,R8)       NEXT STE ADDRESS               <-- stays 4

— two consecutive instructions, one of which must change and one of which must
not, and neither names a DAT field. The only mechanical defence is to read the
whole basic block around every flagged site, which is bounded: 16 modules.

---

## 6. Found while writing the cards: the strip-the-flags idiom, 215 sites

`DMKBLD`'s VIRT=REAL builder contains

    L     R8,SEGPAGE     LOAD ADDRESS OF PAGE TABLE
    LA    R8,0(,R8)      CLEAR OUT NUMBER OF PAGES

`LA Rn,0(,Rn)` is CP's idiom for stripping flags from a packed pointer, and it
works in System/370 because the flags live in the high byte and `LA` zeroes bits
0-7. **In ESA/390 what `LA` clears depends on AMODE**: bits 0-7 in AMODE 24,
**bit 0 only in AMODE 31**. In 31-bit mode the instruction strips nothing.

Counted across `DMK*.ASSEMBLE`: **215 self-strip sites in 79 modules**, 152 of
them with a comment saying strip, clear, flag, length or without. The longhand
relatives add about 25 more: `=X'00FFFFF8'` (5), `=X'00FFFFF0'` (3),
`=X'00FFFFC0'` (3), `=X'00FF0000'` (3), and `I-122`'s `=A(X'FFFFFE')`.

This is `I-126`, and the reason it is recorded rather than fixed is the shape of
its failure, not its size:

* **Invisible in M1.** CP runs AMODE 24 through a clean IPL, so all 215 behave
  exactly as today. No diagnostic exists and no test can fail.
* **Simultaneous in M2.** The instant the PSW goes AMODE 31, 215 strips become
  no-ops in 79 modules at once — the hardest possible shape to bisect.
* **In none of the existing enumerations.** `R01-SHIFT-SITES.md` counts shift
  constants; `dattab.py` counts DAT-field references; the 358 figure counts
  format-sensitive table accesses. This is an *instruction idiom*, and no sweep
  in this project looks for idioms.

It belongs on **M2**'s ledger, whose estimate was made without it. Converting 215
sites before CP can boot would be the wrong order.

---

Every step is checkable from the artifact rather than by reading: `dumpscan.py`
reads CP's own dump, so the segment table at the address in `CR1` can be
inspected directly, and a correct STE is recognisable at a glance — **bit 0
zero** is the whole test for the failure we have now.
