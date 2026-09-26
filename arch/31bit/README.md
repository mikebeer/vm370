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

Six programs in `tests/hardware/`, each answering one question, each with
its own pass code so that a stale program left in storage cannot masquerade
as a pass.

| Test | Pass | Question |
|---|---|---|
| `01-dat-tables` | `00600D` | Are hand-built DAT tables accepted, and does DAT run? |
| `02-page-table-walked` | `00600D` | Is the page table actually being walked? |
| `03-amode31` | `006003` | Does the AMODE 31 switch work, and does DAT survive it? |
| `04a-virtual-above-line` | `006004` | Does an above-the-line **virtual** address translate? |
| `04b-real-above-line` | `006005` | …to an above-the-line **real** frame? |
| `05-channel-subsystem` | `006006` | Does MSCH/SSCH/TSCH drive a real device? |

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

`herc.conf` deliberately attaches **one device and no DASD**. A bare-metal
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

`macros/` holds `XAOPS.MACRO`: twelve ESA/390 instructions as macros, because
CE's assembler predates 1983 and knows neither the channel subsystem nor
`BSM`.

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
execution in the tests above. The other seven were read from Hercules source
and are unverified; `macros/XATEST.ASSEMBLE` assembles one of each so the
listing can be checked. One opcode is disputed: `RSCH` reads `B238` in the
Hercules dispatch table and `B23B` in a reading of the 370-XA Reference
Summary GX20-0157-2.

## What the conversion involves

Measured against the maintained CE source — 201 CP `.ASSEMBLE` members —
with a statement parser that skips comments and takes the opcode from
column 1 or after the label. Full detail in `../../docs/`.

**The biggest item is a compatibility decision, not code volume.** CP runs
64 KB segments of sixteen 4 KB pages; ESA/390 has only 1 MB segments. The
consequence is shared segments: `DMKATS` and the named-saved-system
machinery are built on 64 KB granularity, so the minimum shareable unit
becomes 1 MB and every existing saved-system definition changes by 16×. No
parameter or table row solves that.

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

## Milestones

| | | Status |
|---|---|---|
| **M0** | Assembler macros for the instructions CE does not know | done, awaiting listing validation |
| **M1** | CP IPLs in ESA/390 mode and writes to the console — DAT off, no paging, no guests | not started |
| **M2** | DAT on with ESA/390 tables, still no guests | blocked on the segment-size decision |
| **M3** | One S/370-mode guest logs on and runs CMS | not started |
| **M4** | Two guests, isolated | not started |

## What this stage does *not* do

A 31-bit CP that still presents S/370-mode virtual machines gives no guest
more than 16 MB — which is what VM/XA did, and it means **CMS needs no
changes at all for M1–M4**. Converting CMS to run 31-bit virtual machines is
a separate, downstream stage: smaller than CP on every axis except linkage,
but coupled to CP through 126 `DIAGNOSE` references whose parameter lists
carry addresses.

So this work does not shorten the path to an application with an 18 MB heap
until that second stage lands. Worth being explicit about.
