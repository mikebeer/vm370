#!/usr/bin/env python3
"""Check a conversion deck against the assembler's own list of flagged sites.

A build costs about thirty-five minutes, so a deck that misses one of the 176
sites `asmerr.py` confirmed costs thirty-five minutes to find out.  This reads
the flagged list straight out of the build log and the `./ R` / `./ D` / `./ I`
anchors straight out of the decks, and answers three questions before the build
rather than after it:

    COVERED     flagged, and a card's range includes its sequence number
    UNCOVERED   flagged, and no card touches it -- the build WILL fail here
    EXTRA       a card touching a line the assembler did not flag

`EXTRA` is not an error.  Most of this conversion's real work is on lines that
name no renamed symbol -- the alignment slack, `LA R4,16(,R4)`, the new header
field -- and `I-124` is the standing reminder that those are the sites no
diagnostic reaches.  So `EXTRA` is printed to be read, not to be eliminated: an
empty `EXTRA` list would mean the deck did nothing but rename.

    python3 deckchk.py <build-log> [deck-dir] [--mod DMKXXX]

Exit 0 when every flagged site is covered, 1 when any is not.
"""
import collections
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
DECKS = os.path.join(HERE, '..', 'updates')

# `./ R 00108000 00108400 $ 00108010 010`  -- replace a range
# `./ D 00108000`                          -- delete
# `./ I 00108000 $ 00108010 010`           -- insert after
CTL = re.compile(r'^\./ ([RDI])\s+(\d{8})(?:\s+(\d{8}))?')


def anchors(path):
    """[(verb, first, last)] for every control card in a deck."""
    out = []
    for line in open(path, errors='replace'):
        m = CTL.match(line)
        if m:
            v, a, b = m.group(1), int(m.group(2)), int(m.group(3) or m.group(2))
            out.append((v, a, b))
    return out


def main():
    args = sys.argv[1:]
    if not args:
        print(__doc__)
        return 2
    log = args[0]
    deckdir = args[1] if len(args) > 1 and not args[1].startswith('-') else DECKS
    only = args[args.index('--mod') + 1] if '--mod' in args else None

    import asmerr
    flags, _ = asmerr.harvest(log)
    flagged = collections.defaultdict(list)
    for f in flags:
        if asmerr.symbols(f) and f.seq:
            flagged[f.mod].append((int(f.seq), f.text))

    # One deck per module per update level; a module may have several.
    decks = collections.defaultdict(list)
    for name in sorted(os.listdir(deckdir)):
        m = re.match(r'^([A-Z0-9]+)\.(XA\d+DK)$', name)
        if m:
            decks[m.group(1)].append(os.path.join(deckdir, name))

    mods = sorted(set(flagged) | set(decks))
    if only:
        mods = [m for m in mods if m == only]

    rc, any_deck = 0, False
    print('%-9s %8s %9s %7s   %s'
          % ('MODULE', 'FLAGGED', 'UNCOVERED', 'EXTRA', 'DECKS'))
    detail = []
    for mod in mods:
        sites = sorted(flagged.get(mod, []))
        spans = [s for p in decks.get(mod, []) for s in anchors(p)]
        if not sites and not spans:
            continue
        if spans:
            any_deck = True
        covered, uncovered = [], []
        for seq, text in sites:
            if any(a <= seq <= b for _, a, b in spans):
                covered.append((seq, text))
            else:
                uncovered.append((seq, text))
        touched = {seq for seq, _ in sites}
        extra = [(v, a, b) for v, a, b in spans
                 if not any(a <= s <= b for s in touched)]
        print('%-9s %8d %9d %7d   %s'
              % (mod, len(sites), len(uncovered), len(extra),
                 ' '.join(os.path.basename(p).split('.')[1]
                          for p in decks.get(mod, [])) or '-'))
        if uncovered:
            rc = 1
            detail.append((mod, uncovered, extra))
        elif extra:
            detail.append((mod, [], extra))

    if not any_deck:
        print()
        print('### no deck in %s matches any flagged module.' % deckdir)
        print('### Nothing was checked, which is not the same as nothing wrong.')
        return 2

    for mod, uncovered, extra in detail:
        if uncovered:
            print()
            print('%s -- %d flagged site(s) NO CARD TOUCHES.  The build will'
                  % (mod, len(uncovered)))
            print('fail on each of these with IFO188:')
            for seq, text in uncovered:
                print('  %08d  %s' % (seq, text[:58]))
        if extra:
            print()
            print('%s -- %d card(s) on lines the assembler did not flag.  Read'
                  % (mod, len(extra)))
            print('them: this is where the work no diagnostic reaches lives (I-124).')
            for v, a, b in extra:
                print('  ./ %s %08d%s' % (v, a, '' if a == b else ' %08d' % b))

    print()
    print('Exit %d.  A clean run means every site the ASSEMBLER named is' % rc)
    print('covered.  It says nothing about the 67 sites it cannot name.')
    return rc


if __name__ == '__main__':
    sys.exit(main())
