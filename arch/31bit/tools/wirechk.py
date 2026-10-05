#!/usr/bin/env python3
"""Is every COPY/MACRO member we update actually wired into DMKLCL EXEC?

`I-149`: nine architecture constants were moved out of `CORE COPY` into
`EQU COPY`.  `EQU.XA0037DK` was generated, listed in `EQU.AUXLCL`, staged onto
the A-disk, and confirmed read -- and never applied, because `DMKLCL EXEC` is
the list of members whose AUX decks `VMFASM` applies and it did not name `EQU`.
All nine symbols came back `IFO188 UNDEFINED SYMBOL` in five modules, two of
which had assembled clean the build before.

Every other check here asks whether an artifact is CORRECT.  This one asks
whether it is CONNECTED, which is the question none of them was asking:

    mkdeck.card()   a card is well formed
    auxcheck()      a deck is listed in its member's AUXLCL
    symchk.py       a symbol does not collide
    replchk.py      a replacement preserves what it covers
    iochk.py        the staged card matches the deck on disk
    wirechk.py      a member we update is named in DMKLCL EXEC   <-- this

`auxcheck` came closest and was satisfied: `EQU.AUXLCL` listed `XA0037DK`
faithfully.  The AUXLCL was right and nobody was reading it.

A module needs no entry -- `VMFASM DMKxxx DMKLCL` names the module itself, and
its AUXLCL is found by that name.  Only MEMBERS, which are reached by `COPY`
from inside a module, depend on the list.

    python3 wirechk.py
"""
import glob
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
UPDATES = os.path.join(HERE, '..', 'updates')
SRC = '/home/claude/vmce/source/cp'
CMSSRC = '/home/claude/vmce/source/cms'
LIST = os.path.join(UPDATES, 'DMKLCL.EXEC')


def main():
    if not os.path.exists(LIST):
        print('### no DMKLCL.EXEC -- run build.py first')
        return 2
    named = set()
    for line in open(LIST, errors='replace'):
        f = line.split()
        # ' &1 &2 NAME     TYPE'
        if len(f) >= 4 and f[0] == '&1' and f[1] == '&2':
            named.add(f[2].upper())

    members, bad = [], []
    for path in sorted(glob.glob(os.path.join(UPDATES, '*.XA*DK'))):
        base = os.path.basename(path)
        name = base.split('.')[0]
        if os.path.exists(os.path.join(SRC, '%s.ASSEMBLE' % name)) or \
                os.path.exists(os.path.join(CMSSRC, '%s.ASSEMBLE' % name)):
            continue                      # a module, found by its own name
        members.append((name, base))
        if name.upper() not in named:
            bad.append((name, base))

    print('%d member deck(s); DMKLCL.EXEC names %d member(s)'
          % (len(members), len(named)))
    for name, base in members:
        print('  %-9s %-11s %s' % (name, base,
                                   'wired' if name.upper() in named
                                   else '### NOT IN DMKLCL.EXEC'))
    if not bad:
        print()
        print('every member we update is wired into the control file')
        return 0
    print()
    for name, base in bad:
        print('### %s is updated by %s and is NOT named in DMKLCL.EXEC, so'
              % (name, base))
        print('### VMFASM will never apply that deck -- the symbols it defines')
        print('### come back IFO188 and the ones it REMOVES stay removed.')
    return 1


if __name__ == '__main__':
    sys.exit(main())
