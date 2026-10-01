#!/usr/bin/env python3
"""Print the basic block around every flagged site, with its silent neighbours.

`I-124` concluded that the only defence against a converted field's *neighbours*
is to read the whole basic block around each flagged site, and `DMKBLD` proved
the point: 37 sites the assembler named, **46 it could not**, and the 46 included
`S R9,F4` reaching `PAGSWP` through an assumed four-byte gap and a single
`SRL R1,8` serving two strides that happened to agree at 16.

"Read the block" is discipline, and discipline is what this project keeps finding
it cannot rely on.  So this tool does the reading mechanically: it takes the
assembler's flagged list, finds each site in the source, widens to the enclosing
basic block, and marks the lines that match a pattern already known to be a
silent conversion site.  What is left is a page to read per module instead of a
module.

A **marked** line is a candidate, never a verdict.  Three of the patterns below
exist because a specific site taught them, and the list is therefore a record of
what has already been missed rather than a theory of what can be:

    F4            `S R8,F4  BACK UP TO SWPTABLE POINTER` -- PAGSWP is four
                  bytes below PAGCORE, and PAGFREE moved it (I-130)
    F16           the PAGTABLE header size in DMKATS x6 and DMKBLD x1 -- and
                  ALSO pages-per-segment at DMKBLD 00373000, where it converts
                  the other way.  Same spelling, opposite answers.
    self-strip    `LA Rn,0(,Rn)`, which DMKPGS 00303000 documents as
                  `24 BIT ADDRESSING` (I-126, I-128)
    branch        a branch within two lines of a flagged comparison.  Converting
                  `CLI SEGPAGE+3,SEGINV` to `TM SEGPTO+3,SEGINVAL` inverts the
                  sense, and the branch reads perfectly well on its own.

    python3 block.py <build-log> --mod DMKXXX [--marked]
"""
import collections
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

SRC = '/home/claude/vmce/source/cp'

# A basic block ends at a label in the name field or at an unconditional branch.
LABEL = re.compile(r'^[A-Z@#$][A-Z@#$0-9]{0,7}\s+\S')
UNCOND = re.compile(r'^\s+(B|BR|BAL|BALR|BCT|CALL|GOTO|EXIT|RETURN)\s')
BRANCH = re.compile(r'^\s+(B[A-Z]{0,3})\s+\S')

MARKS = [
    ('F4', re.compile(r'^\s+[SA]L?\s+R?\d+,F4\b'),
     'PAGSWP sits four bytes below the page table -- PAGFREE moved it'),
    ('F16', re.compile(r'^\s+[SA]L?\s+R?\d+,F16\b'),
     'the PAGTABLE header size, OR pages-per-segment -- read which'),
    ('F2', re.compile(r'^\s+[SA]L?\s+R?\d+,F2\b'),
     'a halfword PTE stride; a fullword steps by 4'),
    ('strip', re.compile(r'^\s+LA\s+R?(\d+),0\(,?R?\1\)'),
     'strips the high byte, where nothing lives any more (I-126/I-128)'),
    # Matching masks by VALUE was a mistake the synthetic log caught: the
    # pattern required six hex digits and `N R0,=A(X'FFF0')  CHECK FOR REAL PAGE
    # ALLOCATED` has four, so the one mask in the sample went unmarked.  Match by
    # OPCODE instead -- every mask over a DAT field changes, whatever its value,
    # so the opcode is the reliable signal and the value is not.
    ('mask', re.compile(r"^\s+(N|NR|O|OR|X|XR|NI|OI|XI)\s+\S+,"),
     'a mask or flag update -- every one over a DAT field moves'),
    ('shift', re.compile(r'^\s+(S[RL]L|SRDL|SLDL)\s+R?\d+,(4|8|16|20|24)\b'),
     'a segment/page stride -- R01-SHIFT-SITES has the table'),
    ('step16', re.compile(r'^\s+LA\s+R?\d+,16\(,?R?\d*\)'),
     'a PTE value stepping by one page; ESA/390 steps by 4096'),
    # Any PARTIAL byte mask, not just B'0111'.  The synthetic log had
    # `ICM R0,B'0110',SEGPAGE+1` go unmarked because the pattern wanted the
    # three-byte form; a partial access to a packed field is the thing of
    # interest, and B'0111' is only its most common shape (I-132).
    ('partial', re.compile(r"^\s+(ICM|STCM|CLM)\s+R?\d+,B'[01]{4}'"),
     "a partial-byte access to a packed field; B'0111' is 24 bits (I-132)"),
    ('vmseg', re.compile(r'^\s+(L|IC|STC|CLI|TM)\s+R?\d*,?VMSEG\b'),
     'the STD: origin bits 1-19, length bits 25-31 (I-128/I-129)'),
]


def source(mod):
    path = os.path.join(SRC, '%s.ASSEMBLE' % mod)
    out = []
    for line in open(path, errors='replace'):
        out.append((line[72:80].strip(), line[:72].rstrip()))
    return out


def blocks(lines, sites):
    """{site index: (start, end)} widened to the enclosing basic block."""
    spans = {}
    for i in sites:
        a = i
        while a > 0:
            prev = lines[a - 1][1]
            if LABEL.match(lines[a][1]) or (prev.strip()
                                            and UNCOND.match(prev)):
                break
            a -= 1
        b = i
        while b < len(lines) - 1:
            if UNCOND.match(lines[b][1]) or LABEL.match(lines[b + 1][1]):
                break
            b += 1
        spans[i] = (a, b)
    return spans


def main():
    args = sys.argv[1:]
    if not args or '--mod' not in args:
        print(__doc__)
        return 2
    log = args[0]
    mod = args[args.index('--mod') + 1]
    only_marked = '--marked' in args

    # Sites come from the assembler when a log has them and from the sweep when
    # it does not.  Without this the tool is unusable exactly when it is most
    # wanted -- before a build, while writing the deck -- and `asmerr.py` showed
    # the two lists agree on all 176 sites with no holes, so the sweep is a sound
    # stand-in.  `--sweep` forces it; a log with nothing in it falls back.
    import asmerr
    import dattab
    want, origin = set(), 'the assembler'
    if '--sweep' not in args:
        flags, _ = asmerr.harvest(log)
        want = {f.seq for f in flags
                if f.mod == mod and asmerr.symbols(f) and f.seq}
    if not want:
        want = {s.seq for s in dattab.scan(dattab.SRC)
                if s.mod == mod and s.verdict != 'ok' and s.seq}
        origin = "dattab.py's sweep (the log has no diagnostics for %s)" % mod
    if not want:
        print('### no site for %s in either the log or the sweep' % mod)
        return 2

    lines = source(mod)
    # The log right-justifies the sequence in eight columns, so it comes back
    # without leading zeros -- `339000` where the source holds `00339000`.
    # Keying on the string found nothing for three modules and reported it as
    # "0 sites ... every change is one the assembler already named", which is a
    # clean-looking lie.  deckchk.py was unaffected because it compared ints.
    idx = {int(seq): i for i, (seq, _) in enumerate(lines) if seq.isdigit()}
    sites = sorted(idx[int(s)] for s in want if s.isdigit() and int(s) in idx)
    spans = blocks(lines, sites)

    # Merge overlapping blocks: two flagged sites in one block is one read.
    merged, cur = [], None
    for i in sites:
        a, b = spans[i]
        if cur and a <= cur[1]:
            cur = (cur[0], max(cur[1], b), cur[2] + [i])
        else:
            if cur:
                merged.append(cur)
            cur = (a, b, [i])
    if cur:
        merged.append(cur)

    marks = collections.Counter()
    print('%s: %d site(s) from %s, in %d basic block(s)'
          % (mod, len(sites), origin, len(merged)))
    print()
    for a, b, hits in merged:
        body = []
        for i in range(a, b + 1):
            seq, text = lines[i]
            if not text.strip() or text.lstrip().startswith('*'):
                continue
            tag = ''
            for name, pat, why in MARKS:
                if pat.search(text) and i not in hits:
                    tag, marks[name] = name, marks[name] + 1
                    break
            flag = '>>' if i in hits else ('%-6s' % tag if tag else '      ')
            body.append((flag, seq, text, tag))
        if only_marked and not any(t for _, _, _, t in body):
            continue
        print('--- block at %s' % lines[a][0])
        for flag, seq, text, _ in body:
            print('  %-6s %-9s %s' % (flag, seq, text[:58]))
        print()

    print('Marked neighbours by pattern:')
    if not marks:
        print('  none -- which is a result, not a pass: it means every change in')
        print('  this module is one the assembler already named.')
    for name, n in marks.most_common():
        why = next(w for nm, _, w in MARKS if nm == name)
        print('  %-8s %3d  %s' % (name, n, why))
    print()
    print('>> is a site from %s.' % origin)
    print('Everything else in these blocks')
    print('is a line no diagnostic reaches, marked or not -- the marks are a')
    print('record of what has already been missed, not a theory of what can be.')
    return 0


if __name__ == '__main__':
    sys.exit(main())
