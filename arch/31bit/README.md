# 31-bit — ESA/390

Converting CP and CMS from S/370 to ESA/390, so that a virtual machine can
address storage above the 16 MB line.

**Status: the hardware question is answered; the software conversion has not
started.** Six standalone tests establish that every architectural facility
a 31-bit CP needs exists and behaves as documented on **stock, unpatched
Hercules**. That is necessary and it is not the same as the conversion being
tractable.

A note on naming: this is not VM/ESA. That was an IBM product with its own
CMS, shared segments and service structure. This is a 31-bit VM/370 CE.

---

## What is proven

Thirteen programs in `tests/hardware/`, each answering one question, each with
its own pass code so that a stale program left in storage cannot masquerade
as a pass. **All thirteen pass**, the seventh on two independently built
emulators — a Windows 3.x build and a Hercules 3.13 built from source on
Linux, which reached the pass by different paths (status on the first `TSCH`
in one, after several polls in the other).

| Test | Pass | Question |
|---|---|---|
| `01-dat-tables` | `00600D` | Are hand-built DAT tables accepted, and does DAT run? |
| `02-page-table-walked` | `00600D` | Is the page table actually being walked? |
| `03-amode31` | `006003` | Does the AMODE 31 switch work, and does DAT survive it? |
| `04a-virtual-above-line` | `006004` | Does an above-the-line **virtual** address translate? |
| `04b-real-above-line` | `006005` | …to an above-the-line **real** frame? |
| `05-channel-subsystem` | `006006` | Does MSCH/SSCH/TSCH drive a real device? |
| `06-initial-status` | `006007` | Does `ORB5_I` give a zero condition code, so `SIO`'s synchronous contract has an equivalent? |
| `07-io-interrupt` | `006008` | Does an **I/O interruption** arrive and identify its subchannel from lowcore — the way `DMKIOS`/`DMKIOT` actually work? |
| `08-lra` | `006009` | Does `LRA` behave as `TRANS` assumes, in both addressing modes? |
| `09-frame-sharing` | `00600A` | Can 4 KB sharing **and** 4 KB isolation coexist inside one 1 MB segment? |
| `10-dasd-read` | `00600B` | Does a real CKD chain work — SEEK, SEARCH, TIC, READ — the way `DMKIOS` issues them? |
| `11-storage-keys` | `00600C` | Do storage keys give read-only sharing per page — CP-67's other half? |
| `12-ste-flags` | `00600D` | Is CP's segment-flag collision survivable, and what happens if the invariant breaks? |

Test 4b stores at virtual `X'01005000'` — segment 16, page 5 — in 31-bit
mode with DAT on. The byte arrives at real `X'01100000'`, and real `X'5000'`,
where a 24-bit truncation would have landed, stays zero. Test 5 writes a
line to a 3215 console from a hand-built PMCW, ORB and format-1 CCW: device
status exactly `CE|DE`, subchannel status zero, residual zero.

Verified on Hercules 3.07 (Windows, built 23 March 2010) with
`ARCHMODE ESA/390`. **Stock, not the S/380 build** — the banner reads
`Hercules Version 3.07` with `Modes: S/370 ESA/390 z/Arch`, no `:380-5.0`
suffix and no `S/380` in the mode list. That matters: had these run on the
patched build, the result would have demonstrated only that the patch works,
which was never in doubt.

## Running them

No operating system, no assembler, no IPL. Each test is a Hercules script
that pokes bytes into real storage and starts the CPU with `restart`.

1. Put `tests/hardware/herc.conf` in a directory of its own.
2. Copy one test file there as `hercules.rc`.
3. Start Hercules on that config, from that directory.
4. Read the instruction address in the resulting PSW.

`restart` takes no address — it reads the restart new PSW from real address
zero, which each script plants with `r 0=0008000000002000`.

**To run a second test you must exit Hercules, or use `stop` / `sysclear` /
`script hercules.rc` at the panel.** `stop` and `restart` alone re-run
whatever is already in storage, which will look exactly like the new test
passing. That cost a full cycle during development, and it is why every test
has a distinct pass code.

Test 10 needs a second config — copy `herc.conf`, append
`0190 3350 scratch.cckd`, keeping the console first so it stays subchannel
0000, and create the volume with
`dasdinit -z scratch.cckd 3350 SCRTCH 10`. Otherwise `herc.conf` deliberately
attaches **one device and no DASD**. A bare-metal
test builds its own channel programs and has no operating system to stop it
addressing the wrong subchannel; during development a write command reached
subchannel `0000` while a writable CE pack was attached, and only the device
rejecting the command code prevented a disk being written to.

**Do not set `ARCHMODE ESA/390` in the config CE boots from.** CP is S/370
code and dies at IPL — observed as a disabled wait, `PSW=000A0000 00000017`,
with control registers still at Hercules reset values. See `../24bit/`.

## Rebuilding them

`tests/hardware/build/` holds `asm.py`, a two-pass assembler, and the
scripts that generate each test's pokes. It resolves labels, checks every
displacement against the 12-bit base-displacement field, checks every
alignment the machine enforces, and bounds-checks writes into the image.

Hand assembly was fine at ten instructions and unreliable at thirty. The
assembler caught two of its own authoring bugs before any Hercules run.

    cd tests/hardware/build
    python3 ssch1.py        # prints a listing, writes the poke commands

## Three facts that are not in the manuals

Each of these cost a debugging cycle, and each came from reading Hercules's
source rather than the Principles of Operation — because the emulator is
what accepts or rejects a control block.

**CR0 carries the DAT translation format, and DAT checks it before reading
any table.** Bits 8–12 must be `10110`; `CR0_TRAN_ESA390 = 0x00B00000`.
Loading CR1 alone gives a translation-specification exception, code `0012`,
on the first translated reference — before a single table entry is examined.
A guest's leftover CR0 will not satisfy it.

**A subchannel is never enabled until `MSCH` says so.** `config.c:740` sets
only the valid bit at device creation; `device_reset()` clears the enable
bit. **`SSCH` on a disabled subchannel returns condition code 3 silently** —
no exception, no message, nothing on the log. `STSCH` → set the enable bit
→ `MSCH`, always.

**`LPM` must be `X'80'`, not `X'00'`.** `SSCH` tests `orb.lpm & pmcw.pam`,
and `pam` is `0x80`, so zero means "no path available" rather than "any
path". `MSCH` cannot change `pam`, which is why reading the PMCW with
`STSCH` first is the safe route.

And one that is in the manuals but easy to misread: **`BAL`/`BALR` are
mode-sensitive.** They place the instruction-length code, condition code and
program mask in bits 0–7 only in 24-bit mode; in 31-bit mode they set bit 0
to zero and put the address in bits 1–31. So they self-correct, and the
hazard is only at **mode boundaries** — a base register established in
24-bit code and used after a `BSM`. That is what broke test 3, at
`V:400020B4`, fixed with `LA 15,0(0,15)`.

## Milestone 0 — instructions for CE's assembler

`macros/` holds `XAOPS.MACRO`: **twenty-four** ESA/390 instructions as macros,
because CE's assembler predates 1983 and knows neither the channel subsystem nor
`BSM`. The count is measured rather than chosen — see below.

    SSCH     MACRO
    &LAB     SSCH  &ORB
    &LAB     DS    0H
             DC    X'B233',S(&ORB)
             MEND

An S-type address constant produces exactly the base register and
displacement an S-format instruction wants, resolved through the active
`USING`, so these behave like instructions rather than hand-poked constants.

    MACLIB GEN XALIB XAOPS

**This is CP's own idiom.** Twenty-one sites in CP already hand-encode
instructions the assembler does not know, including
`DMKVATZP DC X'E60B',S(ARCHTECT,0(R9))` for the ECPS:VM assists.

Five encodings — `MSCH`, `SSCH`, `TSCH`, `STSCH`, `BSM` — are proven by
execution in the tests above.

**And as of 27 September all of them are proven against CE's own assembler.**
`XAOPS.MACRO` was read onto MAINT's 191 disk through the card reader,
`MACLIB GEN XALIB XAOPS` produced all twenty-four members, and
`macros/XATEST.ASSEMBLE` assembled against them:

    ASSEMBLER (XF) DONE
    NO STATEMENTS FLAGGED IN THIS ASSEMBLY
    HIGHEST SEVERITY WAS    0
    TOTAL RECORDS READ FROM SYSTEM LIBRARY      139

The library count is the part that matters — it rules out a call being silently
ignored, which is exactly how the first z390 validation fooled itself. Every
object code matches, and every S-type displacement is arithmetically exact:
with `USING *,R15` at `X'02'`, `SCHIB` at `X'B8'` assembled as `F0B6`. On a
later run the same operand had moved and assembled as `F0E2` — still exact,
which is better evidence than repeating identical bytes. The listing is kept at
`macros/validate/XATEST-CE-XF.LISTING`.

The `RSCH` opcode is `B238`, now confirmed by the assembler that will build the
nucleus. The `B23B` once flagged from the 370-XA Reference Summary is `RCHP`, a
different instruction — and `RCHP` is now a macro in its own right.

### The list is complete, and that is measured

`tools/mkprobe.py` generates a probe containing **every** mnemonic Hercules
marks available in ESA/390 mode, each with no operands, so that only
`IFO078 UNDEFINED OP CODE` has to be counted. Assembled with the `GLOBAL MACLIB`
list cleared:

| | |
|---|---|
| mnemonics probed | **351** |
| unknown to Assembler XF | **186** |
| known to XF | 163 |

Of the 186, the 24 macros cover every one belonging to the channel subsystem, to
ESA/390 DAT, or to the 4 KB storage keys. The other 162 are floating point (64),
access registers and dual address space (32), z/Architecture additions (32), the
vector facility (26), expanded storage (4), `BAS`/`BASR` (2) and two
unclassified — none of which CP uses. Tables in `macros/validate/`.

The probe corrected the guess twice more: **`PTLB` needs no macro** (it is S/370
`B20D` and XF knows it), while **`XSCH` and `CHSC` were on no earlier list** yet
both belong to the channel subsystem.

**One consequence to know before writing any code.** `LHI`, `AHI`, `CHI`, `MHI`,
`BRAS` and `BRC` are all unknown to XF. Every new sequence written for this
conversion needs a base register and a literal pool, exactly like the code around
it. New code cannot be written in a more modern style than its neighbours.

**What is left in the assembly chapter**: nothing the milestones need. The four
expanded-storage and page-movement instructions — `MVPG`, `PGIN`, `PGOUT`,
`LKPG` — are the only entries among the 162 a later stage might want, and `MVPG`
is the one worth remembering, since `DMKPGS` and `DMKPTR` copy pages. They are
recorded in `XAOPS.MACRO` rather than defined, because an unused macro is
maintenance surface for no gain.

## What the conversion involves

Measured against the maintained CE source — 201 CP `.ASSEMBLE` members —
with a statement parser that skips comments and takes the opcode from
column 1 or after the label. Full detail in `../../docs/`.

**What looked like the biggest item has a documented precedent.** CP runs
64 KB segments of sixteen 4 KB pages; ESA/390 has only 1 MB segments. Since
VM/370 shares whole page tables — `SYSHRSG=` names segments — its sharing
granularity is its segment size, so moving to 1 MB appears to cost a 16x
coarsening, and measured against `DMKSNT` it would force the entire first
megabyte common (`../../docs/04-SHARED-SEGMENTS.md`, recomputable with
`tools/snt-collisions.py`).

**CP-67 ran 1 MB segments and shared at 4 KB.** It gave each virtual machine
its own page table populated from a model, sharing the *frames* rather than
the table, and declared shared **pages** — `SWPTABLE FIRSTSP=/LASTSP=`. So
the coarsening is a property of VM/370's implementation rather than of
ESA/390, and the fix has IBM's own precedent on the same architecture family.
`../../docs/05-CP67-PRIOR-ART.md` has the quotations. It moves work into
`DMKATS` and the `NAMESYS` path rather than removing it.

**I/O is ten instruction sites, not 1,493 references.** Every S/370 I/O
instruction in `DMKIOS` is a single instruction with the same `0(R1)`
operand, and the CAW is built in two places. A shim that synthesises a CSW
at `X'40'` after each `TSCH` — which is precisely what Hercules does in the
other direction — leaves all 1,917 CAW/CSW references working unchanged.
The hard part is about a dozen `BC 4,...  BRANCH IF CSW STORED` branches:
`SIO` stores a CSW synchronously with cc=1, and `SSCH` only queues.

**`DMKVAT` is probably the least of the DAT work, not the most.** It is
already parameterised by DAT architecture — `GPR 9 = ARCHITECTURE CONTROL
INDEX` indexes a table whose entries include `PTEINCR`, `PINVBIT` and
`ZEROBIT` — and four of its eight variants already use fullword page table
entries, one of them with a 2,048-segment, 1 MB-segment geometry. See
`../../docs/02-CP-VERIFIED.md`; whether those rows are live or dead
future-proofing is an open question.

**CCWs do not change.** The ESA/390 Principles of Operation states the S/370
24-bit format "is carried into the 370-XA mode", selected by one ORB bit,
and MVS/XA itself never converted.

## AMODE 31 is a prerequisite, not a later step

`08-lra.rc` was written to close the largest untested dependency in the DAT
path: `TRANS` is invoked 174 times and every one goes through `LRA`, and
Appendix F of the Principles of Operation lists "Changes to LOAD REAL
ADDRESS" without saying what they are.

The worry was `LRA`'s **result** — if it truncated to 24 bits in 24-bit mode,
`TRANS` could never return an above-the-line real address. The result is fine:
`control.c` caps at 2 GB, not 16 MB, and the addressing mode does not enter
into it.

**The operand address is truncated instead, and that is worse:**

    24-bit mode:  LRA 2,0(0,6)   R6 = 01005000  ->  cc 0, R2 = 00005000
    31-bit mode:  LRA 2,0(0,6)   R6 = 01005000  ->  cc 0, R2 = 01100000

In 24-bit mode the effective address is masked to `005000` **before**
translation. `LRA` is asked about segment 0 page 5, which is validly mapped,
and answers correctly about the wrong address — condition code 0, a
plausible-looking real address, and the wrong page.

**So while CP runs AMODE 24, its 174 `TRANS` sites cannot ask about an
above-the-line virtual address at all.** The question is truncated before it
is put, silently. Converting the modules containing `TRANS` to AMODE 31 is
therefore a **prerequisite** for paging above the line, not an independent
choice that can be deferred — which is why it now appears in M2 below rather
than being left implicit.

The other four cases confirm the condition-code contract `TRANS` depends on:
cc=1 for an invalid segment-table entry, cc=2 for an invalid page-table entry,
cc=3 beyond the segment-table length.

**A note on test design, because this nearly slipped through.** A version of
case A that checked only cc=0 would have *passed* — cc=0 is exactly what a
truncated-but-valid translation returns. Comparing the returned real address
against the expected one is what caught it. The same trap applies to anything
else in this series that checks a condition code without checking the answer.

## Milestones

| | | Status |
|---|---|---|
| **M0** | Assembler macros for the instructions CE does not know | **done, verified on CE, and measured complete** — 24 members, severity 0, and a 351-mnemonic probe showing nothing needed is missing. `../../docs/14-M0-CLOSED.md` |
| **M1** | CP IPLs in ESA/390 mode and writes to the console — DAT off, no paging, no guests, no DASD beyond IPL | not started — **the critical path** |
| **M2** | DAT on with ESA/390 tables, **`TRANS`-bearing modules converted to AMODE 31**. No guests, no shared segments | not started, **unblocked** |
| **M3** | One S/370-mode guest logs on and runs CMS — includes frame-level shared segments in `DMKATS` | not started |
| **M4** | Two guests, isolated | not started |

**M2 was blocked and is not any more.** It waited on a compatibility decision
about shared segments at 1 MB granularity, which was the plan's only external
dependency. `../../docs/05-CP67-PRIOR-ART.md` removes it: sharing frames
rather than page tables keeps 4 KB granularity, so no saved-system layout
changes and nobody has to rule on `CMSOLD`. The critical path is now
M0 → M1 → M2 → M3, entirely self-directed.

**AMODE 31 conversion moved INTO M2**, per the `LRA` finding above: without
it, `TRANS` cannot see an above-the-line virtual address, so M2's tables would
be correct and unusable.

**Shared segments moved from M2 to M3, which is where they are actually
needed.** CP does not need shared segments to run with DAT on; CMS needs them
because it is IPL'd by name through `DMKSNT`. Splitting them out keeps M2 to
the table formats alone, and defers the `DMKATS` rework — the one piece of
work the CP-67 finding *added* — until there is a guest to test it with.

## Risks and issues live in a register, not here

Risks used to be a four-item ranking in this section. They are now a scored
register, separate from the milestones above, because the two answer different
questions and were quietly interfering with each other:

- **[`../../docs/12-RISKS.md`](../../docs/12-RISKS.md)** — 21 risks with
  probability, impact, weight (P × I) and a named mitigation each, plus a table
  of **which milestone retires which risk**. That mapping is what this section
  could not provide: it found two weight-6 risks owned by no milestone at all,
  and one — guest-visible storage-key semantics reaching `DMKPRV` — that had no
  owner anywhere.
- **[`../../docs/13-ISSUES.md`](../../docs/13-ISSUES.md)** — known defects,
  including the retracted claims. The top open item is a single macro: CP's
  `MSG` blocks ~20 modules under z390, three of them DAT modules.

The top risk is no longer the `SIO` condition-code contract, which
`06-initial-status.rc` retired. It is **R-01: seventy hard-coded shift amounts
across twelve modules**, which encode the page and segment geometry as bare
numeric literals that no symbol rename will ever touch, and whose failure mode
is a plausible translation to the wrong page.

`DMKATS` frame sharing is new work but not a new risk — it is bounded, and
IBM did it first.

### The `SIO` gap is prototypable, and test 6 should prove it

I previously wrote that Hercules ignores `ORB5_I`, the
initial-status-interruption bit, and that the `SIO` condition-code problem
therefore could not be tested before M1. **That was wrong.** Hercules's own
release notes put "I/O initial status interruption" in **version 1.39, 24
November 1999**, so every build since — 3.07 included — should have it.

Hyperion 4.x implements it fully, with Principles of Operation citations:

    /* Process Initial-Status-Interruption Request           */
    /* SA22-7201-05:  p. 16-11, Zero Condition Code          */
    if (dev->scsw.flag1 & SCSW1_I)
    {
        STORE_FW(dev->scsw.ccwaddr,ccwaddr);
        dev->scsw.flag1 |= SCSW1_Z;              /* zero condition code */
        dev->scsw.flag3 |= (SCSW3_SC_INTER | SCSW3_SC_PEND);
    }

`SCSW1_Z`, the zero-condition-code flag, is precisely the substitute for
`SIO`'s synchronous condition code — and `channel.c`'s `AIPSX()` builds the
whole deferred-condition-code table, "Figure 16-5, the Deferred-Condition-Code
Meaning for Status-Pending Subchannel". That is the mechanism the conversion
needs, implemented and cited.

**`06-initial-status.rc` is that test, and it passes.** It
sets `ORB5_I` in ORB flag5 (`X'A0'` — format-1 plus initial status), then
asserts three things about the first status to arrive: `SCSW1_Z` set,
intermediate status set, and the deferred condition code in SCSW byte 0
equal to zero. Then it confirms the write still completed `CE|DE`.

**Result: `006007` on both builds tested.** The console prints

    ISI OK -- SCSW1_Z SET, DEFERRED CC 0: SIO CONTRACT HAS AN XA EQUIVALENT

so the top risk is a known quantity before a line of CP has been touched, and
no emulator upgrade is needed for it. 3.13's source shows why — `channel.c`
sets `SCSW1_Z`, sets `SCSW3_SC_INTER | SCSW3_SC_PEND`, **and** calls
`QUEUE_IO_INTERRUPT`, so the interruption is genuinely delivered and not
merely recorded. The `@IWZ` change markers around it are old, consistent with
the 1999 release note.

### And the interrupt path works too — with a third silent gate behind it

`07-io-interrupt.rc` closes the remaining gap: tests 5 and 6 both polled
`TSCH`, and CP does not poll. It starts a write, loads an **enabled wait**
PSW, and expects to wake up in a handler at `X'78'`, which then identifies
the subchannel from lowcore `X'B8'` — exactly what `DMKIOT` does to find its
`IOBLOK`. Passes `006008`.

**Getting there needs CR6, and this is the nastiest of the three gates.**

    /* Isolate the interruption subclass */
    i = ((dev->pmcw.flag4 & PMCW4_ISC) >> 3);
    /* Test interruption subclass mask bit in CR6 */
    if ((regs->CR_L(6) & (0x80000000 >> i)) == 0)
        return 0;               /* interrupt NOT enabled */

CR6 is the I/O-interruption subclass mask. A subchannel's ISC defaults to 0,
so CR6 bit 0 — `X'80000000'` — must be on or the interruption is **never**
presented. Not deferred: never.

**Measured, not assumed.** Running the identical image with CR6 forced to zero
(`r 20D8=00000000`):

- **the console line still prints.** The CCW ran, the device did its work,
  the I/O genuinely succeeded.
- no PSW, no wait-state message, no code. The CPU sits in its enabled wait
  until the emulator is killed.

So the trap does not merely fail silently, **it looks like success** — the
expected output appears on the console while the operating system is hung. A
converted CP that gets `DMKIOS` perfectly right and forgets CR6 will IPL,
write its initialisation message, and stop, with nothing in any log to say
why. That is worth knowing before M1 rather than during it.

Still unproven: an interruption arriving while another is pending, the ISC
mechanism with more than one class in play, and `DMKIOT`'s queue walk. Those
need more than one device, which this deliberately minimal config lacks.

It polls `TSCH` rather than taking an I/O interruption, so it proves the
status mechanism and not interruption delivery. Status pending is a
subchannel condition that `TSCH` clears whether or not interrupts are
enabled, so the SCSW contents are the same either way — but a test with a
real I/O new PSW and handler proves more, and belongs before CP relies on
the interrupt path.

## Running the lab on Linux

The tests were developed against a Windows 3.x build and re-run against
Hercules 3.13 built from source on Linux. Two things bit, both worth knowing
before blaming a test:

**Codepage names differ between versions.** `herc.conf` carries
`CODEPAGE 819-1047`, which 3.13 rejects with
`HHCCF051E Codepage conversion table 819-1047 is not defined` — its table
spells them with a slash, `819/1047`. The error is not fatal and the run
continues on the default, so it is easy to miss.

**The device modules must be installed, not just built.** Running `hercules`
straight out of the build tree gives
`HHCCF042E Device type 3215-C not recognized`, because the loadable module
directory is `/usr/local/lib/hercules` and `hdt1052c` — which registers both
`1052-C` and `3215-C` — is not there yet. With no device attached there is no
subchannel 0000, so `SSCH` correctly returns condition code 3 and test 6
reports `000C03`, which looks exactly like a real SSCH failure. `make install`
first.

**And 3.13 will not link against modern gcc without one patch.** `softfloat`
declares `float_exception_flags` and `float_rounding_mode` `__thread`, and
libtool's generated symbol table references them as non-TLS, so `ld` fails
with `TLS definition … mismatches non-TLS reference` — reported confusingly as
`libsoftfloat.a: error adding symbols: bad value`. Dropping `__thread` from
both declarations links cleanly. Safe for this lab, which uses no floating
point and one CPU; **not** a change to carry into a real Hercules build, where
those flags are per-CPU state. Also configure with the default shared modules:
`--disable-shared` statically links every device module and they all define
`hdl_depc`, `hdl_init` and `hdl_ddev`.

## What this stage does *not* do

A 31-bit CP that still presents S/370-mode virtual machines gives no guest
more than 16 MB — which is what VM/XA did, and it means **CMS needs no
changes at all for M1–M4**. Converting CMS to run 31-bit virtual machines is
a separate, downstream stage: smaller than CP on every axis except linkage,
but coupled to CP through 126 `DIAGNOSE` references whose parameter lists
carry addresses.

So this work does not shorten the path to an application with an 18 MB heap
until that second stage lands. Worth being explicit about.
