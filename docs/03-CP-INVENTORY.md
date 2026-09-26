# CP architecture-dependency inventory

Measured 26 September 2026 against Adrian's maintained CE source
(`systems/vmce/source/cp`, 201 `.ASSEMBLE` + 59 `.MACRO` + 56 `.COPY`),
with a statement parser that skips comment lines and takes the opcode from
column 1 or after the label. Supersedes the estimates in 01-PROPOSAL.md §3,
which were made from module counts rather than from reading the code.

Encoding note: these files are clean 80-column records. `DMKVAT` and
`CORE` contain **no** U+E000-encoded control bytes, so the private-use
encoding described in the CE README applies only to some members.

## Headline: the DAT conversion is not a format change

`CORE.COPY` defines `CORTABLE`, `SWPTABLE`, `SEGTABLE` and `PAGTABLE` and
is used by 41 modules. Reading it turns up **two geometry changes and a set
of bit collisions**, none of which are visible from counting references.

### 1. Segment size goes from 64 KB to 1 MB — a 16× change

CP runs 64 KB segments of sixteen 4 KB pages. The evidence is in
`CORE.COPY` itself:

    PAGTSWP  EQU   (PAGCORE-PAGSTMP+16*L'PAGCORE) LENGTH OF A
    *                            FULL 16 ENTRY PAGE TABLE

and confirmed by `DMKCPI`'s `CTLREGS`, which sets `PAGE4K` without
`SEG1M` — the `EQU` COPY member defines `SEG1M EQU X'10'` as CR0 bit 11,
and CP does not set it.

**ESA/390 has only 1 MB segments.** There is no 64 KB option. So this is
not a field-width change, it is a sixteenfold change to CP's virtual
memory geometry:

  - a 16 MB address space needs 16 segment table entries, not 256
  - each page table holds up to 256 entries, not 16
  - `PAGTSWP` and `PAGBMP`, the contiguous page-and-swap-table size
    constants, both change — **65 references**, concentrated in `DMKCFG`
    (21), `DMKPGS` (16) and `DMKATS` (15)

**The sharpest consequence is shared segments.** `DMKATS` is the
shared-segment support and the named-saved-system machinery is built on
64 KB granularity. Under ESA/390 the minimum shareable unit becomes 1 MB.
Every existing saved-system definition changes granularity by 16×, and
anything that shares less than a megabyte has to over-share or be
redesigned. This is a compatibility question, not just an engineering one,
and it deserves Adrian's judgement before anything else in the DAT work.

### 2. Storage key granularity goes from 2 KB to 4 KB

S/370 storage keys cover 2 KB; ESA/390 keys cover 4 KB. CP tracks this
explicitly, per half-page:

    SWPKEY1  DS    1X         S*3 VIRTUAL STORAGE KEY, 1ST 2048 BYTES
    SWPKEY2  DS    1X         S*4 VIRTUAL STORAGE KEY, 2ND 2048 BYTES
    SWPREF1  EQU   X'08'          FIRST HALF PAGE REFERENCED
    SWPCHG1  EQU   X'04'          FIRST HALF PAGE CHANGED
    SWPREF2  EQU   X'02'          SECOND HALF PAGE REFERENCED
    SWPCHG2  EQU   X'01'          SECOND HALF PAGE CHANGED

Under ESA/390 each pair collapses to one. **28 references to the key
fields** (`DMKPTR` 10, `DMKPRV` 6) and **27 to the half-page reference and
change bits** (`DMKPTR` 19). The logic simplifies, but a guest that reads
its own keys through `ISK` expects 2 KB semantics — so this reaches
`DMKPRV`'s privileged-instruction simulation, not only the paging code.

### 3. The page table entry doubles, halfword to fullword

    PAGCORE  DS    1H             REAL PAGE ADDRESS

ESA/390's PTE is a fullword. Every page table doubles in size, and any
code indexing entries by `*2` — a shift of 1 — becomes `*4`. **125
references to the PTE fields**, led by `DMKPTR` (35) and `DMKATS` (21).

`PAGTABLE` also carries a **16-byte CP-private header at negative
offsets** — `PAGSTMP`, `PAGACT`, `PAGTOT`, `PAGSHR`, `PAGSWP` — before the
hardware entries at offset 0. That survives unchanged, which is
convenient: the header is CP's own and the hardware never sees it.

### 4. Segment table entry: every field moves, and two flags collide

    SEGPAGE  DS    1F             POINTER TO PAGE TABLE
             ORG   SEGPAGE
    SEGPLEN  DS    BL.4       S*1 PAGE TABLE LENGTH (NO. PAGES - 1)
    SEGINV   EQU   X'01'          SEGMENT INVALID FLAG
    SEGMIG   EQU   X'10'          SEGMENT MIGRATED (IF POINTER = 0)
    SEGENQ   EQU   X'40'          SEGMENT ENQUEUED (IF POINTER = 0)

| CP / S/370 | ESA/390 |
|---|---|
| `SEGPLEN` bits 0-3, pages less one | `PTL` bits 28-31, 16-entry units less one |
| page table origin bits 8-28 | `PTO` bits 1-25, 64-byte aligned |
| `SEGINV` = `X'01'` | invalid = `X'20'` |
| `SEGMIG` = `X'10'` | **collides with the COMMON SEGMENT bit** |
| `SEGENQ` = `X'40'` | **collides with the lowest `PTO` bit** |

The two collisions are survivable but fragile: CP sets `SEGMIG` and
`SEGENQ` only when the pointer is zero, and the hardware does not examine
other fields of an invalid entry. That needs to become an explicit
invariant rather than an accident, because an entry that is invalid to CP
but valid to the hardware would translate to `X'000000x0'`.

**113 references to the STE fields**, led by `DMKPGS` (36) and `DMKBLD`
(32) — not `DMKVAT`, which has 10.

### The DAT-format-sensitive surface, totalled

    STE fields                          113
    PTE fields                          125
    table-size constants (PAGTSWP/BMP)   65
    2 KB half-page keys                  28
    2 KB half-page reference/change      27
                                       ----
                                        358

Separately, `CORTABLE` (259 references, `DMKPTR` 101) and the rest of
`SWPTABLE` (210, `DMKPTR` 54) are CP's own formats — the hardware never
sees them — but they point at the tables, so entry sizes propagate.

## Statement totals

| Category | Count | Notes |
|---|---|---|
| S/370 I/O instructions | **166** | cross-checks the 165 counted independently in an R6 extraction |
| CAW/CSW-shaped references | **1,493** | the shim surface |
| DAT table field references | **459** | 16 modules; 358 format-sensitive, see above |
| `LCTL` / `STCTL` | 172 / 28 | |
| `LPSW` / `SSM` | 123 / 30 | |
| `LRA` | 76 | |
| `ISK` / `SSK` | 38 / 16 | storage keys, 2 KB → 4 KB |
| `PTLB` / `RRB` | 4 / 13 | |
| `STNSM` / `STOSM` | 5 / 5 | |
| `SPKA` / `SPX` / `STPX` | 10 / 5 / 1 | |
| `SIGP` | 11 | |
| `BAL` / `BALR` | 3,482 / 118 | see the correction below |
| "address packed with flags" | 567 | crude regex, indicative only |

174 of 201 modules touch something architecture-dependent, but most of
those are a single `BAL`.

## Correction: `BAL`/`BALR` largely self-correct

**`BAL` and `BALR` are mode-sensitive in ESA/390.** They place the ILC,
condition code and program mask in bits 0-7 of R1 only when executing in
**24-bit** mode. In 31-bit mode they set bit 0 to zero and put the updated
instruction address in bits 1-31.

So the 3,600 link-register stores are **not** 3,600 things to fix. A module
converted wholesale to run AMODE 31 from entry has its `BAL`/`BALR`
executing in 31-bit mode, and they behave correctly.

The real exposure is **mode boundaries**: a base or link register
established in 24-bit code and used in 31-bit code. That is what broke DAT
step 3 — the `BALR 15,0` ran at entry in 24-bit mode and the register was
used as a base after the `BSM`. And it is where Adrian's `SAVE.COPY`
finding sits: processor identity deliberately overlaying a fullword that
holds a three-byte return address is a boundary problem that no
mode-sensitivity rescues.

## The DAT table surface has different owners than assumed

| Module | Refs | Lines | On the original list? |
|---|---|---|---|
| **DMKPGS** | **96** | 1,322 | **no** |
| **DMKATS** | **73** | 957 | **no** |
| **DMKBLD** | **63** | 1,120 | **no** |
| DMKVAT | 55 | 1,335 | yes |
| DMKPTR | 54 | 2,589 | yes |
| DMKCFG | 49 | — | no |
| DMKVMA | 30 | — | no |
| DMKRPA | 10 | — | no |
| DMKCPP | 7 | — | no |
| DMKCPI | 6 | — | no |
| DMKMCH | 4 | — | no |
| DMKCPU | 4 | — | no |

Top five = 341 of 459, 74%. Sixteen modules in total.

**`DMKPGS`, `DMKATS` and `DMKBLD` are each larger consumers of these
fields than `DMKVAT`**, and none was in the proposal. `DMKPGS` is
page/segment management, `DMKATS` is shared-segment support, `DMKBLD`
builds control blocks including the ECBLOK.

**`DMKPAG` is resolved and is not a gap.** It is 1,349 lines of paging
*device* code — its own symbols are `PAGEIOB`, `PAGECYL`, `PAGESRCD`,
`PAGERW`, `PAGESK` — and it touches `SWPTABLE` only for DASD addresses
(`SWPCYL`, `SWPDPAGE`, `SWPCODE`). It is in scope for the **I/O**
conversion, not the DAT one. The table side of paging is `DMKPTR`.

## Where the I/O work concentrates

Highest S/370 I/O instruction counts:

    DMKCKP    25      checkpoint            nucleus
    DMKFMT    22      formatter             STAND-ALONE
    DMKDMP    22      dump                  STAND-ALONE
    DMKCPI    21      initialisation        nucleus
    DMKLD00E  19      loader                STAND-ALONE
    DMKIOS    10      real I/O supervisor   nucleus
    DMKIOT     5      I/O interrupt         nucleus
    DMKDIR     5      directory             STAND-ALONE
    DMKDDR     3      DASD dump/restore     STAND-ALONE

Highest CAW/CSW reference counts:

    DMKFMT   114  (stand-alone)   DMKIOT    89
    DMKIOS    67                  DMKVSP    68
    DMKDDR    44  (stand-alone)   DMKDMP    34  (stand-alone)
    DMKCKP    32                  DMKDIR    32  (stand-alone)

The stand-alone utilities carry a large share of both. They are not needed
to boot, so milestone 1 can ignore `DMKFMT`, `DMKDMP`, `DMKLD00E`,
`DMKDIR` and `DMKDDR` entirely — roughly 71 of the 166 I/O instructions
and 224 of the 1,493 CAW/CSW references.

## Method and limits

Statement parsing: comment lines (`*`, `.`) skipped; opcode taken from the
first blank-delimited field when column 1 is blank, otherwise the second
field. Columns beyond 71 ignored. **This does not handle macro-generated
statements**, so instructions emitted by macros are invisible to the
count — a real undercount of unknown size, and CP's `CALL`/`RETURN` macros
certainly hide linkage. The largest known instance is `TRANS`, invoked 174
times, which carries `LCTL`, `LRA` and a conditional branch each time.

The "address packed with flags" figure searches for `ICM`/`STCM` with a
3-byte mask, `AL3(` constants, and `=X'00FFFFFF'` / `=X'FF000000'`
literals. It will have false positives and will miss hand-rolled cases.
**567 is indicative, not a work estimate**, and it is the category most
likely to be badly wrong in either direction. On inspection the real
population is 582 `ICM`/`STCM` sites with a 3-byte mask; the 421 `AL3`
sites are mostly format-0 CCW templates and CAW stores, which do not
change.
