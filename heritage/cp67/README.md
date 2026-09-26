# CP-67 / CMS

**Empty.** Nothing has been imported yet.

## What should go here

A readable CP-67 source tree, with the provenance of the copy recorded
alongside it — where it came from, what date or level it represents, and what
condition it arrived in. Recovered listings and OCR'd decks are not
interchangeable with a tape image, and a reader needs to know which they are
looking at before drawing a conclusion from it.

## Before importing

**Settle the licence question first.** CP/CMS was distributed as IBM Type-III
unsupported software, which is not the same as being public domain, and the
existing preservation efforts have taken different views on redistribution.
Whatever this repository does should be a deliberate decision with the
reasoning written down, not a side effect of a `git add`.

**Record where the copy came from.** The known starting point is
[moshix/CP-67-CMS-Source](https://github.com/moshix/CP-67-CMS-Source). If the
copy is taken from there, say so and pin the commit; if it comes from
elsewhere, say that instead.

## The question worth answering from the source

The System/360 Model 67 offered both 24-bit and 32-bit virtual addressing,
selected by a mode bit — the earliest instance of the problem
`../../arch/31bit/` is working on.

**Did CP-67 use the 32-bit mode?** OS/360 did not. If CP-67 did, then there
is prior art for a control program managing two addressing modes on one
machine, written by the people who invented the technique, and it is worth
reading before designing the ESA/390 equivalent. If it did not, that is also
worth knowing, and cheaper to establish than to assume.

The places to look are the PSW and control-register handling at
initialisation, and the DAT table build — the 67's table format differs from
S/370's, so whatever routine constructs it will show which mode it targets.
