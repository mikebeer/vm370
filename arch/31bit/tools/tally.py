#!/usr/bin/env python3
"""Regenerate 13-ISSUES.md's status tally from the table itself.

The tally said `fixed 68, closed 11, open 9, fix known 3`.  The table holds 75,
23, 13 and 9.  It was a hand-maintained summary of a hand-maintained table, and
it drifted by 24 entries without anyone noticing -- which is the same shape as
the stale build log (I-131), the dropped AUXLCL entry (I-138), the staged card
file (I-140) and the uncounted "10 cards left" (I-141): a figure that looks
current because it is written down.

A summary derived from its source cannot drift.  So derive it.

    python3 tally.py [--check]      # --check exits 1 if the file needs rewriting
"""
import collections
import os
import re
import sys

DOC = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                   '..', '..', '..', 'docs', '13-ISSUES.md')
ROW = re.compile(r'^\| \*\*I-(\d+)\*\* \|')
# The retracted entries -- claims of mine that turned out to be wrong -- are
# named in the prose below the tally, so the count there is derived too.
RETRACTED = ['I-21', 'I-22', 'I-23', 'I-24', 'I-25', 'I-27']
WORDS = {17: 'seventeen', 23: 'twenty-three', 24: 'twenty-four',
         25: 'twenty-five', 26: 'twenty-six', 27: 'twenty-seven',
         6: 'six', 7: 'seven'}


def status(line):
    return line.rstrip().rstrip('|').rsplit('|', 1)[1].strip()


def main():
    text = open(DOC).read()
    lines = text.split('\n')
    rows = [l for l in lines if ROW.match(l)]
    st = collections.Counter(status(l) for l in rows)

    order = ['fixed', 'documented', 'closed', 'open', '**z390 only**',
             'fix known', 'worked around']
    body = [('| %s | %d |' % (k, st[k])) for k in order if st[k]]
    for k in sorted(set(st) - set(order)):
        body.append('| %s | %d |' % (k, st[k]))

    # Replace the tally rows: the contiguous run of `| x | n |` lines that
    # follows the last issue row.
    last = max(i for i, l in enumerate(lines) if ROW.match(l))
    a = last + 1
    while a < len(lines) and not re.match(r'^\| .+ \| \d+ \|$', lines[a]):
        a += 1
    b = a
    while b < len(lines) and re.match(r'^\| .+ \| \d+ \|$', lines[b]):
        b += 1
    out = lines[:a] + body + lines[b:]

    closed = st['closed']
    # One substitution, always capitalised: the phrase begins a sentence.  The
    # first version had two patterns, a bold one and a bare one, and the bare
    # one lowercased what the bold one had just written -- so --check reported
    # the file stale immediately after rewriting it.  A fixup that is not
    # idempotent is a fixup that cannot be checked.
    new = re.sub(r'\b[Ss]ix of the [\w-]+ closed entries',
                 '%s of the %s closed entries'
                 % (WORDS[len(RETRACTED)].capitalize(),
                    WORDS.get(closed, closed)),
                 '\n'.join(out))

    if '--check' in sys.argv:
        if new != text:
            print('### 13-ISSUES.md tally is stale -- run tally.py')
            return 1
        print('tally matches the table: %d rows' % len(rows))
        return 0
    open(DOC, 'w').write(new)
    print('%d issue rows; tally rewritten:' % len(rows))
    for l in body:
        print('  ' + l)
    return 0


if __name__ == '__main__':
    sys.exit(main())
