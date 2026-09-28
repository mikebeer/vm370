#!/usr/bin/env python3
"""Which S/370-only sites does each deck actually cover?

Every other check in this project answers a different question.  `s370only.py`
reads base source and lists the sites; `status.py` says whether a module still
carries a renamed PSA symbol; CE says the module assembles.  **None of them
notices a site a deck simply did not touch.**  `DMKVSJ` was committed as
complete while an `HDV` at seq 00324000 sat unconverted, because the scan that
cleared it was an ad-hoc one-liner with a bug -- `substr($0,10,8)` on
`         HDV   0(R5)` yields `HDV   0(`, which matched nothing (`I-67`).

So this takes the site list from `s370only.py`, reads each deck's own `./ R`
and `./ D` control cards, and reports the difference.  It cannot be fooled by
a bad scan because it does not scan: it asks the authoritative tool for the
sites and the decks for the ranges.

    python3 coverage.py <opcode.c> <vmce> [--all]

Not every uncovered site is a defect, and the tool does not pretend to know
which: `DMKSAV`'s five belong to `DMKSAVNC`, which runs on the build machine in
S/370 mode and must stay that way (`I-59`), and the `ISK`/`SSK`/`RRB` sites
belong to the storage-key pass, which is sequenced separately.  `DECLARED`
below records the ones that are deliberate, so anything else in the report is
a site nobody has decided about.
"""
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
UPDATES = os.path.join(HERE, '..', 'updates')

# Sites left in S/370 form on purpose.  A reason, not a suppression: each entry
# has to say why, and the report prints it.
DECLARED = {
    ('DMKSAV', '00426000'): 'DMKSAVNC, build machine, S/370 -- I-59',
    ('DMKSAV', '00429000'): 'DMKSAVNC, build machine, S/370 -- I-59',
    ('DMKSAV', '00601000'): 'DMKSAVNC, build machine, S/370 -- I-59',
    ('DMKSAV', '00613100'): 'DMKSAVNC, build machine, S/370 -- I-59',
    ('DMKSAV', '00613300'): 'DMKSAVNC, build machine, S/370 -- I-59',
}

KEY = ('ISK', 'SSK', 'RRB')


def sites(opcode_c, root):
    """module -> {seq: mnemonic}, from s370only.py's own listing."""
    out = subprocess.run(
        [sys.executable, os.path.join(HERE, 's370only.py'), opcode_c, root,
         '--all'], capture_output=True, text=True).stdout
    found, cur = {}, None
    for line in out.splitlines():
        m = re.match(r'^(\w+) \(([0-9A-F]+)\)$', line)
        if m:
            cur = m.group(1)
            continue
        m = re.match(r'^\s+(\w+)\s+(\d{8})$', line)
        if m and cur:
            found.setdefault(m.group(1), {})[m.group(2)] = cur
    return found


def covered(path):
    """The (from, to) sequence ranges a deck's control cards replace or delete."""
    rng = []
    for line in open(path):
        m = re.match(r'\./ ([RD]) (\d{8})(?: (\d{8}))?', line)
        if m:
            rng.append((int(m.group(2)), int(m.group(3) or m.group(2))))
    return rng


def main():
    opcode_c, root = sys.argv[1], sys.argv[2]
    found = sites(opcode_c, root)
    decks = {}
    for f in sorted(os.listdir(UPDATES)):
        if '.XA' in f:
            decks.setdefault(f.split('.')[0], []).append(f)

    print('DECK COVERAGE OF S/370-ONLY SITES  --  tools/coverage.py')
    print()
    print('%-8s %-6s %-6s %s' % ('MODULE', 'SITES', 'OPEN', 'NOTE'))
    print('-' * 74)
    total_open = 0
    for mod in sorted(decks):
        if mod not in found:
            continue
        rng = []
        for f in decks[mod]:
            rng += covered(os.path.join(UPDATES, f))
        left = [(s, op) for s, op in sorted(found[mod].items())
                if not any(a <= int(s) <= b for a, b in rng)]
        declared = [(s, op) for s, op in left if (mod, s) in DECLARED]
        key = [(s, op) for s, op in left if op in KEY and (mod, s) not in DECLARED]
        open_ = [(s, op) for s, op in left
                 if op not in KEY and (mod, s) not in DECLARED]
        total_open += len(open_)
        note = []
        if declared:
            note.append('%d declared' % len(declared))
        if key:
            note.append('%d key-family, deferred' % len(key))
        if open_:
            note.append('OPEN: ' + ' '.join('%s %s' % (s, o) for s, o in open_))
        print('%-8s %-6d %-6d %s'
              % (mod, len(found[mod]), len(open_), '; '.join(note)))
    print('-' * 74)
    print('%d channel sites in decked modules that no deck covers '
          'and nothing declares' % total_open)

    if '--all' in sys.argv:
        print()
        print('Modules with sites and no deck at all:')
        rest = sorted(m for m in found if m not in decks)
        for i in range(0, len(rest), 8):
            print('  ' + ' '.join('%-8s' % m for m in rest[i:i + 8]))
    return 0


if __name__ == '__main__':
    sys.exit(main())
