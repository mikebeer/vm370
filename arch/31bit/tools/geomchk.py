#!/usr/bin/env python3
"""geomchk.py -- find page/segment GEOMETRY constants we have not converted.

VM/370 CP uses 64 KB segments of 16 pages with 2-byte page-table entries.  The
ESA/390 conversion moves to 1 MB segments of 256 pages with 4-byte entries, so
every constant that encoded the old geometry has to change together:

  N    R1,=XL4'0000F000'   a 4-bit page number -- cannot express 256 pages
  SRL  R1,11               page*2, i.e. a 2-byte page-table entry
  SLL  R1,2                page*2 -> page*8, same assumption
  SRL  Rn,16 / SLL Rn,16   a 64 KB segment number (1 MB wants 20)
  16*2                     the length of a 16-entry, 2-byte page table

Converting one of a group and not the rest is worse than converting none: the
arithmetic becomes internally inconsistent and the result is a plausible
address that points at the wrong entry.  That is I-162: DMKPTR's GETENTR2 had
its swap-table displacement converted to 256-entry geometry while the page
number feeding it stayed 4 bits wide, so `TM SWPFLAG,SWPTRANS+SWPALLOC` read
an unrelated entry and CP looped in INTRAN forever with no I/O issued.

So this reports a site only when OUR decks do not already replace that
sequence number.  Sites are grouped:

  PROVEN   the constant can only mean the old geometry (mask, *2 table size)
  REVIEW   the constant is geometry-SHAPED but has other legitimate uses
           (a shift of 16 is also how CP reaches a halfword); each one needs
           reading before it is called a defect.

Usage:  geomchk.py [--proven] [MODULE ...]
"""
import os
import re
import sys

SRC = '/home/claude/vmce/maintenance/files/394'
UPD = '/home/claude/vm370/arch/31bit/updates'

PROVEN = [
    ('PAGE-MASK-4BIT', re.compile(r"X?L?4?'0*F000'"),
     "4-bit page number: 16 pages/segment, cannot express 256"),
    ('PTE-SIZE-2', re.compile(r'\bS[RL]L\s+R\d+,11\b'),
     "shift of 11 = page*2, a 2-byte page-table entry"),
    ('PAGTAB-LEN-16x2', re.compile(r'\b16\*2\b'),
     "length of a 16-entry 2-byte page table"),
    ('PTE-MASK-FFF0', re.compile(r"X'FFF0'"),
     "halfword PTE: strips flags AND leaves page*16 for ACORETBL; an "
     "ESA/390 PTE holds the real address, so it leaves X'F000'"),
]
REVIEW = [
    ('SEG-SHIFT-16', re.compile(r'\bS[RL]L\s+R\d+,16\b'),
     "shift of 16 = 64 KB segment number (1 MB wants 20)"),
    ('SEG-MASK-64K', re.compile(r"X?L?4?'0*FFFF0000'"),
     "64 KB segment mask"),
]


def replaced():
    """{module: set(sequence numbers our decks replace)} from ./ R headers."""
    out = {}
    hdr = re.compile(r'^\./ R\s+(\d{8})(?:\s+(\d{8}))?')
    for f in sorted(os.listdir(UPD)):
        m = re.match(r'^(DMK[A-Z0-9]+|[A-Z0-9]+)\.(XA\w+DK)$', f)
        if not m:
            continue
        mod = m.group(1)
        s = out.setdefault(mod, set())
        for line in open(os.path.join(UPD, f), 'r', errors='replace'):
            h = hdr.match(line)
            if h:
                lo = int(h.group(1))
                hi = int(h.group(2)) if h.group(2) else lo
                s.add((lo, hi))
    return out


def covered(ranges, seq):
    return any(lo <= seq <= hi for lo, hi in ranges)


def scan(only):
    rep = replaced()
    rows = []
    for f in sorted(os.listdir(SRC)):
        m = re.match(r'^(DMK[A-Z0-9]{3,5})\.ASSEMBLE$', f)
        if not m:
            continue
        mod = m.group(1)
        if only and mod not in only:
            continue
        ranges = rep.get(mod, set())
        for n, line in enumerate(open(os.path.join(SRC, f), 'r',
                                      errors='replace'), 1):
            if line.startswith('*'):
                continue
            code, seqf = line[:71], line[72:80].strip()
            if not seqf.isdigit():
                continue
            seq = int(seqf)
            for bucket, pats in (('PROVEN', PROVEN), ('REVIEW', REVIEW)):
                for tag, pat, why in pats:
                    if pat.search(code) and not covered(ranges, seq):
                        rows.append((bucket, mod, seq, n, tag, code.rstrip(),
                                     why))
    return rows


def main():
    args = [a for a in sys.argv[1:] if not a.startswith('--')]
    only_proven = '--proven' in sys.argv
    rows = scan(set(args))
    for bucket in ('PROVEN', 'REVIEW'):
        if only_proven and bucket != 'PROVEN':
            continue
        sel = [r for r in rows if r[0] == bucket]
        print('=== %s: %d unconverted site(s)' % (bucket, len(sel)))
        cur = None
        for b, mod, seq, n, tag, code, why in sel:
            if mod != cur:
                print('  %s' % mod); cur = mod
            print('    %08d  %-16s %s' % (seq, tag, code.strip()[:52]))
        print()
    print('-- %d PROVEN, %d REVIEW; a site is listed only when no XA deck'
          % (len([r for r in rows if r[0] == 'PROVEN']),
             len([r for r in rows if r[0] == 'REVIEW'])))
    print('   of ours replaces its sequence number.')


if __name__ == '__main__':
    main()
