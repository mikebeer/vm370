#!/usr/bin/env python3
"""Does every staged card-reader file still match the deck it was made from?

`mkrun.py` copies each deck into `io/rNN.txt` when the run is PREPARED, not
when Hercules reads it.  So a deck regenerated after `mk` and before `run`
finishes is not in the build, and nothing says so: the log shows `readcard
dmkpgs xa0036dk a`, the module assembles, and the diagnostics are the ones
belonging to the OLD cards.  The deck on disk and the module in the nucleus
disagree, and every tool that reads the deck -- `deckchk.py`, `symchk.py`,
`auxcheck` -- reports on the version that was NOT built.

That is the stale-artifact shape that cost a 190-diagnostic log (I-131) and a
silently-dropped AUXLCL entry (I-138), arriving through a third door.  So assert
it instead of remembering it.

    python3 iochk.py [ce-root]
"""
import glob
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from mkrun import card

UPDATES = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                       '..', 'updates')


def expected(mod, ft):
    path = os.path.join(UPDATES, '%s.%s' % (mod, ft))
    if not os.path.exists(path):
        return None
    out = card('ID MAINT NAME %s %s' % (mod, ft))
    for line in open(path):
        out += card(line.rstrip('\n'))
    return out


def main():
    ce = sys.argv[1] if len(sys.argv) > 1 else '.'
    iod = os.path.join(ce, 'io')
    if not os.path.isdir(iod):
        print('### no io/ directory under %s' % ce)
        return 2
    drift, checked, skipped = [], 0, 0
    for path in sorted(glob.glob(os.path.join(iod, 'r*.txt'))):
        head = open(path).readline().split()
        if len(head) != 5 or head[:3] != ['ID', 'MAINT', 'NAME']:
            continue
        mod, ft = head[3], head[4]
        want = expected(mod, ft)
        if want is None:          # a CP-owned member, no file of ours
            skipped += 1
            continue
        checked += 1
        if open(path).read() != want:
            drift.append((os.path.basename(path), mod, ft))
    print('%d staged file(s) checked against their source, %d CP-owned skipped'
          % (checked, skipped))
    if not drift:
        print('no drift: every card Hercules will read is the card on disk')
        return 0
    for f, mod, ft in drift:
        print('### DRIFT %-9s %s.%s -- the build will assemble the OLD cards' %
              (f, mod, ft))
    print()
    print('Each one is a module whose deck changed after the run was prepared.')
    print('If it has not been read yet, restage that file; if it has, the')
    print('module must be reassembled before the result means anything.')
    return 1


if __name__ == '__main__':
    sys.exit(main())
