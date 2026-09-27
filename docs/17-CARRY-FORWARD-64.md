# What the 31-bit work hands to 64-bit

27 September 2026. The root README argues the 31-bit stage is not a detour,
because "the two most expensive pieces of the 31-bit conversion carry forward to
64-bit unchanged". That was an argument. This is the ledger, item by item, with
the numbers that decide each one.

**The short answer: most of it carries, and one decision made now determines how
much.** Several constants change value *twice* — once for ESA/390 and again for
z/Architecture — so whether they are parameterised or substituted decides
whether the 64-bit pass is an edit or a re-derivation. That is why this document
exists before M1 step 2 rather than after M4.

## The ledger

| | Verdict | |
|---|---|---|
| Channel subsystem conversion — `DMKIOS`, `DMKIOT`, the CSW shim, CR6 | **unchanged** | arrived with 370-XA 1983, untouched since |
| 4 KB storage keys — `ISKE` `SSKE` `RRBE`, and `DMKPRV`'s 2 KB simulation | **unchanged** | keys are 4 KB in both |
| Frame-level sharing — `DMKATS`, `DMKPGS`, reference counting | **unchanged** | architecture-independent by construction |
| Page and segment geometry — 4 KB / 1 MB | **unchanged** | identical in both |
| `AUXLCL` update-level delivery, `VMFASM`, `DMKLCL MACLIB` | **unchanged** | CE infrastructure, not architecture |
| CE build and run harness — card import, headless driving, printer path | **unchanged** | ditto |
| The 18-module clean baseline | **unchanged** | the reference any change is measured against |
| `XAOPS` mechanism — macro plus `DC X'..',S(...)` | **unchanged** | CE's assembler knows no z/Arch instruction either |
| Six of the 24 macros — `IPTE` `IVSK` `TPROT` `ISKE` `SSKE` `RRBE` | **unchanged** | and forward-compatible, see below |
| Mode-boundary discipline — `BAL`/`BALR` self-correction, `BSM` boundaries | **unchanged** | same problem one level up |
| `asm.py`, `mkprobe.py`, `shifts.py`, `archdep.py` | **retargetable** | structure survives, tables extend |
| Self-relative branches — 912 sites, 127 modules | **gets much worse** | 46 at risk now, all 912 then — see below |
| Table entry width — the halfword→fullword PTE work | **parameterise** | 4 bytes for ESA/390, **8** for z/Arch |
| The four shift symbols — `PAGSHFT` `SEGSHFT` `PTLSHFT` `KEYSHFT` | **parameterise** | two of four change again |
| The 13 hardware tests | **mostly re-ask** | I/O ones pass as-is; DAT ones need new tables |
| PSW format and lowcore | **redo** | 8 bytes → 16, different layout |
| DAT table levels — CR1, region tables | **redo** | two levels → up to five |
| Addressing mode switching | **redo** | `SAM64`, and `LPSWE` for the PSW |

## What carries unchanged, and why it is safe to say so

**The channel subsystem is the big one.** `SSCH`, `MSCH`, `TSCH`, `STSCH`,
`CSCH`, `HSCH`, `RSCH`, `TPI`, `SAL`, `STCRW`, `STCPS`, `RCHP`, `SCHM`, `XSCH`
and `CHSC` are all marked available in z/Architecture in Hercules's own opcode
table, with the same formats. The ORB, SCHIB, IRB and SCSW do not change, and
format-1 CCWs carry through. So `DMKIOS`'s ten instruction sites, the CSW shim
after `TSCH`, `DMKIOT`'s interrupt entry, and the `INTTIO`-as-subchannel-number
change are **done once for both architectures**.

**CR6 carries too**, which matters more than its size suggests. The
I/O-interruption subclass mask is CR6 in both, and `07-io-interrupt.rc` measured
what happens without it: the console line prints, the device does its work, and
the CPU hangs in an enabled wait with nothing in any log. That trap is identical
at 64-bit, and knowing it is a permanent asset.

**Storage keys are 4 KB in both.** So `R-12` — a guest reading its own keys
through `ISK` expecting 2 KB semantics, and `DMKPRV` bridging it — is solved once.
38 `ISK`, 16 `SSK` and 13 `RRB` sites get converted once.

**And two of the macro encodings are deliberately forward-compatible**, which was
luck turned into a property. Hercules marks `IPTE` as `RRR` and `SSKE` as
`RRF_M`, because z/Architecture added an `R3` register field and a
conditional-SSKE mask respectively in the high nibble of byte 2. ESA/390 has
neither, so `XAOPS` emits that byte as zero — and zero is exactly what
z/Architecture reads as "no R3 specified" and "no mask". **Both macros are
already valid z/Architecture instructions.** Had they been written as bare
4-byte constants with a guessed byte 2, that would not be true.

## What carries only if it is parameterised

This is the part that changes what we do this week.

**Table entry width changes twice.** S/370 page-table entries are halfwords;
ESA/390 makes them fullwords, which is 125 references in CP; **z/Architecture
makes them 8 bytes.** Any site that names the width symbolically changes once per
architecture in one place. Any site that hard-codes 4 has to be found again.

**Two of the four shift symbols change again.** From
[`R01-SHIFT-SITES.md`](R01-SHIFT-SITES.md):

| Symbol | S/370 | ESA/390 | z/Architecture |
|---|---|---|---|
| `PAGSHFT` pages per segment | 4 | **8** | 8 — unchanged |
| `SEGSHFT` segment size | 16 | **20** | 20 — unchanged |
| `KEYSHFT` storage-key block | 11 | **12** | 12 — unchanged |
| `PTLSHFT` bytes per page table | 6 | **10** | **changes again** — entries double from 4 bytes to 8 |

Two of four survive the second transition untouched, one changes again, and the
fourth — `PAGSHFT` — survives precisely because page and segment sizes are
identical in ESA/390 and z/Architecture. **So naming them is worth doing even if
64-bit never happens, and doubly so if it does.**

**And CP already has the precedent for doing this properly.** `ARCHTECT` is a
table of eight rows, indexed by `IC R9,EXTCR0+1` from the *guest's* CR0, whose
entries include `PTEINCR`, `PINVBIT`, `ZEROBIT` and `SEGMASK` — page-table entry
increment, invalid bits, and segment mask, parameterised per DAT format.
`02-CP-VERIFIED.md` established that four of its eight variants already use
fullword page-table entries and one has 1 MB segments with 2,048 of them. IBM
wrote architecture-parameterised DAT constants into CP in 1979. **The 70 shift
literals are the sites where they did not**, and the fix is to extend the pattern
rather than invent one.

## What has to be redone, with the cost measured

**The PSW is the expensive one.** ESA/390's PSW is 8 bytes; z/Architecture's is
16, with a different layout. Measured in CP's source:

| | Sites | Modules |
|---|---|---|
| `LPSW` | **123** | 22 |
| `LCTL` | 172 | 52 |
| `STCTL` | 28 | 13 |
| `BAL` | 3,482 | 156 |
| `BALR` | 118 | 47 |

Every `LPSW` becomes `LPSWE` (`B2B2`), and `PSA.MACRO`'s PSW slots move and widen
— a change to the member 171 of 201 modules include. Control registers become
64-bit, so `LCTL`/`STCTL` become `LCTLG` (`EB2F`) / `STCTLG`. **The 3,482 `BAL`
and 118 `BALR` sites are not affected** — both exist in z/Architecture and both
self-correct on addressing mode, the same finding that retired that worry for
31-bit.

**DAT gains levels.** ESA/390 has segment and page tables. z/Architecture inserts
region-third, region-second and region-first tables above them, up to five levels,
and CR1 stops being a segment-table designation and becomes an
address-space-control element carrying a designation type. The ESA/390
translation-format field in CR0 — the first of the three silent gates, bits 8–12
= `10110` — has no z/Architecture counterpart, because the table type moves into
the ASCE. So that gate does not carry, though the lesson behind it does: check
the control registers before blaming the tables.

**Mode switching changes.** `SAM64` (`010E`) is z/Architecture-only, as are
`LPSWE`, `LRAG` (`E303`), `LURAG` (`B905`), `STURG` (`B925`),
`IDTE` (`B98E`) and `LPTEA` (`B9AA`). Those, plus the grande instruction set,
are what a 64-bit `XAOPS` adds.

> **A discrepancy to resolve, recorded rather than guessed.** `XAOPS.MACRO`
> states that "SAM24, SAM31 AND SAM64 ARE Z/ARCHITECTURE, NOT ESA/390". Hercules
> marks `SAM24` (`010C`) and `SAM31` (`010D`) as **available in ESA/390 mode**,
> only `SAM64` as z-only. One of the two is wrong and resolving it needs the
> ESA/390 Principles of Operation, which this project does not have to hand. It
> is immaterial either way: `BSM` and `BASSM` are unambiguously ESA/390 and are
> proven by execution in test 3. Filed as `I-28`.

## What the tools need, and what they already do

`mkprobe.py` was written to measure which ESA/390 mnemonics CE's Assembler XF
lacks. **Inverting its filter answers the same question for z/Architecture with
no new code** — `GENx___x___x900` instead of `GENx(370|___)x390x900`. There are
**321 z/Architecture-only mnemonics** against 351 for ESA/390, so the 64-bit
assembler gap is measurable the same afternoon it becomes relevant.

`shifts.py` re-runs with different values in its `MEANING` table. `asm.py`'s
structure — two passes, label resolution, 12-bit displacement checks, alignment
checks, bounds-checked image writes — is architecture-neutral; it needs z/Arch
opcodes and the 16-byte PSW. `archdep.py` needs the z-only instruction list,
which the above supplies.

**The 13 hardware tests split cleanly.** Tests 5, 6, 7 and 10 — channel
subsystem, initial status, I/O interruption, CKD chain — should pass in z/Arch
mode unchanged, and running them there is a cheap early check that the carry-
forward claim is real. Test 11, storage keys, likewise. Tests 1, 2, 4a, 4b, 8, 9
and 12 are DAT and need 8-byte entries and region tables. Test 3 becomes
AMODE 64.

## The one thing that follows for this week

**M1 step 2 should introduce names, not values.** The `PSA` change adds the
ESA/390 lowcore names at `X'B8'`/`X'BC'` and marks `CHANID`, `IOELPNTR` and
`ECSWLOG` as S/370-only. Marking them rather than deleting them is the choice
that carries: a 64-bit pass wants the same three fields flagged, and a deleted
field leaves no trace of the decision. The same logic says the shift work in M2
defines `PAGSHFT`, `SEGSHFT`, `PTLSHFT` and `KEYSHFT` as symbols with one
definition point, rather than substituting 8, 20, 10 and 12 at 70 sites.

Neither costs anything extra now. Both are the difference between a 64-bit stage
that edits four definitions and one that re-derives seventy sites.

## Self-relative branches: the item that gets worse, not better

Everything else in this ledger either carries forward unchanged or needs a value
parameterised. This one is different: **the 64-bit pass inherits a bigger problem
than the 31-bit pass faces**, and it is invisible to every check either pass runs.

CP branches with `BNZ *-4`, `BC 6,*-4`, `B *+8` — 912 times across 127 nucleus
modules (`tools/selfrel.py`). A self-relative branch encodes a *byte distance*,
so it is correct only while the instructions it spans keep their lengths.

* **This pass** converts I/O instructions. `SSCH` and `TSCH` are longer than
  `SIO` and `TIO`, so the polling loops around them break — 46 sites in the four
  bootstrap modules, and those are being fixed as each module is converted.
* **A z/Architecture pass** converts data movement everywhere: `L` to `LG`,
  `ST` to `STG`, RX to RXY, four bytes to six. At that point every one of the
  912 is suspect — forward ones too, because a `*+8` that skipped two four-byte
  instructions now skips into the middle of a six-byte one.

And it fails in the worst possible way. The assembler accepts it. The loader
accepts it. Execution branches to a garbage instruction boundary and the only
symptom is a program check with no obvious cause and no relation to the change
that broke it.

The distinctive ones are worse than the round numbers. `*-1` appears 33 times in
`DMKFMT` and four times in `DMKCCW`, addressing a byte *inside* an instruction.
`*+4096` in `DMKVSP` is a page-boundary trick. `*-193` in `DMKRSP` and `DMKCSO`
reaches back into a table. None of those survive any change in layout.

**So the standing rule for this project: remove every self-relative branch in any
module we open, whether or not it sits near a converted site.** While a module is
already being decked the marginal cost is close to zero, and each one removed is a
landmine the 64-bit pass never steps on. Measured by `selfrel.py --module`, a
module is finished when its count reaches zero.

This is the one place where doing the 31-bit stage first makes the 64-bit stage
*cheaper in a way that requires deliberate effort now* rather than as a
by-product. Left alone, 912 sites wait for z/Architecture. Cleared as we go, they
do not.
