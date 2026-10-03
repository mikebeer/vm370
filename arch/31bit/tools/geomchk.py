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

# A shift of 16 is a FIELD WIDTH far more often than it is SEGSHFT, and the two
# cases below account for most of the SEGSHFT-16 rows.  Both were read before
# being named, because the whole point of I-162 is that a plausible
# classification applied without reading is how the five-day bug was made.
#
#   DASD slot addressing.  DMKCKS packs cylinder, page and device code into one
#   word: `SRL R1,16  CYL NUM TO LOW ORDER` then `LA 1(,R1)` / `SLL R1,8` /
#   `SLL R1,8  MAKE ROOM FOR DEVICE CODE`.  The 16 is the cylinder field's
#   width.  Nothing here is a segment and nothing changes.
#
#   Packed halfword pairs.  DMKATS loads `SYSPAGNM`, one word holding a START
#   and an END page number as two halfwords, and splits them with
#   `SRDL R8,16` / `SRL R9,16` before `SLL R8,12` turns each page number into
#   an address.  The 16 is the struct field width; the 12 is the page-size
#   shift, which is 4 KB in BOTH architectures and so also correct.
#   (A 16-bit page number does cap an address space at 256 MB.  That is a real
#   limit for real storage above 256 MB -- M5 territory -- and not for the
#   16 MB this milestone targets.  Recorded, not actioned.)
# Plural and extended forms spelled out rather than trusting a prefix: `\bCYL\b`
# cannot match CYLINDER, which is how `DMKRSP 00954000 GET CYLINDER NUMBER` was
# missed by the first version.  Dropping the trailing \b instead would make
# HEAD match HEADER and RECORD match RECORDING.
DASDGEOM = re.compile(
    r'\b(CYL|CYLS|CYLINDER|CYLINDERS|HEAD|HEADS|SECT|SECTOR|SECTORS|TRACK|'
    r'TRACKS|CCHH|CCHHR|SEEK|RECORD|RECORDS|DEVICE CODE)\b')
# `RECORD` also catches a non-DASD record size -- DMKMON packs one into the
# top halfword -- so the `dasd-field` label is slightly wide there.  The
# conclusion is the same either way and is what the class actually asserts:
# the shift amount is a FIELD WIDTH, not a geometry constant.

# Evidence on the card itself that it really is segment arithmetic.  `SEG.` and
# `STE` have to be in here: `DMKPTR 00793000 STE NO.` and `DMKBLD 00202000
# ADDRESS OF FIRST SEG. TO BUILD` are both genuine sites, and a plain `'SEG '`
# test misses the abbreviated forms.
SEGEVID = re.compile(r'\b(SEGMENT|SEGMENTS|SEG|SEGS|STE|STO|STL)\b')

# A shift of 4 is one hex digit, and CP converts and formats a lot of hex.
# `SLL Rn,4  ASSEMBLE NEXT DIGIT`, `SLDL R2,4  SAVE THE SIGNIFICANT 4 BITS`,
# `SRL R3,4  4 PLACES TO THE RIGHT`.  Also register-field and bit isolation,
# and DMKSCH's exponential smoothing -- `(15*OLD + NEW)/16` -- where the 16 is
# a filter weight and has no geometry in it at all.
NIBBLE = re.compile(
    r'\b(DIGIT|DIGITS|HEX|4 BITS|FOUR BITS|NIBBLE|PARITY|BIT INDEX|'
    r'PLACES|EBCDIC|DECIMAL|PRINTABLE|CHARACTER|REG|REGISTER|MASK BITS|'
    r'ISOLATE)\b|/16\b|\*16\b|15\*')
# PSW and interruption-code fields.  A System/370 BC-mode PSW packs the
# interruption code into bits 16-31, so a shift or mask of 16 there is a PSW
# field boundary.  Guests stay S/370 machines until M4, so these stay as they
# are and are not segment arithmetic.
INTCODE = re.compile(r'\b(INTERUPTION|INTERRUPTION|INT CODE|CSW|CC|COND|PSW)\b')
# 3270 buffer addressing splits a 12-bit address into two 6-bit characters, so
# a shift of 6 in a display module is a terminal-protocol field, not PTLSHFT.
GRAF3270 = re.compile(r'\b(3270|BUFFER|SBA|ADDRESS BYTE|SCREEN|SIX BIT|'
                      r'SIX BITS|ADDRCURS)\b|X.3F3F.|,X3F\b')
# The CORTABLE index idiom, and the reason a shift of 4 is so often innocent:
#
#     LR  R2,R12         a real address
#     SRL R2,12          -> page number        (4 KB pages, both architectures)
#     SLL R2,4           -> * 16               (16-byte entry, both)
#     AL  R2,ACORETBL    + table origin
#
# A CORTABLE entry is four fullwords in CORE.COPY and `CORE.XA0033DK` does not
# change it -- it converts the PAGTABLE and SEGTABLE DSECTs only.  Our own
# working I-163 fix proves the size independently: `SRL R7,8  REAL ADDRESS TO
# CORTABLE INDEX` is (addr>>12)<<4 collapsed, which is right only for a 16-byte
# entry.  So both halves of the idiom are architecture-independent and a bulk
# PAGSHFT 4->8 pass would corrupt all thirteen sites.
#
# The inverse appears too, and its comment misleads: DMKCPI's
# `SRL R11,4  GET NO OF PAGES  DIV BY 16` follows `SL R11,ACORETBL`, so it
# divides the table's BYTE SIZE by the entry length to get an entry count.  It
# is not pages-per-segment, which is what the words sound like.
CORTBL = re.compile(r'\b(ACORETBL|CORETBL|CORTABLE|CORFLAG|CORE TABLE|CORETABLE)\b')
PACKEDHW = re.compile(r'\bS[RL]L\s+R\d+,12\b|\bSRDL\s+R\d+,16\b')


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
    if re.search(r'\bS[RL][DL]?L\s+R\d+,4\b', code) \
            and not SEGEVID.search(code.upper()):
        if CORTBL.search(up):
            return 'cortable-entry NOT-A-SITE'
        if NIBBLE.search(code.upper()):
            return 'nibble-or-weight NOT-A-SITE'
    # The 64 KB mask class, which never reached these checks: both sites
    # are `N R1,=XL4'FFFF0000'  ZERO INTERUPTION CODE`, clearing the low
    # halfword of a System/370 BC-mode PSW, where the interruption code
    # lives.  Nothing to do with a segment mask.
    if (re.search(r"X?L?4?'0*FFFF0000'", code)
            and not SEGEVID.search(code.upper())
            and INTCODE.search(code.upper())):
        return 'psw-intcode NOT-A-SITE'
    # Window, not card: the first half of the pair (`SLL R6,6  SHIFT THEM INTO
    # THE RIGHT PLACE`) names nothing, while the cards around it say
    # `STRIP TO GET SIX BIT ADDR` and `PUT THE PIECES OF ADDR TOGETHER`.
    if (re.search(r'\bS[RL][DL]?L\s+R\d+,6\b', code)
            and not SEGEVID.search(code.upper())
            and GRAF3270.search(up)):
        return 'graf-3270 NOT-A-SITE'
    if re.search(r'\bS[RL][DL]?L\s+R\d+,16\b', code):
        # The card's OWN comment outranks the window.  Four rows were
        # misclassified NOT-A-SITE by window context while saying `SEGMENT` on
        # the card itself -- including `DMKPTR 00796000 ENDING SEGMENT ADDRESS`,
        # in the paging module, which is precisely where I-162 cost five days.
        # A nearby `SLL ,12` or a cylinder in a neighbouring card is weaker
        # evidence than the programmer's own word on the line in question.
        # The whole card, not a fixed comment column: a comment can start at
        # column 30 and `code[40:]` lands INSIDE the word -- which is how
        # `DMKPTR 00796000 ENDING SEGMENT ADDRESS` slipped through the first
        # version of this check.  A shift card's operand is `Rn,nn` and can
        # never contain these words, so searching the whole card is safe here.
        if not SEGEVID.search(code.upper()):
            if DASDGEOM.search(up):
                return 'dasd-field NOT-A-SITE'
            if PACKEDHW.search(up):
                return 'packed-halfword NOT-A-SITE'
            if INTCODE.search(code.upper()):
                return 'psw-intcode NOT-A-SITE'
    for name, syms in FAMILY:
        if any(s in up for s in syms):
            return name
    # Also the whole card past the operand, for the same reason: a fixed
    # column-40 comment slice truncates words that start at column 30.
    com = code[20:71].upper()
    for name, words in WORDS:
        if any(w in com for w in words):
            return name + '?'
    # The card says SEG/STE/STO/STL but no family matched: still segment work,
    # and these are the rows that matter most -- `DMKPTR 00793000 STE NO.` is
    # half of a matched pair with 00796000 and both need the same change.
    if SEGEVID.search(code.upper()):
        return 'segment'
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
    na = [r for r in rows if 'NOT-A-SITE' in r[5]]
    if na:
        import collections as _c
        print('-- %d of the REVIEW rows are classified NOT-A-SITE: the shift'
              % len(na))
        print('   amount is a FIELD WIDTH or an ENTRY SIZE that is the same in')
        print('   both architectures, so a bulk shift pass would corrupt them.')
        for k, n in sorted(_c.Counter(
                r[5].replace(' NOT-A-SITE', '') for r in na).items()):
            print('     %-16s %3d' % (k, n))
        print('   Each class was READ before it was named -- see the comments')
        print('   above each recognizer. That leaves %d rows to read.'
              % (v - len(na)))
        print()
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
