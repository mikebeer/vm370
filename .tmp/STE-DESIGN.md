# The DAT table conversion for a clean IPL — design

1 October 2026. This is wall 11 of `IPL-WALLS.md`, which is where CP stops
today: `PRG018`, a translation-specification exception, raised by `TRANS`'s
`LRA` against a System/370 segment table.

Every bit position below is quoted from **SA22-7201-08** rather than recalled.
That matters more here than anywhere else in the conversion, because a wrong bit
position produces a translation-specification exception that looks exactly like
the one we already have.

---

## 1. The scope question, answered: this is days, not weeks

`WHAT-31BIT-NEEDS.md` names `DMKBLDRT`'s interface the largest undesigned item,
and `IPL-WALLS.md` said the first job was to find out whether a clean IPL needs
that interface **widened** — an ABI change across 24 callers — or only
**reinterpreted**. It needs neither. DMKCPI's own call site settles it:

    CL    R1,=A(X'FFF000') STORAGE OVER 16M VIRTUAL?      @VA11813
    BNH   VBUFFOK        NO WE ARE OK
    L     R1,=A(X'FFF000') SET VIRTUAL STOR TO 16M        @VA11813
    ...
    ST    R1,VMSIZE           SAVE SIZE IN SYSTEM'S VMBLOK.
    SRL   R1,12          BEGIN/ENDING VALUE FOR TABLES    @V304635
    BCTR  R1,R0          MINUS 1 PAGE (BLD WILL COMPENSATE)
    CALL  DMKBLDRT,PARM=NEWSEGS+NEWPAGES

**CP caps its own virtual size at 16 MB**, and passes `(size >> 12) - 1` — a
page number, 0…4094, which fits the 12 bits `DMKBLDRT` masks with
`N R5,F4095`. A 12-bit page number expresses 16 MB whatever the segment size
is, so the packed fullword is unchanged. **The ABI widening belongs to
milestone B, where a guest exceeds 16 MB — not to a clean IPL.**

Two further simplifications fall out, and both cut the work down:

* **`TRANS.MACRO` itself needs no change.** Its expansion is
  `LCTL C1,C1,VMSEG` / `LRA` / condition-code branches, and `LRA` is valid in
  ESA/390. It fails today because the *data* is S/370, not because the
  instruction is. So the 174 `TRANS` sites across 66 modules are **not** in
  scope here. What does eventually break `TRANS` is AMODE 24 against an
  above-the-line address — ledger test 8 — and that is milestone B.
* **The 358 format-sensitive references are not all in scope either.** Only the
  code that *writes* the tables CP builds for itself during initialisation has
  to change now. That is `DMKBLDRT` and the field definitions in `CORE.COPY`.

---

## 2. The three formats, from the Principles of Operation

### Segment-table designation — what `VMSEG` holds and `LCTL C1,C1` loads

    ┌─┬────────────────────┬───┬─┬─┬───────┐
    │ │Segment-Table Origin│   │P│S│  STL  │
    └─┴────────────────────┴───┴─┴─┴───────┘
     0 1                 19      23 24 25 31

* **STO: bits 1-19**, twelve zeros appended — so the segment table is on a
  **4096-byte boundary**.
* P bit 23 (private space), S bit 24 (storage-alteration event).
* **STL: bits 25-31**, in units of 64 bytes.

S/370 put the length in **bits 0-7** and the origin in bits 8-25. CP writes
exactly that, in two instructions:

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
  entries read `F00561D0`, and the `F` is `SEGPLEN`.
* **PTO: bits 1-25**, six zeros appended — page tables on a **64-byte
  boundary**.
* **I: bit 26** (segment invalid), **C: bit 27** (common segment),
  **PTL: bits 28-31**.

### Page-table entry — and it becomes a fullword

    ┌─┬───────────────────┬─┬─┬─┬─┬────────┐
    │ │       PFRA        │ │I│P│ │        │
    └─┴───────────────────┴─┴─┴─┴─┴────────┘
     0 1                19 20 21 22 23 24 31

* **PFRA: bits 1-19**; **I: bit 21**; **P: bit 22**.
* **Bits 0, 20 and 23 must be zero**; bits 24-31 are ignored.

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
`PTL` for 256 pages is also 15, because `PTL` counts in units of 16 entries. So
the *value* survives; only its bit position moves, from bits 0-3 to 28-31.

---

## 3. The flag collision, and why it is already solved

`CORE.COPY` defines three CP-private flags inside the fullword `SEGPAGE`:

| Flag | Value in `SEGPAGE+3` | Bit | ESA/390 meaning |
|---|---|---|---|
| `SEGINV` | `X'01'` | 31 | part of `PTL` |
| `SEGMIG` | `X'10'` | 27 | **C — common segment** |
| `SEGENQ` | `X'40'` | 25 | **lowest bit of `PTO`** |

All three collide, which is undesigned item 2 of `WHAT-31BIT-NEEDS.md`. But the
project already holds the measurement that resolves it: with the invalid bit
set, `X'00000070'` *is* correctly segment-invalid, while without it
`X'00000050'` is a valid common segment with page-table origin `X'40'` and the
hardware walks a page table on top of the CSW.

And `CORE.COPY` says when the flags are meaningful: *"(IF POINTER = 0)"*. They
are only read when there is no page table — that is, when the segment is
**invalid anyway**. So:

> **Set `I` (bit 26, `X'20'` in byte 3) on every entry that is not present, and
> leave `SEGMIG` and `SEGENQ` where they are.** With `I` on, the hardware does
> not interpret `PTO`, `C` or `PTL`, so the two CP flags are free to keep their
> bit positions and their meanings.

The one flag that must move is **`SEGINV`**: `X'01'` is inside `PTL`, and it is
the bit the hardware now reads at 26. `SEGINV` becomes `X'20'`.

**Bit 0 must still be vacated**, which is what forces `SEGPLEN` out of bits 0-3
regardless of everything above.

---

## 4. What has to change, module by module

| Where | Change | Size |
|---|---|---|
| `CORE.COPY` `SEGTABLE` | `SEGPLEN` bits 0-3 → `PTL` bits 28-31; `SEGINV` `X'01'` → `X'20'`; document `SEGMIG`/`SEGENQ` as valid only with `I` set | 1 deck |
| `CORE.COPY` `PAGTABLE` | `PAGCORE` halfword → fullword; `PAGINVAL` `X'08'` → bit 21; `PAGTSWP` 16 entries → 256 | same deck |
| `DMKBLDRT` | the segment-table **length** arithmetic (`SRDL R0,8`), pages-per-segment, `STC R15,VMSEG` → `STL` in bits 25-31, and the **4096-byte** segment-table / **64-byte** page-table alignment | the real work |
| `DMKBLD` elsewhere | `ICM R0,B'0110',SEGPAGE+1`, `TM SEGPAGE+3,...`, `SLL R3,2` index arithmetic | within the same module |

`R01-SHIFT-SITES.md` already enumerates the shift constants with module, line
and sequence number: **4 → 8** (16 pages/segment → 256), **16 → 20** (64 KB →
1 MB segment), **6 → 10** (×64-byte page table). Those are the three that apply
here. Shift 12 stays 12, because pages remain 4 KB.

### The one genuinely new requirement

**Alignment.** CP allocates tables with `DMKFREE`, which returns doubleword
granularity. ESA/390 wants the segment table on a page boundary and each page
table on a 64-byte boundary. This is not a format change and no existing site
expresses it, so it is the part of this work with no precedent in the source —
and therefore the part to design before writing any card.

---

## 5. Order of work

1. `CORE.COPY`'s `SEGTABLE` and `PAGTABLE`, with `SEGINV` moved. Nothing
   executes differently yet; this makes the symbols mean the right thing.
2. The alignment decision for `DMKBLDRT`'s two `DMKFREE` calls.
3. `DMKBLDRT`'s arithmetic and the entries it writes.
4. Rebuild and IPL. The expected next result is **not** a clean IPL — it is a
   *different* failure, because the first `LRA` will succeed and CP will get
   further. The project's record is that each wall hides the next one, and
   budgeting for that has been more accurate than any estimate of what remains.

Every step is verifiable from the artifact rather than by reading: `dumpscan.py`
reads CP's own dump, so the segment table at the address in `CR1` can be
inspected directly, and a correct STE is recognisable at a glance — **bit 0
zero** is the whole test for the failure we have now.
