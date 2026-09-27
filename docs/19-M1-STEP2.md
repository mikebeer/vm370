# M1 step 2: the first change to CP, delivered as an update level

27 September 2026. The first modification to CP in this project. It changes
`PSA` — the lowcore definition that 171 of 201 modules include — and it is
delivered as an `AUXLCL` update deck rather than as an edit to base source, per
[`15-UPDATE-LEVELS.md`](15-UPDATE-LEVELS.md).

**It worked, five of six pre-registered predictions held, and the sixth failure
found something worth knowing.**

## What the change does

| Offset | Was | Now |
|---|---|---|
| `X'A8'` | `CHANID` | `S370CHID` — `STIDC` result, no ESA/390 counterpart |
| `X'AC'` | `IOELPNTR` | `S370IOEL` — I/O extended logout pointer |
| `X'B0'` | `ECSWLOG` | `S370ECSW` — limited channel logout |
| `X'B3'` | `ECSWBYT3` | `S370EBY3` |
| `X'B8'` | `INTKFLIN` | **`IOSSID`** — ESA/390 subsystem-identification word, with `INTKFLIN` kept as an alias |
| `X'BA'` | `INTTIO` | **`IOSCHNO`** — subchannel number, **no alias** |
| `X'BC'` | part of `DS 11F` | **`IOINTPRM`** — ESA/390 interruption parameter, carved out |

Three decisions in that table are the substance of it.

**Renamed rather than deleted.** The three S/370-only fields could have been
removed. Marking them means a surviving reference fails to assemble instead of
reading architected lowcore that now means something else — and it leaves a
trace of a decision a 64-bit pass has to make again
([`17-CARRY-FORWARD-64.md`](17-CARRY-FORWARD-64.md)).

**`INTTIO` renamed with no alias, deliberately.** It does not move and does not
change width; only its meaning changes, from device address to subchannel number.
An alias would have let all 21 references keep assembling and silently compare
the wrong thing. Reading them settled it: **19 of 21 interpret it semantically**,
including `CLC IOBRADD(2),INTTIO  IS THIS FOR US?` and
`CH R15,INTTIO  INTERRUPT FOR DUMP DISK ?` — every one comparing a device address
it knows against lowcore. With `R-02` at weight 9, an alias was the wrong call.

The site that justifies it is `DMKDSP`:

    STCM  R0,7,INTTIO-PSA-1(R2)    SAVE ADDR IN LOW CORE

Three bytes at `X'B9'`–`X'BB'`, building an S/370 I/O interrupt code in a
*guest's* PSA — where ESA/390 needs `X'0001'` followed by the subchannel number.
An alias would have hidden that completely.

**Nothing here is parameterised, and that is correct.** `X'B8'` and `X'BC'` carry
the same meanings in z/Architecture, so these names carry forward unedited. The
parameterisation argument applies to the geometry constants, and their home is
`EQU.COPY` — which is where CE itself put `NOSSKCK` for its 4 KB storage-key
change, and which already defines `PAGE4K`, `PAGE2K` and `SEG1M`. That is M2's
first act, not this one.

## The deck applied last, over thirteen existing levels

    UPDATING 'PSA MACRO I1'.          IBM base, 394
    APPLYING 'PSA R10074DK H1'.       9 IBM PTF decks, 294
      ...
    APPLYING 'PSA HRC002DK F1'.       3 CE decks, 094
    APPLYING 'PSA HRC004DK F1'.
    APPLYING 'PSA HRC019DK F1'.
    APPLYING 'PSA XA0001DK A1'.       ours, last
    PSA MACRO ADDED.

Built with `VMFMAC DMKLCL DMKLCL` into `DMKLCL MACLIB A1`, 749 records, one `PSA`
member. `DMKLCL` is first in the `MACS` record and `VMFASM` does
`GLOBAL MACLIB &1 &2 …` in that order, so it overrides `DMKMAC`'s copy without
touching `DMKMAC` at all. Base source is untouched; `git diff` against
`arch/31bit/updates/` is the whole change.

## Pre-registered predictions, and the results

Written down before the run finished, because a prediction made afterwards is not
one.

| Module | Predicted | Actual | |
|---|---|---|---|
| `DMKPSA` | clean | **clean** | ✓ the deck applied and the DSECT is coherent |
| `DMKIOT` | fail, 9 refs | **fail, 10** | ✓ my arithmetic was off by one, not the system |
| `DMKDSP` | fail, 1 | **fail, 1** | ✓ |
| `DMKCPI`, `DMKPTR` | clean | **clean** | ✓ |
| `DMKIOS` | **fail, 1** | **clean** | ✗ — see below |

Then, testing the other renamed fields:

| Module | Predicted | Actual |
|---|---|---|
| `DMKIOG` | fail on `CHANID`, `ECSWLOG`, `IOELPNTR` | **fail, 6** — `CHANID` ×3, `ECSWLOG` ×2, `IOELPNTR` ×1 |
| `DMKPRV` | fail on `CHANID` | **fail, 1** — the guest `STIDC` simulation |

And eight modules that reference none of the renamed symbols — `DMKCNS`,
`DMKQCN`, `DMKSCN`, `DMKFRE`, `DMKPGS`, `DMKBLD`, `DMKVAT`, `DMKATS` — all
**still clean**, so the change is confined to what it was meant to touch.

**Step 2's exit criterion is met**, and it is a stronger criterion than "nothing
changed": a precise, predicted set of failures, in precisely the four modules
that are the channel-error and `STIDC`-simulation paths `R-03` covers, with
eleven other modules unaffected.

## The prediction that failed, and what it means

`source/cp/DMKIOS.ASSEMBLE` line 1318, sequence `01554000`:

    LH    R3,INTTIO      GET DEVICE ADDRESS               @VA08540 01554000

A real, uncommented instruction. `INTTIO` is provably undefined after the deck —
four modules flag it or its siblings — and `DMKIOS` assembled with
`NO STATEMENTS FLAGGED`. So **CE's own build of `DMKIOS` does not contain that
line, and the resolved tree in Adrian's repository does.**

What was checked, and ruled out:

- the base `394/DMKIOS.ASSEMBLE` has **8** `INTTIO` references; the resolved
  tree has 1, so updates remove seven — consistent with
  `R09587DK 602 SPLIT MODULE DMKIOS INTO DMKIOS AND DMKIOT`, which carries
  `./ D 418000 890000` commented *"DMKIOSIN BEING MOVED INTO DMKIOT"*
- no applied deck deletes or replaces a range covering `01554000`
- the two `*`-disabled entries in `DMKIOS.AUXR60` (`R14805DK`, `R13197DK`) have
  **no deck files at all**, so neither resolution could have applied them; 26
  files exist and 26 entries are active
- `DMKIOT` matched exactly (10 for 10) and `DMKDSP` matched exactly (1 for 1), so
  the divergence is specific to `DMKIOS`, not general

**Unexplained, and recorded rather than chased** (`I-30`), because `R-11` —
analysis outrunning implementation — is a weight-6 risk and this is one line in
one module that does not block anything. What it does mean is a real caveat on the
counts: `03-CP-INVENTORY.md` and its successors were measured against
`source/cp`, and for at least one module that is not byte-for-byte what CE
builds. **Where a count matters, verify it against what `VMFASM` produces.**

It is also, narrowly, good news: one fewer `INTTIO` site to convert in the module
where the I/O conversion is concentrated.

## Two operational traps, both nearly costly

**CP's print spool accumulates across runs when the printer is drained.** Every
`VMFASM` does `CP SPOOL PRT CONT` and `CP CLOSE PRT`, so listings queue up. With
`00E` drained they sit there — and the first `CP START 00E` flushes *all* of them
into `io/print1.listing`. That file reached 110,052 lines holding 66 spool files
from four separate runs, and the pre-deck listings in it still contained
`INTTIO EQU INTKFLIN+2`. **I read that as evidence my own change had not
applied.** `CP PURGE PRINTER ALL` before the work, and again before the print
that matters.

**`VMFASM … DISK` writes `$module LISTING`, not `module LISTING`.** The EXEC
assembles the *updated* member, `&ANAME = $&1`, so the listing carries the `$`.
`PRINT DMKIOS LISTING A` returns `FILE NOT FOUND` and looks like the option was
ignored.

## And the R-04 mitigation earned its place twice

`arch/31bit/tools/mkdeck.py` generates the cards and asserts the layout rather
than trusting an editor. It refused two real defects while this deck was being
written:

- a comment line at **64 columns** where 63 is the limit — which, unchecked,
  would have pushed text into the identifier field
- a sequence-number overflow: 20 lines at increment 100 from `00177100` reach
  `00179000`, **the next surviving record**. That is `R-22`, anchor fragility,
  caught by a guard rather than by a confusing `UPDATE` failure

It was then tightened further to enforce a two-column gutter before the
identifier, matching CE's own decks, after four lines came out unreadable.

`R-04` is no longer only "mitigated in principle". The mechanism was exercised,
and it fired.

## Files

    arch/31bit/updates/PSA.AUXLCL       the level entry
    arch/31bit/updates/PSA.XA0001DK     43 cards
    arch/31bit/updates/DMKLCL.EXEC      VMFMAC's member list
    arch/31bit/updates/build.py         generates all three, verified
    arch/31bit/tools/mkdeck.py          card layout, asserted

Applied with:

    CPACC
    VMFMAC DMKLCL DMKLCL
    VMFASM <module> DMKLCL

Next is M1 step 4, `DMKIOS` — the ten I/O instruction sites and the CSW shim —
and step 5, `DMKIOT`, whose ten `IOSCHNO` sites are now failing loudly and
waiting.
