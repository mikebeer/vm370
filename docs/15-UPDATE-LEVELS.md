# CE's update levels — and a retracted claim about baselines

27 September 2026. This document replaces an earlier version whose central
claim was wrong. The correction is kept in full, because the mistake is
instructive and because a register that quietly rewrites its own errors is worth
less than one that carries them (`I-27`).

## The retraction

The earlier version said: *"every one of g4ugm's 187 CP modules is present in CE,
byte-identical apart from a trailing newline and a control-byte encoding … the CP
source this project has been analysing is IBM's Release 6 source."*

The diff was right. The conclusion drawn from it was wrong.
[`g4ugm/vm370.source`](https://github.com/g4ugm/vm370.source) **carries CE's own
community modifications**:

    EXTRN HDKD7CIO                                        HRC065DK 00142100
    TM    RDEVADD,RDEVLDEV        Is this a logical dev?  HRC065DK 00234040

`HRC065DK` is a CE update identifier and `HDKD7CIO` is in a CE-only module.
`DMKQCN` carries 74 such lines; `DMKIOS` nine. So g4ugm is **not an independent
IBM baseline** — it is the same post-update tree as CE's `source/cp`. Two copies
of the same tree agreeing with each other proves nothing about IBM's original,
which is exactly what I claimed it proved.

**What made this a trap:** the diff was clean, the counts matched, the conclusion
was flattering, and the check that would have caught it — does the "pristine"
tree contain the *other* tree's change markers? — takes one `grep`. It is the
same failure shape as the first z390 validation (`I-18`) and as the duplicate
card deck (`I-26`): a result that looks like confirmation because nothing was
done to make it falsifiable.

## What CE actually contains, which is better than g4ugm

CE ships the genuine IBM base source *and* the update history, using IBM's own
VM/370 update mechanism. `maintenance/files/<disk>` mirrors the CE minidisks:

| Disk | Holds |
|---|---|
| **394** | CP **base** source and macros — `DMKIOS.ASSEMBLE`, 2,804 lines, **zero** HRC markers |
| **294** | IBM Release 6 PTF update decks — **1,281** of them |
| **094** | CE's own update decks — **354**, plus the `AUXHRC` level files |
| **194** | CP build EXECs and control files — `DMKR60.CNTRL`, `DMKHRC.CNTRL` |
| **594** | `DMKLCL.CNTRL` — the **local** level |
| 393 / 093 / 593 | the same structure for CMS |

So the pristine baseline was inside CE all along, and it is more precise than
g4ugm, because every changed line carries its update identifier in columns 73–80.
"Did IBM write this line, or did CE?" is answerable by reading the line.

`source/cp` is the **resolved** tree — base plus all update levels applied:

| | `maintenance/files/394` | `source/cp` |
|---|---|---|
| `DMKIOS.ASSEMBLE` | 2,804 lines | 2,494 lines |
| HRC-marked lines | 0 | 9 |

CE's own `README.md` says as much: "`source/cp` and `source/cms` contain
**editable** assembler, macros and COPY members", while
"`maintenance/files/<disk>` preserves selected original base, control, update"
files. `UPSTREAM.md` documents the resolution being checked against native CMS
`UPDATE` return codes.

### So how much of what we measured is IBM's?

| | |
|---|---|
| Total lines in `source/cp` | 229,737 |
| Lines carrying a CE (`HRC`) update id | **4,565 — about 2%** |
| Modules containing at least one | **97 of 201** |

**That is the honest version of the retracted claim.** The tree analysed in
`03-CP-INVENTORY.md`, `08-MACRO-UNDERCOUNT.md` and `09-DAT-WORK-SHAPE.md` is the
resolved tree, which is the right one to analyse because it is what assembles.
It is overwhelmingly IBM's code, but not purely — and where it matters, the
update id on the line says which.

## The finding that changes M1 step 2

`594/DMKLCL.CNTRL`:

    TEXT MACS DMKLCL DMKHRC DMKMAC DMSLCL CMSHRC CMSLIB OSMACRO
    LCL  AUXLCL
    HRC  AUXHRC
    TEXT AUXR60

Three stacked update levels, and **the top one is local, and it is empty.** Only
one `.AUXLCL` file exists in the whole tree (`DMKDMP.AUXLCL`, a duplicate that
`UPSTREAM.md` discusses). `AUXLCL` is CE's designed extension point for exactly
the kind of change this project makes, and nobody is using it.

**So the conversion should be written as an `AUXLCL` update level, not as edits
to base source.** A change becomes `DMKIOS.AUXLCL` naming `DMKIOS.XA00001DK`,
whose content is IBM update control cards:

    ./ I 00234000 $ 00234040 010
             TM    RDEVADD,RDEVLDEV        Is this a logical dev?  XA00001DK

Four things follow, and they are all improvements:

**`R-04` is largely neutralised.** The top risk in the register after `R-01` is
tooling corrupting column-sensitive source across 217 constant sites and 70 shift
literals. Update decks never rewrite an existing line: they insert, delete or
replace whole records, anchored on the sequence numbers in columns 73–80 that CP
maintains anyway. The failure mode that broke `TRACE`→`CPTRACE` cannot occur,
because no existing line is edited in place.

**The conversion becomes a reviewable delta.** "What does 31-bit CP change?" is
answered by a directory of update decks rather than by diffing two trees. That is
also the form Adrian could merge, review or reject piecemeal.

**It survives CE maintenance.** If CE issues a new `HRC` update, our `LCL` level
still applies on top rather than being overwritten — subject to `R-22` below.

**And it is how CP is actually built.** `EXEC VMFASM DMKIOS DMKLCL` — no new
toolchain, no modified build procedure, nothing for anyone to take on trust.

### The new risk that comes with it

Update decks are anchored on base sequence numbers. If CE renumbers a member or
issues an `HRC` update touching the same anchors, an `AUXLCL` deck can apply to
the wrong place or fail. `UPSTREAM.md` records that "DMKGRF and DMSSTT required
correct host handling of repeated sequence anchors" and that "PSA's
sequence-number increment also required a host" fix — so anchor fragility is a
known property of this mechanism, not a hypothetical. Filed as `R-22`.

97 of 201 modules already carry `HRC` lines, so the overlap is real rather than
theoretical — including `DMKPSA`, which M1 step 2 is about to change.

## Where that leaves g4ugm

Useful, but not for what it was checked for. It confirms independently that CE's
update resolution is not corrupt, since a separately maintained copy of the same
resolved tree agrees with it line for line. It contains no `.MACRO` or `.COPY`
members, so it does not close `R-14`. And it stores control bytes raw where CE
hoists them into the private-use area — CE's representation being the sound one,
as `I-02` now records.

Not vendored. Recorded in `../heritage/README.md` with that scope.
