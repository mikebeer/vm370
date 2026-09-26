# VM/370 CE snapshots

**Empty.** Nothing has been imported yet.

## What should go here

Enough of a pinned CE source state to make the measurements in `../../docs/`
reproducible, and nothing more. The live tree is Adrian Sutherland's and the
31-bit work should track his maintenance rather than diverge from a frozen
copy.

A snapshot needs three things recorded with it:

- **Date and commit** of the upstream tree it was taken from
- **What it covers** — the CP `.ASSEMBLE` and `.MACRO`/`.COPY` members are
  what the counts are measured over; disk images and vendor assets are not
  needed for that and are large
- **The measurement scripts** that produced the numbers, so a later reader
  can re-run them against a newer tree and see what moved

## The counts a snapshot is meant to anchor

From `../../docs/03-CP-INVENTORY.md`, measured with a statement parser that
skips comments and takes the opcode from column 1 or after the label:

| | |
|---|---|
| CP `.ASSEMBLE` members | 201 |
| S/370 I/O instructions | 166 |
| `TRANS` macro invocations | 174 |
| `CALL` macro invocations | 4,104 |
| DAT table field references | 459 |
| CAW/CSW references | 1,917 |
| Three-byte `ICM`/`STCM` sites | 582 |
| CMS `.MACRO`/`.COPY` members | 139 |

The 166 I/O instructions cross-check against 165 counted independently from
an unrelated extraction, which is the kind of agreement that only means
something if the tree it was counted over can still be identified.

## Not a fork

If the 31-bit work needs to modify CE source, that belongs in a fork of the
upstream repository with periodic rebases — not in a snapshot directory,
where a change would be invisible to upstream and would quietly invalidate
the counts above.
