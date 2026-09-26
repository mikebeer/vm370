# Ledger: what is answered, how firmly, and what is open

26 September 2026. A status account for the 31-bit CP question, sorted by
**strength of evidence** rather than by topic — because "we checked" means
very different things depending on whether something was executed, read, or
counted.

The one-line summary: **the hardware question is closed, the software is
mapped, and no CP code has been written.**

---

## 1. Answered by execution

The strongest category: a program ran on a real emulator and produced a
distinct pass code. Eight tests in `../arch/31bit/tests/hardware/`, all
passing on **stock, unpatched** Hercules — verified both from a 3.x build's
banner and from a 3.13 built from clean source, so no /380 patch is involved
anywhere.

| Question | Answer | Test |
|---|---|---|
| Are hand-built ESA/390 DAT tables accepted, and does DAT run? | yes | 1 |
| Is the page table actually walked, or is it being faked? | walked | 2 |
| Does the AMODE 31 switch work, and does DAT survive it? | yes | 3 |
| Does an above-the-line **virtual** address translate? | yes | 4a |
| …to an above-the-line **real** frame? | yes | 4b |
| Can `MSCH`/`SSCH`/`TSCH` drive a real device with a format-1 CCW? | yes | 5 |
| Does `ORB5_I` produce `SCSW1_Z` and a deferred condition code of 0? | yes | 6 |
| Does an **I/O interruption** arrive and identify its subchannel? | yes | 7 |
| Does `LRA` behave as `TRANS` assumes, in both addressing modes? | **no, in 24-bit** | 8 |

Test 4b is the load-bearing one: a store at virtual `X'01005000'` — segment
16, page 5 — in 31-bit mode with DAT on lands at real `X'01100000'`, and real
`X'5000'`, where a 24-bit truncation would have gone, stays zero.

Test 6 passed on two independently built emulators, reaching it by different
paths (status on the first `TSCH` in one, after several polls in the other).

**And one negative result, which is evidence of the same quality.** Running
test 7's identical image with CR6 forced to zero: the console line still
prints, the CCW runs, the device does its work — and the CPU sits in its
enabled wait until the emulator is killed, with no PSW, no message and no
code. The failure *looks like success*.

### And one answer that was a negative

**`LRA`'s operand address is truncated by the addressing mode.** In 24-bit
mode, `LRA 2,0(0,6)` with R6 = `01005000` returns cc=0 and R2 = `00005000` —
the effective address was masked to `005000` before translation, so the
instruction answered correctly about segment 0 page 5 instead. In 31-bit mode
the same instruction returns `01100000`. `LRA`'s *result* is not truncated;
its *question* is.

**Consequence: converting the `TRANS`-bearing modules to AMODE 31 is a
prerequisite for paging above the line.** While CP runs AMODE 24 its 174
`TRANS` sites cannot ask about an above-the-line virtual address at all, and
the failure is silent — cc=0 with a plausible real address from the wrong
page. This moved AMODE 31 conversion into M2.

### What that closes

**There is no hardware blocker to a 31-bit CP, and no emulator upgrade is
needed.** Every architectural facility the conversion depends on exists and
behaves as documented on the build the project already runs.

### Three silent gates, all found the hard way

Each is a one-line omission with no diagnostic, and each cost real time:

1. **CR0 translation format.** Bits 8–12 must be `10110`
   (`CR0_TRAN_ESA390 = 0x00B00000`), checked *before any table is read*. CR1
   alone gives a translation-specification exception, code `0012`.
2. **`PMCW5_E`.** A subchannel is never enabled until `MSCH` says so.
   `SSCH` on a disabled subchannel returns condition code 3 **silently**.
3. **CR6.** The I/O-interruption subclass mask. ISC defaults to 0, so bit 0
   must be on or the interruption is *never* presented — and the symptom is
   a hang that looks like success. The worst of the three.

---

## 2. Answered by reading CP source

Measured against Adrian's maintained tree with a statement parser. Firm about
*what the code says*, silent about whether the code was ever exercised.

**The DAT geometry changes, and by how much:**

- Segments go 64 KB → 1 MB. `PAGTSWP EQU (PAGCORE-PAGSTMP+16*L'PAGCORE)`,
  "LENGTH OF A FULL 16 ENTRY PAGE TABLE"; `CTLREGS` sets `PAGE4K` without
  `SEG1M`.
- Page table entries go halfword → fullword. `PAGCORE DS 1H`. 125 references.
- Segment table entry fields all move, and two CP flags collide with ESA/390
  meanings: `SEGMIG X'10'` with the common-segment bit, `SEGENQ X'40'` with
  the lowest `PTO` bit. 113 references. Survivable only because CP sets both
  exclusively when the pointer is zero — an accident that must become an
  explicit invariant.
- Storage keys go 2 KB → 4 KB. `SWPKEY1`/`SWPKEY2`, `SWPREF1/2`, `SWPCHG1/2`
  collapse pairwise. 55 references, and it reaches `DMKPRV` because a guest
  reading its own keys through `ISK` expects 2 KB semantics.

**Where the work actually is, which was not where I first said:**

| Module | DAT-table refs | Was on my original list? |
|---|---|---|
| DMKPGS | 96 | no |
| DMKATS | 73 | no |
| DMKBLD | 63 | no |
| DMKVAT | 55 | yes |
| DMKPTR | 54 | yes |

**I/O is ten instruction sites, not 1,493 references.** Every S/370 I/O
instruction in `DMKIOS` is one instruction with the same `0(R1)` operand; the
CAW is *built* in two places. A shim synthesising a CSW at `X'40'` after each
`TSCH` leaves all 1,917 CAW/CSW references working. The hard part is about a
dozen `BC 4,… BRANCH IF CSW STORED` branches plus channel logout.

**`TRANS`, invoked 174 times, concentrates the translation interface** — one
macro carrying `LCTL`/`LRA`/branch. Converting it once covers 174 sites.

**Three retractions, all in the project's favour:**

- `DMKVAT` is probably the *least* of the DAT work, not the most. It is
  already parameterised by DAT architecture (`GPR 9 = ARCHITECTURE CONTROL
  INDEX` indexing `ARCHTECT`, whose entries include `PTEINCR`, `PINVBIT`,
  `ZEROBIT`), and four of eight variants already use fullword PTEs — `CODE70`
  has `SEGMASK X'7FF00000'`, 2,048 segments of 1 MB.
- `BAL`/`BALR` self-correct in 31-bit mode. The 3,600 link-register stores are
  not 3,600 bugs; only mode *boundaries* matter. `CALL`'s 4,104 invocations
  are safe too, because it flags pageable targets in bit 0 — the bit ESA/390
  leaves free.
- The packed-address population is 582 `ICM`/`STCM` three-byte-mask sites,
  not 567 mixed with CCW templates. The `AL3` sites are format-0 CCW
  templates and CAW stores, which do not change.

### New: CP's lowcore, and a coincidence worth having

`PSA.MACRO`, 688 lines, invoked by **171 of 201 modules**. Offsets computed
from the macro itself, honouring its `ORG` redefinitions:

    CHANID     X'A8'   STIDC result -- S/370 only, replaced by the subsystem
    IOELPNTR   X'AC'   I/O Extended Logout pointer -- S/370 only
    ECSWLOG    X'B0'   Limited Channel Logout -- no ESA/390 equivalent
    INTKFLIN   X'B8'   "IO INTERRUPT KEY, FLAGS, INTERFACE..."
    INTTIO     X'BA'   "IO INTERRUPT DEVICE ADDRESS (HALFWORD)"

ESA/390 puts `ioid` — the subsystem id — as a **fullword at `X'B8'`**, and the
interruption parameter at `X'BC'`. So `INTKFLIN` already sits on exactly that
fullword, and **`INTTIO` at `X'BA'` is its low halfword — which under ESA/390
is the subchannel number**, since `ioid` is `X'0001'` in the high halfword and
the subchannel in the low.

Test 7 confirms it empirically: it compared `X'B8'` for four bytes against
`00010000` and matched.

**So `INTTIO` does not move and does not change width. Its meaning changes
from device address to subchannel number** — the conversion is a lookup, not a
relayout, and CP already chains `RDEVBLOK` by device address. The three
S/370-only fields above (`CHANID`, `IOELPNTR`, `ECSWLOG`) are the ones with
nothing to map to.

---

## 3. Answered by documentation and prior art

- **CCWs do not change.** The PoO states the S/370 24-bit format "is carried
  into the 370-XA mode", selected by one ORB bit; MVS/XA never converted.
- **Sharing need not be segment-granular.** CP-67 ran 4 KB pages in 1 MB
  segments — ESA/390's exact geometry — and shared at **page** granularity,
  declaring shared *pages* (`SWPTABLE FIRSTSP=/LASTSP=`) where VM/370 declares
  shared *segments* (`SYSHRSG=`). Each machine got its own page table
  populated from a model; storage keys gave write protection. See
  `05-CP67-PRIOR-ART.md`. **This removed what had been the only item needing
  a compatibility decision.**
- **CP-67 ran 24-bit**, not the Model 67's 32-bit mode.
- **Stage 1 needs no CMS changes**, if CP presents S/370-mode virtual
  machines — the VM/XA precedent, corroborated by Gum.
- **Initial-status interruption has been in Hercules since 1.39**, November
  1999.
- **The 31-bit ELF ABI reserves R13 as the literal pool pointer**, which
  collides with CP's use of R13. Only matters where C meets assembler — and
  CE already has C components.

### Milestone 0

All twelve `XAOPS` encodings are sourced: five by execution, seven against
z390's opcode table, which is not derived from Hercules. `RSCH` is `B238`; the
`B23B` I once flagged is `RCHP`, a different instruction.

---

## 4. Open, and closable here

The lab now includes a Hercules built from source in this environment, so
these need nobody else. Roughly in value order:

1. **Frame-level sharing on ESA/390.** Two page tables pointing at one frame,
   with storage keys for write protection — turning `05`'s conclusion from
   documented precedent into a demonstrated result on the target
   architecture.
3. **A DASD read.** The real `DMKIOS` case: a CCW chain, a real device, status
   that matters. Needs an empty scratch volume, which `dasdinit` can create
   here — so the old "never against a CE pack" conflict is resolved rather
   than merely avoided.
4. **The STE flag-collision invariant.** Build a segment table entry with
   `SEGMIG`/`SEGENQ` set and the pointer zero; confirm the hardware ignores
   them.
5. **Multiple devices**: an interruption arriving while another is pending,
   ISC with more than one class, `DMKIOT`'s queue walk. All need a larger
   config than the deliberately minimal one.
6. **Storage key semantics** at 4 KB versus a guest's 2 KB expectations —
   `ISK`/`SSK` behaviour, standalone.

## 5. Open, needs Adrian

1. **Are `ARCHTECT`'s `CODE60`/`CODE70` rows live, or dead future-proofing?**
   The one question where he may simply know.
2. Is the `DMKATS` frame-sharing reading right?
3. Has `VMCE-WIDE-PLAN.md` selected a direct 64-bit route that supersedes
   this?
4. The asset handover — `RECOVERED-RECORDS`, `ASSET-ROOT`, pinned tools.
5. Repository access to `mainframe-lab`.

## 6. Open, needs Mike's machines

1. The three /380 measurements: real CR13 with a guest *executing*, the
   `ECMODE` flag in `USER DIRECT`, and `MEMTEST` with the failure captured.
   Lower stakes now — ESA/390's main disadvantage was the sharing granularity
   loss, and that is gone.
2. Which build test 6 ran on. Provenance tidiness only; my own run settles
   the result.

## 7. Open, and genuinely unquantified

The honest end of the ledger.

1. ~~**The macro undercount.**~~ **CLOSED** — see
   `08-MACRO-UNDERCOUNT.md`. Of 59 CP macros only 10 emit anything
   architecture-dependent, and weighted by invocation `TRANS` is the entire
   undercount: 522 instructions (`LCTL` ×348, `LRA` ×174) plus one `CLRIO`.
   `CALL`, `SWTCHVM`, `LOCK` and `GOTO` are all clean. But it turned up
   something an instruction count could never find: **six
   architecture-dependent constants in `PSA.MACRO`** — `XPAGNUM X'00FFF000'`
   at 73 references, `CPCREG0 X'81800CC0'` (CP's own CR0) at 38,
   `X2048BND X'00FFF800'` at 25, `XRIGHT24` at 23, `X40FFS X'40FFFFFF'` at
   18 — 217 reference sites with one definition point each.
2. ~~**`DMKPGS` and `DMKBLD`**~~ **READ** — see `09-DAT-WORK-SHAPE.md`.
   `DMKBLDRT`'s parameter is a packed halfword that cannot express a 31-bit
   range, so it is an ABI change with 8 callers; 70 hard-coded shift amounts
   across twelve modules encode the table geometry in bare literals; and
   `DMKPGS` turns out to be the *other half* of the shared-segment machinery
   (`DMKATS` attaches, `DMKPGS` releases), which widens `05`'s conclusion.
   **`DMKPTR` is now the last unread module in the top five** — 54 DAT
   references, 2,589 lines, and the busiest module in CP by `CORTABLE` use.
3. **CMS's 139 `.MACRO`/`.COPY` members**, entirely unexamined. `TRANS`
   showed what macros can hide.
4. **`USER DIRECT`** is not in the source tree — `UDIRECT.COPY` is the control
   block layout, not the directory — so virtual machine storage sizes are
   unknown.
5. **Whether CE's existing C components follow the 31-bit ABI** and its R13
   convention.

## 8. And the thing no amount of reading settles

**No CP code has been written.** Everything above is evidence, measurement or
documentation. M1 — CP IPLing in ESA/390 mode with DAT off, writing one
initialisation message — is still the first line of real work, and the point
at which the estimates start being tested rather than refined.
