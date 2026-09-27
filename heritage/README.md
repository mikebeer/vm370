# heritage

Preserved ancestors. Two directories, two different reasons.

    cp67/       CP-67 / CMS — the S/360-67 original, 1967-1972
    vm370ce/    VM/370 CE release snapshots

## Why keep CP-67

CP-67 is where all of this came from. It was the IBM Cambridge Scientific
Center's control program for the System/360 Model 67 — successor to CP-40,
direct ancestor of VM/370 — and it established essentially everything this
repository is still working on: a control program that virtualises a machine
by trapping privileged instructions and translating addresses through
hardware DAT, with a single-user conversational monitor as the guest.

It also very nearly did not survive. CP/CMS was distributed as unsupported
Type-III software rather than a product, so there was no service structure
obliged to keep a copy, and what exists now exists because individuals kept
tapes and listings. That is a thin margin for the origin of an entire line of
operating systems.

**There is a technical reason too, and it is not sentimental.** The
System/360 Model 67 was IBM's first machine with dynamic address translation,
it had genuine 32-bit addressing fifteen years before 370-XA, and it grouped
4 KB pages into **1 MB segments** — which is ESA/390's geometry, not
VM/370's. So the 64 KB segment that makes `../arch/31bit/`'s hardest problem
is a VM/370-era choice rather than something inherited, and the machine
CP-67 ran on was in that respect closer to where this project is going.

CP-67's CMS also still ships with VM/370 CE, as the `CMS67` named saved
system — and it is the only entry in CE's system name table that shares no
segments, which makes it the one saved system the 1 MB change leaves alone.

The frustrating part, now checked rather than assumed: the surviving recovery
is CMS only — zero references to segment tables, page tables, `LRA` or
`PTLB` across 200,000 lines, because CMS is a guest that never translates an
address. And the 1966 CP-40 paper in the same repository does not substitute
for it: CP-40 relocated through a 64-entry associative memory with no segment
tables at all, and shared no storage between virtual machines. Detail in
[`cp67/README.md`](cp67/README.md).

## Why keep CE snapshots

Mundane but load-bearing. The analysis in `../docs/` is measured against a
specific state of the CE source — 201 CP `.ASSEMBLE` members, 174 `TRANS`
invocations, 166 S/370 I/O instructions, 582 three-byte `ICM`/`STCM` sites.
When the upstream tree moves, those counts stop matching, and without a
snapshot a reader cannot tell whether a number is stale or was wrong to
begin with.

A snapshot is not a fork. The 31-bit work should track Adrian's maintenance
rather than diverge from a frozen copy; what belongs here is enough to make
the measurements reproducible, tagged with the date and commit it came from.

## Status

**No source files imported yet**, and neither body should be added without
settling provenance and licence first — see each directory's README. The
`cp67/` README is not a placeholder, though: it records what CE already
carries of CP-67, and what the surviving recovery does and does not contain.

## Sources

- [CP-67-CMS-Source](https://github.com/moshix/CP-67-CMS-Source) — the
  surviving recovery. CMS source, macros and listings; **no control program**
- [Original source code for the IBM CP/67 CMS operating system from
  1973](https://retrocomputingforum.com/t/original-source-code-for-the-ibm-cp-67-cms-operating-system-from-1973/1500)
  — the retrocomputing thread on that recovery
- [CP/CMS](https://en.wikipedia.org/wiki/CP/CMS) and
  [CP-67](https://en.wikipedia.org/wiki/CP-67) — background and dates
- [IBM CP-40](https://en.wikipedia.org/wiki/IBM_CP-40) — the predecessor,
  for where the design originates

## A differential baseline, not preserved here

[`g4ugm/vm370.source`](https://github.com/g4ugm/vm370.source) — Dave Wade's
VM/370 release source, 187 CP and 174 CMS `.ASSEMBLE` members. It is
deliberately *not* snapshotted into this repository: it is 37 MB of source this
project does not build, and CE is the tree being converted.

Its value is as a differential baseline. Diffing CE against it showed that
**every one of its 187 CP modules is in CE, byte-identical apart from a trailing
newline and CE's control-byte encoding** — which verifies, for the first time,
that the analysis in `../docs/` was measured against IBM's Release 6 source
rather than a community fork. See `../docs/15-PRISTINE-BASELINE.md`.

It contains no `.MACRO` or `.COPY` members, so it does not supply the
OSMACRO/DOSMACRO libraries (risk `R-14`).
