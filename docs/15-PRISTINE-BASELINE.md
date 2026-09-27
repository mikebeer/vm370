# A pristine IBM baseline, and what diffing CE against it proved

27 September 2026. [`g4ugm/vm370.source`](https://github.com/g4ugm/vm370.source)
— Dave Wade's VM/370 release source — turned out not to contain either of the
two things it was checked for, and to settle something more important that
nobody had checked at all.

## What it is not

**It does not close `R-14`.** 187 CP and 174 CMS `.ASSEMBLE` members and
**zero `.MACRO` or `.COPY` members**, so the OSMACRO/DOSMACRO libraries that
~24 modules need are not there. That risk stands unchanged.

**It does not supply the `DIRECT` command.** It has `DMKDIR.ASSEMBLE`, the
standalone directory program, which CE already has. The CMS `DIRECT` command
that compiles `USER DIRECT` onto the directory cylinder is absent from both
trees, so `06-LEDGER.md`'s note that the file's record format is undocumented in
the tree stands too — though `11-RUNNING-CE.md` made that moot by reading the
file from a running system.

## What it does settle, which matters more

**Every one of its 187 CP modules is present in CE, and CE's copies are
byte-identical apart from a missing trailing newline and a control-byte
encoding.**

    MODULE      G4UGM      CE   DIFF LINES
    DMKIOS       2493    2494        2
    DMKPSA        704     705        2
    DMKIOT       1266    1267        2
    DMKCNS       2415    2416        4
    DMKDSP       3011    3012        4
    DMKCPI       4039    4040        4
    DMKVAT       1334    1335        2
    DMKPTR       2588    2589        2
    DMKATS        956     957        2
    DMKPGS       1321    1322        4
    DMKBLD       1119    1120        2

Every "2" is the same thing — the last line, `END DMKxxx`, with
`\ No newline at end of file` on the pristine side. Every "4" is that plus one
line carrying a control byte.

**This is a load-bearing verification that had never been done.** Everything in
`03-CP-INVENTORY.md`, `08-MACRO-UNDERCOUNT.md` and `09-DAT-WORK-SHAPE.md` was
measured against Adrian's CE tree, and every conclusion assumed those
measurements describe *IBM's* VM/370 rather than a community fork of it. The
assumption was never stated, let alone checked. It is now checked: **the CP
source this project has been analysing is IBM's Release 6 source.** The 217
constant references, the 70 shift literals, the flag collisions, the lowcore
offsets — all of it is IBM code.

### The 14 modules CE adds

    DMKRIO  DMKSNT  DMKSYS      site configuration -- generated, not IBM source
    DMKGRU  DMKGRV  DMKGRX      additions
    DMKPEC  DMKPED  DMKPEQ      additions
    HDKCQA  HDKCQU  HDKD58      community device support
    HDKD7C  HDKD8C

`DMKRIO`, `DMKSNT` and `DMKSYS` being CE-only is exactly right — they are the
generated configuration modules, and `DMKSNT` is the one
`tools/snt-collisions.py` reads. The `HDK` prefix marks community-added code
rather than IBM's `DMK`, which is a useful convention to know when deciding
whether a module is safe to modify.

## And it decoded `I-02`

`10-BUILD-ENVIRONMENT.md` recorded that `DMKCPI` fails under z390 with
`MZ390E error 138, invalid ascii source line 365`, attributed to "the U+E000
private-use encoding the CE README describes", with the fix given as "the
documented reverse encoding". The diff shows exactly what that encoding is.

The one differing line in `DMKPGS`:

    g4ugm:   PUNCH  '  <0x02>  SPB'
    CE:      PUNCH  '  U+E002  SPB'

So **CE hoists control bytes into the private-use area: `U+E0xx` represents byte
`0xxx`.** Six distinct codepoints across 26 CP members:

| Codepoint | Byte | Occurrences |
|---|---|---|
| `U+E002` | `X'02'` | 15 |
| `U+E017` | `X'17'` | 10 |
| `U+E005` | `X'05'` | 10 |
| `U+E027` | `X'27'` | 7 |
| `U+E015` | `X'15'` | 5 |
| `U+E016` | `X'16'` | 2 |

**CE is the correct tree here, not the pristine one.** The pristine source
carries raw control characters in a text file, which is precisely what editors,
diff tools, terminals and card punches mangle. CE's encoding is lossless and
survives text handling. So the fix for `I-02` is the reverse mapping —
`U+E0xx → 0xxx` — and *not* substituting g4ugm's copy of the module, which was
the tempting shortcut and would have been a silent step backwards.

It also flags something operational for M1 and M2: when one of those 26 members
is read onto a CE disk through the card reader, the substitution has to happen
on the way in, and the deck has to carry the raw control byte. Only one of the
26 — `DMKCPI` — is in the M1 nine.

## What to do with it

Not vendor it. It is 37 MB of source this project does not build, and CE is the
tree being converted. Its value is as a **differential baseline**: a way to ask
"did IBM write this line, or did CE?" of any module, in one command.

    git clone --depth 1 https://github.com/g4ugm/vm370.source.git
    diff <(sed 's/[[:space:]]*$//' g4ugm/cp/DMKIOS.ASSEMBLE) \
         <(sed 's/[[:space:]]*$//' vmce/source/cp/DMKIOS.ASSEMBLE)

Recorded in `../heritage/README.md` as a reference rather than a snapshot.
