# VM/370 CE 31-bit — what is proven, and a proposed staged plan

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

**The consequence I most want your judgement on is shared segments.**
`DMKATS` and the named-saved-system machinery are built on 64 KB
granularity; ESA/390 makes the minimum shareable unit 1 MB. Every existing
saved-system definition changes granularity by 16×, and anything sharing
less than a megabyte must over-share or be redesigned. No table row or
parameter solves that — it is a design decision about compatibility.

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

**One thing Hercules cannot prototype.** It ignores `ORB5_I`, the
initial-status-interruption bit — the facility IBM added for exactly the
`SIO` condition-code problem. Gum, *IBM J. Res. Develop.* 27(6), free at
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

**M0 — the assembler. Done, awaiting validation.** CE's `ASSEMBLE` predates
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
tests above; the other seven were read from Hercules source and `XATEST`
checks them against a listing. `RSCH` is disputed — `B238` in the Hercules
dispatch table, `B23B` in a reading of GX20-0157-2.

**M1 — CP IPLs in ESA/390 mode and writes to the console.** DAT off, no
paging, no guests, no DASD beyond IPL. Test 5 with real CP code, isolating
PSW format, lowcore, control registers and the console path. The stand-alone
utilities are out of scope, which removes 71 of the 166 I/O instructions and
224 of the CAW/CSW references. Pass: a CP initialisation message.

**M2 — DAT on, ESA/390 tables, still no guests.** `CORE`, `DMKPTR`,
`DMKPGS`, `DMKBLD`, `TRANS`. The 64 KB → 1 MB change lands here, so §3a
needs settling first.

**M3 — one S/370-mode guest logs on and runs CMS.** `DMKVAT` plus
`DMKPRV`. Less frightening than it was, per §3b.

**M4 — two guests, isolated.** Your `VK-AC-08` already requires this.

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

**Comments on §3a** — the segment size change and shared segments. The item
most likely to need a design decision, and the one I am least able to
judge.

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
