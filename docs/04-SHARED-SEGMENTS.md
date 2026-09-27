# Shared segments at 1 MB: the collision is two items, not nineteen

> **Superseded in its conclusion, and its one open caveat has now come back
> POSITIVE. Read [05-CP67-PRIOR-ART.md](05-CP67-PRIOR-ART.md) with it.**
>
> **Segment 15 is NOT benign.** The "Loose ends" section below flagged one
> check that could overturn that finding: whether any virtual machine's
> private storage reaches 14–16 MB. It needed `USER DIRECT`, which is a CMS
> file and not in the source tree. That file has now been read, by running
> VM/370 CE itself (`11-RUNNING-CE.md`), and the answer is yes —
> **eight machines default to 15 MB, two to 14 MB, `XNET` to 16 MB, and
> twenty-one can be defined up to 16 MB.** CMS's shared segments sit at
> 15.0–15.7 MB, inside that private storage.
>
> So under VM/370-style segment sharing at 1 MB, making segment 15 common
> would expose the private storage of most machines on the system. The
> collision is real.
>
> **Which makes frame-level sharing necessary rather than merely tidier.**
> `05` is no longer the elegant option; it is the only one.
>
> Everything measured below is correct, but it rests on an assumption that
> turns out to be false: that sharing must be segment-granular, because a
> segment table entry is the smallest thing you can repoint. CP-67 ran **1 MB
> segments and shared at 4 KB granularity**, by giving each virtual machine
> its own page table and sharing the frames rather than the table.
>
> So the collision table below is the cost of **keeping VM/370's sharing
> implementation** under ESA/390 — not the cost of moving to ESA/390.
> `CMSOLD` is not a blocker, and the compatibility decision this document
> asked Adrian for does not need making. See `05` §5.

26 September 2026. Supersedes the §3a framing in 01-PROPOSAL.md and the
`PAGTSWP` discussion in 03-CP-INVENTORY.md, both of which described this as
a compatibility decision about every saved system. Measured, it is two
specific problems and one false alarm.

Reproduce with:

    python3 arch/31bit/tools/snt-collisions.py path/to/source/cp/DMKSNT.ASSEMBLE

## The question, stated correctly

CP runs 64 KB segments; ESA/390 has only 1 MB segments; **a segment is
shared or not as a whole.** Sixteen 64 KB segments fit in one ESA/390
segment.

So the question is not how much granularity changes. It is: **which pages
are private today and would become common under 1 MB segments?** A saved
system whose shared segment lands in the same megabyte as another's private
storage exposes that storage to everybody. That is an isolation failure, not
an inefficiency, and it is the thing worth measuring.

`DMKSNT`'s `NAMESYS` macros give both halves: `SYSHRSG` names the shared
segments in 64 KB units, `SYSPGNM` the saved pages in 4 KB units. Private
pages are the difference.

## The measurement

Ten saved systems, nineteen distinct 64 KB shared segments, collapsing into
three 1 MB segments:

| Saved system | 64 KB segs | Shared at | 1 MB seg |
|---|---|---|---|
| CMSOLD | 1 | 0.062–0.125 MB | **0** |
| CMSVSAM | 224–228 | 14.000–14.312 MB | 14 |
| CMSAMS | 230–235 | 14.375–14.750 MB | 14 |
| CMSSEG | 240 | 15.000–15.062 MB | 15 |
| CMSDOS | 241 | 15.062–15.125 MB | 15 |
| INSTVSAM | 241 | 15.062–15.125 MB | 15 |
| GCCLIB | 242–243 | 15.125–15.250 MB | 15 |
| CMS | 248–250 | 15.500–15.688 MB | 15 |
| CMSTEST | 248–250 | 15.500–15.688 MB | 15 |
| **CMS67** | **none** | — | — |

## 1. Segment 15, with six saved systems in it, is the false alarm

`CMSSEG`, `CMSDOS`, `INSTVSAM`, `GCCLIB`, `CMS` and `CMSTEST` all force
segment 15 common. That looks like the worst collision in the table and it
is the benign one: **no saved system has any private page between 15 and
16 MB.** Everything up there is shared already, so collapsing it into one
common segment over-shares nothing.

This is not luck. CE deliberately parked its shared segments at the top of
the address space, and says so — `CMSSEG`'s comment reads "We define the
CMSSEG shared segment at 15MB to maximize the VM size." That decision,
taken for an unrelated reason, is what makes the 1 MB change survivable.

`CMSDOS` and `INSTVSAM` both claim segment 241, and `CMS` and `CMSTEST`
both claim 248–250. Those overlaps exist **today**, at 64 KB, so CE already
treats those pairs as mutually exclusive. The 1 MB change does not create
them.

## 2. Segment 14 needs VSAM and AMS separated

`CMSVSAM` (segments 224–228) and `CMSAMS` (230–235) both force segment 14
common, and **each has private saved pages inside it**:

    CMSVSAM   16 private pages at 14.312-14.375 MB
    CMSAMS    32 private pages at 14.750-14.875 MB

Under 1 MB segments each would see the other's private storage, and so
would any virtual machine with either attached. These are meant to be
loadable together — VSAM and its access-method services.

Fixable by moving one of them so their megabytes differ: there is unused
space below 14 MB, and CE has relocated saved systems before for exactly
this kind of reason. It is a layout edit to `DMKSNT`, not a design change.

## 3. Segment 0 is the real blocker, and it is `CMSOLD` alone

`CMSOLD` shares 64 KB segment 1 — `X'10000'` to `X'20000'`. Under ESA/390
that forces **the entire first megabyte to be a common segment**, and the
first megabyte is where every saved system keeps its low storage:

    CMSOLD    17 private pages at 0.000-0.129 MB
    CMS       17 private pages at 0.000-0.129 MB
    CMSTEST   17 private pages at 0.000-0.129 MB
    CMS67     19 private pages at 0.000-0.074 MB

Those are the PSA and nucleus low core. Sharing them across virtual
machines is not a degradation, it is the end of isolation.

**CE already knows this address range is a problem.** Change `@D03` in
`DMKSNT` reads:

    Change definitions to support a CMS Nucleus which is relocated to
    high memory to relieve the storage contraint between X'10000' and
    X'20000'

`X'10000'`–`X'20000'` *is* segment 1. The modern CE nucleus was moved out
of it. `CMSOLD` is the deliberately-frozen VM/370 1.3 Sixpack CMS kept as a
fallback — its comment says it "is intended to never be updated and to serve
as a backup if the production and test versions of CMS are broken."

So the options are narrow and none of them is a redesign:

- **Retire `CMSOLD`** under 31-bit CP. It is a backup for a 24-bit system;
  a 31-bit CP keeping a 24-bit fallback of its own CMS is arguably the wrong
  artefact anyway.
- **Relocate its shared segment above 1 MB**, which is the same move CE
  already made for the production nucleus. It breaks the "never updated"
  intent, which is the point of the thing.
- **Keep it, 24-bit only**, and refuse to attach it under a 31-bit CP.

This is a question for Adrian because it is about what CE promises its
users, not about what the hardware allows.

## What this does to the estimate

*(Written before 05-CP67-PRIOR-ART.md. The counts stand; the framing is
superseded — with frame-level sharing there is no decision here at all.)*

The proposal said "every existing saved-system definition changes
granularity by 16×, and anything sharing less than a megabyte must
over-share or be redesigned." That is true of the arithmetic and wrong
about the consequence. Measured:

- **Segment 15**: six saved systems, no private pages, nothing to do
- **Segment 14**: move `CMSVSAM` or `CMSAMS` — a `DMKSNT` layout edit
- **Segment 0**: decide what happens to `CMSOLD` — the only real decision
- **`CMS67`**: shares nothing, unaffected

One decision and one layout edit, not ten redesigns.

## Loose ends

**`CMSDOS`, `INSTVSAM` and `GCCLIB` declare shared segments containing pages
they do not save** — 8, 8 and 3 pages respectively. A shared segment whose
pages are absent from `SYSPGNM` is either intentional (zero-filled, or
don't-care tail) or an existing latent bug. It does not change the collision
result, but it should be understood before `DMKSNT` is edited, because it
means `SYSHRSG` and `SYSPGNM` are not redundant descriptions of the same
thing.

**The private-page analysis uses saved pages, not run-time storage.** A
virtual machine defined with more storage than its saved system uses could
have private pages anywhere below its size, including inside segment 14 or
15. Confirming that needs the `USER DIRECT` file, which lives on a CMS disk
rather than in the source tree — `UDIRECT.COPY` is the control block layout,
not the directory. **This is the one check that could make segment 15 stop
being benign**, and it is worth doing before relying on the conclusion
above.
