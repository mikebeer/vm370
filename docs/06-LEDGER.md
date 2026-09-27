# Ledger: what is answered, how firmly, and what is open

26 September 2026. A status account for the 31-bit CP question, sorted by
**strength of evidence** rather than by topic — because "we checked" means
very different things depending on whether something was executed, read, or
counted.

The one-line summary: **the hardware question is closed, the software is
mapped, M0 is verified on CE itself, and no CP code has been written.**

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

### Milestone 0 — now answered by execution, not documentation

**Moved up a category on 27 September.** All twelve `XAOPS` encodings were
sourced five by execution and seven against z390's opcode table; they are now
**accepted by CE's own Assembler XF**, with `MACLIB GEN` producing all twelve
members, `HIGHEST SEVERITY WAS 0`, and 139 records read from the library — which
is what rules out a silently ignored macro call. All seven S-type displacements
are arithmetically exact, which is the one thing z390 could not vouch for.
`RSCH` is `B238`, confirmed by the assembler that will build the nucleus. See
`14-M0-CLOSED.md`.

Still unwritten for M2: `IPTE`, `IVSK`, `TPROT`, and the 4 KB-key trio
`ISKE`/`SSKE`/`RRBE`.

---

## 4. Open, and closable here

The lab now includes a Hercules built from source in this environment, so
these need nobody else. Roughly in value order:

1. ~~**Frame-level sharing on ESA/390.**~~ **DONE** — `09-frame-sharing.rc`,
   and `11-storage-keys.rc` for the read-only half. Two page tables pointing at one frame,
   with storage keys for write protection — turning `05`'s conclusion from
   documented precedent into a demonstrated result on the target
   architecture.
3. ~~**A DASD read.**~~ **DONE** — `10-dasd-read.rc`, passing `00600B`
   against a scratch 3350 made with `dasdinit`. First test to exercise
   command chaining, status modifier and TIC.
4. ~~**The STE flag-collision invariant.**~~ **DONE** — `12-ste-flags.rc`
   measured both directions. The invariant holds while `SEGINV` is set, and
   without it the hardware walks a page table in lowcore. Real and unenforced.
5. **Multiple devices**: an interruption arriving while another is pending,
   ISC with more than one class, `DMKIOT`'s queue walk. Still open, and now the
   only untested item on the I/O path. Needs a larger config and a second
   busy device; lower value than the others were, since its likely finding is
   that the channel subsystem queues correctly.
6. **Storage key semantics** at 4 KB versus a guest's 2 KB expectations —
   `ISK`/`SSK` behaviour, standalone.

## 5. Open, needs Adrian

1. ~~**Are `ARCHTECT`'s `CODE60`/`CODE70` rows live?**~~ **ANSWERED from the
   source** — see `02-CP-VERIFIED.md`. Neither live-for-CP nor dead: the index
   comes from `IC R9,EXTCR0+1`, the *guest's* CR0, so all eight rows exist to
   shadow whatever DAT format a virtual machine selects. CP names only
   `CODE80` ("STANDARD VM/370 FORMAT"). **This was the last item needing
   Adrian, so the plan now has no external dependency.** It also corrected the
   row: `CODEB0`, not `CODE70`, is ESA/390's geometry.
2. Is the `DMKATS` frame-sharing reading right?
3. Has `VMCE-WIDE-PLAN.md` selected a direct 64-bit route that supersedes
   this?
4. ~~The asset handover — `RECOVERED-RECORDS`, `ASSET-ROOT`, pinned tools.~~
   **CLOSED** — the OSMACRO/DOSMACRO libraries that the handover was mostly
   about are already on CE's `CMSDSK 190`, and four modules depending on them
   assemble clean. See `16-NATIVE-BASELINE.md`.
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
   **`DMKPTR` has now been read too**, completing the top five: it already
   tracks sharing **per frame** via `CORFLAG,CORSHARE` (84 references) and
   counts resident shared pages, so the frame-sharing change needs no new
   bookkeeping — that substrate is already at the right granularity.
3. ~~**CMS's 139 `.MACRO`/`.COPY` members**~~ **SURVEYED** — 137 `.MACRO`
   plus 2 `.COPY`, run through `macroexp.py`. **They hide almost nothing:
   4 architecture-sensitive instructions in total** (one `LPSW` in `DBGSECT`,
   invoked 4 times) and **zero S/370 I/O**. The 271 hidden `DC`s are DSECT and
   table generators — `FVS`, `BGCOM`, `DTFCP`.
   **And CMS has no `PSA.MACRO`-equivalent hoard of 24-bit masks**: zero
   24-bit-shaped constants in its macros, and only 7 inline hex literals of
   that shape across all 175 modules, against CP's 217 named references. On
   this axis CMS is far cleaner than CP, which is good news for stage 2.
4. ~~**`USER DIRECT`**~~ **READ** — by running CE itself; see
   `11-RUNNING-CE.md`. **Eight machines default to 15 MB, two to 14 MB, `XNET`
   to 16 MB, and 21 can be defined to 16 MB**, so private storage routinely
   occupies 14–16 MB where CMS's shared segments sit. That closes
   `04-SHARED-SEGMENTS.md`'s last caveat **against** segment-level sharing and
   makes the frame-level route necessary rather than preferable. Background
   below, still accurate: It is a **CMS
   file**, compiled onto the directory cylinder by the `DIRECT` command;
   `DMKUDR` then reads the compiled form, which its prologue describes as
   "written using a pageable access method", and `UDIRECT.COPY` is that
   structure's layout. **The `DIRECT` command itself is not in the recovered
   CE CMS source**, so the file's record format is not documented anywhere in
   the tree — it would have to come from a running system or the VM/370
   manuals. DIRMAINT is the later z/VM licensed program for the same job and
   does not exist for VM/370.
   Virtual machine storage sizes therefore remain unknown — but that question
   was only ever needed for the segment-level sharing analysis, which
   `05-CP67-PRIOR-ART.md` superseded, so nothing depends on it now.
5. **Whether CE's existing C components follow the 31-bit ABI** and its R13
   convention.

## 7a. And the build question, answered by building

**Eighteen CP modules assemble clean on CE's own Assembler XF, unmodified** —
the M1 nine, the DAT five, and four OS/VS-macro users. Every one reports
`NO STATEMENTS FLAGGED`. That makes M1 step 3 done with an empty error list, and
it means all four of z390's failure classes were dialect artifacts rather than
CP defects. `16-NATIVE-BASELINE.md`.

## 8. And the thing no amount of reading settles

**No CP code has been written** — but the reason is no longer build access.
`10-BUILD-ENVIRONMENT.md` measured it: **132 of 201 CP modules assemble today
under z390 on Linux**, including `DMKIOS`, `DMKPSA`, `DMKVAT` and `DMKATS`, and
seven of the M1 nine. Development needs no mainframe environment; only
producing a bootable nucleus does. Everything above is evidence, measurement or
documentation. M1 — CP IPLing in ESA/390 mode with DAT off, writing one
initialisation message — is still the first line of real work, and the point
at which the estimates start being tested rather than refined.
