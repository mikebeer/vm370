# The DAT conversion: what it took, and how the sites were found

1 October 2026. Companion to `27-STE-DESIGN.md`, which is the design. This is
the **method and the measurements** — written while the verification build runs,
so it records what was done and not whether it worked.

Converting CP's segment and page tables from System/370 to ESA/390 touched
**23 modules** and about **700 cards**. The interesting part is not the size. It
is that the assembler could only see **109 of the 232 sites**, and the other 123
were found by four instruments built one after another, each because the previous
one had just been proved blind.

---

## 1. The one structural fact everything follows from

System/370 packs lengths and flags into the **high byte** of a pointer, and
24-bit address formation **ignores** bits 0-7 of a base register. So a packed
word is usable as an address with nothing to strip:

    L     R3,VMSEG       GET SEGTABLE ORIGIN     (length in byte 0)
    LA    R6,0(R3,R6)    POINT TO 1ST STE        (byte 0 ignored)

ESA/390 moves those fields to the **low** bits — STL at 25-31, STE flags at
26-31, PTE flags at 21-22 — which address formation never ignores. **Every
packed pointer therefore needs an explicit mask where it needed none**, and
AMODE 24 does not help, because the bits that stop being ignored are the low
ones. That is `I-128`, and it is the reason most of this work is invisible.

A second consequence, smaller but everywhere: `LA Rn,0(,Rn)`, which CP uses as
*strip the flags*, is documented in `DMKPGS` as what it actually is —

    LA    R3,0(,R3)      24 BIT ADDRESSING

— and in AMODE 31 it clears only bit 0. 215 sites, 79 modules, `I-126`, and
deliberately **not** converted: it is invisible in M1 and simultaneous in M2.

---

## 2. Four instruments, each built because the last one went blind

| instrument | finds a site by | found | blind to |
|---|---|---|---|
| the **assembler** | it NAMES a renamed field | 109 | anything reached by displacement or literal |
| `dattab.py` | its LINE mentions a DAT field | 176 predicted | arithmetic on the next line |
| `block.py` | it SITS NEAR a flagged site | the basic block | a module with no flagged site at all |
| `idiom.py` | it IS a known idiom | 207, 150 in M1 | an idiom not yet learned |

The sequence matters. `CORE.XA0033DK` renames every DAT field **with no alias**,
so the assembler reports each site that names one — `I-121`'s whole point, and it
worked: the build of 1 October flagged 176 statements and `asmerr.py` reconciled
them against `dattab.py`'s independent sweep with **zero holes in either**.

Then `DMKBLD` was converted and measured: **37 sites the assembler named, 46 it
could not.** 45%. That number is the justification for everything after it.

`block.py` exists because `I-124` concluded the only defence against a converted
field's neighbours is to read the whole basic block — and discipline is what this
project keeps finding it cannot rely on. It prints the block and marks the
neighbours matching a known-silent pattern.

`idiom.py` exists because `I-134` broke all three at once: 33 sites reaching the
page-table header through the literal `F16`, one of them in `DMKVAT`, which has
no flagged site for `block.py` to anchor on.

---

## 3. The fourteen idiom classes, and where each came from

Every class is here because a specific site taught it. The list is a record of
what had already been missed, not a theory of what could be.

| class | sites | taught by |
|---|---|---|
| `F16-header` | 33 | `DMKATS`'s `S R2,F16  BACKUP TO HEADER` |
| `vmseg-load` | 30 | `DMKBLD` 00297000, `L R6,VMSEG` with no mask |
| `pack3` | 29 | `DMKCPI`'s `STCM R8,B'0111',CORSWPNT+1` |
| `strip` | 28 | `DMKPGS`'s `LA R3,0(,R3)  24 BIT ADDRESSING` |
| `cortable-index` | 19 | `DMKCPP` 54000000, a PTE used as a CORTABLE index |
| `F4-swap` | 15 | `DMKBLD`'s `S R9,F4` reaching `PAGSWP` |
| `vmseg-add` | 13 | `DMKCFG`'s `AL R7,VMSEG`, which `vmseg-load` missed |
| `vmseg-len` | 10 | `IC Rn,VMSEG` reading the length from byte 0 |
| `seglen-shift` | 8 | `DMKATS`'s `SRL R3,28` extracting `SEGPLEN` |
| `addr-split` | 7 | `DMKCFH`'s `SRDL R0,16`, which no `SRL` pattern matched |
| `F8-shrptr` | 6 | `DMKPGS` 00425000, `F8` reaching `PAGSHR` |
| `pagtswp-lit` | 6 | `DMKBLD`'s `PAGCORE+16*2` |
| `F2-stride` | 3 | a halfword PTE stride |
| **total** | **207** | **150 live in M1** |

**The classes kept arriving, and the module count went 16 → 17 → 19 → 20 → 23.**
It never converged, because each class was discovered by reading a module not yet
read, and each new class found sites in modules nothing else had flagged.

What *did* converge is the shape. Every one of the last five classes is the same
thing: **a quantity that was free to be sloppy because System/370 ignored the
high byte, and is load-bearing now that ESA/390 uses the low bits.**

---

## 4. The numeric coincidences, which are the real difficulty

A rename is mechanical. What is not mechanical is the places where two unrelated
quantities happened to be equal in System/370 and are not in ESA/390. Each had
to be found by reading, and each would have assembled clean.

**A PTE that is also a CORTABLE index.** A halfword PTE *is* `frame × 16`, and a
CORTABLE entry is 16 bytes per page, so the masked PTE is already the index.
`DMKVMA` says it outright:

    LH    R7,PAGCORE     LOAD PAGTABLE ENTRY
    N     R7,RESMASK     CLEAR UNWANTED BITS
    LR    R2,R7          PTE TO R2
    AL    R7,ACORETBL    GET ADDR OF CORTABLE ENTRY
    SLL   R2,8           FORM REAL ADDRESS

One load, two uses, and the conversion goes in **opposite directions** four lines
apart: the shift is removed on the R2 path and an `SRL R7,8` added on the other.

**A byte comparison that tests for the end of a page table.** `DMKPGS`:

    CKSEG    CLM   R1,B'0010',SEGPAGE TEST FOR LAST PAGE

Byte 2 of a page-aligned virtual address is `page-within-segment × 16`. Byte 0 of
a System/370 STE is `(pages−1) × 16`. The same encoding by accident. In ESA/390
nothing lines up and it becomes ten instructions.

**A double shift that splits the designation.** Also `DMKPGS`:

    SLDL  R2,8           NUMBER OF SEGMENTS INTO R2
    SRL   R3,8           ADJUST TO 24 BIT ADDRESSING

One instruction pair extracting both halves of `VMSEG`, which works only because
the length is the high byte.

**One shift serving two strides.** `DMKCPI`'s `R4` holds `X'10'` because it is
both the `BXLE` increment for a 16-byte CORTABLE entry *and* the step of a
System/370 PTE. `DMKBLD`'s `SRL R1,8` is both a CORTABLE index and a PTE.

**And one piece of 1979 craftsmanship that made the conversion possible to get
right by reading.** `DMKBLDRT` writes

    SLL   R1,4+4         SEGMENT COUNT * 16

as a *sum*, because the two shifts mean different things — units to segments,
then segments to pages. The first 4 stays and the second becomes 8. Written as
`SLL R1,8` it would have been impossible to convert correctly, and
`R01-SHIFT-SITES.md`'s "4 → 8" rule would have changed the wrong half.

---

## 5. Values the source wrote out instead of deriving

Nine constants encode a layout decision made in `CORE.COPY`, with nothing
joining them to the declaration. This is `I-116`'s shape — a DSECT and the thing
that depends on it, in different files — and every one is silent.

| constant | was | becomes |
|---|---|---|
| `RESMASK  DC A(X'FFF0')` | halfword PFRA | `A(PAGPFRM)` |
| `CLCNTINV DC X'00FFFFFC'` | S/370 PTO | `A(SEGPTOM)` |
| `CLINVBIT DC X'FFFFFFFE'` | clear bit 31 | `A(X'FFFFFFFF'-SEGINVAL)` |
| `REFMASK  DC X'0000FFFE'` | clear `PAGREF` | `A(X'FFFFFFFF'-PAGREF)` |
| `INVLPTE  DC X'0008'` | invalid halfword PTE | `A(PAGINVW)` |
| `SWLENGTH DC F'192'` ×2 | **a hard-coded `PAGBMP`** | `A(PAGBMP)` |
| `SEGSIZE  DC X'00010000'` | 64 KB | `X'00100000'` |
| `CLRBITS  DC X'00FFFFF8'` | S/370 PTO | `A(SEGPTOM)` |

`SWLENGTH DC F'192'` is the purest case: `PAGBMP` is computed in `CORE.COPY` and
written out as `192` in `DMKVMA` and `DMKATS`, one of which documents it in a
comment as `X'C0'`. Both are now `A(PAGBMP)`, which cannot drift again.

And six sites write the segment-invalid bit as a bare **`1`**:

    TM    3(R3),1        IS THE STE INVALID?            DMKCDB, DMKCDM
    NI    SEGPAGE+3,255-1 CLEAR INVALID STE BIT         DMKCPI
    O     R2,F1          ASSURE SEGINV FLAG             DMKCFG

Byte 3 by displacement *and* the value as a literal. No symbol, so the rename is
blind; no DAT field on the line, so the sweep is blind. `DMKCPI`'s is reachable
only because the same card happens to name `SEGPAGE`.

---

## 6. What was deliberately not converted

| item | why | lands at |
|---|---|---|
| `DMKCFG`'s AP shared-segment copy | needs `MVCL` and a register pair the routine has nothing spare for; unreachable under `AP=NO`. `ABEND 9` instead (`I-139`) | if AP returns |
| `DMKVAT`'s `ARCHTECT` table | describes the **guest's** tables, indexed by the guest's CR0 | milestone B |
| `DMKDSP` 02417000's `L R1,VMSEG` | feeds `ST R1,RUNCR1`; the hardware wants the whole designation | never |
| `I-126`'s 215 `LA Rn,0(,Rn)` | invisible in M1, simultaneous in M2 | **M2** |
| `I-132`'s 278 three-byte fields | 24 bits is adequate below 16 MB | **M5** |

### `DMKVAT` already knew

The most reassuring thing found all day. `DMKVAT` is CP's shadow-table builder
and it is **already parameterised over eight DAT formats**, because System/370
itself had a 2K/4K page by 64K/1M segment matrix with both halfword and fullword
page-table entries:

    INDEX X'40' - SMALL PAGE, SMALL SEG, HALFWORD ENTRIES
          X'60' - SMALL PAGE, SMALL SEG, FULLWORD ENTRIES
    PINVBIT  DC    X'04'          PAGE-INVALID BIT IN PTE
    LOADPTE  LH    R1,0(0,R2)     SHORT PAGE TABLE ENTRIES
             L     R1,0(0,R2)     LONG PAGE TABLE ENTRIES

**`PINVBIT DC X'04'` is the ESA/390 invalid-bit position.** The format derived
from SA22-7201-08 all day is one CP has been able to read since 1972 — a third
witness, agreeing with the manual and with the running machine. When the guest
tables need converting, the mechanism is to extend that table; its author left
`DS 5H  RESERVED FOR FUTURE USE`.

#### And one of its rows *is* our geometry

Read a day later, chasing `I-188`, and it should have been read first. The eight
codes are a matrix, and the last of them is the one this project is building:

    *              X'B0' - LARGE PAGE, LARGE SEG, FULLWORD ENTRIES

Large page is 4 KB, large seg is 1 MB, fullword entries is the ESA/390 PTE. That
is not an approximation of our target — it is our target, named, with its
constants written out beside it:

    CODEB0   DC    X'000FF000'            page-number mask
             DC    X'7FF00000'            segment-number mask
             DC    X'08',X'06'            page-invalid bit, must-be-zero bits
             DC    H'10',H'18',H'4'       PAGSHFT, SEGSHFT, PTEINCR
             DC    H'127',H'1024',H'64'   MAXSEGS, PAGTLEN, PAGINCR

Every one of those is a constant this project derived separately, and in several
cases painfully:

| `CODEB0` | what we arrived at, and where |
|---|---|
| page mask `X'000FF000'` | `DMKPTR 00321400`, written out as `I-162` after a `SRL 11` was found beside it |
| segment mask `X'7FF00000'` | got **wrong** as `X'00F00000'` and it cost a build cycle — `I-188` |
| `PAGSHFT H'10'` | `DMKPTR 00322400 SRL R1,10  GET PAGE NUMBER*L'PAGPFRA` |
| `SEGSHFT H'18'` | `DMKDRD 01096100 SRL R8,18`, and `SRDL 20`+`SLL 2` elsewhere |
| `PTEINCR H'4'` | the fullword PTE, `CORE.XA0033DK`'s `PAGPFRA DS 1F` |
| `PAGTLEN H'1024'` | `PAGTSWP`'s `256*L'PAGPFRA` |
| `PAGINCR H'64'` | the 64-byte `STL` unit — the whole of `I-188` |
| `MAXSEGS H'127'` | `SEGSTLM EQU X'0000007F'`, read out of the PoO |

So the "central EQUs" that P4 proposes to define already exist, in IBM's hand,
in a module every DAT-touching part of CP can see. **P4's shape should change
accordingly**: rather than inventing `PAGSHFT`/`SEGSHFT`/`PTLSHFT`/`KEYSHFT`,
derive them from this row, and treat any site whose constant disagrees with
`CODEB0` as a site to read. That is a checkable rule where the current plan is a
list, and it would have caught `I-188` before it was built: `X'00F00000'`
appears in this very table, at `CODE90` and `CODE50`, which are the **halfword-
entry** rows — a 24-bit truncation of the same geometry, not this one.

The lesson generalises past this table. Three times now the authority for a
conversion has turned out to be inside CP rather than in the manual: `DMKSYM`
for the address map (`symtab.py`), `DMKBLDRT`'s own entry conditions for the
register layout `I-185` got wrong, and `CODEB0` here. The question to ask before
deriving a constant is whether CP already states it.

---

## 7. The design decisions, and the one that was attempted and abandoned

**Alignment.** ESA/390 wants the segment table on a 4096-byte boundary and each
page table on 64. `STE-DESIGN.md` called this the part with no precedent; the
precedent is in the same routine pair, where `DMKBLDRT` already over-allocates,
rounds up and stores the displacement in `VMSEGDSP` for `DMKBLDRL` to reverse
(`I-123`). The segment table is a generalization of that idiom from 64 to 4096,
and `VMSEGDSP`'s halfword holds 4088, so the VMBLOK does not change.

**`PAGORIG`.** The page table has no such idiom, so the `DMKFREE` address goes in
a new header fullword. The gap is **provably unrecoverable** otherwise — for it
to be constant, `DMKFREE`'s address would need a fixed residue mod 64, and it is
first-fit (`I-135`). Reordering the DSECT so the page table sits at the block
origin was attempted and rejected: it would have broken 33 `S Rn,F16` sites that
no diagnostic can reach (`I-130`). The field is named `PAGORIG` and not `PAGFREE`
because `DMKPTR` has had a label of that name since 1979 (`I-136`).

**`PAGBMP` rounded to a multiple of 64.** 3112 → 3136. `SWLENGTH` is the stride
to the attached processor's page table, so a `PAGBMP` that is merely a multiple
of 8 would put the second page table off a 64-byte boundary. 24 bytes a segment
to remove the problem rather than document it.

**The STE is built in a register and stored once.** Byte 3 of an ESA/390 STE
holds two page-table-origin bits as well as I, C and PTL, so a `STC` into it
destroys part of the address. `LR`/`SRL`/`OR`/`O`/`ST` replaces `ST`/`STC`/`OI`,
and the `OR` is safe precisely *because* the page table is 64-byte aligned.

**Cost of the coarser granularity: 2.9%.** 3160 bytes per megabyte of page and
swap tables against 3072 today. The granularity gets coarser — a small virtual
machine's tables grow from 192 bytes to 3160 — but the total for a real virtual
machine is essentially unchanged.

---

## 8. The guards, and the seven checks that could not fail

Every tool in `arch/31bit/tools` exists because something was believed that was
not true. The ones added on 1 October:

- `snapshot.py` — a snapshot is invalid until the log says otherwise (`I-111`)
- `asmerr.py` — reconciles the assembler's list against the sweep, with a
  **cross-check against the count the log states about itself**, because the
  first version matched only MNOTEs and reported 4 sites against a log of 190
- `deckchk.py` — every flagged site must be covered by a card, before the build
- `symchk.py` — every symbol a deck defines must be new *in that scope*
- `auxcheck()` — every deck must be listed in its AUXLCL, or `VMFASM` never
  applies it (`I-138`)
- log archiving — a build log is a **measurement**, and `asmerr.py` and
  `deckchk.py` both read one, so it cannot live where the next run writes
  (`I-131`)

And the count that should be read as a warning rather than a boast: **seven
checks that could not fail**, in two days — `I-111`, the `mkrun` fall-through,
`I-112`, `I-115`, `I-117`, `I-131`, and `I-137`, which is the worst of them. Its
two defects cancelled into a plausible non-zero exit, so eleven modules with
`IFO188` errors were reported benign while five with perfectly good object decks
were reported missing. `build.sh write` would have VMFLOADed a nucleus from
decks in which `L R3,SEGPAGE` had assembled as `L R3,0`.

**A check that fails for the wrong reason is worse than one that does not fail,
because it looks like it is working.**
