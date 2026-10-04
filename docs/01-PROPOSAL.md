# VM/370 CE 31-bit — what is proven, and a proposed staged plan

> **Status, 4 October 2026.** The plan in §6 has largely been carried out, and
> this document is kept as the record of what was proposed. M0, M1, M3a, M3b
> and M3c are done: the converted CP IPLs from DASD in ESA/390 mode, CMS reaches
> `Ready;` by `IPL 190` and by `IPL CMS` with two concurrent sharers, EXEC2 and
> REXX run, and `DEF STOR 32M`/`64M` is accepted. M2's DAT tables are done but
> CP still runs AMODE 24, so guest storage above 16 MB aliases onto the low
> 16 MB (`I-208`) — that is the open M2 work; M4 is largely done by M3c; M5 is
> not started. §2's three /380 measurements were never taken and are moot; the
> `CMSOLD` decision asked for in §3a was never needed, because named systems
> are shared by frame ([33-FRAME-SHARING.md](33-FRAME-SHARING.md)); the
> `DMKBLDRT` ABI change in §6 was not needed either (the packed halfword was
> re-split and the ceiling raised to 256 MB, `I-185`, `I-203`); and the asks of
> Adrian in §7 are overtaken. Current position in
> [30-STATE.md](30-STATE.md), the milestone table in
> [../arch/31bit/README.md](../arch/31bit/README.md), walls in
> [28-IPL-WALLS.md](28-IPL-WALLS.md), issues in [13-ISSUES.md](13-ISSUES.md).
> What still stands: the hardware demonstration in §1 and the §3–§4 account of
> what had to change in CP, which the conversion confirmed.

For Adrian, from Mike. 26 September 2026.

Asking for comments and, if you agree with the shape, approval to start on
the independent parts. Nothing needs your time beyond reading this and one
asset handover — §7.

**Naming**: calling this VM/ESA would be wrong. That was an IBM product
with its own CMS, shared segments and service structure. This is a 31-bit
VM/370 CE. 64-bit is the destination after it, not instead of it.

Backing detail: **03-CP-INVENTORY.md** has the counts, **02-CP-VERIFIED.md**
has two design hypotheses checked against your source — both of which I had
wrong, in the pessimistic direction.

---

## 1. What was demonstrated

Six standalone programs on **stock, unpatched Hercules 3.07**, ARCHMODE
ESA/390, no operating system. Bytes poked into real storage from a script
file and started with `restart` — the same method your `wide/` directory
uses. Each answers one question and has its own pass code, so a stale
program cannot masquerade as a pass.

| Test | Pass | Question |
|------|------|----------|
| 1 | `00600D` | Are hand-built DAT tables accepted and does DAT run? |
| 2 | `00600D` | Is the page table actually being walked? |
| 3 | `006003` | Does the AMODE 31 switch work, and does DAT survive it? |
| 4a | `006004` | Does an above-the-line **virtual** address translate? |
| 4b | `006005` | …to an above-the-line **real** frame? |
| 5 | `006006` | Does MSCH/SSCH/TSCH drive a real device? |

Test 4b stored at virtual `X'01005000'` — segment 16, page 5 — in 31-bit
mode with DAT on; the byte arrived at real `X'01100000'`, and real `X'5000'`
where a 24-bit truncation would have landed stayed zero. Test 5 wrote to a
3215 with a hand-built PMCW, ORB and format-1 CCW: device status exactly
`CE|DE`, subchannel status zero, residual zero.

**Stated no more strongly than the evidence allows: there is no hardware
blocker.** Necessary, and not known a day earlier. It says nothing about
whether converting CP is tractable — §3 is the attempt to find out.

### Three facts that cost time and are not in the manuals

**CR0 carries the translation format and DAT checks it before reading any
table** — `CR0_TRAN_ESA390 = 0x00B00000`. CR1 alone gives a
translation-specification exception on the first translated reference.

**A subchannel is never enabled until `MSCH` says so.** `config.c:740` sets
only `PMCW5_V`; `device_reset()` clears `PMCW5_E`. **`SSCH` with E off
returns cc=3 silently** — no exception, no message.

**`LPM` must be `X'80'`, not `X'00'`.** SSCH tests `orb.lpm & pmcw.pam` and
`pam` is `0x80`, so zero means "no path", not "any path".

---

## 2. The /380 route: closure unsupported, conclusion untested

Closed on 25 September on `CR13 = 91F07000`, measured by a CMS program.
That evidence is invalid; the conclusion may still be right.

**Wrong register.** The same program reported `CR0 = 000000E0`, and
`DMKBLDEC` contains literally `MVI EXTCR0+3,X'E0'`. That is the ECBLOK —
the *virtual* control register image. `STCTL` from a guest is privileged, so
CP simulates it against the ECBLOK. The patch consults `regs->CR(13)`.

**CP assigns CR13 no meaning.** `DMKCPI` does `LCTL C0,C14,CTLREGS` where
`CTLREGS` has `DC 11F'0'` covering CR3–CR13. No `LCTL 0,15` anywhere. No
symbol or comment mentions CR13. `91F07000` appears nowhere in the source.

**Measured real CR13 with CP up: `00000000`** — corroborated as a live CP by
`CR02=FFFFFFFF` (exactly `CTLREGS`), `CR01=0FFFC400` (DAT on) and
`CR00=81800CC0`, one bit from `DMKPSA`'s documented `CPCREG0`.

**But the decisive case is untested.** That sample was probably taken with
CP idle. `DMKDSP` reloads CR4–13 from the ECBLOK on every dispatch when
`VMV370R` is set, so a machine with `ECMODE` propagates the virtual value
into the real register — and the original `STCTL` succeeding at all suggests
`ECMODE` is set there. Three measurements settle it, none needing you.

**Why it still matters.** S/380 needs neither a DAT nor an I/O rewrite, so
it is much cheaper *if* CR13 cooperates. Against that: it needs a patched
emulator, and for a community distribution that is a real cost — everyone
who runs it needs a non-standard build. ESA/390 needs one config line. That
trade is yours to make.

---

## 3. What has to change in CP

Counted across your 201 `.ASSEMBLE` members. The 166 S/370 I/O instructions
cross-check against 165 counted independently in an unrelated R6 extraction.

### 3a. The biggest item is a compatibility decision, not code

**Segment size goes from 64 KB to 1 MB.** CP runs 64 KB segments of sixteen
4 KB pages — `PAGTSWP EQU (PAGCORE-PAGSTMP+16*L'PAGCORE)`, "LENGTH OF A
FULL 16 ENTRY PAGE TABLE", and `DMKCPI`'s `CTLREGS` sets `PAGE4K` without
`SEG1M`. **ESA/390 has only 1 MB segments.**

**The consequence I most want your judgement on is shared segments** —
and since first writing this I have measured it against `DMKSNT` rather
than asserting it. **04-SHARED-SEGMENTS.md has the working; it is much
narrower than I claimed here.** Nineteen 64 KB shared segments collapse into
three 1 MB segments, and what matters is only whether any saved system's
*private* pages land in a megabyte another one makes common:

  - **Segment 15**, with six saved systems in it, is the false alarm — no
    saved system has a private page between 15 and 16 MB, because you parked
    everything up there "to maximize the VM size". Nothing to do.
  - **Segment 14** needs `CMSVSAM` and `CMSAMS` separated; each has private
    pages in the other's megabyte. A `DMKSNT` layout edit.
  - **Segment 0 is the real one, and it is `CMSOLD` alone.** It shares
    64 KB segment 1, `X'10000'`–`X'20000'`, which forces the whole first
    megabyte common — and that is where `CMS`, `CMSTEST`, `CMS67` and
    `CMSOLD` all keep their PSA and nucleus low core. Your own `@D03`
    comment says the production nucleus was relocated high "to relieve the
    storage contraint between X'10000' and X'20000'", so you have already
    made this move once for the live system; `CMSOLD` is the frozen Sixpack
    1.3 fallback left behind in it.

**So the decision I am actually asking for is what happens to `CMSOLD`** —
retire it under 31-bit CP, relocate its shared segment above 1 MB and break
its "never updated" intent, or keep it 24-bit only and refuse to attach it.
*(superseded — see status note)*
That is a question about what CE promises its users, which is yours and not
mine. The rest is a layout edit.

One caveat I cannot close from the source tree: this uses *saved* pages. A
virtual machine defined larger than its saved system could hold private
pages anywhere below its size, including inside segments 14 and 15, which
would stop segment 15 being benign. That needs `USER DIRECT`, which is on a
CMS disk rather than in Git — `UDIRECT.COPY` is the control block layout.

**Storage key granularity goes from 2 KB to 4 KB.** CP tracks it
explicitly: `SWPKEY1`/`SWPKEY2` are "VIRTUAL STORAGE KEY, 1ST/2ND 2048
BYTES", with `SWPREF1`/`SWPCHG1`/`SWPREF2`/`SWPCHG2` per half-page. Each
pair collapses — 55 references. A guest reading its own keys through `ISK`
expects 2 KB semantics, so this reaches `DMKPRV`, not only paging.

### 3b. Retracted: `DMKVAT` is probably the *least* of the DAT work

I ranked its shadow-table translation the largest risk. That was asserted
before reading it, and it is wrong. **`DMKVAT` is already parameterised by
DAT architecture** — its prologue declares `GPR 9 = ARCHITECTURE CONTROL
INDEX`, and R9 indexes `ARCHTECT`, loaded from the guest's CR0 byte 1:

    PTEINCR   SIZE OF PAGE TABLE ENTRY
    PINVBIT   PAGE-INVALID BIT IN PTE
    ZEROBIT   "MUST BE ZERO" BITS IN PTE
    MAXSEGS  SEGMASK  SEGSHFT  PAGEMSK  PAGSHFT  PAGINCR  PAGTLEN

**And four of the eight variants already use fullword page table entries.**
`ARCHTECT`'s comment lists `X'60'`, `X'70'`, `X'A0'`, `X'B0'` as "FULLWORD
ENTRIES", and `CODE70` reads `SEGMASK X'7FF00000'` — bits 1-11, **2,048
segments of 1 MB, a 31-bit address space** — with `PTEINCR 4` and `PINVBIT
X'04'`, which in byte 2 of a fullword PTE is exactly where ESA/390 puts the
invalid bit. The selecting bit is CR0 bit 10, `0x00200000`: the same
encoding stock Hercules rejects in S/370 mode and the /380 patch
repurposes.

Caveats in 02-CP-VERIFIED.md — chiefly that the rows existing does not prove
the paths were exercised, `PAGTLEN 2048` is close to but not identical with
ESA/390, and the STE format differences are in code rather than tables.
**Is `CODE60`/`CODE70` live, or dead future-proofing?** You may know.

### 3c. The table work has different owners than I claimed

| Module | Refs | On my original list? |
|---|---|---|
| **DMKPGS** | **96** | **no** |
| **DMKATS** | **73** | **no** |
| **DMKBLD** | **63** | **no** |
| DMKVAT | 55 | yes |
| DMKPTR | 54 | yes |

Top five = 341 of 459. `DMKPAG` is not a gap — it is paging *device* code
and belongs to the I/O conversion.

### 3d. `TRANS` concentrates the translation interface

The statement count missed macro-generated instructions. The important one
is **`TRANS`, invoked 174 times** — CP's virtual-to-real translation:

    LCTL  C1,C1,VMSEG -  GET SEGMENT TABLE ORIGIN
    LRA   &RV,0(0,&UR)   AND DO HARDWARE TRANSLATE
    BC    8,TRN&NL       PAGE IS RESIDENT

Converting it once covers 174 sites. `VMSEG` (132 references) holds the
segment table designation, whose format is rearranged — S/370 puts length
in bits 0-7 and origin in 8-25, ESA/390 origin in 1-19 and length in 25-31.
Note also that Appendix F of the PoO lists "Changes to LOAD REAL ADDRESS",
so `LRA` semantics need checking rather than assuming.

### 3e. Retracted: `BAL`/`BALR` largely self-correct

I said CP's 3,600 link-register stores were each a latent bug. **They are
not.** `BAL`/`BALR` put the ILC, condition code and program mask in bits
0-7 only in **24-bit** mode; in 31-bit mode they set bit 0 to zero and put
the address in bits 1-31. A module converted wholesale to AMODE 31 needs no
attention. The exposure is **mode boundaries**, which is what broke test 3.

**`CALL`, invoked 4,104 times, is also safe.** It emits
`L R15,=A(&SUBR+X'80000000')`, marking pageable targets with **bit 0** —
exactly the bit ESA/390 leaves free, since addresses occupy bits 1-31 and
`BALR`/`BR` ignore bit 0.

**Your `SAVE.COPY` finding is the real version**, because it packs into bits
1-7, which do become address bits. The population is **582 `ICM`/`STCM`
sites with a 3-byte mask** — `DMKCQR` 41, `DMKCCW` 21, `DMKPTR` 20. The 421
`AL3` sites I had lumped in are mostly **format-0 CCW templates and CAW
stores**, which do not change.

---

## 4. I/O: ten instruction sites, not 1,493 references

CCWs do not change. The PoO states the S/370 24-bit format "is carried into
the 370-XA mode", selected by one ORB bit, and MVS/XA never converted —
GC28-1158-1 ch. 5: *"The EXCPVR interface supports only format 0 CCWs."*

**Every S/370 I/O instruction in `DMKIOS`:** `SIO` at 953 and 2335, `TIO` at
1010, 1104, 2284, 2299, `HDV` at 1021 and 1275, `TCH` at 1233 and 1242.
**Ten sites, every one a single instruction with the same `0(R1)` operand.**
The CAW is *built* in two places, 944 and 2321.

**And the status surface stays untouched.** Across CP: 800 bare `CSW`
(lowcore `X'40'`), 409 `IOBCSW`, 347 `CAW`, 230 `IOBCAW`, 131 `VDEVCSW` —
1,917 references. If the shim synthesises a CSW at `X'40'` after each
`TSCH`, **all of them keep working**, which is precisely what Hercules does
in the other direction: `scsw2csw()` copies SCSW+4..11 and overlays byte 0.

The hard spots are now located precisely:

     988   BC    4,IOSCC1       BRANCH IF CSW STORED
    1017   BC    4,TIOCC1       CC = 1    CSW STORED
    1029   BC    4,HIOCC1       CC = 1 CSW STORED
    1252   TM    CSW,X'04'      IS LOGOUT PENDING INDICATED ?

The first three are the **`SIO` condition-code contract** — `SIO` stores a
CSW synchronously with cc=1, `SSCH` only queues. About a dozen such
branches. The fourth is channel logout, replaced by the ESW/ERW and
`STCRW`. Everything else decodes the status *bytes*, which are bit-for-bit
identical between CSW and SCSW.

**And it is prototypable after all — I had this wrong.** I told you Hercules
ignores `ORB5_I`, the initial-status-interruption bit. It does not. Hercules's
release notes put "I/O initial status interruption" in version 1.39, 24
November 1999, and Hyperion 4.x implements the whole thing with citations —
`SCSW1_Z` for the zero condition code, and an `AIPSX()` routine building
"Figure 16-5, the Deferred-Condition-Code Meaning for Status-Pending
Subchannel". So the `SIO` gap can be tested standalone before any CP code is
touched, which is now the highest-value test outstanding. Gum, *IBM J. Res. Develop.* 27(6), free at
https://www.vm.ibm.com/history/50th/s370eavm.pdf : "To permit the condition
code to be set correctly and in a timely fashion for a START I/O (SIO)
instruction, an interruption can be requested from designated subchannels
when an I/O operation is initiated." Better known now than at M3.

Gum also confirms the guest model: "Except for the TEST CHANNEL (TCH)
instruction for System/370-mode guests, guest I/O instructions cause
interception."

---

## 5. What it means for CMS

**Stage 1 needs no CMS changes at all.** If CP runs ESA/390 internally but
presents **S/370-mode virtual machines**, CMS is untouched — it keeps
issuing `SIO`, keeps its S/370 tables, keeps its 16 MB. That is what VM/XA
did.

The honest cost: Stage 1 gives no guest more than 16 MB, so it does not
solve the application problem. It buys the foundation.

**Stage 2 is 31-bit virtual machines** — the `DMSxxx` modules,
mode-boundary base registers, CMS's own control-block layouts. Comparable
in size to CP's job, strictly downstream, and the point at which the RXC
heap limit actually moves.

---

## 6. Proposed milestones

**M0 — the assembler. Done.** CE's `ASSEMBLE` predates
1983 and knows neither the channel subsystem nor `BSM`. Twelve macros emit
the encodings:

    SSCH     MACRO
    &LAB     SSCH  &ORB
    &LAB     DS    0H
             DC    X'B233',S(&ORB)
             MEND

An S-type constant produces exactly the base-displacement an S-format
instruction wants, resolved through the active `USING`. **This is CP's own
idiom** — twenty-one sites already use `DC X'E6nn',S(...)` for the ECPS:VM
assists, including `DMKVATZP DC X'E60B',S(ARCHTECT,0(R9))`. Shipped as
`XAOPS.MACRO` plus `XATEST.ASSEMBLE`; `MACLIB GEN XALIB XAOPS`.

`MSCH`, `SSCH`, `TSCH`, `STSCH` and `BSM` are proven by execution in the
tests above. The other seven are confirmed against the z390 assembler's opcode
table, which is not derived from Hercules. **The `RSCH` discrepancy I flagged
was my error** — z390 lists `B238 RSCH, B239 STCRW, B23A STCPS, B23B RCHP`,
so `B23B` is RESET CHANNEL PATH, a different instruction, which is how it got
misread. `XATEST` is still worth assembling, because a second source agreeing
about an opcode says nothing about whether the macro emits the operand
correctly.

**M1 — CP IPLs in ESA/390 mode and writes to the console.** DAT off, no
paging, no guests, no DASD beyond IPL. Test 5 with real CP code, isolating
PSW format, lowcore, control registers and the console path. The stand-alone
utilities are out of scope, which removes 71 of the 166 I/O instructions and
224 of the CAW/CSW references.

**Pass: `DMKCPI966I Initialization complete`** — amended 30 September, because
the criterion as first written was *"a CP initialisation message"* and that
turned out to be satisfiable by the **failure** path. On 30 September a
converted CP printed

    DMKDMP908I SYSTEM FAILURE; CODE PRG018 PROCESSOR 00

which is CP writing to the console in ESA/390 mode through a converted console
writer, and is a real result — but it is an abend message, not initialisation.
The console *path* is proven; the milestone is not. `07-M1-WORKLIST.md` and
`WHAT-31BIT-NEEDS.md` both used the stricter target all along, and this is the
plan catching up with them rather than a change of scope. **General lesson:
a pass criterion phrased as "it produces output" is satisfied by a crash.**

**M1 is being run by strategy A, not the strategy B this plan implies —
recorded 30 September, after the fact.** `07-M1-WORKLIST.md` measured both and
chose B: load the nucleus with `loadcore` and `restart` into `DMKCPINT`,
skipping the IPL read. We are instead IPLing a written nucleus from real DASD,
as CE does. The difference is not small, and nobody recorded taking it:

| | modules | S/370 I/O | DAT refs |
|---|---|---|---|
| B — `loadcore`, as planned | 9 | 43 | **12** |
| A — IPL from DASD, as run | 12 | 79 | **82** |

`DMKCKP`, `DMKSAV` and `DMKBLD` are the three modules B exists to defer, and
they carry 70 of those 82 DAT references. That is why `DMKSAV`'s BC-mode PSWs
(`I-102`), `I-107`, `I-108` and `DMKDMP`'s `ISK` sites (`I-109`) have been on
the critical path at all: **none of them is in M1's planned population.** The
clause "no DASD beyond IPL" above is also no longer true of what runs — the
converted CP reads volume labels from sixteen packs.

A is not judged the wrong choice: it is the path CE actually uses, so it has to
work eventually, and it has surfaced defects B would have hidden until M2. But
the worklist's estimate has been quoted since as though B were still in force,
and it is not.

**M1 now requires part of B, and `LRA` is the reason — recorded 30 September
from `I-118`.** M1's premise is *"DAT off, no paging"*, and that premise still
holds: the PSW has DAT disabled throughout initialisation. It does not help.
**`LRA` translates explicitly, whatever the PSW says**, so CP's 174 `TRANS`
sites consult the segment and page tables during initialisation regardless of
whether DAT is enabled. CP builds those tables for itself, in System/370 format,
and loads `CR1` with a System/370 segment-table designation — after which the
first `LRA` raises a **translation-specification exception**, interruption code
`X'12'`, which is what `PRG018` spells: 018 decimal is X'12'.

Measured from CP's own dump: `CR1 = 05FFC840`, and storage at `X'FFC840'` holds

    F00561D0  F00562A8  F0056380  F0056458  ...

CP's segment table, with the high nibble `F` as `SEGPLEN` — a page-table length
of 16 pages for a 64 KB segment. Under ESA/390 those bits are part of the
page-table origin, the length lives in bits 28–31, and **bit 0 is unassigned and
must be zero**; it is 1 in every entry.

`06-LEDGER.md`'s test 8 predicted this from the other direction. It found `LRA`'s
*operand* truncated in 24-bit mode and used that to move AMODE 31 into M2. The
same property of the same instruction now pulls the **segment-table format** into
M1. So the boundary is:

| | Was | Now |
|---|---|---|
| **M1** | architecture only | architecture **plus** a valid ESA/390 STD and STE format for the tables CP builds for itself |
| **M2** | all of the DAT work | the rest of it: PTE widening, the 70 shift sites, AMODE 31, `DMKBLDRT`'s ABI |

**No site count changes — only the sequencing.** The STE work was always in the
358 format-sensitive references; what moved is *when* it has to be done, and it
turns out it cannot be deferred behind a console message.

**M2 — DAT on, ESA/390 tables, still no guests, and no shared segments.**
`CORE`, `DMKPTR`, `DMKPGS`, `DMKBLD`, `TRANS`. **This no longer waits on
you.** It previously did, on §3a; per 05-CP67-PRIOR-ART.md there is no
decision left to make, and shared segments move to M3 because CP does not
need them to run with DAT on — CMS needs them, being IPL'd by name.

**Two amendments to M2, both dated after this section was written:**

- **AMODE 31 is inside M2**, not later. Ledger test 8 found that `LRA`
  truncates its *question* to 24 bits: in AMODE 24, `LRA 2,0(0,6)` with
  R6 = `01005000` answers cc=0 with `00005000`, correctly describing segment 0
  page 5 instead of segment 16 page 5. The result is not truncated; the operand
  address is. So CP's 174 `TRANS` sites cannot ask about an above-the-line
  virtual address while CP runs AMODE 24, **and the failure is silent** — a
  plausible real address from the wrong page. The `TRANS`-bearing modules must
  be AMODE 31 before paging above the line means anything.
- **`DMKBLDRT`'s interface is designed before M2 starts, not during it.** Mike
  ruled on 30 September that virtual 31-bit addressing is mandatory
  (`WHAT-31BIT-NEEDS.md`), which promotes this from "largest undesigned item"
  to first design decision. It packs two addresses into one fullword as
  4 zero + 8 segment + 4 page bits each — 256 × 16 × 4 KB = **exactly 16 MB, by
  construction**, the one place the limit is welded into the definition of a
  virtual machine. ESA/390 needs 19 bits per address, so two do not fit, and it
  is reached by SVC, so this is an ABI change across 24 callers
  (`DMKBLDRT` 8, `DMKBLDRL` 5, `DMKBLDVM` 8, `DMKBLDEC` 3). No replacement
  format is proposed anywhere yet. *(superseded — see status note)*

**M3 — one S/370-mode guest logs on and runs CMS.** `DMKVAT` plus `DMKPRV`,
now also the frame-level shared-segment rework in `DMKATS` and the `NAMESYS`
path. Less frightening than it was on the `DMKVAT` side, per §3b — and CP-67's
PLM offers an *image segment table* trick worth stealing: keep a pre-built
shadow segment table with every entry flagged unavailable and block-move it to
reset, instead of walking and invalidating, on a path taken every time a guest
loads CR0 or a page is stolen.

**M4 — two guests, isolated.** Your `VK-AC-08` already requires this.

**M5 — real storage above 16 MB.** Added 30 September on Mike's decision, and
the reason it is worth writing down rather than leaving implicit is that it was
*missing*: `WHAT-31BIT-NEEDS.md` separates "31-bit" into three independent
things — **A** ESA/390 architecture, **B** 31-bit virtual storage, **C** real
storage above the line — and M0–M4 covered A (M1) and B (M2, M3) while never
naming C. Deferring it is correct; having no milestone for it made a deliberate
deferral look like an oversight.

Three gates, and they lift **together or not at all**, because each one alone
makes the others pointless (`17-CARRY-FORWARD-64.md`):

| Gate | Blocks | Size |
|---|---|---|
| `ISK`/`SSK`/`RRB` mask the operand to 24 bits | managing keys above the line | **67 sites, 17 modules** |
| Format-0 CCWs, including IDAWs | I/O to storage above the line | **240 CCWs, 23 nucleus modules** |
| 24-bit fields in `CORTABLE` and friends | addressing the frames at all | **no count exists** |

Why it is genuinely separable, not just postponed: all three key instructions
take a *real* operand address (`GR_L(r2) & 0x00FFF800`), so the 24-bit ceiling
is on **real** storage only — `23-STORAGE-KEYS.md` establishes that *"CMS could
run with a full 31-bit virtual address space on a 16 MB host, with `ISK`/`SSK`
untouched and CP paging as it does today."* Guest channel programs need no
change either, because `DMKCCW` translates them into real addresses below the
line rather than passing them through.

Two conveniences worth remembering when M5 is picked up. `ISKE`, `SSKE`, `RRBE`
and `IVSK` are all `GENx370x390x900`, so **M5's key work can be written and
tested on CE exactly as it runs today, in S/370 mode** — it does not wait on
M1. And CE already runs with 4 KB keys (`CPCREG0 DC X'81800CC0'`) while
`DMKPTR` still issues paired 2 KB operations, so collapsing those pairs is
redundancy removal rather than a behaviour change.

Two warnings. `DMKPTR` holds a third of the 67 sites and is the page manager —
*"the opposite of a low-risk starting point"* — so the standing order within the
family is the 44 sites outside `DMKPTR` first, `DMKPTR` last and alone. And
`RRB`→`RRBE` is the worst of the three: the operand moves from
base-displacement into a register, so each of `DMKPTR`'s 13 sites needs an
address materialised first, and therefore **a spare register in CP's tightest
code**.

**M5 is not wholly in the future.** Two of the 67 sites are already on M1's
critical path, because they run during initialisation and abend handling:
`I-104`'s `SSK` in `DMKCPI` (storage sizing, fixed) and `I-109`'s four `ISK`s
in `DMKDMP` (the dump, in progress). That is the point `I-104` made and it
generalises to every deferred axis: **ask which single site runs earliest, not
how large the axis is.** A 67-site axis with two sites on the boot path is not
a deferrable axis; it is a two-site job plus a deferrable axis.

Against your framework: the six tests are the hardware half of `EX-AC-02`
and `VK-AC-07`; §3 and §4 are input to the "channel/I/O formats" line item.
Your warning that "changing Hercules's architecture setting cannot perform
those software changes" is exactly right — §3 enumerates what it does not
perform.

---

## 7. On `wide/`, and what is being asked

`systems/vmce/source/wide/README.md` is freestanding z/Architecture — GCC
s390x LP64, `z900`, ELF64 images loaded with `loadcore` and
`restart`/`runtest`, with DAT fixtures already in W-02/03. **The method is
the same as these six tests**, so the harnesses could share tooling. And
`wide/` is explicitly "not an operating system or a CMS boot image", so it
reads as a 64-bit *application* environment proof, leaving the kernels
alone.

Mike's stated preference is a compatible 31-bit VM/370 CE first, 64-bit
later. **If `VMCE-WIDE-PLAN.md` has in fact selected a direct 64-bit
destination that supersedes the 31-bit kernel work, say so** — it changes
everything in §6 and is better said now.

Otherwise:

**Nothing on `CMSOLD` after all — but a sanity check on why.** I twice sent
you a shared-segment worry: first that every saved-system definition changes
by 16x, then that `CMSOLD` forces the first megabyte common. Both assumed
sharing must be segment-granular. **CP-67 ran 1 MB segments and shared at
4 KB granularity**, by giving each virtual machine its own page table and
sharing the frames instead of the table; `SWPTABLE FIRSTSP=/LASTSP=` declares
shared **pages** where `SYSHRSG=` declares shared **segments**. So VM/370's
64 KB segment is downstream of its decision to share page tables, and
ESA/390 does not force the granularity loss. 05-CP67-PRIOR-ART.md has the
quotations. What I would value is you telling me whether that reading of
`DMKATS` is right, because it moves the work into that module rather than
removing it.

**Comments on §3b** — whether `ARCHTECT`'s fullword-entry rows are live or
dead future-proofing.

**Comments on §6** — whether M1..M4 fit your acceptance criteria.

**A one-time asset handover.** Your build guide names inputs not in Git:
`RECOVERED-RECORDS` (the validated native export with `inventory.json` and
`.records` files), `ASSET-ROOT` with `vendor/vm370ce-1.1.2/disks`, and the
pinned OSMACRO/DOSMACRO and native assembler/load/transfer tools. Also
whether `lab.crexx` runs on Windows with Hercules 3.07, or whether moving to
4.9.1 first is shorter.

**Repository access.** `mainframe-lab` is not reachable to Mike's tooling; a
collaborator invite would unblock a clone and a fork. The 31-bit work should
track your maintenance rather than diverge from a snapshot, so a fork with
periodic rebases seems right — but it is your repository.

**No ongoing time.** Mike can proceed on M0 validation, a DASD-read
standalone test, inventory of the `.MACRO` and `.COPY` members, and the
three /380 measurements without further input.

One incidental that may be worth more than the rest: you are on Hercules
4.9.1, so `FEATURE_370_EXTENSION` is available — `archlvl S/370` then
`facility enable HERC_370_EXTENSION`. It gives nothing for addressing, but
it backports relative branches, immediates, MVCLE and CMPSC into S/370
mode, which may be worth something to the cREXX VM and cc370 codegen
entirely independently of this.
