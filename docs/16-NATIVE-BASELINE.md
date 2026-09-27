# The native baseline: 18 CP modules assemble clean, and z390's error list was never CP's

27 September 2026. The question was "do we need to check anything for assembly
before going further?" The answer was yes, one thing: **no real CP module had
ever been assembled by CE's own assembler.** Everything known about CP's
buildability came from z390, and `I-03` already proved the two disagree.

Checking it closed a risk that had been open since the project started, and
retired three defects that turn out not to be defects in CP at all.

## How CP is actually built, from CE's own EXECs

`194/ASMDMK.EXEC` assembles all 201 modules with one line each:

    EXEC VMFASM DMKIOS  &1

and `5E5/CPACC.EXEC` → `VMSETUP CP` accesses the five disks it needs, with CE's
own comments naming them:

    ACCESS 594 E/A      Local CP updates
    ACCESS 094 F/A      HRC   CP updates
    ACCESS 194 G/A      IBM   CP TEXT, Tools
    ACCESS 294 H/A      IBM   CP Updates
    ACCESS 394 I/A      IBM   CP Base source

So the whole procedure is two commands, `CPACC` then `VMFASM <module> DMKLCL`,
and `VMFASM` resolves the update levels itself:

    UPDATING 'DMKIOS ASSEMBLE I1'.
    APPLYING 'DMKIOS R08741DK H1'.
    ... 26 IBM PTF decks ...
    APPLYING 'DMKIOS HRC065DK F1'.
    APPLYING 'DMKIOS HRC069DK F1'.
    APPLYING 'DMKIOS HRC078DK F1'.
    ASMBLING DMKIOS

    ASSEMBLER (XF) DONE
    NO STATEMENTS FLAGGED IN THIS ASSEMBLY
    DMKIOS TXTHRC CREATED

## The baseline

**Eighteen modules, unmodified, every one `NO STATEMENTS FLAGGED`.**

| Set | Modules | Result |
|---|---|---|
| **The M1 nine** | `DMKIOS` `DMKPSA` `DMKIOT` `DMKCNS` `DMKQCN` `DMKSCN` `DMKFRE` `DMKDSP` `DMKCPI` | **9/9 clean** |
| **The DAT five** | `DMKPTR` `DMKPGS` `DMKBLD` `DMKVAT` `DMKATS` | **5/5 clean** |
| OS/VS-macro users | `DMKLNK` `DMKCFG` `DMKDSB` `DMKIMG` | **4/4 clean** |

**That is what M1 step 3 needed.** The step is "assemble the nine modules
unchanged and collect the errors" — and the error list is empty. Which is the
best possible outcome, because it means every error from here on is *ours*. There
is now a reference point, in the same way `arch/24bit` is the reference
implementation for behaviour.

### A detail worth knowing: `VMFASM` names the TEXT by level

`DMKIOT`, `DMKSCN`, `DMKIMG` and `DMKPTR` produced `DMKxxx TEXT`; the rest
produced `DMKxxx TXTHRC`. The difference is whether an `HRC` update actually
applied — those four have no `AUXHRC` level. So **our `AUXLCL` work will produce
`TXTLCL`**, and the nucleus build has to be told to pick it up. Worth catching
now rather than wondering later why a rebuilt module had no effect.

## R-14 is closed: the macro libraries are on CE

`10-BUILD-ENVIRONMENT.md` attributed ~24 module failures to "missing OS/VS macro
and copy libraries … OSMACRO and DOSMACRO, which Adrian's build guide names as
pinned assets and which are not in Git", and `12-RISKS.md` carried that as
**R-14** at weight 4. `06-LEDGER.md` listed the asset handover as one of the last
items needing Adrian.

`LISTFILE * MACLIB *` on a logged-on MAINT:

| Library | Records | Disk |
|---|---|---|
| **`OSMACRO  MACLIB`** | 13,227 | `CMSDSK 190` |
| **`OSMACRO1 MACLIB`** | 14,496 | `CMSDSK 190` |
| **`DOSMACRO MACLIB`** | 4,105 | `CMSDSK 190` |
| **`TSOMAC   MACLIB`** | 8,158 | `CMSDSK 190` |
| `DMKMAC MACLIB` | 12,004 | `MNT194` |
| `DMKHRC MACLIB` | 5,867 | `MNT094` |
| `CMSLIB MACLIB` | 5,907 | `CMSDSK 190` |
| `DMKLCL MACLIB` | **4** | `MNT594` — the empty local level |

They ship with CE, on the CMS system disk, exactly where `DMKR60.CNTRL`'s
`MACS DMKMAC CMSLIB OSMACRO` says to look for them. And the proof is not the
listing but the assemblies: **`DMKLNK`, `DMKCFG` and `DMKDSB` all reference
`MSSCOM` and `OSVSCOM`, `DMKIMG` references `NUCON`, and all four assemble
clean.**

A reasonable hypothesis had been that these libraries would have to come from an
MVS or DOS/VS distribution, since `vm370ce.conf` ships neither. They do
originate there, but CE already carries the extracted MACLIBs, so **nothing needs
downloading and nothing needs asking for.**

## All four z390 failure classes are z390's, not CP's

This is the part that changes the plan rather than just closing a risk. Each of
the four causes in `10-BUILD-ENVIRONMENT.md`'s table was tested on CE by
assembling a module that carries the trigger:

| Class | Under z390 | Trigger module | On CE's Assembler XF |
|---|---|---|---|
| **`I-01`** CP's `MSG` macro — ~20 modules | `AZ390E error 35, expression parsing error` | `DMKPTR`, `DMKBLD` (each 1 `MSG`) | **clean** |
| **`I-02`** U+E000 encoding | `MZ390E error 138, invalid ascii source line` | `DMKCPI` (1 such character) | **clean** |
| **`I-03`** duplicate `USING` ranges | `MNOTE 4` escalated | `DMKDSP` (44 `USING`s) | **clean** |
| **`R-14`** missing OS/VS macros — ~24 modules | undefined symbols | `DMKLNK` `DMKCFG` `DMKDSB` `DMKIMG` | **clean** |

**So "132 of 201 modules assemble" is a property of z390, not of CP.** The 69
failures were never a to-do list. `I-01`'s `MSG` macro is not broken — HLASM and
XF parse `K'&ARG2-2` and `'&ARG2'(1,1) NE ''''` the way CP intends, and z390's
expression parser does not. `I-02` does not exist on the native build at all,
because CE's disks hold native EBCDIC; the private-use encoding is an artifact of
the exported UTF-8 text tree and only matters to tools that read that tree.

The honest correction to `10-BUILD-ENVIRONMENT.md`: **z390's value was never
"two thirds of CP assembles".** It was settling the `RSCH` opcode, validating
`XAOPS` before CE was available, and being a fast local syntax check. Those are
real, and the three-tier conclusion — that the conversion can be written and
checked without a mainframe — still holds. But z390's error output must be read
as *dialect disagreement until proven otherwise*, and the authority on whether CP
assembles is the assembler that builds CP.

## Superseded upward: 186 modules, not 18

**27 September, later the same day.** `ASMDMK DMKHRC` ran CE's own EXEC over all
186 members it lists. **186 assembled, 185 with `NO STATEMENTS FLAGGED`**, and the
one flagged module is `DMKRIO` at severity 4 with four
`UNSUPPORTED DEVICE TYPE` MNOTEs for 3375/3390 DASD in the site configuration --
and its TEXT deck was still created. About 90 seconds of virtual CPU for the lot.

So the claim below is not "eighteen modules assemble", it is **essentially all of
CP assembles on CE's own Assembler XF**. See
[21-NUCLEUS-GAP.md](21-NUCLEUS-GAP.md), which uses this to put a number on the
distance to a nucleus.

## What this means for the milestones

| | |
|---|---|
| **R-14** | **closed** — libraries are on `CMSDSK 190`; four dependent modules assemble clean |
| **I-01, I-02, I-03** | reclassified: z390 dialect artifacts, not CP defects |
| **M1 step 1** | done — `14-M0-CLOSED.md` |
| **M1 step 3** | **done, and empty** — 9/9 M1 modules clean unmodified |
| **M2 baseline** | done too — the DAT five are clean, so M2's errors will also be ours |
| **the last Adrian dependency** | gone. `06-LEDGER.md` §5 item 4 was the asset handover |

M1 step 2 — `PSA.MACRO` — is now the only thing between here and modified CP,
and `15-UPDATE-LEVELS.md` says how: an `AUXLCL` update deck, built with
`VMFASM PSA DMKLCL`, with base source untouched.

## Reproducing

    /cpacc
    /vmfasm dmkios dmklcl

Driven from a Hercules `.rc` per `11-RUNNING-CE.md`. Allow ~20 seconds per
module; `VMFASM` prints its own verdict to the console, so the printer path is
only needed when the listing detail matters.

**One operational note.** These runs take longer than a ten-minute tool timeout,
and a timeout that kills Hercules leaves the warm-start area inconsistent. Launch
it detached and poll for the process to exit:

    nohup hercules -f vm370ce.conf > run.log 2>&1 < /dev/null &

That survives the wrapper being interrupted, which a foreground run does not.
Learned the hard way, once.
