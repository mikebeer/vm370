#!/usr/bin/env python3
"""Enumerate the conversion sites that name no field, so no instrument finds them.

The assembler finds a site that NAMES a renamed symbol.  `dattab.py` finds a site
whose LINE mentions a DAT field.  `block.py` finds a site that SITS NEAR one.
`DMKBLD` measured what is left over: **37 sites the assembler named and 46 it
could not**, and `I-134` is the case that broke all three instruments at once --
33 `S Rn,F16` sites that reach the page-table header by a literal, one of them in
`DMKVAT`, which has no flagged site for `block.py` to anchor on.

So this is the fourth instrument, and the only one that works by **idiom**.  Each
class below is here because a specific site taught it, and each carries the test
that distinguishes it from the identical-looking instruction that must NOT change:

    F16-header   `S Rn,F16  BACKUP TO HEADER` -- 33 real, and 15 look identical
                 and are `RCWTASK` headers, a CORTABLE entry, or (DMKBLD
                 00373000) pages-per-segment, which converts the OTHER way.
                 Test: a DAT field within five lines of the register adjusted.
    F4-swap      `S Rn,F4` reaching PAGSWP four bytes below the page table.
    strip        `LA Rn,0(,Rn)`, which DMKPGS documents as `24 BIT ADDRESSING`.
                 M2 (I-126), not M1 -- except on a VMSEG value, where the bits
                 that stop being ignored are the LOW ones and it is M1 (I-128).
    vmseg-load   `L Rn,VMSEG` used as an address: the STL must be masked off.
    vmseg-len    `IC Rn,VMSEG` reading the length from byte 0, now byte 3.
    pack3        `ICM/STCM/CLM ...,B'0111'` -- a three-byte address field.  M5
                 (I-132), and a structure change rather than an instruction one.

**Classification is by context, never by comment.**  The first pass at `I-134`
read the comments for the word HEADER and mislabelled three sites in two
modules, because `DMKUNT`'s `BACK OFF 16 TO 1ST HEADER STA` is an `RCWTASK`.
A comment says what someone meant; the surrounding code says what the register
holds.

    python3 idiom.py [--class NAME] [--milestone M1|M2|M5] [--sites]
"""
import collections
import glob
import os
import re
import sys

SRC = '/home/claude/vmce/source/cp'

# A DAT field anywhere in the window makes a register a table pointer.  Five
# lines each way: measured against the 48 F16 sites, where it separates the 33
# from the 15 with no false positives in either direction.
WINDOW = 5
DATF = re.compile(r'\b(PAGCORE|PAGPFRA|PAGSTMP|PAGACT|PAGTOT|PAGSHR|PAGSWP'
                  r'|PAGTSWP|PAGBMP|PAGTABLE|PAGINVAL|PAGINV|PAGREF'
                  r'|SEGPAGE|SEGPTO|SEGPLEN|SEGPTL|SEGINV|SEGINVAL|SEGTABLE'
                  r'|SWPTABLE|SWPFLAG|SWPVM|SHRPAGE)\b')
VMSEG = re.compile(r'\bVMSEG\b(?!DSP)')

Class = collections.namedtuple('Class', 'name pat need milestone why')

CLASSES = [
    Class('F16-header', re.compile(r'^\s+(S|SL|A|AL)\s+R?\d+,F16\b'), 'dat', 'M1',
          'the page-table header offset; PAGFREE moves it from 16 to 24'),
    Class('F4-swap', re.compile(r'^\s+(S|SL|A|AL)\s+R?\d+,F4\b'), 'dat', 'M1',
          'PAGSWP sits four bytes below the page table'),
    Class('F2-stride', re.compile(r'^\s+(A|AL|S|SL)\s+R?\d+,F2\b'), 'dat', 'M1',
          'a halfword PTE stride; a fullword steps by 4'),
    Class('vmseg-load', re.compile(r'^\s+L\s+R?\d+,VMSEG\b'), None, 'M1',
          'the STD used as an address: STL is bits 25-31 and must be masked'),
    Class('vmseg-len', re.compile(r'^\s+(IC|STC|CLI|TM)\s+R?\d*,?VMSEG\b'), None, 'M1',
          'the length was byte 0 and is now the low seven bits of byte 3'),
    Class('strip', re.compile(r'^\s+LA\s+R?(\d+),0\(,?R?\1\)'), 'any', 'M2',
          'strips the high byte, where nothing lives in AMODE 31'),
    Class('pack3', re.compile(r"^\s+(ICM|STCM|CLM)\s+R?\d+,B'0111'"), 'any', 'M5',
          'a three-byte address field -- 24 bits by construction'),
]

Site = collections.namedtuple('Site', 'cls mod seq text why')

# Sites the context test accepts and reading rejects.  Listed rather than
# silently dropped: an exception with a reason is a fact about the source, an
# exception without one is a tuned threshold.
EXCEPTIONS = {
    ('F16-header', 'DMKBLD', '00373000'):
        'pages per segment, not the header -- becomes 256, the OTHER direction',
}

# Counts here are of sites NEAR DAT CODE, which is this conversion's scope.  The
# whole-tree totals are larger and belong to the milestones that own them:
# I-126 counts 215 `strip` sites in 79 modules and I-132 counts 278 `pack3`
# sites in 81.  Quoting this tool's numbers as the milestone totals would
# understate both by a factor of seven.
WHOLE_TREE = {'strip': (215, 79, 'I-126'), 'pack3': (278, 81, 'I-132')}


def scan():
    sites, excepted = [], []
    for path in sorted(glob.glob(os.path.join(SRC, 'DMK*.ASSEMBLE'))):
        mod = os.path.basename(path).split('.')[0]
        raw = list(open(path, errors='replace'))
        lines = [l[:72].rstrip() for l in raw]
        seqs = [l[72:80].strip() for l in raw]
        live = [i for i, t in enumerate(lines)
                if t.strip() and not t.lstrip().startswith('*')]
        liveset = set(live)
        for i in live:
            t = lines[i]
            for c in CLASSES:
                if not c.pat.search(t):
                    continue
                if c.need:
                    near = [lines[j] for j in range(max(0, i - WINDOW),
                                                   min(len(lines), i + WINDOW + 1))
                            if j in liveset]
                    joined = ' '.join(near)
                    if c.need == 'dat' and not DATF.search(joined):
                        break
                    if c.need == 'any' and not (DATF.search(joined)
                                                or VMSEG.search(joined)):
                        break
                key = (c.name, mod, seqs[i])
                if key in EXCEPTIONS:
                    excepted.append((key, EXCEPTIONS[key]))
                else:
                    sites.append(Site(c.name, mod, seqs[i], t.strip(), c.why))
                break
    return sites, excepted


def main():
    args = sys.argv[1:]
    only = args[args.index('--class') + 1] if '--class' in args else None
    ms = args[args.index('--milestone') + 1] if '--milestone' in args else None
    sites, excepted = scan()
    bym = {c.name: c.milestone for c in CLASSES}
    if only:
        sites = [s for s in sites if s.cls == only]
    if ms:
        sites = [s for s in sites if bym[s.cls] == ms]

    print('Conversion sites found by IDIOM, not by field name.')
    print('None of these is reported by the assembler, and only the ones that')
    print('happen to sit beside a flagged site are reported by block.py.')
    print()
    byc = collections.Counter(s.cls for s in sites)
    print('%-12s %5s %7s  %s' % ('CLASS', 'SITES', 'LANDS', 'WHY'))
    for c in CLASSES:
        if c.name not in byc:
            continue
        mods = len({s.mod for s in sites if s.cls == c.name})
        print('%-12s %5d %7s  %s' % (c.name, byc[c.name], c.milestone, c.why))
        print('%-12s %5s %7s  in %d modules' % ('', '', '', mods))
    print('%-12s %5d' % ('TOTAL', len(sites)))
    for cls, (n, mods, iss) in sorted(WHOLE_TREE.items()):
        if cls in byc:
            print()
            print('  (%s: %d here, near DAT code.  %s counts %d in %d modules'
                  % (cls, byc[cls], iss, n, mods))
            print('   tree-wide -- that is the milestone total, this is the scope.)')
    if excepted:
        print()
        print('Excepted by reading, with the reason:')
        for (cls, mod, seq), why in excepted:
            print('  %-12s %-8s %-9s %s' % (cls, mod, seq, why))

    print()
    m1 = [s for s in sites if bym[s.cls] == 'M1']
    print('%d of these are LIVE IN M1 -- they must be converted before a clean'
          % len(m1))
    print('IPL, and nothing will report them if they are not.')

    if '--sites' in args:
        print()
        for s in sorted(sites, key=lambda s: (s.cls, s.mod, s.seq)):
            print('  %-12s %-8s %-9s %s' % (s.cls, s.mod, s.seq, s.text[:46]))

    print()
    print('Classification is by CONTEXT, never by comment.  The first pass at')
    print("I-134 read comments for the word HEADER and mislabelled DMKUNT's")
    print("`BACK OFF 16 TO 1ST HEADER STA`, which is an RCWTASK.  A comment says")
    print('what someone meant; the code around it says what the register holds.')
    return 0


if __name__ == '__main__':
    sys.exit(main())
