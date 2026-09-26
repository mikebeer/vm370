# 24-bit — S/370

VM/370 Community Edition as released. This is the **baseline**, not an
archive: every claim the 31-bit work makes about what it changes is measured
against this, and a 31-bit CP that cannot still run an unmodified S/370-mode
guest has failed.

## Status

**Works.** CP and CMS run under Hercules with `ARCHMODE S/370`. Guests get a
16 MB address space and the whole toolchain — `ASSEMBLE`, `LOAD`, the
MACLIBs — is native and self-hosting.

## The one thing to know

**Do not set `ARCHMODE ESA/390` in the config CE boots from.** CP is S/370
code. Symptom is a disabled wait immediately at IPL:

    HHCCP011I CPU0000: Disabled wait state PSW=000A0000 00000017

with the control registers still at Hercules reset values. It is not a
subtle failure and it is not recoverable by restarting — the mode has to go
back.

The ESA/390 lab machine in `../31bit/tests/hardware/herc.conf` is therefore a
**separate config in a separate directory**, on a different console port, so
both machines can run at once and neither can pick up the other's
`hercules.rc`.

## The architecture facts this baseline establishes

These are the numbers the 31-bit conversion has to move, and they come from
CP's own source rather than from the manuals:

**Segments are 64 KB of sixteen 4 KB pages.** `CORE.COPY` carries
`PAGTSWP EQU (PAGCORE-PAGSTMP+16*L'PAGCORE)`, commented "LENGTH OF A FULL 16
ENTRY PAGE TABLE", and `DMKCPI`'s `CTLREGS` sets `PAGE4K` without `SEG1M`.

**Page table entries are halfwords.** `PAGCORE DS 1H`, "REAL PAGE ADDRESS",
with `PAGINVAL EQU X'08'` and `PAGREF EQU X'01'`.

**Storage keys are tracked per 2 KB.** `SWPKEY1` and `SWPKEY2` are "VIRTUAL
STORAGE KEY, 1ST/2ND 2048 BYTES", with `SWPREF1`/`SWPCHG1` and
`SWPREF2`/`SWPCHG2` per half-page.

Each of the three changes under ESA/390, and the first two are why the DAT
tables cannot simply be widened in place. Detail in `../../docs/`.

## What belongs here

- The S/370 Hercules configuration CE is known to boot under
- Regression tests that must keep passing across the conversion
- Anything measured about CE's current behaviour, so that a later claim of
  "unchanged" can be checked rather than asserted

Currently this directory holds documentation only. The configuration and
disk images live in Adrian's tree; a pointer or a snapshot belongs in
`../../heritage/vm370ce/` rather than being duplicated here.
