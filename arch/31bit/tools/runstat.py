#!/usr/bin/env python3
"""What THIS RUN produced: modules OK, defective, missing a deck, not yet run.

Not to be confused with `status.py`, which answers a different and larger
question -- where each CP module stands in the conversion, derived from the load
list, the assembly EXECs, the AUXLCLs and a source scan.  **This file was first
written AS `status.py` and overwrote 308 lines of that tool with 102**, because
it was created with a shell redirect without checking whether the name was taken.
Recovered from git.  The lesson is small and the cost could have been total: a
`cat > file` is a destructive write, and nothing in this project warns about it
the way `mkdeck` warns about a bad card.  `I-145`.

`status.py` answers "is this module converted"; this answers "did this run do
what it was asked".

Asked for as a standing report format, so it is derived from the log every time
rather than counted by hand.  Definitions, stated because each one hides a trap
this project has already fallen into:

  OK        `NO STATEMENTS FLAGGED` **and** an object deck created.  Both halves
            matter: a clean assembly with no deck is not OK, and a deck with
            diagnostics is not either (`I-137`).
  DEFECT    at least one diagnostic that is not `IFO197 *** MNOTE ***`.  Severity,
            not output existence -- assembler XF resolves an undefined symbol as
            ZERO and still writes a deck, so `L R3,SEGPAGE` becomes `L R3,0` and
            `DMKPTR TXTLCL CREATED` appears.  A deck can be a lie.
  MISSING   assembly started and no object deck appeared under any of the three
            names -- `TEXT`, `TXTLCL` or `TXTHRC`.  `asmchk` knew only the first
            two and reported five false positives (`I-137`).
  NOT RUN   the difference between the modules the pass covers and the modules
            the log shows starting.  During staging that is all of them.

The expected total is read from the most recently completed log rather than
written down here, and the report says which log that was -- a remembered
constant is the stale artifact this project keeps tripping over (`I-141`).

    python3 status.py [ce-root] [run]
"""
import glob
import os
import re
import sys

ASM = re.compile(r'ASMBLING (\S+)')
DIAG = re.compile(r'^(IFO\d{3})')
CREATED = re.compile(r'(\S+)\s+(TEXT|TXTLCL|TXTHRC)\s+CREATED')


def read(path):
    mod = None
    started, clean, deck, bad = [], set(), set(), {}
    for line in open(path, errors='replace'):
        m = ASM.search(line)
        if m:
            mod = m.group(1)
            started.append(mod)
        if 'NO STATEMENTS FLAGGED' in line and mod:
            clean.add(mod)
        c = CREATED.search(line)
        if c:
            deck.add(c.group(1))
        d = DIAG.match(line)
        if d and d.group(1) != 'IFO197' and mod:
            bad.setdefault(mod, set()).add(d.group(1))
    return started, clean, deck, bad


def expected(ce):
    """Modules the assembly pass covers, from the newest COMPLETE earlier log."""
    best = (0, None)
    for p in sorted(glob.glob(os.path.join(ce, 'logs', '*.log'))):
        s, _, _, _ = read(p)
        if len(s) > best[0]:
            best = (len(s), os.path.basename(p))
    return best


def main():
    ce = sys.argv[1] if len(sys.argv) > 1 else \
        '/home/claude/vm370/scratchpad/VM370CE.V1.R1.2'
    run = sys.argv[2] if len(sys.argv) > 2 else 'f1'
    log = os.path.join(ce, '%s.log' % run)
    rc = os.path.join(ce, 'hercules.rc')
    if not os.path.exists(log):
        print('no %s.log yet' % run)
        return 2

    want_cards = sum(1 for l in open(rc, errors='replace')
                     if l.strip().startswith('/readcard')) \
        if os.path.exists(rc) else 0
    got_cards = sum(1 for l in open(log, errors='replace') if 'readcard' in l)

    started, clean, deck, bad = read(log)
    ok = sorted(clean & deck - set(bad))
    defect = sorted(bad)
    missing = sorted(set(started) - deck)
    exp, expsrc = expected(ce)
    notrun = max(0, exp - len(started)) if exp else None

    print('cards staged  %d / %d' % (got_cards, want_cards))
    print('modules  OK %-4d  DEFECT %-4d  MISSING %-4d  NOT RUN %s'
          % (len(ok), len(defect), len(missing),
             '%d' % notrun if notrun is not None else '?'))
    if exp:
        print('              (%d expected, from %s)' % (exp, expsrc))
    for m in defect:
        print('  DEFECT  %-9s %s' % (m, ' '.join(sorted(bad[m]))))
    for m in missing:
        print('  MISSING %-9s assembly started, no TEXT/TXTLCL/TXTHRC' % m)
    return 0


if __name__ == '__main__':
    sys.exit(main())
