# vm370

Work towards a VM/370 Community Edition that addresses storage above the
16 MB line — and a preserved record of the lineage it comes from.

The repository is organised by **addressing architecture**, because that is
what actually partitions the work. Each directory is a machine architecture
with its own tests, its own tooling and its own honest status.

    arch/24bit/     S/370, 24-bit — the baseline.  What CE is today.
    arch/31bit/     ESA/390 — the current work.  Hardware proven, conversion not started.
    arch/64bit/     z/Architecture — the destination.
    heritage/       Preserved ancestors: CP-67, and CE release snapshots.
    docs/           Analysis that spans architectures.

## Where things stand

| | | |
|---|---|---|
| **24-bit** | S/370 | **Works.** This is VM/370 CE as released. 16 MB ceiling. |
| **31-bit** | ESA/390 | **Hardware proven, M0 complete, conversion not started.** Thirteen standalone tests pass on stock Hercules; CE's own assembler accepts the ESA/390 macros. |
| **64-bit** | z/Architecture | **Not started.** Seeded by the `wide/` proofs in the CE tree. `docs/17-CARRY-FORWARD-64.md` records what the 31-bit work hands it. |

Start at [`arch/31bit/README.md`](arch/31bit/README.md) — that is where the
active work is, and it is the only directory with executable results in it.

## Why three, and in this order

The obvious objection is that 31-bit is a detour if 64-bit is the
destination. It is not, and the reason is specific:

**The two most expensive pieces of the 31-bit conversion carry forward to
64-bit unchanged.** The channel subsystem arrived with 370-XA in 1983 and
z/Architecture did not touch it — `SSCH`, `MSCH`, `TSCH`, the ORB, the SCHIB
and the IRB are the same instructions and the same control blocks. And the
page and segment geometry is the same too: 4 KB pages and 1 MB segments in
both. So CP's I/O rewrite and its segment-table rework are each done once.

**What 64-bit adds on top is mostly above the segment table.** z/Architecture
inserts region tables — first, second and third — giving up to five levels
of translation where ESA/390 has two, and replaces the segment table
designation in CR1 with an address-space-control element that carries a
designation type. The PSW doubles to 16 bytes with an entirely different
layout, which means lowcore changes, and `SAM24`/`SAM31`/`SAM64` replace
`BSM` for mode switching. Real work, but layered on the 31-bit result rather
than in place of it.

Going straight to 64-bit means doing the segment and I/O conversions anyway,
with a second PSW format and three more table levels in flight at the same
time, and with no intermediate state that boots. That is the argument for the
order, not sentiment about 31-bit.

**And 24-bit is not a museum piece.** It is the reference implementation.
Every claim about what the conversion changes is measured against it, and a
31-bit CP that cannot still run an unmodified S/370-mode guest has failed —
which is precisely what `arch/31bit`'s M3 tests.

## Documents

    docs/01-PROPOSAL.md         the plan, and what is being asked of whom
    docs/02-CP-VERIFIED.md      two design hypotheses checked against CP source
    docs/03-CP-INVENTORY.md     the architecture-dependency counts
    docs/04-SHARED-SEGMENTS.md  what 1 MB segments do to CE's saved systems
    docs/05-CP67-PRIOR-ART.md   how CP-67 shared at 4 KB with 1 MB segments
    docs/06-LEDGER.md           what is answered, how firmly, and what is open
    docs/07-M1-WORKLIST.md      the first milestone as an ordered work list
    docs/08-MACRO-UNDERCOUNT.md the inventory's biggest unknown, closed
    docs/09-DAT-WORK-SHAPE.md   what reading DMKBLD and DMKPGS revealed
    docs/10-BUILD-ENVIRONMENT.md what it takes to write CP code, measured
    docs/11-RUNNING-CE.md        CE running headless here, and what that closed
    docs/12-RISKS.md            the risk register, scored and mapped to milestones
    docs/13-ISSUES.md           known issues and defects, including retractions
    docs/14-M0-CLOSED.md        the assembly chapter, measured shut
    docs/15-UPDATE-LEVELS.md    CE's three update levels, and a retracted claim
    docs/16-NATIVE-BASELINE.md  18 CP modules assemble clean on CE, unmodified
    docs/17-CARRY-FORWARD-64.md what the 31-bit work hands to 64-bit
    docs/R01-SHIFT-SITES.md     the 70 geometry shift sites, site by site

**`06` is the status account** — sorted by strength of evidence, because
"checked" means very different things depending on whether something was
executed, read, or counted. Start there to see where the project stands.

`05` is the one to read if you only read one. The conversion's hardest item
looked like segments going from 64 KB to 1 MB, costing a 16x loss of sharing
granularity. CP-67 had **1 MB segments and shared at 4 KB**, because it gave
each virtual machine its own page table and shared the frames rather than the
table. So the granularity loss is a property of VM/370's implementation, not
of ESA/390, and it is avoidable. `04` is the measurement that `05` corrects;
read them in that order.

## Why heritage

Two reasons, one practical and one not.

The practical one: the analysis in `docs/` is measured against a specific
state of the CE source. When that source moves, the counts stop matching, and
a snapshot is the only way a reader can tell whether a number is stale or
wrong.

The other one: CP-67 is where all of this came from, it very nearly did not
survive, and the parts of it that are still legible are worth keeping legible.
See [`heritage/README.md`](heritage/README.md).

## Provenance

VM/370 Community Edition source is maintained by Adrian Sutherland; the
counts in `docs/` were measured against that tree and are not a substitute
for it. Hercules field layouts, required bits and condition-code paths were
read from SDL Hyperion. The S/380 work referenced in the documents is Paul
Edwards's.
