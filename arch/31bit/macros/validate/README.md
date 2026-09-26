# Validating XAOPS by differential assembly

`XAOPS.MACRO` emits twelve ESA/390 instructions that CE's assembler does not
know. Five were proven by execution under Hercules. The question this answers
is different and was the one actually in doubt: **does an S-type address
constant resolve through the active `USING` exactly as an S-format
instruction's operand does?**

The obvious check — assemble and read the listing against a table of opcodes —
does not answer that. This does. It assembles each instruction **twice in one
program**, once as an assembler's own built-in instruction and once through the
XAOPS macro, then diffs the generated object code.

    ./validate.sh /path/to/z390

## Result

    instruction z390 built-in    XAOPS macro      verdict
    ----------------------------------------------------------
    SSCH       B233F0DA         B233F0DA         MATCH
    MSCH       B232F066         B232F066         MATCH
    TSCH       B235F09A         B235F09A         MATCH
    STSCH      B234F066         B234F066         MATCH
    CSCH       B2300000         B2300000         MATCH
    HSCH       B2310000         B2310000         MATCH
    RSCH       B2380000         B2380000         MATCH
    SAL        B2370000         B2370000         MATCH
    TPI        B236F062         B236F062         MATCH
    STCRW      B239F062         B239F062         MATCH
    BSM        0B10             0B10             MATCH
    BASSM      0CEF             0CEF             MATCH
    ----------------------------------------------------------
    12 of 12 match exactly

Identical to the byte, **base register and displacement included** — `F` is
R15 and `0DA` is the displacement the macro's `S(ORB)` produced, the same one
the real instruction's operand produced. So the idiom works, and Milestone 0 is
validated rather than merely assembled.

## Why z390 and not CE's assembler

[z390](https://github.com/z390development/z390) is an independent assembler
that already knows the channel-subsystem instructions — which is also why it
could settle the `RSCH` opcode dispute (`B238`; `B23B` is `RCHP`, a different
instruction).

CE's own `ASSEMBLE` **cannot** play this role, because it predates 1983 and has
no built-in to compare against. There, the macros are the only way to get the
instructions at all. So this validates the macro mechanism on an assembler that
can check it, before relying on it on one that cannot.

## Two mechanical differences worth knowing

**z390 wants one macro per file**, named for the macro; a CMS MACLIB holds many
per member. `validate.sh` splits `XAOPS.MACRO` accordingly. On CMS it is one
`MACLIB GEN XALIB XAOPS`.

**Each macro is renamed with an `X` prefix** for the test, so z390's built-in
cannot shadow it. Without that, `SSCH ORB` assembles as the real instruction
and the macro is never invoked — which is exactly what happened on the first
attempt here, producing correct bytes that proved nothing about the macros.
