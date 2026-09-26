# CP-67 as prior art: 1 MB segments with page-granular sharing

26 September 2026. **This corrects the conclusion of 04-SHARED-SEGMENTS.md.**
That document found that `CMSOLD`'s shared segment forces the entire first
megabyte common under ESA/390, and called it the one real blocker. The
arithmetic is right. The conclusion assumed something that is not true: that
sharing has to be segment-granular because segments are the unit of sharing.

CP-67 ran **1 MB segments and shared storage at 4 KB granularity.** It is an
existence proof, from IBM, on the same architecture family, that the two are
separable.

> **And it is no longer only historical.**
> `../arch/31bit/tests/hardware/09-frame-sharing.rc` executes the mechanism on
> ESA/390 and passes: two address spaces with their own page tables, one
> sharing a frame at virtual `01005000` and differing at `01006000` — the same
> virtual address in the same 1 MB segment. Broken deliberately in both
> directions to confirm it discriminates. So §5's conclusion rests on
> execution now, not on a 1973 manual.

Sources: `GY20-0590-2`, *CP-67 Program Logic Manual*, May 1973 (300 pages, no
text layer — OCR'd at 200 dpi, so quoted wording is transcribed and may carry
scanning errors); `GH20-0857-1`, *CP-67/CMS Version 3.1 Installation Guide*,
October 1971 (text layer, quoted verbatim); `GH20-0802-2`, *System Description
Manual*, September 1971. All from bitsavers.

## 1. CP-67's geometry was ESA/390's geometry

From the PLM's address description:

> The twelve low-order bits of the address provide addressability for 4K bytes
> of storage (one page) … The next eight bits of the address provide
> addressability for 1024K bytes of storage (one segment) … The four
> high-order bits of the address provide addressability for 4096K bytes of
> storage.

12 + 8 + 4: **4 KB pages, 1 MB segments, 16 segments to a 16 MB space.** That
is ESA/390's page and segment geometry exactly, in 1967. Segment table entries
were four bytes, "aligned on a 64-byte boundary" — also ESA/390's rule.

So VM/370's 64 KB segment is not an inheritance from CP-67. It is a later
choice, and §3 below is why it was made.

Incidentally, **CP-67 ran in 24-bit mode**, not the Model 67's 32-bit mode —
it could "simulate a Model 65 or Model 67 (simplex, 24 bit addressing)". The
32-bit facility existed in the hardware and this control program did not use
it, which closes a question left open in `../heritage/cp67/README.md`.

## 2. Shareability was declared per page

The Installation Guide's saved-system macros — CP-67's `DMKSNT` equivalent:

    ttt   SWPTABLE DASDORG=ccc,FIRSTP=aa,LASTP=bb,
            FIRSTSP=xx,LASTSP=yy,DISK=ddd

    where
      aa    is the first page saved;
      bb    is the last page saved;
      xx    is the first shared page, if any;
      yy    is the last shared page, if any;

**`FIRSTSP` and `LASTSP` are page numbers.** Compare VM/370:

    SYSHRSG=(248,249,250)

which are 64 KB **segment** numbers. Same job, one unit of granularity
coarser by a factor of sixteen — and that is the whole of the difference this
project has been wrestling with.

## 3. Why the units differ: shared page tables versus shared frames

This is the mechanism, and it is what makes the difference.

**VM/370 shares the page table itself.** `SYSHRSG` names segments, CP points
several virtual machines' segment table entries at one common page table, and
one page table serves all of them. Cheap — a single table, a single set of
frames — and the granularity is forced to be exactly one segment, because a
segment table entry is the smallest thing you can repoint. Segment size *is*
sharing granularity. When VM/370 wanted finer sharing than a megabyte, the
only lever available was to make the segment smaller, and S/370 offered 64 KB.
That is the trade, and it is why the 16× coarsening hurts.

**CP-67 gives each user their own page table and shares the frames.** The
Installation Guide is explicit that the declaration produces a *model*:

> The SWPTABLE macro builds a model SWPTABLE that is mapped to the virtual
> machine SWPTABLE in core to give that machine access (through paging) to the
> saved system.

and the PLM, on a second user IPLing an already-resident shared system:

> When a subsequent user IPL's the same system, no paging is required, but the
> PAGTABLE of such a user is set to point to the shared pages.

A page table entry is per-page, so populating individual entries from a model
shares at **page** granularity regardless of how large a segment is. The
entry points of `PAGSHARE` and `PPAGOUT` confirm the code works at that
level — `PAGSHARE` takes "GPR 4 = first shared page number; GPR 5 = PAGTABLE
address; GPR 6 = count of saved pages", and `PPAGOUT` takes a segment table
entry address *plus* "the address of the PAGTABLE entry for the first page"
and "the number of pages to be released".

The cost is one page table per sharing virtual machine instead of one in
total. Under ESA/390 that is 256 fullwords — **1 KB per virtual machine per
shared megabyte.** On a machine with 64 MB it is not a consideration.

## 4. Write protection came from storage keys, not from DAT

Worth separating carefully, because it is easy to over-credit. Storage keys
do not make sharing finer-grained — the page tables do that. Keys stop a
sharer from *writing* to what it shares:

> For store protection of the shared pages, the users are run with protection
> key = F. All shared pages' storage keys are set to zero and all other pages
> belonging to these users have storage keys = F.

`PAGTRANS`'s own flow confirms it: *"If shared page, get key '0', non-shared
pages get key 'F'."* A key-F program storing into a key-0 page takes a
protection exception. Reentrant code shared read-only, enforced per page,
with no involvement from the segment tables at all.

ESA/390 keys cover 4 KB rather than S/370's 2 KB, which for this purpose is
an improvement: one key per page instead of two.

## 5. What this does to 04-SHARED-SEGMENTS.md

The collision table in that document is still correct, but it describes **the
cost of keeping VM/370's sharing implementation**, not the cost of moving to
ESA/390. Three options, and the third is CP-67's:

| | Granularity | Page tables | `CMSOLD` at `X'10000'` |
|---|---|---|---|
| Share page tables, 64 KB segments | 64 KB | one | works — today's CE |
| Share page tables, 1 MB segments | 1 MB | one | **breaks** — first megabyte common |
| Share frames, 1 MB segments | **4 KB** | one per VM | **works** |

**So `CMSOLD` is not a blocker and there is no compatibility decision to
make.** Sharing at frame granularity keeps every existing saved-system layout
working at its current granularity, `CMSOLD` included, and the ESA/390
segment-table common-segment bit — which is what would force a whole megabyte
common — is simply never used. That bit is a TLB optimisation, not the
sharing mechanism.

This does move work rather than remove it: `DMKATS` and the `NAMESYS` path go
from repointing one segment table entry to populating a range of page table
entries per virtual machine, and the shared frames need locking and
reference-counting that a single shared page table gets for free. That is
engineering inside two modules, with a documented precedent, rather than a
question about what CE promises its users.

## 6. A second find: CP-67's shadow tables, and a reset trick

Not about sharing, but directly relevant to `DMKVAT` — and to
02-CP-VERIFIED.md, which argued `DMKVAT` is less frightening than it looks.
CP-67 already did shadow tables for a virtual 67 running with translation on,
with terminology worth borrowing:

> **First level memory**: The memory of the real 360/67.
> **Second level memory**: The memory of a virtual 360/67.
> **Third level memory**: The memory of a virtual machine running under the
> virtual 360/67.
> **Copy segment table**: A copy, in first level memory, of the segment table,
> in second level memory …
> **Image segment table**: A copy, in first level memory, of the shadow
> segment table, with 00 in the first byte of each entry, and bit 31 set to 1
> (unavailable bit) in each entry.

Two ideas in there:

**The image segment table is a reset trick.** Rather than walk the shadow
segment table invalidating entries, CP-67 keeps a pre-built copy with every
entry already flagged unavailable and copies it over the shadow table — "in
order to reset it quickly with all the entries flagged with the unavailable
bit on". One block move instead of a loop, on a path taken every time a guest
loads control register 0 or a page is stolen.

**The monosegment fast path.** CP-67 distinguishes a "monosegment machine"
(*"a virtual 67 in which segments 1 through 15 are not used"*) from a
multisegment one, and *"monosegment virtual machines are handled with much
less overhead"* — a monosegment guest needs only its single shadow page table
reset, no segment table copy at all. Under ESA/390 the equivalent threshold is
a guest using no more than 1 MB, which most CMS guests exceed, so this is
worth knowing rather than worth copying. The image-table trick has no such
limit.

## Caveats

**The PLM is OCR.** 300 scanned pages at 200 dpi with no text layer. Quoted
wording is transcribed and the tables and figures came through poorly. The
Installation Guide quotations are from its text layer and are reliable. Any
claim here that a decision rests on should be checked against the scan.

**The exact page-table plumbing is inferred, not quoted.** That CP-67 shared
at page granularity is documented four ways — `FIRSTSP`/`LASTSP`, the "model
… mapped to the virtual machine SWPTABLE" wording, the per-page storage keys,
and `PAGSHARE`/`PPAGOUT`'s page-level entry conditions. Whether the shared
page table in `PAGTRANS` is copied from or pointed at in some hybrid way is
not something the OCR resolves, and it does not change the conclusion.

**The 1971 edition, `GY20-0590-1`, has a text layer** and a "Shared Pages"
section around page 103. It is the cheaper source for anyone re-checking
this, and it is 18 MB rather than 126 MB.
