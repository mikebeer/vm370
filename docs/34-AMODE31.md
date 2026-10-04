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

## Step 1 (built 4 October, XA0046DK + PSA XA0001DK): the LRA alone runs in AMODE 31

The LRA runs in AMODE 31 and CP returns to AMODE 24 straight after it. Two
shapes, chosen by the macro at expansion time:

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
TRL31    LRA   R2,0(0,R1)     TRANSLATE, IN AMODE 31
         BSM   0,R15          BACK TO THE CALLER'S MODE
```

`BASSM R15,R15` takes the branch target from R15 (bit 0 on: AMODE 31,
address X'420') before it stores the return address — the next instruction,
with bit 0 off because the caller is in AMODE 24 — into R15. `BSM 0,R15`
goes back and restores AMODE 24. The PSA is at real 0 and every module
addresses it from base register 0, so the stub needs no base register, and
`ATRL31` is a 3-byte adcon behind an `X'80'`, so the loader relocates bytes
1-3 only and there is no question of an RLD on bit 0. +2 bytes a site.

**The other register forms** (`TRANS 9,1`, `7,1`, `2,8`, `2,5`, `8,1`, …;
twelve sites) keep the LRA inline:

```
         LA    R15,TR&NL.L    THE LRA, TO RUN IN AMODE 31
         O     R15,=X'80000000' (CP ITSELF RUNS AMODE 24)
         BSM   0,R15
TR&NL.L  LRA   &RV,0(0,&UR)   AND DO HARDWARE TRANSLATE
         LA    R15,TR&NL.B    BIT 0 OFF: BACK TO AMODE 24
         BSM   0,R15          CC STILL LRA'S
TR&NL.B  DS    0H
```

+16 bytes a site; DMKPTRAN's own `LRA R7,0(,R1)` uses the same seven cards.
The first build of step 1 (i221) used this shape everywhere, and **DMKMON —
X'FF8' bytes long on a single 4 KB base — lost its last four literals to
the 16 bytes its one TRANS grew by** (`IFO209` ×4, `I-216`). The stub is
the answer to that, not an optimisation: call-site size is a hard
constraint in these modules (`I-56` found the same wall in DMKDMP).

Why this is sound:

- **R15** is the scratch register because the macro's non-resident path,
  `CALL DMKPTRAN`, has always returned with R15 = DMKPTRAN's entry address
  (SVC 12 restores R14/R15 from their values at the SVC, and CALL loads
  R15). No site can have depended on R15 surviving a TRANS. The two bare
  `TRANS` sites with no options (DMKCCW `CCWNXT9`, DMKISM) were read: R15 is
  dead at both.
- **The condition code** the following `BC` tests is LRA's: `L`, `LA`,
  `BASSM` and `BSM` leave it alone; `O` sets it but runs before the LRA.
- **Returning to AMODE 24**: BASSM saves the caller's mode in bit 0 of R15,
  and in the inline form `LA` in AMODE 31 yields bit 0 zero; `BSM 0,R15`
  takes either as "set AMODE 24".
- **Nothing else in CP notices** while real storage stays below 16 MB: every
  real address CP computes fits 24 bits, so the 215 `LA Rn,0(,Rn)` strip
  sites (`I-126`) and the longhand `X'00FFFFFF'` masks keep working. They
  become work only when CP itself goes AMODE 31 (step 2).

Cost: about 300 bytes of nucleus. A macro change, so a full rebuild.

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

## Step 2 (planned): CP itself at AMODE 31

Set bit 32 in the IPL PSW (`DMKSAV IPLDATA`), the new PSWs in `DMKPSA` and
the wait PSWs; then every `LA Rn,0(,Rn)` that strips flags from a packed
pointer becomes `N Rn,=A(X'00FFFFFF')` (or the pointer loses its flags), and
`BAL`/`BALR` results carry bit 0 instead of ILC and CC, which the places that
read those bits (DMKPRG, trace) must stop expecting. `tools/idiom.py` lists
the sites. Only needed when CP's own control blocks or the guest's real frames
live above 16 MB — i.e. with step 3 (M5), not before.

## Verification planned for step 1

`def stor 32m`; `st s1ff0000 deadbeef`; `d ff0000.10` shows zeros;
`d 1ff0000.10` shows `DEADBEEF`; `st s1000000 cafe0001`; `d 0.10` unchanged;
then the IPL CMS regression (w46) unchanged.
