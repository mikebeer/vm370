#!/usr/bin/env python3
"""Enumerate and classify every access to CP's DAT table fields.

`STE-DESIGN.md` step 1 said: *"`CORE.COPY`'s `SEGTABLE` and `PAGTABLE`, with
`SEGINV` moved.  Nothing executes differently yet; this makes the symbols mean
the right thing."*

**That was wrong, and this tool exists because measuring it showed so.**  The
page-table entry goes from a **halfword** to a **fullword**, and CP reaches it
with 13 `LH` and 5 `STH` instructions.  Change the DSECT alone and every one of
those silently accesses the wrong two bytes of a fullword -- and **assembles
clean**, because `LH` on a fullword field is perfectly legal assembler.  That is
the shape of `I-116` again: two halves individually correct, in different files,
with no diagnostic anywhere.  At 86 `PAGCORE` references it is `I-116` with two
orders of magnitude more places to hide.

So the first step is not an edit.  It is this sweep, used as the checklist for the
edit and re-run afterwards to prove the class is closed -- the discipline that
closed `I-109` and `I-114`.

## What it classifies, and on what authority

Field layouts from `CORE.COPY`; target layouts from **SA22-7201-08**:

    STE   ┌─┬─────────────────────────┬─┬─┬────┐   bit 0 MUST be zero
          │ │    Page-Table Origin    │I│C│PTL │   PTO 1-25, I 26, C 27, PTL 28-31
          └─┴─────────────────────────┴─┴─┴────┘

    PTE   ┌─┬───────────────────┬─┬─┬─┬─┬────────┐  PFRA 1-19, I 21, P 22
          │ │       PFRA        │ │I│P│ │        │  bits 0,20,23 zero
          └─┴───────────────────┴─┴─┴─┴─┴────────┘  bits 24-31 IGNORED

That last line is load-bearing: **bits 24-31 of a PTE are ignored by the
hardware**, so CP's private `PAGREF` flag has somewhere safe to live in the
fullword.  It does not have to be found a new home outside the entry.

## A documented undesigned item that turns out not to exist

`WHAT-31BIT-NEEDS.md` lists the `SEGMIG`/`SEGENQ` collision with ESA/390 STE bits
as undesigned item 2.  `SEGMIG` is `X'10'`, which is the **C (common segment)**
bit, and that half of the problem is not real: **`SEGMIG` is defined in
`CORE.COPY` and referenced nowhere else in the tree** -- not in a module, not in
a `COPY`, not in a `MACRO`.  It is a dead symbol.  Only `SEGENQ` is live, with
**two** references, both in `DMKBLD`.

    python3 dattab.py [source-dir] [--all] [--module MOD]

Verdicts:

  **CHANGE**  the instruction is wrong after the format change and will not say so
  **REVIEW**  depends on a length or mask that has to be read
  **ok**      unaffected: an address, a `USING`, or a fullword access that stays one
"""
import collections
import os
import re
import sys

SRC = '/home/claude/vmce/source/cp'

# Bit positions that MOVE, with their old and new values in the named byte.
MOVED = {
    'SEGINV':   ("X'01' at SEGPAGE+3 (bit 31, inside PTL)",
                 "X'20' at SEGPAGE+3 (bit 26, the architected I bit)"),
    'SEGENQ':   ("X'40' at SEGPAGE+3 (bit 25, the lowest PTO bit)",
                 "unchanged -- only read when the pointer is zero, so only "
                 "with I set, where the hardware ignores bit 25"),
    'SEGPLEN':  ("bits 0-3, which must become zero",
                 "PTL at bits 28-31 -- same VALUE, 15 for a full table"),
    'PAGINVAL': ("X'08' at PAGCORE+1 (halfword bit 12)",
                 "X'04' at PAGCORE+2 (fullword bit 21)"),
    'PAGREF':   ("X'01' at PAGCORE+1",
                 "X'01' at PAGCORE+3 -- bits 24-31 are IGNORED by the hardware"),
}

HALFWORD = {'LH', 'STH', 'AH', 'SH', 'CH', 'MH'}
ADDRONLY = {'LA', 'USING', 'DROP', 'EQU', 'ORG'}
LENGTHY = {'MVC', 'CLC', 'XC', 'NC', 'OC', 'MVCL'}
MASKED = {'ICM', 'STCM', 'CLM'}
BITWISE = {'TM', 'OI', 'NI', 'XI', 'MVI', 'CLI'}

FIELDS = ['SEGPAGE', 'SEGPLEN', 'SEGINV', 'SEGMIG', 'SEGENQ',
          'PAGCORE', 'PAGINVAL', 'PAGREF', 'PAGTSWP', 'PAGBMP',
          # SHRTABLE's per-segment word is an STE in all but name.  CORE.COPY
          # does not define it and no symbol links the two -- only a COMMENT in
          # SHRTABLE.COPY says so: "THE ENTRY IS THE SAME AS 'S*1 SEGPAGE' IN
          # THE SEGTABLE".  So renaming SEGPAGE does not reach its 59 sites, and
          # the first version of this sweep could not see them at all.  Third
          # instance of I-116's shape: a field and its twin in different files
          # with nothing but prose joining them.
          'SHRPAGE']

# Most specific first.  A line naming both a container and a flag within it is a
# site for the FLAG: that is what the instruction is actually about, and what
# decides whether the bit position moves.
SPECIFICITY = ['SEGINV', 'SEGMIG', 'SEGENQ', 'SEGPLEN', 'PAGINVAL', 'PAGREF',
               'PAGTSWP', 'PAGBMP', 'SEGPAGE', 'PAGCORE', 'SHRPAGE']

Site = collections.namedtuple('Site', 'mod seq op field text verdict why')


def classify(op, field, text):
    """CHANGE / REVIEW / ok, and the reason."""
    if op in ADDRONLY:
        if field == 'PAGCORE' and re.search(r'\b2\(', text):
            return 'CHANGE', 'steps by 2 -- a fullword entry steps by 4'
        return 'ok', 'address or declaration only'

    if field == 'PAGCORE' and op in HALFWORD:
        return 'CHANGE', ('halfword access to what becomes a fullword -- '
                          'assembles clean, reads the wrong two bytes')
    if field in ('PAGINVAL', 'PAGREF') and op in BITWISE:
        return 'CHANGE', 'bit moves: %s -> %s' % MOVED[field]
    if field == 'SEGINV' and op in BITWISE:
        return 'CHANGE', 'bit moves: %s -> %s' % MOVED[field]
    if field == 'SEGPLEN':
        return 'CHANGE', 'bits 0-3 must be vacated: %s -> %s' % MOVED[field]
    if field == 'SEGENQ':
        return 'REVIEW', MOVED['SEGENQ'][1]
    if field == 'SHRPAGE':
        return ('CHANGE' if op not in ADDRONLY else 'ok',
                'an STE in all but name -- same format change, and no symbol '
                'links it to SEGPAGE')
    if field in ('PAGTSWP', 'PAGBMP'):
        return 'CHANGE', ('derived from 16 entries per segment; a 1 MB segment '
                          'has 256, and each entry doubles in width')
    if op in LENGTHY:
        return 'REVIEW', 'explicit length -- may encode 16 entries or 2 bytes'
    if op in MASKED:
        if field in ('SEGPAGE', 'PAGCORE'):
            return 'CHANGE', ('byte mask over the entry: the S/370 page-table '
                              'origin is bytes 1-3, the ESA/390 one is bits 1-25')
        return 'REVIEW', 'byte mask over a field whose bytes move'
    if field == 'SEGPAGE' and op in BITWISE:
        return 'CHANGE', 'byte-level access to an entry whose bit meanings move'
    if field == 'SEGPAGE' and op in ('L', 'ST', 'LR', 'A', 'S', 'C', 'N', 'O'):
        return 'ok', 'fullword access to a field that stays a fullword'
    if field == 'PAGCORE' and op in ('L', 'ST'):
        return 'ok', 'already a fullword access'
    return 'REVIEW', 'unclassified -- read it'


def scan(src):
    sites = []
    import glob
    files = (sorted(glob.glob(os.path.join(src, 'DMK*.ASSEMBLE')))
             + sorted(glob.glob(os.path.join(src, '*.COPY')))
             + sorted(glob.glob(os.path.join(src, '*.MACRO'))))
    for f in files:
        mod = os.path.basename(f).split('.')[0]
        for line in open(f, errors='replace'):
            text, seq = line[:72].rstrip(), line[72:80].strip()
            if not text or text.lstrip().startswith('*'):
                continue
            # One LINE is one site.  A line reading `TM SEGPAGE+3,SEGINV`
            # mentions two fields but is a single instruction with a single
            # verdict, and counting it twice inflates the work by a third.
            # The flag is the specific thing being tested, so the flag wins.
            present = [f for f in FIELDS if re.search(r'\b%s\b' % f, text)]
            if not present:
                continue
            field = min(present, key=lambda f: SPECIFICITY.index(f))
            m = re.match(r'\S*\s+([A-Z]{1,5})\s', text)
            op = m.group(1) if m else '?'
            v, why = classify(op, field, text)
            sites.append(Site(mod, seq, op, field, text.strip(), v, why))
    return sites


def main():
    src = sys.argv[1] if len(sys.argv) > 1 and not sys.argv[1].startswith('-') else SRC
    args = sys.argv[1:]
    only = args[args.index('--module') + 1] if '--module' in args else None
    sites = [s for s in scan(src) if not only or s.mod == only]

    by_v = collections.Counter(s.verdict for s in sites)
    print('%d references to CP\'s DAT table fields, %d modules\n'
          % (len(sites), len({s.mod for s in sites})))

    print('%-9s %7s %7s %5s   %s' % ('MODULE', 'CHANGE', 'REVIEW', 'ok', 'FIELDS'))
    mods = collections.defaultdict(collections.Counter)
    flds = collections.defaultdict(set)
    for s in sites:
        mods[s.mod][s.verdict] += 1
        flds[s.mod].add(s.field)
    for mod in sorted(mods, key=lambda m: -mods[m]['CHANGE']):
        c = mods[mod]
        print('%-9s %7d %7d %5d   %s'
              % (mod, c['CHANGE'], c['REVIEW'], c['ok'],
                 ' '.join(sorted(flds[mod]))))
    print('%-9s %7d %7d %5d' % ('TOTAL', by_v['CHANGE'], by_v['REVIEW'], by_v['ok']))

    print('\nBy field:')
    fv = collections.defaultdict(collections.Counter)
    for s in sites:
        fv[s.field][s.verdict] += 1
    for f in FIELDS:
        c = fv[f]
        tot = sum(c.values())
        note = ''
        if tot == 0:
            note = '  <- DEFINED BUT NEVER REFERENCED'
        print('  %-9s %3d total: %d change, %d review, %d ok%s'
              % (f, tot, c['CHANGE'], c['REVIEW'], c['ok'], note))

    if '--all' in args:
        print('\nEvery site needing work:')
        for s in sites:
            if s.verdict == 'ok':
                continue
            print('  %-7s %-6s %-8s %-6s %s' % (s.verdict, s.mod, s.seq, s.op,
                                                s.text[:52]))
            print('          %s' % s.why[:100])
    else:
        print('\n(--all lists every CHANGE and REVIEW site with its reason)')

    print('\nEvery one of these assembles clean either way.  That is the point:')
    print('an LH on a fullword field is legal assembler, so the only thing that')
    print('reports this class is a sweep.  I-116 was the same shape with one site.')
    return 0


if __name__ == '__main__':
    sys.exit(main())
