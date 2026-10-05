# AMODE 31: how CP reaches virtual storage above 16 MB — M2's second half

4 October 2026. `I-208` measured the gap left after the DAT tables: in a 32M
virtual machine `st s1ff0000 deadbeef` showed up at `ff0000`, and
`st s1000000` at `0`. The tables are right; the question put to them is not.

## The mechanism, precisely

CP runs with PSW bit 32 off — AMODE 24. LOAD REAL ADDRESS forms its
second-operand address under the current addressing mode, so `LRA R2,0(,R1)`
with R1 = `01FF0000` asks about `FF0000` (README, "AMODE 31 is a
prerequisite", measured with `08-lra.rc`: cc 0 and a plausible real address
for the wrong page). Every `TRANS` — 174 sites in 66 modules — is that LRA,
and DMKPTRAN's own `LRA R7,0(,R1)` is the same instruction. Everything after
the LRA is register arithmetic on the full 32-bit value (`SRL 20`, `N
X'000FF000'`), and every CP control block lives below 16 MB, so the
truncation is the whole fault.

## Step 1 (built 4 October, XA0046DK + PSA XA0001DK + EQU XA0037DK): the LRA alone runs in AMODE 31

Three findings shaped this, each from a failed build (I-216, I-218 and w53):

1. **Every guest is a 24-bit machine today**, and CP's own callers know it:
   DMKDGD hands TRANS `L R1,RCWADDR` — the CCW with the command code still
   in byte 0 — DMKVSP hands it the CAW with the key in byte 0, DMKVCN,
   DMKVIO and others likewise; a scan of all 211 TRANS/DMKPTRAN sites shows
   it is the rule, not the exception. They relied on `LRA` in AMODE 24
   ignoring byte 0 and on DMKPTRAN's first instruction, `LA R1,0(,R1)
   STRIP HIGH BYTE`. Removing that strip (i225) cost every CMS minidisk:
   `DMSACC112S DEVICE ERROR`, then BLD002 (w53). So **masking a guest
   address to 24 bits is correct for a 24-bit guest**, and only a caller
   that knows it holds a clean 31-bit address may say otherwise.
2. **Call-site size is a hard constraint** (I-56 again): the first inline
   wrapper, +16 bytes a site, pushed DMKMON (X'FF8' on one base register)
   past its literal pool (I-216). Hence a shared stub.
3. **No literal before ENTER** in a two-base module (I-218).

The design that came out:

**The common form, `TRANS 2,1` (139 of CP's 151 sites)** calls a stub in the
PSA:

```
         L     R15,ATRL31     THE LRA IN AMODE 31: PSA STUB
         BASSM R15,R15        LRA R2,0(0,R1), AND BACK
```

and the stub, at real X'41C' in `PSA.MACRO` (carved from the reserved `DS 5F`
before `INSTWRD1`, so no other PSA offset moves; storage only in DMKPSA, a
DSECT everywhere else):

```
ATRL31   DC    X'80',AL3(TRL31) 31-BIT ENTRY, FOR BASSM
TRL31    LR    R2,R1          24-BIT GUEST: THE ADDRESS IS
         N     R2,XRIGHT24    BITS 8-31, WHATEVER BYTE 0 IS
         LRA   R2,0(0,R2)     TRANSLATE, IN AMODE 31
         BSM   0,R15          BACK TO THE CALLER'S MODE
```

`BASSM R15,R15` takes the branch target from R15 (bit 0 on: AMODE 31,
address X'420') before it stores the return address — the next instruction,
with bit 0 off because the caller is in AMODE 24 — into R15. `BSM 0,R15`
goes back and restores AMODE 24. The PSA is at real 0 and every module
addresses it from base register 0, so the stub needs no base register, and
`ATRL31` is a 3-byte adcon behind an `X'80'`, so the loader relocates bytes
1-3 only. +2 bytes a site. Today the stub always masks to 24 bits, so every
guest translation behaves exactly as it did; when 31-bit guests arrive (step
3) the stub will test the VMBLOK mode flag and skip the mask for them.

**`OPT=(...,AMODE31)` — the caller holds a clean 31-bit address.** A new
TRANS option, and a new DMKPTRAN PARM flag `AMODE31 EQU X'02'` (EQU COPY;
X'02' and X'01' were free). The macro then expands the LRA inline, unmasked:

```
         LA    R15,TR&NL.L    THE LRA, TO RUN IN AMODE 31
         O     R15,=X'80000000' (CP ITSELF RUNS AMODE 24)
         BSM   0,R15
TR&NL.L  LRA   &RV,0(0,&UR)   AND DO HARDWARE TRANSLATE
         LA    R15,TR&NL.B    BIT 0 OFF: BACK TO AMODE 24
         BSM   0,R15          CC STILL LRA'S
TR&NL.B  DS    0H
```

and `LA R2,BRING+DEFER+AMODE31` passes the flag to DMKPTRAN, whose entry is
now

```
DMKPTRAN TM    SAVER2+3,AMODE31 CLEAN 31-BIT ADDRESS? (I-208)
         BO    PTRA31         YES: KEEP BITS 1-7
         LA    R1,0(,R1)      24-BIT CALLER: STRIP BYTE 0
PTRA31   SLL   R1,1           BIT 0 OFF, NO LITERAL BEFORE
         SRL   R1,1           ENTER (I-218)
```

(SAVER2 is the caller's R2 as the SVC handler saved it, so the flag is
readable before ENTER.) The users today are the console: DMKCDS's STORE
TRANS (00511000) and DMKCDB's DISPLAY TRANS/DMKPTRAN sites (00975000,
01000300, 01056900, 01454000, 01471110), whose hexloc is a 31-bit number
whatever mode the guest is in; two `LA` address sums on that path
(`LA R1,2047(R1)`, `LA R1,1(R14,R1)`) became adds. The other register forms
(`TRANS 9,1`, `7,1`, `2,8`, `2,5`, `8,1`, …; twelve sites) also take the
inline wrapper, unmasked, exactly as the original macro left their operands;
DMKPTRAN's own `LRA R7,0(,R1)` uses the same seven cards after the entry
has masked R1.

Why this is sound:

- **R15** is the scratch register because the macro's non-resident path,
  `CALL DMKPTRAN`, has always returned with R15 = DMKPTRAN's entry address
  (SVC 12 restores R14/R15 from their values at the SVC, and CALL loads
  R15). No site can have depended on R15 surviving a TRANS. The two bare
  `TRANS` sites with no options (DMKCCW `CCWNXT9`, DMKISM) were read: R15 is
  dead at both.
- **R2** is the result register in the stub form, so masking into it costs
  nothing: LRA writes R2 on every condition code.
- **The condition code** the following `BC` tests is LRA's: `L`, `LR`,
  `LA`, `BASSM` and `BSM` leave it alone; `N` and `O` set it but run before
  the LRA.
- **Returning to AMODE 24**: BASSM saves the caller's mode in bit 0 of R15,
  and in the inline form `LA` in AMODE 31 yields bit 0 zero; `BSM 0,R15`
  takes either as "set AMODE 24".
- **Nothing else in CP notices** while real storage stays below 16 MB: every
  real address CP computes fits 24 bits, so the 215 `LA Rn,0(,Rn)` strip
  sites (`I-126`) and the longhand `X'00FFFFFF'` masks keep working. They
  become work only when CP itself goes AMODE 31 (step 2).

Cost: about 300 bytes of nucleus. A macro, EQU and PSA change, so a full
rebuild.

## What step 1 does not do

- A **guest** running in 31-bit mode (PSW bit 32) is not admitted yet: DMKPRV's
  LPSW simulation and DMKDSP's PSW handling treat bit 32 as a specification
  error, and guest operand addresses are formed with `LA` (`DMKPRV 00903000
  LA R6,0(0,R6) 24-BITS ONLY, PLEASE`). CE's CMS is a 24-bit program and does
  not need it; cREXX and a 31-bit CMS (M5) do.
- **Real storage above 16 MB** (R-25, R-27): CCW data addresses are 24-bit in
  format 0, the page frame address in a PTE is already 31-bit, DMKPTR's
  free-list arithmetic and the CORTABLE index (`SRL 8`) are fine; the gate is
  the Hercules `MAINSIZE` and the format-1 CCW question.
- The 65,536-page (**256 MB**) virtual ceiling in DMKBLDRT's packed range
  (`I-185`, `I-203`).

## Step 2 — done, 5 October 13:22 UTC (i241, SNAP-I241): CP itself at AMODE 31

Part 1, the sweep (I-224, XA0047DK): `tools/strips.py` inventoried 275
`LA Rx,0(,Ry)` sites (241 in 78 nucleus modules); 209 in 74 modules became
`N Rx,XRIGHT24` (copies: `LR` + `N`), the rest already masked by earlier
decks. Behaviour-neutral under AMODE 24 and tested so first (i232 = w62).
Part 2, the flip (XA0048DK): DMKCPI's `CPIPSWS` (external, SVC, program,
I/O, machine-check, restart) and DMKMCH's five handler PSWs carry bit 32 as
`X'80',AL3(entry)`; SVC 8/12 carry the mode through SAVERETN; the guest keeps
its own 24-bit PSW. Two modules keep their 24-bit strips because they run
**inside the guest**: DMKLD00E (the loader) and DMKVMI (the IPL simulator).

What the sweep cannot see — the six idioms, each found by running and each
now with its inventory:

| | Idiom | Where it bit | Fix |
|---|---|---|---|
| I-225 | two-register `LA` sum that lands exactly on 16 MB | DMKFRE FREE08 (savearea `FFFFF938`, silent death at IPL) | `LR` + `ALR` |
| I-226, I-232 | a CCW word (`RCWADDR`, command code in byte 0) used as a base or index | DMKDGD IDAL, DMKUNT IDASET, DMKCCW, DMKDIB, DMKTRK, DMKVCA | `N Rx,XRIGHT24` after every `L Rx,RCWADDR` that has no strip of its own (`grep 'L  *R.*,RCWADDR'`) |
| I-228 | `BALR Rx,0` as a condition-code save, `SPM Rx` to restore | DMKLNK: every directory LINK "ALREADY DEFINED" | `IPM Rx` (XAOPS), 16 sites in 13 modules; `BALR Rx,0` that only sets a base is harmless |
| I-229 | the trace subroutines read the CC out of a `BAL` **link** register and return with `B 2(,Rlink)` | DMKCPI's IPL device check saw every DMKRIO device as present; ENABLE drove SSCH at SSID 0 (PRG021) | `IPM Rlink` at entry; the link masked with `SLL 8`/`SRL 8` after the `SPM` (N would set the CC it just restored) |
| I-230 | `doublewords || address` handed to DMKFRET as one word | DMKERMSG → PRG005 at `DEF STOR` after IPL CMS | FRET/FRETR strip byte 0 on entry; the CP-wide contract survives until M4 |
| I-233 | `ICM Rx,B'0111',field+1` leaves byte 0 of Rx as it was | DMKPTR RSPGLOOP at AUTOLOG1's LOGOFF | `SR Rx,Rx` before every ICM-3 whose register is not provably clean: 59 of 100 sites, 29 modules, generated by rule (`icm3cards`), five hand-listed exceptions |

`tools/strips.py` now lists `balr0` and `spm` sites with the CC source
(`balr`, `bal-link`, `ipm`, `load`, `caller`) and `icm3` sites; the two
remaining `SPM` sites it reports as `bal-link` are DMKRGA's (bisync remote
3270, not in our configuration). The ESA/390 `IPM` is the only new opcode.

Three tool lessons came with it: a module's load address is not where a
pageable module executes, so breakpoints need the map from the punched
nucleus deck (`build.sh write` keeps it; I-227); Hercules 3 stops on a
breakpoint once per run, so one probe is one run; and a shared macro that
changes is covered when every module that invokes it is reassembled
(`snapshot.py macro_users`), while a deck anchored on a record an earlier
deck removed is caught by replchk's fifth invariant (ANCHOR-GONE).

Verification (i241, w109–w111): IPL, `enable all`, LOGON with every LINK,
AUTOLOG1's full init (CPWATCH, CMSBATCH, WAKEUP), `IPL 190` at 16M (CMS from
disk, QUERY DISK), `IPL CMS`, EDIT + DIRECT recompile, `DEF STOR 32M`, the
stores and displays above 16 MB of the step-1 run, IPL CMS in the 32M
machine, LOGOFF, operator SHUTDOWN; the 15M GCCLIB/autolog regression
unchanged. Known cosmetics: `d 1ffffff.10` prints its range in 6 hex digits;
`IPL 190` in a 15M machine is CMS's own `DMSINI260T` (CMS loads high).

What step 2 does not do: real storage above 16 MB (M4: format-1 CCWs, the
packed `count || address` words, `XPAGNUM`); 31-bit guests (step 3); the
256 MB per-VM ceiling (I-185).

## Step 3 (scoped 5 October): a guest in 31-bit mode

A guest with PSW bit 32 on runs in AMODE 31 on the hardware the moment
DMKDSP loads its PSW; everything else is CP's simulation of that guest, which
assumes a 24-bit machine in exactly the places the sweep touched. Measured:

- **PSW validity.** DMKDSP `GETMASK` rejects any bit in `VMPSW+4` (`TM
  VMPSW+4,X'FF'`, 01342000); DMKPRV's LPSW (`CLI VMPSW+4,0`, 00741000) and
  DMKSVC's new-PSW load (`CLI VMPSW+4,0`, 00419000) likewise. Three sites:
  allow `X'80'` for an EC-mode guest, keep refusing bits 33-39.
- **Guest addresses CP forms.** The sweep's `N Rx,XRIGHT24` is right for CP's
  own packed pointers and wrong for a 31-bit guest's operand addresses: DMKPRV
  00395100, 00903000, 00920000 (`24-BITS ONLY, PLEASE`), the TRANS stub's
  mask, DIAG handlers that take a guest address (DMKHVC: 9 swept sites), the
  console STORE/DISPLAY (already `AMODE31`), DMKVSI/DMKCCW's CAW and CCW
  address handling (format-0 CCWs are 24-bit by definition; a 31-bit guest
  still uses them, and IDAWs carry 31-bit addresses). Each such site becomes
  mode-dependent: mask when the VMBLOK says 24-bit, keep bits 1-7 when it
  says 31. The mode lives in one new VMBLOK flag, set from the guest's PSW bit
  32 whenever CP accepts a PSW (DSP/PRV/SVC above), so the test is one `TM`.
- **Interrupt reflection.** DMKPSA/DMKPRG/DMKIOT/DMKSVC/DMKDSP store the
  guest's old PSW and load its new one as 8 bytes; bit 32 travels with them
  unchanged, so only the validity checks and the ILC/CC arithmetic on
  `VMPSW+4` (DMKPRG 00290000–00653000, DMKPRV 01594000–01709000: `L R1,VMPSW+4`
  / add ILC / `ST`) need to keep bit 0 — an `O` of the saved bit after the
  add, or arithmetic on bits 1-31 only.
- **Shadow tables** (DMKVAT) only matter for a guest that runs its own DAT;
  CMS does not. A 31-bit guest's own segment tables would be ESA/390 format
  — out of scope until something needs it.
- **CMS.** CE's CMS is a 24-bit program: `DMSINI` sizes storage with DIAG
  X'60', loads high (I-232's `DMSINI260T`), and every CMS address is 24-bit.
  A 31-bit CMS is M5; step 3 gives it the machine to run on and is verified
  with a test program IPLed from the reader that sets bit 32, stores above
  16 MB and takes an interrupt there.

Estimate: ~25 sites in 8 modules plus the VMBLOK flag; two builds.

## Verification of step 1 — done, 5 October 01:54 UTC (w62, SNAP-I231)

`def stor 32m` → `STORAGE = 32768K`; `st s1ff0000 deadbeef` → `d ff0000.10`
all zeros, `d 1ff0000.10` = `DEADBEEF`; `st s1000000 cafe0001` → `d 0.10`
unchanged, `d 1000000.10` = `CAFE0001`; `d k1ff0000` → `01FF0000 TO 01FF07FF
KEY = 06`; a store at 1FF0FF8 lands at 1FF0FF8; `d 2000000.10` → `EXCEEDS
STORAGE`; then `IPL CMS`, `QUERY DISK`, `LOGOFF`, operator `SHUTDOWN`, all
clean. w63: the 15M GCCLIB / autolog regression unchanged. Known cosmetic
leftover: `d 1ffffff.10` parses its range in 24 bits (`INVALID RANGE -
FFFFFF-00000E`) and the non-addressable "TO" address uses `XPAGNUM`
(X'00FFF000') — both for the I-126 sweep.

## The seven things step 1 had to learn (I-216 – I-223)

| | Finding | Rule |
|---|---|---|
| I-216 | +16 bytes a TRANS site cost DMKMON (X'FF8' on one base) its literal pool | call-site size is a hard constraint; shared stub in the PSA |
| I-218 | `N R1,=X'7FFFFFFF'` as DMKPTRAN's entry instruction read the literal off the caller's R10 | no literal, no R10 reference, before ENTER in a two-base module |
| I-219 | callers hand TRANS CCW/CAW words with byte 0 in use; CMS lost its minidisks without the strip | a 24-bit guest's addresses are masked to 24 bits; only `OPT=AMODE31` callers are 31-bit |
| I-220 | `TM SAVER2+3` at the entry instruction read the previous caller's R2 | SAVER2 is written by ENTER; test after it |
| I-221 | `DEF STOR 32M` built a 16-entry segment table (CR1 STL 0) | DMKBLDRT's end page is a halfword, not `F4095` |
| I-222 | `DMKPTR410W` on every first touch above 16 MB | SAVEWRK9 byte 0 is the page-in error switch; clear it with XC, not with the address |
| I-223 | CP looped in DMKPGS's release walk on the next IPL | addresses CP computed over the whole machine are 31-bit and say so (AMODE31) |

Each was found by a Hercules breakpoint, register dump or instruction trace
over the HTTP console, not by reading; the first three guesses of the
evening were all wrong.
