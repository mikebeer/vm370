# What environment is needed to write CP code

27 September 2026. `06-LEDGER.md` closed with "no CP code has been written,
and the blocker is build access". That was too pessimistic, and this measures
why.

**Two thirds of CP assembles today, on Linux, with no mainframe environment at
all.** The native CE build is needed to produce a bootable nucleus — not to
develop the conversion.

## The measurement

[z390](https://github.com/z390development/z390) is a Java mainframe assembler.
It already earned its place here by settling the `RSCH` opcode and validating
`XAOPS` (`../arch/31bit/macros/validate/`). Pointed at Adrian's CP source, with
CP's `.COPY` members renamed to `.CPY` and its `.MACRO` members to `.MAC`, and
**one same-length macro rename**, all 201 modules were run through it:

| Outcome | Modules | |
|---|---|---|
| `rc=0` clean | **117** | |
| `rc=4` warnings only | **15** | |
| | **132 (66%)** | **usable today** |
| `rc=12` | 67 | |
| `rc=16` | 2 | |

The one rename: **`TRACE` is a z390 directive**, so it shadows CP's `TRACE`
macro and z390 tries to resolve `CODE=` as a symbol. Renaming CP's macro to
`TRACZ` fixes it. Same collision as `XAOPS` had, same cause.

### The M1 set: seven of nine

| Module | | Module | |
|---|---|---|---|
| `DMKIOS` | **clean** | `DMKPSA` | **clean** |
| `DMKQCN` | **clean** | `DMKFRE` | **clean** |
| `DMKSCN` | **clean** | `DMKCNS` | warnings |
| `DMKIOT` | warnings | `DMKCPI` | **fails** |
| `DMKDSP` | **fails** | | |

**`DMKIOS` assembles clean** — the I/O supervisor, the central module of the
conversion, 2,494 lines. So does `DMKPSA`, which carries the lowcore
definition. Of the DAT five, `DMKATS` and **`DMKVAT`** are clean too.

## Why the other 69 fail, and none of it is z390's fault

Grouped by cause:

**~24 modules: missing OS/VS macro and copy libraries.** `MSSCOM`, `MODESET`,
`WAITT`, `OSVSCOM`, `NUCON`, `VSCOMM`, `ACTDCB`. These are not in CP's own
library — they come from **OSMACRO and DOSMACRO**, which Adrian's build guide
names as pinned assets and which are not in Git. So this failure class *is* the
asset-handover item, and now its exact scope is known rather than assumed.

**~20 modules: CP's `MSG` macro.** `AZ390E error 35, expression parsing error`
on lines like

    MSG   'STORAGE IS VIRTUAL=REAL'
    MSG   'DMKPTR410W CP ENTERED; PAGING ERROR'

`MSG.MACRO` does substring and length arithmetic on a quoted operand
(`'&ARG2'(1,1) NE ''''`, `K'&ARG2-2`), and z390's expression parser disagrees
with HLASM about it. **One macro**, and it blocks `DMKPGS`, `DMKBLD` and
`DMKPTR` — three of the five DAT modules. Worth fixing early: it is the single
highest-leverage item on this list.

**`DMKCPI`: source encoding.** `MZ390E error 138, invalid ascii source line
365`. This is the **U+E000 private-use encoding** the CE README describes.
`03-CP-INVENTORY.md` noted that `DMKVAT` and `CORE` are clean of it, so it
applies only to some members — `DMKCPI` is one. It needs the documented reverse
encoding applied before assembly, which is a preprocessing step, not a source
problem.

**`DMKDSP`: z390 strictness.** `MNOTE 4, 'Duplicate USING ranges found for - 2
and 0 using highest'`. HLASM tolerates overlapping `USING` ranges; z390
escalates. A dialect difference, not a defect in CP.

**A few: `no base register found`** — addressability knock-ons, mostly
downstream of the missing symbols above.

## So the environment is three tiers, not one

**Tier 1 — available now, needs nothing from anyone.** z390 and a JDK, on
Linux or Windows. 132 of 201 modules, including `DMKIOS`, `DMKPSA`, `DMKVAT`
and `DMKATS`. Enough to **write the conversion and have it checked**: edit a
module, assemble it, read the errors, iterate. That is where the M1 and M2 work
actually happens.

**Tier 2 — the asset handover, and now precisely justified.** The pinned
OSMACRO/DOSMACRO libraries plus the source-encoding reversal would recover most
of the remaining 69. This is worth asking Adrian for as a specific, small
thing — two macro libraries and an encoding note — rather than as "the build
environment".

**Tier 3 — the native CE build.** CMS, `ASSEMBLE`, `LOAD`, `GENMOD`, the disk
images, `lab.crexx`. Needed to produce **TEXT decks, a bootable nucleus and a
saved system** — that is, to turn converted source into something that IPLs.
Not needed to write or check the source.

**The blocker was misdiagnosed.** Development does not need Adrian's
environment. Integration does. That is a much better position, and it means M1
and M2 source work can start immediately.

## Two hazards found while doing this

**CP source is strictly column-sensitive, and naive edits corrupt it.** The
first rename attempt used `TRACE` → `CPTRACE`, two characters longer. That
pushed each line's `@V40759` change-marker into **column 72, the continuation
column**, and the macro began failing with "continuation line < 16
characters". The rename had to be the same length. Any tool that rewrites CP
source — including anything automating the 217 constant references or the 70
shifts — must preserve columns 1–71 exactly and leave 72–80 alone.

**z390 built-ins shadow CP macros.** `TRACE` was found because it failed.
Anything else where CP's macro name collides with a z390 directive will behave
the same way: the macro is silently ignored and its operands are parsed as
something else. Worth a systematic check of CP's 59 macro names against z390's
directive list before trusting a clean `rc=0`.

## Reproducing

    # CP's COPY and MACRO members, renamed for z390's conventions
    for f in source/cp/*.COPY;  do cp "$f" cpy/$(basename ${f%.COPY}).CPY; done
    for f in source/cp/*.MACRO; do cp "$f" cpy/$(basename ${f%.MACRO}).MAC; done
    sed 's/^\( *\)TRACE \(&CODE=\)/\1TRACZ \2/' cpy/TRACE.MAC > cpy/TRACZ.MAC

    # one module, with the same-length rename applied to its call sites
    sed 's/^\( *\)TRACE \(CODE=\)/\1TRACZ \2/' source/cp/DMKIOS.ASSEMBLE > DMKIOS.MLC
    java -cp z390/classes mz390 DMKIOS.MLC "sysmac(+cpy)" "syscpy(+cpy)"

z390's classes build with
`javac -d classes -sourcepath src src/mz390.java src/az390.java`.
