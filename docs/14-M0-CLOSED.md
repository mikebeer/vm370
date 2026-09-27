# M0 closed: CE's own assembler accepts XAOPS

27 September 2026. `12-RISKS.md` opened with **R-17 — CE's assembler rejects
`XAOPS`** — at probability Low, impact High, because the macros had only ever
been validated under z390, and z390 is not the assembler that has to accept
them. `07-M1-WORKLIST.md` made settling it M1 step 1: *"`MACLIB GEN XALIB
XAOPS`, then confirm a module containing `SSCH` assembles. M0 is done but has
never been used in anger."*

It has now been used in anger. **R-17 is closed, and M0 is complete rather than
complete-with-an-asterisk.**

## The result

`XAOPS.MACRO` and `XATEST.ASSEMBLE` were read onto MAINT's 191 disk through
CE's card reader, built into a MACLIB, and assembled by CE's own assembler.

    maclib gen xalib xaops
    Ready;

    maclib map xalib (term
    MACRO    INDEX  SIZE
    SSCH         2    40        CSCH        74     7
    MSCH        43     9        HSCH        82     6
    STSCH       53     9        RSCH        89     7
    TSCH        63    10        TPI         97     6
    SAL        104     9        STCRW      114     8
    BSM        123    19        BASSM      143    64

**All twelve members.** Then:

    global maclib xalib
    assemble xatest (disk

    ASSEMBLER (XF) DONE
    NO STATEMENTS FLAGGED IN THIS ASSEMBLY
    HIGHEST SEVERITY WAS    0
    TOTAL RECORDS READ FROM SYSTEM LIBRARY      139
    TOTAL RECORDS PUNCHED                         8

Four things in that output, in order of how much they settle:

**`TOTAL RECORDS READ FROM SYSTEM LIBRARY 139`.** This is the one that rules out
the failure mode `I-18` was about — a macro call silently ignored because the
name resolved to something else. 139 records came out of `XALIB MACLIB`, so the
definitions were genuinely fetched. A clean assembly with a library count of
zero would have proved nothing.

**`HIGHEST SEVERITY WAS 0`.** Not "warnings only". Nothing was flagged at all.

**`TOTAL RECORDS PUNCHED 8`.** A real `XATEST TEXT` deck exists. The macros do
not merely parse, they produce object code.

**It is Assembler XF**, not Assembler F. Worth knowing for its own sake — `I-03`
records that z390 escalates overlapping `USING` ranges where HLASM tolerates
them, and XF's tolerances are the ones that actually matter.

## Every encoding, as emitted

From `../arch/31bit/macros/validate/XATEST-CE-XF.LISTING`:

| Instruction | Object | | Instruction | Object |
|---|---|---|---|---|
| `STSCH SCHIB` | `B234F0B6` | | `SAL` | `B2370000` |
| `MSCH SCHIB` | `B232F0B6` | | `TPI PARM` | `B236F04E` |
| `SSCH ORB` | `B233F096` | | `STCRW PARM` | `B239F04E` |
| `TSCH IRB` | `B235F0EA` | | `BSM R1,0` | `0B10` |
| `CSCH` | `B2300000` | | `BSM 0,R4` | `0B04` |
| `HSCH` | `B2310000` | | `BASSM R14,R15` | `0CEF` |
| `RSCH` | `B2380000` | | | |

Every opcode matches. Including **`RSCH` = `B238`**, which settles `I-21` on the
only authority that counts for a build: the assembler that will produce the
nucleus now emits it.

### The part z390 could not have told us

The macros exist to make `DC X'B233',S(&ORB)` behave like a real S-format
instruction — base register and displacement resolved through the active `USING`.
That is the mechanism, and it is the thing a different assembler cannot vouch
for. Checked arithmetically against the listing's own location column, with
`USING *,R15` established at `X'02'`:

| Operand | At | Displacement | Emitted |
|---|---|---|---|
| `SCHIB` | `X'B8'` | `B8 − 02 = 0B6` | `F0B6` |
| `ORB` | `X'98'` | `98 − 02 = 096` | `F096` |
| `IRB` | `X'EC'` | `EC − 02 = 0EA` | `F0EA` |
| `PARM` | `X'50'` | `50 − 02 = 04E` | `F04E` |
| `MASKSAVE` | `X'54'` | `54 − 02 = 052` | `F052` |
| `CR1VAL` | `X'4C'` | `4C − 02 = 04A` | `F04A` |
| `CRSAVE` | `X'58'` | `58 − 02 = 056` | `F056` |

All seven exact. The S-type constant does the full base-register selection an
S-format instruction needs.

**And the `DS 0H` earned its place.** Generated addresses run `000006`, `00000A`,
`00000E`, `000012`, `000016`, `00001A`, `00001E`, `000022`, `000026`, `00002A`,
`00002E`, `000030`, `000032` — contiguous, halfword-aligned, no pad byte anywhere.
The comment in `XAOPS.MACRO` said this "costs nothing to be sure"; it is now
measured rather than asserted.

### And the four that need no macro

`STOSM AD04F052`, `STNSM ACFBF052`, `LCTL B711F04A`, `STCTL B60FF056` — all
assembled natively in the same run. The claim that CE's assembler already knows
them, which CP's own usage implied, is now direct evidence.

## What is genuinely left in the assembly chapter

Honest scope: **the channel subsystem and mode switching are fully closed. The
ESA/390 DAT instructions are not written yet.** `XAOPS.MACRO` says so in its own
"NOT INCLUDED, AND WHY" section, and M2 will need them:

- `IPTE` — invalidate page table entry
- `IVSK` — insert virtual storage key
- `TPROT` — test protection
- `ISKE` / `SSKE` / `RRBE` — the 4 KB-key counterparts of `ISK`/`SSK`/`RRB`,
  which `R-12` will need

These are **unwritten, not unverified**, and the distinction matters: the
mechanism they would use is now proven, so adding them is a mechanical exercise
with a known cost rather than an open question.

## How to get a file into CE, which is the reusable part

Every remaining M1 step needs source on a CE disk, so the import path is worth
recording properly. It cost two cycles.

**CP drains the real unit-record devices at IPL.** This is the whole trap:

    RDR  00C DRAINED   SYSTEM
    PUN  00D DRAINED   SYSTEM   CLASS = P      SEP
    PRT  00E DRAINED   SYSTEM   CLASS = A      SEP

A drained reader is never read, so the deck sits there and `READCARD` says
`READER EMPTY OR NOT READY`. Every subsequent step then fails for reasons that
have nothing to do with the real problem — a whole run's worth of misleading
errors from one line in the IPL messages. `CP START 00C` first.

**The ID card.** A real deck needs a CP ID card as its first card. From
`DMKRSP`'s own parser, which accepts three forms — `ID `, `USERID `, and
`CP67USERID ` — plus optional `CLASS` and `NAME`:

    ID MAINT NAME XAOPS MACRO

`NAME` sets the spool file's name and type, so `QUERY READER` shows what the
deck is. Class defaults to `A` (`MVI SFBCLAS,C'A'`).

**The recipe, as it now works:**

    /cp spool 00c class *
    /cp start 00c                      un-drain: without this, nothing works
    /cp query reader all               confirm the file arrived, and its RECDS
    /readcard xaops macro a
    /listfile xaops macro a (label     confirm the record count matches the deck

**And `START` itself triggers the read, so do not also `devinit`.** That cost
the second cycle: `CP START 00C` read `io/card.txt` and a following `devinit` of
the same device read it *again*, leaving two identical spool files queued. The
second `READCARD` then picked up the duplicate instead of the next deck, and
`XATEST ASSEMBLE` arrived on disk as a 194-record copy of `XAOPS MACRO`. It
assembled — with `IFO047 UNEXPECTED END OF FILE ON SYSTEM INPUT`, because a file
of pure macro definitions has no `END` — which is a plausible-looking failure of
the macros that was nothing of the sort. **Always check `LISTFILE`'s record count
against the deck size.**

To swap decks, `devinit` the reader *once per new file* and let that be the
trigger.

**Getting a listing back out.** `PRINT fn ft fm` then `CP CLOSE 00E`, with
`CP START 00E` first for the same drain reason. CE's `000E 1403` writes
`io/print1.listing`, and the bytes are **ASCII with a one-byte carriage control
per line** — not EBCDIC, despite the device having no `ascii` option. Strip the
first byte of each line and it is readable text. The alternative,
`ASSEMBLE x (PRINT`, skips the disk file; `(DISK` keeps `fn LISTING` as a
fallback and can still be printed afterwards, which is the safer order.

## What this closes

| | |
|---|---|
| **R-17** | closed — CE's Assembler XF accepts every macro, and the S-type constants resolve exactly |
| **I-04** | closed — `XATEST` listing checked, all twelve encodings read off it |
| **I-21** | reconfirmed on the authority that matters — `RSCH` is `B238` |
| **M0** | complete. No asterisk, no listing check outstanding |
| **M1 step 1** | done |

M1 step 2 is `PSA.MACRO` — add the ESA/390 names at `X'B8'`/`X'BC'`, keep
`INTTIO` where it is, and mark `CHANID`/`IOELPNTR`/`ECSWLOG` S/370-only. Step 3
is assembling the nine modules and collecting the errors, which is the step that
tests whether the counts in `07-M1-WORKLIST.md` were honest.
