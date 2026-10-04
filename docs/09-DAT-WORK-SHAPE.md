# The real shape of the DAT conversion

> **Status, 4 October 2026.** The DAT conversion this document shaped is done
> — `XA0033`–`0037DK`, 1 MB segments, fullword PTEs, the shift sites named
> and changed ([29-DAT-CONVERSION.md](29-DAT-CONVERSION.md),
> [27-STE-DESIGN.md](27-STE-DESIGN.md)) — and CP runs on the result. §1 was
> wrong in its conclusion: `DMKBLDRT`'s packed halfword was kept and re-split
> 4+8 for 1 MB segments, no ABI change and no caller touched; `I-185` then
> widened the page numbers to 16 bits, which is why `DEF STOR` tops out at
> 256 MB (`I-203`). §3's frame-sharing work landed in `DMKCFG`, `DMKPGS`,
> `DMKVMA` and `DMKBLD`, not `DMKATS`
> ([33-FRAME-SHARING.md](33-FRAME-SHARING.md), M3c done). The one M2 item
> still open is AMODE 31: CP runs 24-bit, so guest storage above 16 MB aliases
> onto the low 16 MB (`I-208`). Current position in [30-STATE.md](30-STATE.md);
> issues in [13-ISSUES.md](13-ISSUES.md). The shift inventory and the `DMKPTR`
> `CORSHARE` finding stand.

26 September 2026. `03-CP-INVENTORY.md` counted 492 DAT-table field
references and named `DMKPGS`, `DMKATS` and `DMKBLD` as the top consumers,
none of which had been read. Two of them have now been read, and the field
count turns out to be the *easy* part.

Three things the field references do not capture, all found by reading:

1. **`DMKBLDRT`'s parameter format is a packed halfword**, and it cannot
   express a 31-bit address range. An interface change, with 8 callers.
2. **70 hard-coded shift amounts encode the table geometry**, in bare literals
   like `SLL R9,6` that no field-name search can see.
3. **`DMKPGS` is the other half of the shared-segment machinery**, not just a
   paging module — which widens `05-CP67-PRIOR-ART.md`'s conclusion.

---

## 1. `DMKBLDRT`'s interface cannot carry a 31-bit range

From the module's own entry conditions:

    * ENTRY CONDITIONS -
    *        GPR 1 = BEGINING AND ENDING ADDRESS TO BUILD TABLES.
    *        BYTES 0-1 = BEGINING ADDRESS
    *              FIRST 4 BITS = 0,NEXT 8 BITS = SEGMENT, NEXT 4 = PAGE
    *        BYTES 2-3 = ENDING ADDRESS
    *              FIRST 4 BITS = 0,NEXT 8 BITS = SEGMENT, NEXT 4 = PAGE

Two addresses in one fullword, each a halfword of *4 zero bits, 8 segment
bits, 4 page bits*. That is 256 segments of 16 pages of 4 KB — **exactly
16 MB, and exactly the S/370 64 KB-segment geometry.**

Under ESA/390 an address needs 11 segment bits and 8 page bits. Nineteen bits
per address, so two of them do not fit in a fullword at all. **This is not a
field widening, it is an ABI change** — and `DMKBLDRT` is called via SVC, so
every caller is affected. *(superseded — see status note)*

**Eight callers**, which is the good news:

    DMKCFG  DMKCFP  DMKCPI  DMKDEF  DMKDEH  DMKLOG  DMKPGS  DMKPTR

`DMKCPI` is on M1's path, but M1 runs with DAT off and can stub the call —
consistent with `07-M1-WORKLIST.md` deferring `DMKBLD` entirely.

The companion entry points are similarly bounded: `DMKBLDRL` (release) has 5
callers, `DMKBLDVM` 8, `DMKBLDEC` 3.

## 2. Seventy shifts encode the geometry

`DMKBLD` is a nest of hard-coded shift constants, and its own comments say
what each one means:

     205   SRL   R1,16          ADDRESS OF FIRST SEG. TO BUILD
     232   SLL   R1,4+4         SEGMENT COUNT * 16
     257   SLL   R9,6           LENGTH OF OLD TABLE
     329   SRL   R3,4           DROP THE PAGE NUMBER
     278   SLL   R7,6           TIMES 64 BYTES PER TABLE

Measured across the twelve DAT-touching modules, 284 literal-shift
instructions, of which the amounts sort cleanly into three groups:

| Shift | Count | Encodes | Becomes |
|---|---|---|---|
| **4** | **33** | 16 pages per segment | **8** (256 pages) |
| **16** | **27** | 64 KB segment | **20** (1 MB) |
| **6** | **5** | ×64-byte page table | **10** (×1024) |
| **11** | **4** | 2 KB storage-key granularity | **12** (4 KB) |
| **4+4** | **1** | segment count ×16 | **4+8** |
| | **70** | **must change** | |
| 12, 2, 3, 20, 1 | 141 | 4 KB page, fullword, doubleword, 1 MB | unchanged |
| various | 71 | — | need individual inspection |

**Shift 12 staying valid is worth noticing**: pages remain 4 KB in ESA/390, so
every page-offset extraction survives untouched. And four shift-20s already
exist in `DMKPGS` — 1 MB-shaped arithmetic in a 64 KB-segment system, which
is either a coincidence of scale or a hint that someone thought about this
before.

Where the 70 live:

    shift 4    DMKBLD 8, DMKCPI 7, DMKPGS 6, DMKCFG 4, DMKPTR 2,
               DMKVMA 2, DMKMCH 2, DMKVAT 1, DMKCPP 1
    shift 16   DMKATS 6, DMKCFG 6, DMKCPP 5, DMKPGS 4, DMKPTR 3,
               DMKBLD 1, DMKVAT 1, DMKCPI 1
    shift 6    DMKBLD 4, DMKCPI 1
    shift 11   DMKMCH 2, DMKPTR 1, DMKRPA 1

The comments confirm the reading in nearly every case — `SRL R5,16  LEAVE
ONLY SEGMENT NUMBER`, `SLL R4,4  TIMES 16 FOR NUM. SEG EN`, `SRL R1,11  GET
PAGE NUMBER*2` — so this is evidence rather than inference. Each of the 70
still needs individual confirmation, because a shift of 4 might be
multiplying by sixteen for an unrelated reason, but the population is
enumerable and the line numbers are known.

**`DMKMCH` and `DMKRPA` were not on any earlier list.** `DMKMCH` is
machine-check handling, with two shift-4s and two shift-11s — the latter
being "PUT THE FAILING STORAGE ADDRESS" through a 2 KB-granular shift, which
is storage-key arithmetic in the error path.

## 3. `DMKPGS` is half of the shared-segment machinery

Its function, from its own prologue:

    *  1.    TO RELEASE THE PAGES OF A USER'S VIRTUAL STORAGE SPACE
    *  2.    TO LOCATE A NAMED SYSTEM WHICH RESIDES IN THE USER'S
    *        VIRTUAL STORAGE.

with `DMKPGSPS - RELEASE A NAMED SYSTEM FROM USER'S VIRTUAL STORAGE`.

So the named-saved-system machinery is split: **`DMKATS` attaches, `DMKPGS`
releases.** `05-CP67-PRIOR-ART.md` concluded that moving to frame-level
sharing puts work into "`DMKATS` and the `NAMESYS` path". That is incomplete —
it is `DMKPGS` too, and `DMKPGS` is the *largest* DAT-table consumer in CP at
96 references.

Which makes the frame-sharing change: `DMKATS` (73 refs) + `DMKPGS` (96) +
the `NAMESYS`/`DMKSNT` declaration format. Still bounded, still with IBM's
precedent, but two large modules rather than one.

---

## What this does to M2's estimate

M2 is *DAT on with ESA/390 tables, `TRANS`-bearing modules at AMODE 31, no
guests, no shared segments*. Its work, now enumerable:

| Item | Population | Source |
|---|---|---|
| DAT-table field references | 492 | `03-CP-INVENTORY.md` |
| Geometry-encoding shifts | **70** | this document |
| Architecture-dependent constants | 6 defs, **217 refs** | `08-MACRO-UNDERCOUNT.md` |
| `TRANS` macro sites | 174 (one macro) | `08-MACRO-UNDERCOUNT.md` |
| `DMKBLDRT` interface + callers | **8** | this document |
| AMODE 31 for `TRANS`-bearing modules | — | `08-lra.rc` |

**Nothing in that table is unbounded any more.** Six weeks ago the DAT work
was "492 references and three unread modules"; it is now a list with line
numbers, and the largest single item — 492 field references — is the most
mechanical.

## `DMKPTR`, and a piece of good news for frame sharing

Read 27 September, completing the top five. `DMKPTR` manages "the inventory of
real system pages" — the frame allocator, plus `DMKPTRAN`, the page-fault
handler that `TRANS` calls when a page is not resident.

**It already tracks sharing per frame.** 84 references, through a `CORTABLE`
flag:

     395   TM    CORFLAG,CORSHARE     SHARED PAGE
     711   OI    CORFLAG,CORSHARE     FLAG CORTABLE ENTRY (SHARED)
     902   NI    CORFLAG,255-CORSHARE CLEAR FLAGS
    1091   TM    CORFLAG,255-CORSHARE-CORRSV  PICK ANY UNLOCKED
    1457   TM    VMOSTAT-VMBLOK(R15),VMSHR    RUNNING SHARED SYSTEM

plus an entry point `DMKPTRSC - NUMBER OF RESIDENT, SHARED PAGES`.

`CORTABLE` is CP's real-page inventory, one entry per **frame**, and
`CORSHARE` is a flag on the frame. So CP's bookkeeping for shared storage is
**already frame-oriented**, not segment-oriented — the segment-level part is
only how the page tables get pointed at it.

That matters for `05-CP67-PRIOR-ART.md`'s conclusion. Moving to frame-level
sharing needs `DMKATS` and `DMKPGS` changed and `DMKSNT`'s declaration format
widened from segments to pages, but it does **not** need a new way to track
which frames are shared, how many are resident, or whether they can be stolen.
That substrate exists and is already at the right granularity.

So the sharing path is three modules — `DMKATS` attaches, `DMKPGS` releases,
`DMKPTR` owns the frames — and the third one needs the least work of the
three.

**All five top DAT consumers have now been read.**
