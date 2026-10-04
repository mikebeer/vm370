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

## Step 1 (built 4 October, XA0046DK): the LRA alone runs in AMODE 31

```
         LA    R15,TR&NL.L    THE LRA, TO RUN IN AMODE 31
         O     R15,=X'80000000' (CP ITSELF RUNS AMODE 24)
         BSM   0,R15
TR&NL.L  LRA   &RV,0(0,&UR)   AND DO HARDWARE TRANSLATE
         LA    R15,TR&NL.B    BIT 0 OFF: BACK TO AMODE 24
         BSM   0,R15          CC STILL LRA'S
TR&NL.B  DS    0H
```

in `TRANS.MACRO`, and the same seven cards around DMKPTRAN's LRA. Why this
is sound:

- **R15** is the scratch register because the macro's non-resident path,
  `CALL DMKPTRAN`, has always returned with R15 = DMKPTRAN's entry address
  (SVC 12 restores R14/R15 from their values at the SVC, and CALL loads
  R15). No site can have depended on R15 surviving a TRANS.
- **The condition code** the following `BC` tests is LRA's: `O` sets it but
  runs first; `LA` and `BSM` leave it alone.
- **Returning to AMODE 24**: in AMODE 31 `LA` yields a 31-bit address with bit
  0 zero, which is what `BSM 0,R15` takes as "set AMODE 24".
- **Nothing else in CP notices** while real storage stays below 16 MB: every
  real address CP computes fits 24 bits, so the 215 `LA Rn,0(,Rn)` strip
  sites (`I-126`) and the longhand `X'00FFFFFF'` masks keep working. They
  become work only when CP itself goes AMODE 31 (step 2).

Cost: six instructions per site, about 3.5 KB of nucleus. A macro change,
so a full rebuild.

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
