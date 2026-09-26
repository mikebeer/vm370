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

The known recovery is [moshix/CP-67-CMS-Source](https://github.com/moshix/CP-67-CMS-Source).
Its README says it is CMS; that has been checked rather than taken on trust,
and it holds.

**The source is CMS and nothing else.** Some 200,000 lines across
`CMSSource.txt` and `CMSAssemblyListings.txt`, with about 130 CSECTs — all
of them CMS commands and nucleus: `EDIT`, `LISTF`, `MACLIB`, `STAT`,
`FILEDEF`, `TXTLIB`, `UPDATE`, `NUCON`, `GENMOD`, `LOGIN`. Counting
occurrences of what a control program cannot avoid:

    SEGTAB / "SEGMENT TABLE"      0
    PAGTAB / "PAGE TABLE"         0
    LRA                           0
    PTLB                          0
    VMBLOK                        0
    "32 BIT"                      0

That is not a hole in the recovery, it is what CMS is: a guest that never
translates an address. The DAT and sharing design lives in CP, and no CP is
present.

Its provenance also bears repeating: recovered from tape reels "found in a
dumpster (literally!)", read through VM/370 because the tape format is too
old for z/VM, and **two files had permanent read errors, so some content is
lost.**

## The 1966 paper is CP-40, and its answer does not transfer

The repository's other substantial item is a 34-page May 1966 paper, *A
Virtual Machine System for the 360/40*. That is CP-40, CP-67's predecessor,
and it is a design document about the *control program* — which made it look
like the prior art the source is missing. It is not, for a concrete reason.

CP-40's relocation hardware was not tables at all:

> The CPU has been modified to permit dynamic relocation of storage
> addresses by the addition of a 64 word (one per 4096 byte page of core
> memory) by 16 bit associative memory. A privileged operation to load and
> interrogate the memory has been added to the instruction set.

A 64-entry fully associative map — one entry per 4 KB frame of the machine's
entire 256 KB of core — interrogated directly, with no segment table, no page
table and no table walk. Sixteen virtual machines of 256 KB each. There is no
segment concept to learn a segment-size lesson from.

**And CP-40 had no shared storage between virtual machines.** What the paper
shares is the read-only *disk*, giving "all users access to a library of
often-used systems and routines", plus partitioned unit-record equipment.
Named saved systems and shared segments are a later VM/370 invention.

So the ancestry of the problem in
[`../../docs/04-SHARED-SEGMENTS.md`](../../docs/04-SHARED-SEGMENTS.md) reads:

    CP-40      no shared storage at all
    CP-67      unknown - control program source lost
    VM/370     64 KB shared segments
    ESA/390    1 MB, shared or not as a whole

The one generation that might have had something to say is the one whose
control program did not come back. **If a CP-67 control program source or
listing exists anywhere, it is worth more to this project than anything else
in this directory** — but the CMS recovery and the CP-40 paper, both now
read, do not substitute for it.

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
