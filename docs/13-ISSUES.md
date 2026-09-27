# Known issues and defects

27 September 2026. Concrete things that **are** wrong, in our artifacts or in
the environment we depend on. Forward-looking risks live in
[12-RISKS.md](12-RISKS.md); the boundary is that an issue has already happened
and can in principle be reproduced.

Closed entries are kept deliberately. Several of them are retracted
conclusions, and a register that quietly drops its own errors is worth less than
one that carries them — three of the entries below are places where a confident
claim in this repository turned out to be wrong, and knowing that is part of
calibrating the rest.

**Status values.** `open` · `fix known` (root cause understood, not applied) ·
`fixed` (corrected in this repo) · `worked around` (living with it) ·
`documented` (environment behaviour, not ours to fix) · `closed` (a wrong claim,
retracted and corrected).

---

## Open

| ID | Title | Description | Status |
|---|---|---|---|
| **I-01** | CP's `MSG` macro fails under z390 | `AZ390E error 35, expression parsing error` on lines like `MSG 'STORAGE IS VIRTUAL=REAL'`. `MSG.MACRO` does substring and length arithmetic on a quoted operand (`'&ARG2'(1,1) NE ''''`, `K'&ARG2-2`) and z390's expression parser disagrees with HLASM. **One macro blocking ~20 modules, including `DMKPGS`, `DMKBLD` and `DMKPTR` — three of the five DAT modules.** The single highest-leverage fix on this list. | open |
| **I-02** | `DMKCPI` source encoding | `MZ390E error 138, invalid ascii source line 365` — the U+E000 private-use encoding the CE README describes. Applies only to some members; `DMKVAT` and `CORE` are clean. Reverse substitution verified to give `rc=0` on `DMKCPI`, taking the M1 set to 8 of 9, but the step is not yet in the pipeline. | fix known |
| **I-03** | `DMKDSP` duplicate `USING` ranges | `MNOTE 4, 'Duplicate USING ranges found for - 2 and 0 using highest'`. HLASM tolerates overlapping `USING`; z390 escalates. A dialect difference, not a defect in CP. | worked around |
| **I-05** | 59 macro names never cross-checked against z390 directives | `TRACE` was found because it failed. Any CP macro name colliding with a z390 directive behaves identically but may not fail — producing a false clean assembly. The cross-check is mechanical and has not been run. Mitigation for R-13. | open |
| **I-06** | `dat4b.py` fills unused PTEs with `X'20'` | `X'20'` is the *segment*-invalid bit; a page table entry needs `X'400'`. Harmless where it appears, because those entries are never referenced — but wrong if the idiom is copied, and it nearly was, into `lra1.py` case C. | open |
| **I-07** | `herc.conf` carries an invalid codepage name | `CODEPAGE 819-1047` is rejected by Hercules 3.13 (`HHCCF051E`), which spells it `819/1047`. Non-fatal — the run continues on the default — so it is easy to miss entirely. | open |
| **I-08** | M1's exit criterion is satisfiable by a hung CP | M1 is defined as "CP IPLs in ESA/390 mode and writes one console message". Test 7 proved that a CP which gets `DMKIOS` right and omits CR6 **prints exactly that message and then hangs forever**, with nothing in any log. The milestone as worded passes on a dead system. Needs strengthening to require progress *past* the message — a second message, or a line of console input, which puts `DMKCNSIN` on the path. | open |
| **I-09** | M2 names no observable | "DAT on with ESA/390 tables, no guests" may not describe a runnable state: CP's own execution is largely real-mode, and the tables it builds are for virtual machines. With nothing to dispatch, nothing translates, so M2 either has no observable or collapses into M3. Needs an explicit one — e.g. `DMKBLD` builds a table set and `TRANS` returns a correct above-the-line real address for a virtual address in it, self-checked inside CP. | open |
| **I-10** | M3 bundles two independent risks | M3 contains both "a guest logs on and runs CMS" and "frame-level shared segments in `DMKATS`", so a failure has two candidate sources — the thing the milestone ladder exists to prevent. The split is already available in the machinery: **`IPL 190` by device address needs no `DMKSNT`, no `DMKATS` and no shared segments**, while `IPL CMS` by saved-system name needs all three. Proposed M3a / M3b. | open |
| **I-11** | IPL-from-DASD is owned by no milestone | M1 explicitly defers `DMKCKP`, `DMKSAV` and the whole IPL path under strategy B, and no later milestone picks them up. A CP that can only be started by poking storage from the Hercules panel is a lab artifact, not a system. Those three modules also carry 70 of the 82 DAT references M1 avoided. See R-09. | open |
| **I-12** | CMS stage 2 has no milestone number | The stated goal — an application with an 18 MB heap — is unreachable through M0–M4, all of which leave every guest at 16 MB. The CMS work is surveyed and measured but unnumbered. See R-10. | open |

## Environment — documented, not ours to fix

| ID | Title | Description | Status |
|---|---|---|---|
| **I-13** | Hercules 3.13 will not link with modern gcc | `softfloat` declares `float_exception_flags` and `float_rounding_mode` `__thread`; libtool's generated symbol table references them as non-TLS, so `ld` fails with `TLS definition … mismatches non-TLS reference` — reported misleadingly as `libsoftfloat.a: error adding symbols: bad value`. Dropping `__thread` links cleanly. Lab-only; see R-21. | worked around |
| **I-14** | `--disable-shared` breaks the device modules | Statically linking every device module collides, because they all define `hdl_depc`, `hdl_init` and `hdl_ddev`. Configure with the default shared modules. | documented |
| **I-15** | Device modules must be installed, not just built | Running `hercules` from the build tree gives `HHCCF042E Device type 3215-C not recognized`, because `hdt1052c` is not in `/usr/local/lib/hercules`. With no device attached there is no subchannel 0000, so `SSCH` correctly returns cc=3 and test 6 reports `000C03` — which looks exactly like a real SSCH failure. `make install` first. | documented |
| **I-16** | OPERATOR cannot IPL CMS under CE | Its directory entry gives it 2 MB, while CE's CMS saved system has shared segments at 15.5 MB, so the segments fall outside the machine. `cp define storage 16m` first, or log on as MAINT (`15M 16M`). | documented |

## Closed

| ID | Title | Description | Status |
|---|---|---|---|
| **I-17** | `TRACE` collides with a z390 directive | z390's built-in `TRACE` shadowed CP's macro and z390 tried to resolve `CODE=` as a symbol. Fixed by renaming to `TRACZ` — and the rename **must be the same length**: the first attempt, `CPTRACE`, pushed each line's `@V40759` change marker into column 72 and the macro began failing with "continuation line < 16 characters". This is where R-04 comes from. | fixed |
| **I-18** | First `XAOPS` validation proved nothing | z390's built-in instruction definitions shadowed the macros under test, so the validation exercised z390 rather than `XAOPS`. Fixed by X-prefix renaming throughout `macros/validate/`. | fixed |
| **I-19** | `snt-collisions.py` assumed `SYSHRSG` starts where `SYSPGNM` starts | `CMSOLD` broke the assumption. Fixing it is what revealed the segment-0 finding, so the bug was productive. | fixed |
| **I-20** | Storage-key negative control broke the guard, not the guarantee | The first negative control for `11-storage-keys.rc` patched `ISKE` to read the wrong frame, which tests the guard rather than bypassing it — giving `001201` instead of the `001203` a real bypass would produce. | fixed |
| **I-21** | `RSCH` opcode "dispute" | Recorded as a genuine conflict between Hercules (`B238`) and a reading of the 370-XA Reference Summary (`B23B`). There was no dispute: z390's table gives `B238 RSCH, B239 STCRW, B23A STCPS, B23B RCHP`. `B23B` is RESET CHANNEL PATH, a different instruction. My error, not the sources'. | closed |
| **I-22** | "Hercules cannot prototype the `SIO` gap" | Claimed that `ORB5_I` was ignored, so the `SIO` condition-code contract could not be tested before M1. Wrong: initial-status interruption has been in Hercules since **version 1.39, 24 November 1999**. `06-initial-status.rc` tests it and passes. Retracted in three documents. | closed |
| **I-23** | "Segment 15 is the false alarm" | `04-SHARED-SEGMENTS.md` concluded that the segment-15 collision was benign, resting on saved-page analysis, with one caveat it could not check. Reading the real `USER DIRECT` closed that caveat **against** the conclusion: eight machines default to 15 MB, two to 14 MB, `XNET` to 16 MB, and 21 can be defined to 16 MB, so private storage routinely occupies exactly where CMS's shared segments sit. Corrected in `04`, `05` and `11`. | closed |
| **I-04** | `XATEST` listing never checked | Seven of twelve `XAOPS` encodings came from z390's opcode table rather than from execution, and the listing that would confirm them had never been produced. Now produced by CE's own Assembler XF and saved as `macros/validate/XATEST-CE-XF.LISTING`; all twelve object codes read off it and correct. See [14-M0-CLOSED.md](14-M0-CLOSED.md). | fixed |
| **I-26** | Duplicate spool file from `START` plus `devinit` | `CP START 00C` un-drains the real reader *and* triggers a read; a following `devinit` of the same device read the same file again, queueing two identical spool files. The second `READCARD` took the duplicate, so `XATEST ASSEMBLE` landed on disk as a 194-record copy of `XAOPS MACRO` and failed with `IFO047 UNEXPECTED END OF FILE ON SYSTEM INPUT` — a plausible-looking macro failure that was nothing of the kind. Fix: `devinit` once per new deck, and always check `LISTFILE`'s record count against the deck size. | fixed |
| **I-27** | "g4ugm verifies CE against IBM" | Claimed that diffing `g4ugm/vm370.source` against CE proved CE's CP source is IBM's Release 6 source unmodified. The diff was right; the conclusion was not. g4ugm carries CE's own `HRC` update markers and references CE-only `HDK*` modules, so it is the same resolved tree — two copies of one tree agreeing proves nothing about IBM. The check that would have caught it is one `grep` for the other tree's change ids. Corrected in [15-UPDATE-LEVELS.md](15-UPDATE-LEVELS.md); the real baseline is CE's own `maintenance/files/394`. | closed |
| **I-24** | `CODE70` identified as ESA/390's `ARCHTECT` row | `CODE70` is 2 KB pages. **`CODEB0`** is the ESA/390 row — 4 KB pages, 1 MB segments, fullword PTEs, 2,048 segments. | closed |
| **I-25** | `CPCREG0` classified as a constant | It is a live CR0 save area: `STCTL C0,C0,CPCREG0  SAVE IN REAL 0 FOR CP`. Would have been treated as a fixed bit pattern across 38 reference sites. | closed |

## Counts

| Status | Count |
|---|---|
| open | 11 |
| fix known | 1 *(I-02, counted in open above)* |
| environment | 4 |
| closed / fixed | 12 |

**Six of the twelve closed entries are retracted claims of my own** — I-21,
I-22, I-23, I-24, I-25. Four were wrong in the project's favour, one (I-23) against it, and one
(I-27) was wrong in the flattering direction — which is the one to watch. That ratio is itself worth watching: a review
that only ever finds good news is not reviewing.
