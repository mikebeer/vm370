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
and it offered **both 24-bit and 32-bit virtual addressing**, selected by a
mode bit. Which makes it the earliest case of exactly the problem
`../arch/31bit/` is working on: a control program facing two addressing modes
on one machine. Whether CP-67 itself ever exploited the 32-bit mode, or
stayed at 24 bits like OS/360 did, is worth establishing from the source
rather than assuming — and if it did, the way it handled the boundary is
directly relevant prior art.

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

**Both directories are empty.** Neither body of source is in this repository
yet, and neither should be added without settling provenance and licence
first — see each directory's README.

## Sources

- [CP-67-CMS-Source](https://github.com/moshix/CP-67-CMS-Source) — a
  preserved CP-67/CMS source tree
- [Original source code for the IBM CP/67 CMS operating system from
  1973](https://retrocomputingforum.com/t/original-source-code-for-the-ibm-cp-67-cms-operating-system-from-1973/1500)
  — the retrocomputing thread on that recovery
- [CP/CMS](https://en.wikipedia.org/wiki/CP/CMS) and
  [CP-67](https://en.wikipedia.org/wiki/CP-67) — background and dates
- [IBM CP-40](https://en.wikipedia.org/wiki/IBM_CP-40) — the predecessor,
  for where the design originates
