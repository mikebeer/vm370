# 64-bit — z/Architecture

The destination. **Not started**, and deliberately downstream of
`../31bit/`.

## Status

Nothing here executes yet. What exists is a seed and a scope.

**The seed** is `systems/vmce/source/wide/` in the CE tree — freestanding
z/Architecture proofs built with GCC s390x LP64 targeting `z900`, loaded as
ELF64 images with `loadcore` and started with `restart`/`runtest`, with DAT
fixtures already present. Its README is explicit that it is "not an
operating system or a CMS boot image", so it reads as a 64-bit *application*
environment proof that leaves the kernels alone.

**The method is the same as the 31-bit tests** — poke an image into real
storage, start the CPU, read the resulting PSW — so the two harnesses can
share tooling. `../31bit/tests/hardware/build/asm.py` is the obvious
candidate to hoist once something here needs it.

## What carries forward from 31-bit, and what does not

This is the whole reason for the ordering, so it is worth being precise.

**Carries forward unchanged:**

*The channel subsystem.* It arrived with 370-XA in 1983 and z/Architecture
did not touch it. `SSCH`, `MSCH`, `TSCH`, `CSCH`, `HSCH`, the ORB, the SCHIB,
the IRB — same instructions, same control blocks, same condition codes. CP's
I/O conversion is done once.

*Page and segment geometry.* 4 KB pages and 1 MB segments in both. So the
expensive 64 KB → 1 MB segment rework, and everything it drags in around
shared segments and named saved systems, is also done once.

*Storage key granularity.* 4 KB in both, having been 2 KB under S/370.

**Does not carry forward:**

*The PSW.* 16 bytes with a different layout, against 8 under ESA/390. That
reaches lowcore, every new/old PSW pair, and every place CP builds or
inspects a PSW — which is a lot of places.

*Translation depth.* z/Architecture inserts region tables — region first,
second and third — above the segment table, giving up to five levels where
ESA/390 has two. CR1 stops holding a segment table designation and holds an
address-space-control element carrying a designation type, so translation
starts at whichever level the ASCE names.

*Mode switching.* `SAM24`, `SAM31` and `SAM64` replace `BSM`/`BASSM`. They
are cleaner — no branch, no register convention — but they are different
instructions, and `XAOPS.MACRO` deliberately does not define them because
they are not ESA/390.

*Register width.* 64-bit general registers, `LG`/`STG`/`AG` and the whole
grande instruction set. Mechanical, and pervasive.

## Which ELF ABI, and an R13 collision to watch

`wide/` builds ELF64 with GCC s390x LP64 targeting `z900`, so it is governed
by the **s390x** ELF ABI. Its 31-bit sibling — *S/390 ELF Application Binary
Interface Supplement*, v1.02, November 2002 — is the ESA/390 one, and the two
are separate documents; the 31-bit volume's own trademark table distinguishes
"S/390 / System/390" from "zSeries / z/Architecture". Worth naming which one
applies before quoting a calling convention at anybody.

Neither governs CP. CP is assembler built natively into TEXT decks; ELF
headers, relocations, the GOT and the PLT describe a loader it does not have.
The ABI matters at exactly one boundary: where C meets assembler.

**And at that boundary there is a register collision.** The 31-bit ABI
reserves **R13 as the literal pool pointer**, set up in every function prolog,
because "S/390 instructions cannot hold 31-bit addresses directly, so a
program has to build an address in a register and access memory through that
register". CP uses R13 for its own linkage, and `CALL` loads R15. CE already
has C components — `kernel-c`, and the lwIP networking — so this boundary
already exists in the tree, and which convention they were built to is worth
establishing rather than assuming.

The 31-bit volume is also a useful read for a second reason: its "Data
objects", "Function calls" and "Branching" sections are explicitly "intended
to explain addressing modes", which makes them an authoritative worked
treatment of getting 31-bit addresses into registers — the same problem CP
hits at every 24/31-bit mode boundary. Not a convention to adopt, but the
canonical discussion of the difficulty.

It also confirms the geometry independently: "Processes execute in a 31-bit
virtual address space" and "The hardware page size for the ESA/390
architecture is 4096 bytes."

## Open questions

**Does a 64-bit CP need 64-bit guests to be worth it?** The 31-bit answer is
no — a 31-bit CP running S/370-mode guests is a valid, useful intermediate.
Whether the same holds one level up has not been thought through.

**Which ABI does `wide/` build to, and do CE's existing C components follow
the same one?** See the R13 note above.

**Is `wide/` the intended destination, or a parallel track?** If
`VMCE-WIDE-PLAN.md` has selected a direct 64-bit route that supersedes the
31-bit kernel work, the ordering argument in the root README is wrong and the
milestones in `../31bit/` need rethinking. This is an open question to Adrian,
noted in `../../docs/01-PROPOSAL.md` §7.

## References

ESA/390 Principles of Operation SA22-7201 and z/Architecture Principles of
Operation SA22-7832; the latter's chapter 3 covers the ASCE and the region
table hierarchy, and its Appendix on comparisons with ESA/390 is the shortest
route to a change list.
