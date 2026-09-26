# Milestone 0 — ESA/390 instructions for CE's assembler

VM/370 CE's assembler is from the 1970s. The channel subsystem arrived
with 370-XA in 1983 and `BSM` with the 31-bit addressing facility the same
year, so none of those mnemonics are known to it. Every module of a 31-bit
CP would fail to assemble on the first `SSCH`.

Rather than change the toolchain — which would mean either getting a newer
assembler onto CMS or cross-assembling on the PC, both of which disturb
Adrian's reproducible build — each instruction is a macro that emits its
own encoding.

## Files

    XAOPS.MACRO       the macro definitions, one per instruction
    XATEST.ASSEMBLE   assembles one of each so the listing can be checked

## Install

    MACLIB GEN XALIB XAOPS

and in any module that needs them:

    GLOBAL MACLIB XALIB DMSSP CMSLIB

## Why it works

An S-type address constant, `S(expr)`, produces exactly the 4-bit base
register and 12-bit displacement that an S-format instruction wants,
resolved through the active `USING`. So

    DC    X'B233',S(ORB)

assembles to the same four bytes the real `SSCH ORB` would, base register
selection included. The macros behave like instructions, not like
hand-poked constants, which is what makes this viable across 201 modules
rather than a handful.

Each macro starts with `DS 0H` because an S-type constant forces halfword
alignment — without it a misaligned `DC` would get a pad byte inserted
between the opcode and the operand. In an instruction stream that cannot
normally happen, but it costs nothing.

## Verify before trusting

**Five encodings are proven by execution.** `MSCH`, `SSCH`, `TSCH`, `STSCH`
and `BSM` were run under Hercules 3.07 in ESA/390 mode from hand-assembled
bytes: `MSCH` enabled a subchannel, `SSCH` started a format-1 channel
program, `TSCH` returned clean status, the device wrote its line, and `BSM`
switched into 31-bit mode and back.

    MSCH   B232        STSCH  B234        BSM    0B
    SSCH   B233        TSCH   B235

**The rest were read from Hercules source and have not been executed.**

    CSCH   B230        TPI    B236        RSCH   B238
    HSCH   B231        SAL    B237        STCRW  B239
    BASSM  0C

**One opcode is disputed.** `RSCH` reads as `B238` in the Hercules dispatch
table and as `B23B` in a reading of the 370-XA Reference Summary
GX20-0157-2. `B238` is used here because it came from a direct quote of the
table that would actually execute, but check it against the Principles of
Operation before relying on `RSCH`.

To check any of them, assemble `XATEST` with `(PRINT` and compare the
object column against the table above. Only the first two bytes are fixed —
the base and displacement halfword depends on where the operands land — but
those two bytes are what decide which instruction the machine executes.

## Not included, and why

`STOSM` and `STNSM` need no macro. They exist in S/370 EC mode and CE's
assembler already knows them; CP itself uses each five times. Same for
`LCTL` and `STCTL`, which CP uses 172 and 28 times. If any of those four
fails to assemble, the problem is the assembler level rather than this
MACLIB — which is why `XATEST` exercises them too.

`SAM24`, `SAM31` and `SAM64` are z/Architecture, not ESA/390. In ESA/390
the addressing mode changes with `BSM` or `BASSM`.

`IPTE`, `IVSK` and `TPROT` are ESA/390 DAT instructions the assembler will
not know either, but nothing needs them yet. Add them when the DAT work
reaches the point of invalidating individual page table entries.

## The two things worth knowing about `BSM`

`BSM 0,RX` branches to `RX` and takes the addressing mode from its bit 0 —
one means 31-bit, zero means 24-bit.

**`BSM RY,0` does something less obvious and more useful.** With the second
operand zero no branch is taken at all, and the instruction only reports
the *current* mode in bit 0 of `RY`, which is the sign bit. So

    SR    RY,RY
    BSM   RY,0
    LTR   RY,RY

tests the addressing mode without needing any address above the 16 MB
line. That matters more than it sounds: every test that distinguishes the
modes *by truncation* necessarily uses an above-the-line address, which
would conflate "did the mode switch work" with "does above-the-line
translation work". This separates them.

`BASSM` is the instruction a mixed-mode calling convention is built on — it
saves the return address with bit 0 set to the caller's mode, so the callee
returns with `BSM 0,R1` and restores it. If CP ever presents a mixed 24/31
interface to its own routines, this is the mechanism.
