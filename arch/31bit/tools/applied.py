#!/usr/bin/env python3
"""applied.py -- which source cards the build actually assembles.

Every tool here that reads `SRC/DMKxxx.ASSEMBLE` reads the 1979 base file.  That
is not the file the assembler sees.  VMFASM applies an AUX chain of APAR decks
first -- about forty for `DMKIOS` -- and those decks delete and replace cards
wholesale.  A tool that scans the base file therefore reports sites that are not
in the program.

I-176 is what that costs.  I spent a run of steps on `DMKIOSIN`, the I/O
interruption supervisor at `DMKIOS.ASSEMBLE:436`, with eight live `INTTIO`
references and no deck of ours covering sequence 00400000-00699999.  All true of
the file.  But `DMKIOS.R09587DK` says

    ./ * DMKIOSIN BEING MOVED INTO DMKIOT
    ./ D 418000 890000

-- 473 cards deleted before our decks ever apply -- and `DMKIOS.AUXR60` says the
same thing in one line I had not read:

    R09587DK 602 SPLIT MODULE DMKIOS INTO DMKIOS AND DMKIOT

The real handler is `DMKIOTIN`, in a module we had already converted.

So this answers one question: for a module, which sequence ranges does the
applied chain DELETE?  A site inside one of those is not a finding.

    python3 applied.py DMKIOS [DMKIOT ...]        the deleted ranges
    python3 applied.py --dead DMKIOS INTTIO       which references are dead

and as a library, which is the point:

    import applied
    gone = applied.deleted('DMKIOS')
    if applied.covered(gone, seq): continue      # not in the program

There is a SECOND axis, and it caught the same investigation a second time.  The
one `INTTIO` reference in `DMKIOS` the applied chain leaves alone, at
`01554000`, is still not assembled: it sits under `AIF (NOT &AP).APCHK6`, and
`&AP` is 0.  So a card can be absent from the program by deletion OR by
conditional assembly, and both have to be checked before a site is a finding.
The globals are set in `OPTIONS.COPY` and `LOCAL.COPY` and read here rather than
assumed -- `&AP` is 0 only because `HRC035DK`'s `&AP SETB 1` sits behind
`AIF (&MP EQ 0).O1` with `&MP` 0, which is not guessable from the name.

`--dead` reports both axes.  The AIF test is deliberately shallow: it matches
`AIF (NOT &X).LAB` and `AIF (&X EQ n).LAB` against the `.LAB ANOP` they jump to,
which is the form CP uses, and says `conditional` without evaluating anything it
does not recognise.  A site it cannot classify is reported live, which is the
safe direction -- it over-reports work rather than hiding it.

Three honest limits.  The AUX chain is read in file order and a range is reported
deleted if ANY applied deck deletes it; a later deck re-inserting cards into a
deleted range would not be noticed.  An `*` in column 1 of an AUX line marks a
deck as NOT applied -- `DMKIOS.AUXR60` has two, `*R14805DK` and `*R13197DK` --
so those are skipped, which is the difference between reading the control file
and globbing the directory.  And macro expansion is not modelled at all: a site
inside a macro body is invisible here.
"""
import os
import re
import sys

SRC = '/home/claude/vmce/maintenance/files/394'
# 394 is a maintenance level and does not hold every module; `source/cp` is the
# full set.  Callers hand us whatever module names their own source directory
# has, so look in both rather than assuming one.  A module in neither is
# reported as having nothing deleted and nothing skipped, which is the safe
# direction: it over-reports work rather than hiding it.
SRCDIRS = (SRC, '/home/claude/vmce/source/cp')


def src_path(module):
    for d in SRCDIRS:
        p = os.path.join(d, '%s.ASSEMBLE' % module)
        if os.path.exists(p):
            return p
    return None
# Where update decks live.  394 holds the base source; the APAR decks are split
# across the maintenance levels, and ours sit in the repository.
DECKDIRS = ('/home/claude/vmce/maintenance/files/294',
            '/home/claude/vmce/maintenance/files/094',
            '/home/claude/vm370/arch/31bit/updates')
AUXDIRS = DECKDIRS

CTL = re.compile(r'^\./\s+([RIDS*])\s*(\d+)?\s*(\d+)?', re.I)

OPTS = ('/home/claude/vmce/maintenance/files/094/OPTIONS.COPY',
        '/home/claude/vmce/maintenance/files/394/LOCAL.COPY')
# `AIF (NOT &X).LAB` and `AIF (&X EQ 0).LAB` -- the two forms CP uses to skip a
# block.  Anything else is left unclassified on purpose.
AIF_NOT = re.compile(r'^\s+AIF\s*\(\s*NOT\s+(&[A-Z0-9]+(?:\(\d+\))?)\s*\)\s*\.(\S+)')
AIF_EQ = re.compile(r'^\s+AIF\s*\(\s*(&[A-Z0-9]+(?:\(\d+\))?)\s+EQ\s+(\d+)\s*\)'
                    r'\s*\.(\S+)')
ANOP = re.compile(r'^\.(\S+)\s+ANOP')
SETB = re.compile(r'^(&[A-Z0-9]+(?:\(\d+\))?)\s+SET[BA]\s+(\d+)')


def globals_():
    """{'&AP': 0, ...} -- the assembly-option globals, read not assumed.

    An option set inside a skipped AIF block does not count, which is exactly
    how `&AP` ends up 0 despite `&AP SETB 1` appearing in the file.
    """
    out, skip_to = {}, None
    for path in OPTS:
        if not os.path.exists(path):
            continue
        for line in open(path, 'r', errors='replace'):
            code = line[:71]
            a = ANOP.match(code)
            if a:
                if skip_to == a.group(1):
                    skip_to = None
                continue
            if skip_to:
                continue
            m = AIF_EQ.match(code)
            if m and out.get(m.group(1)) == int(m.group(2)):
                skip_to = m.group(3)
                continue
            m = AIF_NOT.match(code)
            if m and not out.get(m.group(1)):
                skip_to = m.group(2)
                continue
            s = SETB.match(code)
            if s:
                out[s.group(1)] = int(s.group(2))
    return out


def conditional(module):
    """{seq: '&X'} -- cards skipped because a global makes their AIF taken."""
    g = globals_()
    path = src_path(module)
    if not path:
        return {}
    out, skip_to, why = {}, None, None
    for line in open(path, 'r', errors='replace'):
        code, s = line[:71], line[72:80].strip()
        a = ANOP.match(code)
        if a:
            if skip_to == a.group(1):
                skip_to, why = None, None
            continue
        if skip_to:
            if s.isdigit():
                out[int(s)] = why
            continue
        m = AIF_EQ.match(code)
        if m and g.get(m.group(1)) == int(m.group(2)):
            skip_to, why = m.group(3), m.group(1)
            continue
        m = AIF_NOT.match(code)
        if m and not g.get(m.group(1)):
            skip_to, why = m.group(2), m.group(1)
    return out


def chain(module):
    """The deck names to apply, in the order VMFASM applies them.

    An AUX file lists its updates NEWEST FIRST and they are applied OLDEST
    FIRST, so each file's entries are reversed.  The files themselves go in
    maintenance order -- R60, then HRC, then our own LCL last.  Both facts are
    checked against a build log rather than assumed: `h1.log`'s thirty
    `APPLYING 'DMKIOS ...'` lines are exactly what this returns, in order.

    A `*` in column 1 means the deck is NOT applied, which is the difference
    between reading the control file and globbing the directory.
    """
    out = []
    for d in AUXDIRS:
        if not os.path.isdir(d):
            continue
        for f in sorted(os.listdir(d)):
            if not re.match(r'^%s\.AUX' % module, f):
                continue
            here = []
            for line in open(os.path.join(d, f), 'r', errors='replace'):
                if not line.strip() or line.startswith('*'):
                    continue
                name = line.split()[0]
                if re.match(r'^[A-Z0-9]+DK$', name):
                    here.append(name)
            out.extend(reversed(here))
    return out


def effective(module):
    """[(seq, text)] -- the cards the assembler actually sees.

    The base file with the whole AUX chain applied: deletions removed,
    replacements and insertions carrying the decks' own cards at the sequence
    numbers the control cards assign.  This is the only honest input for a
    scanner, because a `./ R` both REMOVES a base card and ADDS a new one, and
    the added one can carry the very instruction being counted -- 36 S/370-only
    instructions across the tree arrive that way, 22 of them in DMKFMT.

    Sequence numbers are the ordering key, exactly as UPDATE treats them, so
    the merge is a dict keyed by sequence and sorted at the end.
    """
    path = src_path(module)
    if not path:
        return []
    cards = {}
    for line in open(path, 'r', errors='replace'):
        s = line[72:80].strip()
        if s.isdigit():
            cards[int(s)] = line[:71].rstrip()

    for name in chain(module):
        p = deck_path(module, name)
        if not p:
            continue
        pending = None      # (seq, inc) for cards following a control card
        for line in open(p, 'r', errors='replace'):
            if line.startswith('./'):
                m = CTL.match(line)
                pending = None
                if not m:
                    continue
                op = m.group(1).upper()
                if op == '*' or not m.group(2):
                    continue
                lo = int(m.group(2))
                hi = int(m.group(3)) if m.group(3) else lo
                # `$ first inc` -- where the following cards are numbered.
                tail = re.search(r'\$\s*(\d+)\s*(\d+)?', line)
                if op in ('R', 'D'):
                    for k in [k for k in cards if lo <= k <= hi]:
                        del cards[k]
                if op in ('R', 'I') and tail:
                    pending = (int(tail.group(1)),
                               int(tail.group(2)) if tail.group(2) else 100)
                continue
            if pending is not None:
                seq, inc = pending
                cards[seq] = line[:71].rstrip()
                pending = (seq + inc, inc)
    return sorted(cards.items())


def deck_path(module, name):
    for d in DECKDIRS:
        p = os.path.join(d, '%s.%s' % (module, name))
        if os.path.exists(p):
            return p
    return None


def deleted(module):
    """{(lo, hi)} -- sequence ranges the applied chain deletes or replaces.

    A `./ D` deletes outright.  A `./ R` replaces, which also means the original
    cards are gone -- so for the question "is this base-file card in the
    program?" both answer no.
    """
    out = set()
    for name in chain(module):
        p = deck_path(module, name)
        if not p:
            continue
        for line in open(p, 'r', errors='replace'):
            m = CTL.match(line)
            if not m:
                continue
            op = m.group(1).upper()
            if op not in ('D', 'R') or not m.group(2):
                continue
            lo = int(m.group(2))
            hi = int(m.group(3)) if m.group(3) else lo
            out.add((lo, hi))
    return out


def covered(ranges, seq):
    return any(lo <= seq <= hi for lo, hi in ranges)


def assembled(module):
    """[(seq, text)] -- the cards the assembler sees AND generates code for.

    `effective()` with conditional assembly applied, evaluated over the merged
    cards rather than the base file so a deck that adds or removes an `AIF` is
    accounted for.  This is the list a scanner should use: for `DMKIOS` it
    contains ZERO references to `INTTIO`, which is why the module assembles
    clean against a PSA that renames the symbol away -- the observation that
    took a dozen steps to explain by hand, reproduced here mechanically.
    """
    g = globals_()
    out, skip_to = [], None
    for seq, text in effective(module):
        a = ANOP.match(text)
        if a:
            if skip_to == a.group(1):
                skip_to = None
            continue
        if skip_to:
            continue
        m = AIF_EQ.match(text)
        if m and g.get(m.group(1)) == int(m.group(2)):
            skip_to = m.group(3)
            continue
        m = AIF_NOT.match(text)
        if m and not g.get(m.group(1)):
            skip_to = m.group(2)
            continue
        out.append((seq, text))
    return out


def live(module):
    """[(seq, text)] -- base-file cards the applied chain does NOT remove."""
    gone = deleted(module)
    rows = []
    path = src_path(module)
    if not path:
        return []
    for line in open(path, 'r', errors='replace'):
        s = line[72:80].strip()
        if s.isdigit() and not covered(gone, int(s)):
            rows.append((int(s), line[:71].rstrip()))
    return rows


def main():
    args = [a for a in sys.argv[1:] if not a.startswith('--')]
    fl = set(a for a in sys.argv[1:] if a.startswith('--'))
    if not args:
        print(__doc__.strip().split('\n\n')[0])
        return 0

    if '--dead' in fl and len(args) >= 2:
        module, sym = args[0], args[1]
        gone = deleted(module)
        cond = conditional(module)
        path = src_path(module)
        d = c = a = 0
        for i, line in enumerate(open(path, 'r', errors='replace'), 1):
            code, s = line[:71], line[72:80].strip()
            if line.startswith('*') or not s.isdigit() or sym not in code:
                continue
            if covered(gone, int(s)):
                d += 1
                print('  %5d  %s  DEAD -- deleted by the applied chain' % (i, s))
            elif int(s) in cond:
                c += 1
                print('  %5d  %s  DEAD -- not assembled, %s is 0'
                      % (i, s, cond[int(s)]))
            else:
                a += 1
                print('  %5d  %s  live' % (i, s))
        print('-- %s: %d live reference(s) to %s; %d deleted, %d unassembled'
              % (module, a, sym, d, c))
        return 0

    for module in args:
        ch = chain(module)
        gone = sorted(deleted(module))
        base = len([1 for l in open(src_path(module), 'r', errors='replace')
                    if l[72:80].strip().isdigit()])
        n = len(live(module))
        print('=== %s: %d decks applied, %d of %d base cards survive'
              % (module, len(ch), n, base))
        big = [(lo, hi) for lo, hi in gone if hi - lo >= 10000]
        if big:
            print('    wholesale removals (>= 10000 in sequence):')
            for lo, hi in big:
                print('      %08d - %08d' % (lo, hi))
    return 0


if __name__ == '__main__':
    sys.exit(main())
