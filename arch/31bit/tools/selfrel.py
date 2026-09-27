#!/usr/bin/env python3
"""Enumerate self-relative branches, which no other check can see.

`R-26`.  CP's polling loops are written `BNZ *-4`, which lands exactly on the
preceding instruction.  Any replacement longer than four bytes -- and every
ESA/390 channel replacement is, because `SSCH` and `TSCH` need a subsystem ID
loaded and a block named -- leaves the branch pointing **inside** the
replacement.  It assembles perfectly. The loader is happy. At execution it
branches to a garbage instruction boundary, and the only symptom is a program
check with no obvious cause.

    python3 selfrel.py /path/to/vmce [--nucleus] [--module DMKCKP]

The 64-bit pass has the same problem on a far larger scale, and that is the
reason to remove these as we go rather than when they bite.  This pass converts
I/O instructions only, so only I/O polling loops are at risk.  A z/Architecture
pass converts *data movement everywhere*: `L` becomes `LG`, `ST` becomes `STG`,
RX becomes RXY, and a four-byte instruction becomes six.  At that point every
self-relative branch in CP is suspect, not just the ones near channel I/O.

So each `*-n` turned into a label now is one fewer landmine then, and the count
this prints is a carry-forward measure as much as a current one.
See ../../../docs/17-CARRY-FORWARD-64.md.
"""
import os
import re
import sys

# `*-4` and `*+8` and friends, in the operand of anything.  Also catches the
# `BC 6,*-4` form, where the displacement follows a mask.
PAT = re.compile(r'\*[-+]\d+')


def main():
    root = sys.argv[1] if len(sys.argv) > 1 else '/home/claude/vmce'
    src = os.path.join(root, 'source', 'cp')
    nucleus = {m.group(1) for m in re.finditer(
        r'&1 &2 &3 (\S+)',
        open(os.path.join(root, 'maintenance', 'files', '194',
                          'CPLOAD.EXEC')).read())} - {'LOADER', 'LDT'}
    only = None
    if '--module' in sys.argv:
        only = sys.argv[sys.argv.index('--module') + 1]

    hits = {}
    for name in sorted(os.listdir(src)):
        if not name.endswith('.ASSEMBLE'):
            continue
        mod = name[:-9]
        if only and mod != only:
            continue
        if '--nucleus' in sys.argv and mod not in nucleus:
            continue
        for line in open(os.path.join(src, name), errors='replace'):
            body = line[:71]
            if body.startswith('*') or body.startswith('.'):
                continue
            # The operand field only: a `*` in a comment is not a branch.
            m = re.match(r'(?:\S{0,8})\s+(\S+)\s+(\S+)', body)
            if not m:
                continue
            for d in PAT.findall(m.group(2)):
                hits.setdefault(mod, []).append((m.group(1), d,
                                                 line[72:80].strip()))

    print('SELF-RELATIVE BRANCHES  --  R-26')
    print()
    print('%-9s %5s  %s' % ('MODULE', 'COUNT', 'DISPLACEMENTS'))
    print('-' * 72)
    tot = nuc = 0
    for mod in sorted(hits, key=lambda m: -len(hits[m])):
        ds = {}
        for _, d, _s in hits[mod]:
            ds[d] = ds.get(d, 0) + 1
        tot += len(hits[mod])
        if mod in nucleus:
            nuc += len(hits[mod])
        print('%-9s %5d  %s'
              % (mod, len(hits[mod]),
                 ' '.join('%s x%d' % (k, v)
                          for k, v in sorted(ds.items(),
                                             key=lambda kv: -kv[1]))[:48]))
    print('-' * 72)
    print('%-30s %d' % ('modules affected', len(hits)))
    print('%-30s %d' % ('sites, total', tot))
    print('%-30s %d' % ('sites, in nucleus modules', nuc))
    if only:
        print()
        for op, d, seq in hits.get(only, []):
            print('  %-8s %-6s seq %s' % (op, d, seq))
    return 0


if __name__ == '__main__':
    try:
        sys.exit(main())
    except BrokenPipeError:      # piped through head
        sys.exit(0)
