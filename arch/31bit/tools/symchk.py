#!/usr/bin/env python3
"""Check that every symbol a deck DEFINES is not already defined in the tree.

`CORE.XA0033DK` added `PAGFREE` to the `PAGTABLE` DSECT.  `DMKPTR` has had a
label of that name since 1979 --

    PAGFREE  EQU   *  ENTRY FROM WITHIN DMKPTRAN

-- a subroutine that gets a free page, in the paging module, where "PAG" plus
"FREE" is the obvious name for both things.  The assembler caught it:
`IFO196 PAGFREE HAS BEEN PREVIOUSLY DEFINED`, **once**, in a list of 147
diagnostics, in the one module that collides.  It cost a 35-minute build, and the
next candidate name tried -- `PAGFRET` -- would have collided in `DMKVAT`.

A collision is cheap to find before the build and expensive after, and there is
nothing to judge: a symbol is either already defined or it is not.  So:

    python3 symchk.py [deck-dir] [source-dir]

Exit 1 if any deck defines a name the tree already uses.  Clean output is
`N decks define M symbols, no collisions`.

What counts as a definition: a card whose name field is non-blank and whose
operation is a definition rather than a reference.  A `DS`, `DC`, `EQU` or `CSECT`
in the name field defines; a branch target label defines too, which is why
`BLDRPTE` -- the loop label in `DMKBLD`'s page-table initialiser -- is checked
along with the DSECT fields.
"""
import glob
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
DECKS = os.path.join(HERE, '..', 'updates')
SRC = '/home/claude/vmce/source/cp'

# `NAME     OP    operands` on a source card (columns 1-61 of the deck card).
DEFN = re.compile(r'^([A-Z@#$][A-Z@#$0-9]{0,7})\s+(\S+)')
# Operations that do NOT define the name field as a new symbol in a way that can
# collide -- a continuation or a macro call can legitimately repeat a name.
NOTDEF = {'AIF', 'AGO', 'ANOP', 'MACRO', 'MEND', 'MEXIT', 'END', 'TITLE'}


def defined_by(path):
    """Symbols a deck's source cards define."""
    out = []
    for line in open(path, errors='replace'):
        if line.startswith('./'):
            continue
        text = line[:61].rstrip()
        if not text or text.startswith('*'):
            continue
        m = DEFN.match(text)
        if m and m.group(2) not in NOTDEF:
            out.append((m.group(1), text))
    return out


COPY = re.compile(r'^\s+COPY\s+(\S+)')


def file_symbols(src):
    """{file stem: {symbol}} for every member and module in the tree."""
    syms = {}
    pats = (glob.glob(os.path.join(src, 'DMK*.ASSEMBLE'))
            + glob.glob(os.path.join(src, '*.COPY'))
            + glob.glob(os.path.join(src, '*.MACRO')))
    for path in sorted(pats):
        stem = os.path.basename(path).split('.')[0]
        s = syms.setdefault(stem, set())
        for line in open(path, errors='replace'):
            text = line[:72].rstrip()
            if not text or text.startswith('*'):
                continue
            m = DEFN.match(text)
            if m and m.group(2) not in NOTDEF:
                s.add(m.group(1))
    return syms


def copiers(src):
    """{member: {modules that COPY it}} -- the scope a member's symbols reach."""
    out = {}
    for path in sorted(glob.glob(os.path.join(src, 'DMK*.ASSEMBLE'))):
        mod = os.path.basename(path).split('.')[0]
        for line in open(path, errors='replace'):
            m = COPY.match(line[:72])
            if m:
                out.setdefault(m.group(1), set()).add(mod)
    return out


def main():
    args = [a for a in sys.argv[1:] if not a.startswith('-')]
    deckdir = args[0] if args else DECKS
    src = args[1] if len(args) > 1 else SRC

    syms = file_symbols(src)
    cp = copiers(src)
    decks = sorted(glob.glob(os.path.join(deckdir, '*.XA*DK')))
    if not decks:
        print('### no decks in %s -- nothing was checked, which is not the'
              % deckdir)
        print('### same as nothing wrong.')
        return 2

    # SCOPE is the whole point, and the first version of this tool got it wrong:
    # it compared names tree-wide and reported 17 collisions where there is 1.
    # Assembler symbols are per-ASSEMBLY.  A deck on a MODULE reaches only that
    # module and the members it copies; a deck on a MEMBER reaches every module
    # that copies it, which is why PAGFREE in CORE.COPY collided with DMKPTR's
    # label and why DMKCKP's SNSIO and DMKCPI's SNSIO coexist happily.
    nsym, bad = 0, []
    for path in decks:
        base = os.path.basename(path)
        target = base.split('.')[0]
        if target.startswith('DMK') and target in syms and (
                os.path.exists(os.path.join(src, target + '.ASSEMBLE'))):
            scope = {target} | {m for m in syms
                                if m in [c for c, mods in cp.items()
                                         if target in mods]}
            kind = 'module'
        else:
            scope = cp.get(target, set())
            kind = 'member copied by %d module(s)' % len(scope)
        for sym, text in defined_by(path):
            nsym += 1
            clash = sorted(f for f in scope
                           if f != target and sym in syms.get(f, ()))
            if clash:
                bad.append((base, kind, sym, clash, text))

    print('%d decks define %d symbols, %s'
          % (len(decks), nsym,
             'no collisions' if not bad else '%d COLLISION(S)' % len(bad)))
    for base, kind, sym, clash, text in bad:
        print()
        print('  %s (%s) defines %s' % (base, kind, sym))
        print('    %s' % text)
        print('    already defined in %s%s'
              % (', '.join(clash[:6]), ' ...' if len(clash) > 6 else ''))
    if bad:
        print()
        print('The assembler reports this as IFO196 ... HAS BEEN PREVIOUSLY')
        print('DEFINED, once, in the one module that collides -- which is easy')
        print('to lose in a list of a hundred diagnostics and costs a build.')
    else:
        print()
        print('Scope matters more than the count here: a deck on a MODULE reaches')
        print('that module and what it copies, while a deck on a MEMBER reaches')
        print('every module that copies it.  Comparing names tree-wide instead')
        print('reported 17 collisions where there is 1 -- the blocksize.py error.')
    return 1 if bad else 0


if __name__ == '__main__':
    sys.exit(main())
