#!/usr/bin/env python3
"""geomchk.py -- find page/segment GEOMETRY constants we have not converted.

VM/370 CP uses 64 KB segments of 16 pages with 2-byte page-table entries.  The
ESA/390 conversion moves to 1 MB segments of 256 pages with 4-byte entries, so
every constant that encoded the old geometry has to change together:

  N    R1,=XL4'0000F000'   a 4-bit page number -- cannot express 256 pages
  SRL  R1,11               page*2, i.e. a 2-byte page-table entry
  SLL  R1,2                page*2 -> page*8, same assumption
  16*2                     the length of a 16-entry, 2-byte page table
  X'FFF0'                  a halfword PTE's flags AND page*16 in one mask
  SRL  Rn,4 / SLL Rn,4     PAGSHFT, 16 pages per segment      (ambiguous)
  SRL  Rn,16 / SLL Rn,16   SEGSHFT, a 64 KB segment number    (ambiguous)
  SRL  Rn,6                PTLSHFT, page-table length         (ambiguous)

Converting one of a group and not the rest is worse than converting none: the
arithmetic becomes internally inconsistent and the result is a plausible
address that points at the wrong entry.  That is I-162 -- DMKPTR's GETENTR2 had
its swap-table displacement converted to 256-entry geometry while the page
number feeding it stayed 4 bits wide -- and I-163 one card later.  Five days
for three cards.

So this reports a site only when OUR decks do not already replace that
sequence number, and it separates what it can prove from what it cannot:

  PROVEN   the constant can only mean the old geometry (a 4-bit page mask, a
           16*2 table length, a shift of 11).  Still read it, but the shape
           alone is enough to put it on the list.
  REVIEW   the constant is geometry-SHAPED and has other legitimate uses.  A
           shift of 4 is also how you reach a nibble; a shift of 16 is also
           how you reach a halfword; DMKMCH's `SRL R3,11 / SLL R3,11` is 2 KB
           rounding and DMKSSP's `16*2` is a device index table.  Each needs
           reading before it is called anything.

REVIEW rows carry a CANDIDATE classification from the symbols and comment
around them -- segment, page, swap, cortable, key, length -- and a `?` when
nothing in the context decides it.  A candidate is a reading aid, NOT a
verdict: the whole point of I-162 is that a plausible classification applied
without reading is how the five-day bug was introduced.

Composite shifts are called out separately.  `SLL R1,4+4` in DMKBLD holds TWO
different pieces of arithmetic -- one undoes a VMSEG packing, the other is
pages-per-segment -- so collapsing it into one symbolic constant would be a
bug, not a conversion.

Usage:  geomchk.py [--proven] [--shifts] [--dat] [MODULE ...]
          --proven  only the provable classes
          --shifts  only the ambiguous shift classes, as a conversion audit
          --dat     only modules that touch the DAT structures
"""
import os
import re
import sys

import applied

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
# Ambiguous by construction.  The shift amount is the only signal, and it is
# not a strong one, so these exist to be READ, not to be converted in bulk.
SHIFTS = [
    ('PAGSHFT-4', re.compile(r'\bS[RL][DL]?L\s+R\d+,4\b'),
     "4 = 16 pages per segment (PAGSHFT); ESA/390 wants 8"),
    ('PTLSHFT-6', re.compile(r'\bS[RL][DL]?L\s+R\d+,6\b'),
     "6 = page-table length unit (PTLSHFT); ESA/390 wants 10"),
    ('SEGSHFT-16', re.compile(r'\bS[RL][DL]?L\s+R\d+,16\b'),
     "16 = 64 KB segment number (SEGSHFT); 1 MB wants 20"),
    ('SEGSHFT-20', re.compile(r'\bS[RL][DL]?L\s+R\d+,20\b'),
     "20 = already a 1 MB segment number -- may be converted already"),
]
REVIEW = SHIFTS + [
    ('SEG-MASK-64K', re.compile(r"X?L?4?'0*FFFF0000'"),
     "64 KB segment mask"),
]
# Our own update identifiers: XAnnnnDK.  A card carrying one is ours.
OURS = re.compile(r'^XA\d{4}DK$')
COMPOSITE = re.compile(r'\bS[RL][DL]?L\s+R\d+,\s*\d+\s*\+\s*\d+')

# Candidate classification.  Ordered: the first family whose symbols appear in
# the window wins, because a card naming SEGPAGE and PAGCORE is doing segment
# work on the way to a page table.
FAMILY = [
    ('swap',     ('SWPTABLE', 'SWPFLAG', 'SWPVM', 'SWPPAG', 'SWPVPAGE',
                  'SWPCYL', 'SWPKEY')),
    ('cortable', ('ACORETBL', 'CORTABLE', 'CORFPNT', 'CORFLAG', 'CORSWPNT',
                  'CORPGPNT')),
    ('segment',  ('SEGPAGE', 'SEGTABLE', 'SEGPTO', 'SEGPTL', 'VMSEG',
                  'SEGINV', 'SEGPLEN')),
    ('page',     ('PAGTABLE', 'PAGCORE', 'PAGPFRA', 'PAGINV', 'PAGTSWP',
                  'PAGBMP', 'PAGSWPE')),
    ('key',      ('ISK', 'SSK', 'RRB', 'STORKEY', 'KEY')),
    ('length',   ('LENGTH', 'SIZE', 'COUNT')),
]
WORDS = [('segment', ('SEGMENT', 'SEG ')), ('page', ('PAGE',)),
         ('key', ('KEY', '2K', '2048')), ('length', ('LENGTH', 'SIZE'))]

# The segment-table-length idiom.  `IC Rn,xxxCR1` / `LA Rn,1(0,Rn)` /
# `SLL Rn,6` computes (STL+1)*64 bytes from a control-register-1 length code,
# and the ESA/390 PoO says bits 25-31 of CR1 give that length "in units of 64
# bytes" -- the same unit System/370 uses in bits 0-7.  So the SHIFT is correct
# in both architectures and this is not a site.  What moves is the FIELD: byte
# 0 becomes byte 3, so the `IC` displacement changes, and only when guests stop
# being S/370 machines at M4.  Called out by name because a bulk PTLSHFT 6->10
# pass would corrupt both of these.
SEGTABLEN = re.compile(r'\bIC\s+R\d+,\w*CR1\b')


def replaced():
    """{module: {(lo,hi)}} -- the sequence ranges our decks replace."""
    out = {}
    hdr = re.compile(r'^\./ R\s+(\d{8})(?:\s+(\d{8}))?')
    for f in sorted(os.listdir(UPD)):
        m = re.match(r'^([A-Z0-9]+)\.(XA\w+DK)$', f)
        if not m:
            continue
        s = out.setdefault(m.group(1), set())
        for line in open(os.path.join(UPD, f), 'r', errors='replace'):
            h = hdr.match(line)
            if h:
                lo = int(h.group(1))
                s.add((lo, int(h.group(2)) if h.group(2) else lo))
    return out


def dat_modules():
    """Modules that touch the DAT structures, DERIVED rather than listed.

    A hardcoded list goes stale silently; `COPY CORE` and the CORE.COPY symbol
    names are in the source and cannot.
    """
    sym = re.compile(r'\b(COPY\s+CORE|SEGPAGE|SEGPTO|PAGCORE|PAGPFRA|SWPFLAG|'
                     r'CORTABLE|ACORETBL|PAGTABLE|SEGTABLE|SWPTABLE)\b')
    out = set()
    for f in sorted(os.listdir(SRC)):
        m = re.match(r'^(DMK[A-Z0-9]{3,5})\.ASSEMBLE$', f)
        if not m:
            continue
        with open(os.path.join(SRC, f), 'r', errors='replace') as fh:
            for line in fh:
                if not line.startswith('*') and sym.search(line[:71]):
                    out.add(m.group(1))
                    break
    return out


def classify(window, code, wide=()):
    """Candidate family for a shift site, from the symbols and words near it.

    `wide` is a larger window used only for the segment-table-length idiom,
    whose `IC Rn,xxxCR1` can sit several cards above the shift -- in DMKVAT it
    is six cards up, with a CH/BNH/LH bounds check in between.
    """
    up = ' '.join(window).upper()
    if (SEGTABLEN.search(' '.join(wide or window).upper())
            and re.search(r'\bS[RL]L\s+R\d+,6\b', code)):
        return 'segtab-len NOT-A-SITE'
    for name, syms in FAMILY:
        if any(s in up for s in syms):
            return name
    com = code[40:71].upper()
    for name, words in WORDS:
        if any(w in com for w in words):
            return name + '?'
    return '?'


def covered(ranges, seq):
    return any(lo <= seq <= hi for lo, hi in ranges)


def scan(only, dat_only):
    rep, dat = replaced(), dat_modules()
    rows = []
    for f in sorted(os.listdir(SRC)):
        m = re.match(r'^(DMK[A-Z0-9]{3,5})\.ASSEMBLE$', f)
        if not m:
            continue
        mod = m.group(1)
        if only and mod not in only:
            continue
        if dat_only and mod not in dat:
            continue
        ranges = rep.get(mod, set())
        # Scan the cards the assembler actually sees, not the 1979 base file.
        # The applied APAR chain deletes cards wholesale, conditional assembly
        # skips more, and the decks' own replacement cards carry constants the
        # base file never had -- so the base file is wrong in both directions.
        # I-176 cost a detour through DMKIOS's I/O interruption supervisor,
        # 473 cards an APAR had already moved into DMKIOT.
        cards = applied.assembled(mod)
        lines = [t for _s, t in cards]
        for i, (seq, code) in enumerate(cards):
            if code.startswith('*'):
                continue
            if covered(ranges, seq):
                continue
            # A card OUR OWN decks inserted is converted by definition, and it
            # carries our identifier in columns 64-71.  The `covered()` test
            # above cannot catch these: it holds the sequence numbers a deck
            # REPLACES, and an inserted card gets a NEW number -- `./ R
            # 01054000` replaces 01054000 but the card it writes is 01054100.
            # Without this, scanning the effective source reports 19 of our own
            # ESA/390 conversions as unconverted sites, which is how this check
            # was found: `SRDL R14,20` next to `SLL R14,2` and `SEGSTOM` is
            # 1 MB segments and a fullword STE, not a site to fix.
            if OURS.match(code[63:71].strip()):
                continue
            window = [l[:71] for l in lines[max(0, i - 4):i + 5]]
            wide = [l[:71] for l in lines[max(0, i - 8):i + 5]]
            for bucket, pats in (('PROVEN', PROVEN), ('REVIEW', REVIEW)):
                for tag, pat, _why in pats:
                    if not pat.search(code):
                        continue
                    cand = (classify(window, code, wide)
                            if bucket == 'REVIEW' else '')
                    if COMPOSITE.search(code):
                        cand = (cand + ' COMPOSITE').strip()
                    rows.append((bucket, mod, seq, tag, code.rstrip(), cand,
                                 mod in dat))
    return rows


def main():
    args = [a for a in sys.argv[1:] if not a.startswith('--')]
    fl = set(a for a in sys.argv[1:] if a.startswith('--'))
    rows = scan(set(args), '--dat' in fl)
    want = []
    if '--proven' in fl:
        want = ['PROVEN']
    elif '--shifts' in fl:
        want = ['REVIEW']
    else:
        want = ['PROVEN', 'REVIEW']
    for bucket in want:
        sel = [r for r in rows if r[0] == bucket]
        print('=== %s: %d unconverted site(s)' % (bucket, len(sel)))
        if bucket == 'REVIEW':
            print('    (candidate classes are a READING AID, not a verdict --'
                  ' see I-162)')
        cur = None
        for b, mod, seq, tag, code, cand, isdat in sel:
            if mod != cur:
                print('  %s%s' % (mod, '  [DAT]' if isdat else ''))
                cur = mod
            print('    %08d  %-14s %-34s %s'
                  % (seq, tag, code.strip()[:34], cand))
        print()
    comp = [r for r in rows if 'COMPOSITE' in r[5]]
    if comp:
        print('=== COMPOSITE shifts -- two pieces of arithmetic in one card;'
              ' do NOT collapse into one EQU')
        for b, mod, seq, tag, code, cand, isdat in comp:
            print('    %-8s %08d  %s' % (mod, seq, code.strip()[:46]))
        print()
    p = len([r for r in rows if r[0] == 'PROVEN'])
    v = len([r for r in rows if r[0] == 'REVIEW'])
    vd = len([r for r in rows if r[0] == 'REVIEW' and r[6]])
    print('-- %d PROVEN, %d REVIEW (%d of the REVIEW rows are in modules that'
          % (p, v, vd))
    print('   touch the DAT structures).  A site is listed only when no XA')
    print('   deck of ours replaces its sequence number.')
    print()
    print('   Scanned against the EFFECTIVE source -- the base file with the')
    print('   applied APAR chain merged in -- not the 1979 base file, which')
    print('   was wrong in BOTH directions.  It showed 2 PROVEN and 17 REVIEW')
    print('   phantoms in cards the build never assembles (one of them in')
    print('   DMKPTR, inside an &AP block, where a patch would have had no')
    print('   effect at all), and it HID 7 REVIEW sites that arrive on the')
    print('   CE APAR decks\' own cards -- including two PTLSHFT-6 sites in')
    print('   DMKVAT, the DAT module. Cards carrying OUR identifier are')
    print('   skipped: 19 of them are conversions we already made, which')
    print('   `covered()` cannot catch because a replaced card 01054000 is')
    print('   rewritten as a NEW card 01054100. I-176.')


if __name__ == '__main__':
    main()
