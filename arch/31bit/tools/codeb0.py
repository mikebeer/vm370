#!/usr/bin/env python3
"""Check every DAT constant in the tree against `DMKVAT`'s own geometry table.

`I-188` cost a build cycle to a constant I derived: `X'00F00000'` for the 1 MB
segment-number mask, reasoned out as "bits 8-11" and true only of a 16 MB
machine.  The right value was already in the source, three thousand cards away,
in the table `DMKVAT` uses to shadow guest page tables.  That table has one row
per `CR0` DAT code, and the eight codes are a matrix of page size by segment
size by page-table-entry width:

    X'40' - SMALL PAGE, SMALL SEG, HALFWORD ENTRIES
    ...
    X'B0' - LARGE PAGE, LARGE SEG, FULLWORD ENTRIES

`CODEB0` is 4 KB pages, 1 MB segments and a fullword PTE -- which is this
project's target architecture, exactly and by name.  So its row is the
authority, and every geometry constant we write should agree with it:

    CODEB0   DC    X'000FF000'            page-number mask
             DC    X'7FF00000'            segment-number mask
             DC    X'08',X'06'            page-invalid bit, must-be-zero bits
             DC    H'10',H'18',H'4'       PAGSHFT, SEGSHFT, PTEINCR
             DC    H'127',H'1024',H'64'   MAXSEGS, PAGTLEN, PAGINCR

What makes this a CHECK rather than a note is that the other seven rows are the
wrong answers, spelled out.  `X'00F00000'` is not a value nobody wrote down --
it is `CODE50`'s and `CODE90`'s segment mask, the **halfword-entry** rows, a
24-bit truncation of the same geometry.  `X'0000F000'` is `CODE80`'s page mask.
`X'00FF0000'` is `CODE80`'s segment mask, the one every site started from.  So a
constant can be named: not merely "wrong" but "this is CODE90's value, and you
want CODEB0's".

The table is read from the source rather than hardcoded here, so if a deck ever
converts `DMKVAT` the check converts with it.

    python3 codeb0.py              # every disagreement, by module
    python3 codeb0.py --table      # the eight rows as parsed
    python3 codeb0.py --ours       # only cards carrying an XAnnnnDK identifier
"""
import glob
import os
import re
import sys

import applied

OURS = re.compile(r'^XA\d{4}DK$')
HEX = re.compile(r"X'([0-9A-F]{8})'")
ROW = re.compile(r'^(CODE[0-9A-F]0)\s+DC\s+')
DCX = re.compile(r"^\s+DC\s+X'([0-9A-F]{8})'")

# What each of the six words in a row means, in order.
MEANING = ['page-number mask', 'segment-number mask']

# The three halfwords after the two flag bytes, and then the three after that.
HALF = re.compile(r"^\s+DC\s+H'(\d+)',H'(\d+)',H'(\d+)'")
SHIFTNAME = ['PAGSHFT', 'SEGSHFT', 'PTEINCR']
LENNAME = ['MAXSEGS', 'PAGTLEN', 'PAGINCR']
SHIFTOP = re.compile(r'\b(SRL|SLL|SRA|SLA|SRDL|SLDL|SRDA|SLDA)\s+R\d+,(\d+)')


def table():
    """The eight rows of DMKVAT's geometry table, from the source."""
    cards = applied.assembled('DMKVAT')
    rows = {}
    cur = None
    for seq, text in cards:
        c = text[:71]
        if c.startswith('*'):
            continue
        m = ROW.match(c)
        if m:
            cur = m.group(1)
            rows[cur] = []
        if cur is None:
            continue
        h = DCX.match(c) or (HEX.search(c) if ROW.match(c) else None)
        if ROW.match(c):
            h = HEX.search(c)
        if h and len(rows[cur]) < 2:
            rows[cur].append((h.group(1), seq))
        # A row ends at its DS 5H filler.
        if 'DS' in c and '5H' in c:
            cur = None
    return rows


def halfwords():
    """The two H'a',H'b',H'c' triples of each row: shifts, then lengths."""
    cards = applied.assembled('DMKVAT')
    rows = {}
    cur = None
    for seq, text in cards:
        c = text[:71]
        if c.startswith('*'):
            continue
        m = ROW.match(c)
        if m:
            cur = m.group(1)
            rows[cur] = []
        if cur is None:
            continue
        h = HALF.match(c)
        if h and len(rows[cur]) < 2:
            rows[cur].append(tuple(int(g) for g in h.groups()))
        if 'DS' in c and '5H' in c:
            cur = None
    return rows


def main():
    rows = table()
    if '--table' in sys.argv:
        for name in sorted(rows):
            vals = ' '.join(f"X'{v}'" for v, _ in rows[name])
            print(f'  {name}  {vals}')
        return 0

    b0 = [v for v, _ in rows.get('CODEB0', [])]
    if len(b0) < 2:
        print('### CODEB0 not parsed -- has DMKVAT moved?  Run --table.')
        return 1
    page_ok, seg_ok = b0[0], b0[1]
    print(f"CODEB0, the authority: page mask X'{page_ok}', "
          f"segment mask X'{seg_ok}'")

    # Every 8-digit hex constant that appears as a mask in ANY row is a
    # geometry constant, and only CODEB0's two are right for us.
    known = {}
    for name in rows:
        for i, (v, _) in enumerate(rows[name]):
            known.setdefault(v, []).append(
                f'{name} {MEANING[i] if i < len(MEANING) else "field %d" % i}')
    wrong = {v: w for v, w in known.items() if v not in (page_ok, seg_ok)}
    print(f'{len(wrong)} constant(s) in the other rows are the wrong answers, '
          f'named:')
    for v in sorted(wrong):
        print(f"  X'{v}'  {'; '.join(wrong[v])}")
    print()

    # The shift counts, the same way.  CODE80's PAGSHFT of 11 is the S/370
    # page shift that geomchk's PROVEN rows keep finding; naming it as CODE80's
    # turns "this looks wrong" into "this is the halfword-PTE row's value".
    hw = halfwords()
    if 'CODEB0' in hw and len(hw['CODEB0']) == 2:
        shifts, lens = hw['CODEB0']
        print()
        print('CODEB0 shifts: ' + ', '.join(
            f'{n}={v}' for n, v in zip(SHIFTNAME, shifts)))
        print('CODEB0 lengths: ' + ', '.join(
            f'{n}={v}' for n, v in zip(LENNAME, lens)))
        badshift = {}
        for name, pair in hw.items():
            if name == 'CODEB0' or len(pair) < 1:
                continue
            for i, v in enumerate(pair[0][:2]):      # PAGSHFT, SEGSHFT only
                if v not in shifts[:2]:
                    badshift.setdefault(v, []).append(
                        f'{name} {SHIFTNAME[i]}')
        print('shift counts belonging to other rows: ' + ', '.join(
            f'{v} ({"; ".join(w)})' for v, w in sorted(badshift.items())))
        print()

    only_ours = '--ours' in sys.argv
    mods = sorted({os.path.basename(p).split('.')[0]
                   for p in glob.glob(applied.SRC + '/DMK*')})
    hits = 0
    for mod in mods:
        if mod == 'DMKVAT':
            continue          # the table itself, and the guest rows must stay
        try:
            cards = applied.assembled(mod)
        except Exception:
            continue
        out = []
        for seq, text in cards:
            c = text[:71]
            if c.startswith('*'):
                continue
            ident = text[63:71].strip() if len(text) > 63 else ''
            mine = bool(OURS.match(ident))
            if only_ours and not mine:
                continue
            for v in HEX.findall(c):
                if v in wrong:
                    out.append((seq, c.rstrip(), v, mine))
        if out:
            print(f'  {mod}')
            for seq, c, v, mine in out:
                tag = 'OURS' if mine else '    '
                print(f'    {seq:08d} {tag} {c}')
                print(f'             -> X\'{v}\' is {"; ".join(wrong[v])}')
                hits += 1
    print()
    print(f'-- {hits} card(s) carry a constant from a row other than CODEB0.')
    print('   A hit is not automatically a defect: DASD cylinder arithmetic')
    print('   and guest-geometry code legitimately use these values, and')
    print('   SEGMASK/PAGEMSK defaults belong to the S/370 guest path.  It is')
    print('   a card to READ, which is all I-188 ever needed.')
    return 0


if __name__ == '__main__':
    sys.exit(main())
