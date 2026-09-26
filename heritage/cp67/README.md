# CP-67 / CMS

**No files imported.** But CP-67 is less absent from this project than that
suggests, and what was learned looking for it is worth recording.

## CP-67's CMS already ships with VM/370 CE

`source/cp/DMKSNT.ASSEMBLE` — CE's system name table — defines it as a named
saved system:

    *----------------------------------------------------------------* @D04
    * CMS67 segment for the CMS component of CP-67.                  * @D04
    *----------------------------------------------------------------* @D04
    CMS67    NAMESYS    SYSSIZE=256K,SYSNAME=CMS67,
                   VSYSADR=190,SYSVOL=VM50-1,SYSCYL=51,
                   SYSSTRT=(007,101),SYSPGCT=19,
                   SYSPGNM=(0-18),VSYSRES=VM14-2

Added by change `@D04`, 2020/05/01. `DMKRSP` also carries a `CP67USERID`
check, so the accommodation is not only in the name table.

So CE can IPL CP-67's CMS as a guest, from volume `VM14-2`, in 19 pages.

**And `CMS67` is the only saved system in that table that shares no
segments at all.** Every other entry has a `SYSHRSG=`; `CMS67` does not.
Which makes it the one named saved system that the 64 KB → 1 MB segment
change leaves completely untouched — see
[`../../docs/04-SHARED-SEGMENTS.md`](../../docs/04-SHARED-SEGMENTS.md).

## The hardware was closer to where we are going than VM/370 is

The System/360 Model 67 grouped **4096-byte pages into segments of one
megabyte**. That is exactly ESA/390's geometry, and exactly what VM/370
does *not* do.

So the 64 KB segment — the single hardest item in the 31-bit conversion —
is a **VM/370-era choice, not an inheritance.** S/370 DAT offered both 64 KB
and 1 MB segments and VM/370 took the smaller one, presumably for finer
sharing granularity. ESA/390 removed the option, which puts the geometry
back where the Model 67 had it in 1966.

The 67 also had genuine **32-bit** addressing, a decade and a half before
370-XA. XA deliberately went to 31 bits instead, for two reasons that are
both still visible in CP's source: `BXH` and `BXLE` do *signed* comparisons,
so the top bit has to stay a sign; and much existing software used bit 0 as
an end-of-list flag. That second reason is why CP's `CALL` macro — which
emits `L R15,=A(&SUBR+X'80000000')`, flagging pageable targets in bit 0 —
is safe under ESA/390 across all 4,104 of its invocations. IBM left bit 0
alone *because* code like CP's existed.

## What does not survive, and it is the part we would want

The known recovery is [moshix/CP-67-CMS-Source](https://github.com/moshix/CP-67-CMS-Source),
and it is **CMS only. There is no control program source in it** — the five
files are CMS source, CMS macros, CMS assembly listings, a printed listing,
and a 1966 paper on CP/CMS for the 360/40.

Its README explains the provenance: recovered from tape reels "found in a
dumpster (literally!)", read through VM/370 because the tape format is too
old for z/VM, and **two of the files had permanent read errors, so some
content is lost.**

That is unfortunate in a specific way. The interesting question — how a
control program handled 1 MB segments, shared segments at 1 MB granularity,
and two addressing modes on one machine — is answered by CP, not by CMS. CMS
does not build DAT tables. So the prior art that would inform
`docs/04-SHARED-SEGMENTS.md` is precisely what did not come back.

If a CP-67 *control program* source or listing exists anywhere, it is worth
more to this project than anything else in this directory.

## If files are imported here

**Settle the licence question first.** CP/CMS was distributed as IBM Type-III
unsupported software, which is not the same as public domain, and existing
preservation efforts have taken different views on redistribution. That
should be a written decision, not a side effect of a `git add`.

**Record what the copy is.** Recovered listings, OCR'd decks and tape images
are not interchangeable, and a reader needs to know which they have before
drawing a conclusion from it — especially given the known read errors.

## Sources

- [moshix/CP-67-CMS-Source](https://github.com/moshix/CP-67-CMS-Source) — the
  CMS recovery, with its own provenance notes
- [IBM System/360 Model 67](https://en.wikipedia.org/wiki/IBM_System/360_Model_67) —
  the 4 KB page / 1 MB segment geometry and the 24/32-bit modes
- [31-bit computing](https://en.wikipedia.org/wiki/31-bit_computing) — why XA
  chose 31 bits rather than the 67's 32
- [Model 67 Functional Characteristics, A27-2719](http://bitsavers.informatik.uni-stuttgart.de/pdf/ibm/360/functional_characteristics/A27-2719-0_360-67_funcChar.pdf) —
  primary source for the table formats, if they are ever needed
- [CP/CMS](https://en.wikipedia.org/wiki/CP/CMS) and
  [IBM CP-40](https://en.wikipedia.org/wiki/IBM_CP-40) — background
