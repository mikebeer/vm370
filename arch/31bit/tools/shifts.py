#!/usr/bin/env python3
"""Enumerate the hard-coded shift amounts that encode CP's page and segment
geometry.

R-01, the only weight-9 risk in the register. Seventy literal shift amounts
across twelve modules encode the 64 KB-segment, 16-pages-per-segment, 2 KB-key
geometry as bare numbers. No symbol rename touches them, no field-name search
finds them, and a missed one does not fail: it produces a plausible translation
to the wrong page.

The mitigation is to give each one a name BEFORE changing any geometry, so the
change has a single definition point. This tool produces the worklist for that,
site by site, with the module's own comment as the evidence for what each shift
means.

    python3 shifts.py /path/to/vmce/source/cp            # summary
    python3 shifts.py /path/to/vmce/source/cp --table    # markdown, per site
    python3 shifts.py /path/to/vmce/source/cp --all      # every module, not just the twelve

CP source is column-sensitive: 1-8 label, 10-14 operation, 16-71 operands then
comment, 73-80 sequence and change id.  Only columns 1-71 are parsed, and the
sequence field is reported separately because it is the anchor an AUXLCL update
deck needs (see docs/15-UPDATE-LEVELS.md).
"""
import os
import re
import sys
from collections import Counter, defaultdict

# Shift instructions with an immediate amount.  The amount is the D2 of a
# base-displacement operand, so "SLL R1,0(R2)" is a VARIABLE shift and is
# excluded -- those are not geometry constants and must not be counted.
SHIFTS = ('SLL', 'SRL', 'SLA', 'SRA', 'SLDL', 'SRDL', 'SLDA', 'SRDA')

# What each amount encodes, and what it becomes under ESA/390.  Derived in
# docs/09-DAT-WORK-SHAPE.md by reading the modules' own comments.
MEANING = {
    4:  ('16 pages per segment',        8,  'PAGSHFT'),
    16: ('64 KB segment',              20,  'SEGSHFT'),
    6:  ('x64 bytes per page table',   10,  'PTLSHFT'),
    11: ('2 KB storage-key block',     12,  'KEYSHFT'),
}
# Amounts that stay valid: 4 KB pages survive ESA/390 untouched, and the
# small ones are fullword/doubleword scaling rather than geometry.
UNCHANGED = {12: '4 KB page offset', 1: 'halfword scale', 2: 'fullword scale',
             3: 'doubleword scale', 20: '1 MB, already'}

# Compound sites already resolved by reading, so nobody re-derives them.
# DMKBLD "SLL R1,4+4  SEGMENT COUNT * 16" is two DIFFERENT facts multiplied:
# VMSEG holds (segment count / 16) - 1, so one 4 undoes that packing and the
# other is the 16-pages-per-segment conversion.  Only the second becomes 8, so
# the site is  4+PAGSHFT,  not  PAGSHFT+4  and not  8+4.  Arithmetically
# identical, but naming the wrong term would encode the wrong fact.  VMSEG's
# one-byte field caps segments at 16*256 = 4096, and ESA/390 needs 2048, so
# unlike DMKBLDRT's packed halfword this one survives unchanged.
RESOLVED = {('DMKBLD', 232): '4+PAGSHFT'}

# The twelve modules that touch the DAT tables.
DAT_MODULES = ('DMKBLD DMKCPI DMKPGS DMKCFG DMKPTR DMKVMA DMKMCH DMKVAT '
               'DMKCPP DMKATS DMKRPA DMKPRV').split()


def parse(line):
    """Return (label, op, operand, comment, seq) from one CP source line."""
    body, seq = line[:71], line[72:80].rstrip()
    if not body.strip() or body[0] in ('*', '.'):
        return None
    label, rest = body[:8].rstrip(), body[9:].rstrip()
    m = re.match(r'(\S+)\s+(\S+)\s*(.*)', rest)
    if not m:
        return None
    op, operand, comment = m.group(1), m.group(2), m.group(3).strip()
    return label, op, operand, comment, seq


def amount(operand):
    """The literal shift amount, or None when the shift is variable."""
    if ',' not in operand:
        return None
    d2 = operand.split(',', 1)[1]
    if '(' in d2:               # base-displacement => variable shift
        return None
    if not re.fullmatch(r'[0-9+\-*]+', d2):
        return None             # symbolic: already named, which is the goal
    try:
        return eval(d2, {'__builtins__': {}}, {}), d2
    except Exception:
        return None


def scan(directory, modules=None):
    sites = []
    for name in sorted(os.listdir(directory)):
        if not name.endswith('.ASSEMBLE'):
            continue
        mod = name[:-len('.ASSEMBLE')]
        if modules and mod not in modules:
            continue
        for n, line in enumerate(open(os.path.join(directory, name),
                                     errors='replace'), 1):
            p = parse(line.rstrip('\n'))
            if not p:
                continue
            label, op, operand, comment, seq = p
            if op not in SHIFTS:
                continue
            a = amount(operand)
            if a is None:
                continue
            value, expr = a
            sites.append(dict(module=mod, line=n, seq=seq, op=op,
                              operand=operand, expr=expr, value=value,
                              comment=comment))
    return sites


def main():
    args = [a for a in sys.argv[1:] if not a.startswith('--')]
    flags = {a for a in sys.argv[1:] if a.startswith('--')}
    directory = args[0] if args else 'source/cp'
    mods = None if '--all' in flags else DAT_MODULES
    sites = scan(directory, mods)

    # A plain literal is the easy case.  The dangerous case is a geometry
    # constant hidden as a TERM inside arithmetic -- "SLL R1,4+4" shifts by 8,
    # which is not a geometry amount, while one of its terms is.  Those sites
    # are invisible to any search for the amount and have to be rewritten by
    # hand, so they are separated out rather than lumped in with the literals.
    def compound(s):
        if s['expr'].isdigit():
            return None
        terms = [t for t in re.split(r'[+\-*]', s['expr']) if t.isdigit()]
        hits = [int(t) for t in terms if int(t) in MEANING]
        return hits or None

    must, comp, safe, look = [], [], [], []
    for s in sites:
        h = compound(s)
        if h:
            s['terms'] = h
            comp.append(s)
        elif s['value'] in MEANING:
            must.append(s)
        elif s['value'] in UNCHANGED:
            safe.append(s)
        else:
            look.append(s)

    if '--table' in flags:
        print('| Module | Line | Seq | Instruction | Now | Becomes | Symbol | '
              "Module's own comment |")
        print('|---|---|---|---|---|---|---|---|')
        for s in sorted(must + comp, key=lambda s: (s['value'], s['module'], s['line'])):
            if s.get('terms'):
                t = s['terms'][0]
                _, new, sym = MEANING[t]
                print('| `%s` | %d | `%s` | `%-5s %s` | %s | %s | `%s` | %s |'
                      % (s['module'], s['line'], s['seq'], s['op'], s['operand'],
                         s['expr'],
                         '**read it** \u2014 see the note below',
                         sym, s['comment'][:44] or '—'))
                continue
            _, new, sym = MEANING[s['value']]
            newexpr = s['expr'].replace(str(s['value']), str(new), 1) \
                if s['expr'].isdigit() else s['expr']
            print('| `%s` | %d | `%s` | `%-5s %s` | %s | %s | `%s` | %s |'
                  % (s['module'], s['line'], s['seq'], s['op'], s['operand'],
                     s['expr'], newexpr, sym, s['comment'][:44] or '—'))
        return

    print('Scanned %s (%s)' % (directory,
                               'all modules' if mods is None
                               else '%d DAT modules' % len(mods)))
    print('literal-shift instructions: %d' % len(sites))
    print()
    print('%-6s %-5s %-28s %-8s %s' % ('SHIFT', 'COUNT', 'ENCODES', 'BECOMES',
                                       'SYMBOL'))
    per = Counter(s['value'] for s in must)
    for v in sorted(per, key=lambda v: -per[v]):
        what, new, sym = MEANING[v]
        print('%-6d %-5d %-28s %-8d %s' % (v, per[v], what, new, sym))
    if comp:
        print()
        for s in comp:
            t = s['terms'][0]
            _, new, sym = MEANING[t]
            print('%-6s %-5s COMPOUND  %s:%d  %s %s  -- terms %s look like '
                  'geometry; which one is which needs READING, not substitution'
                  % ('', '', s['module'], s['line'], s['op'], s['operand'],
                     s['terms']))
    print()
    print('%-6s %-5d %s' % ('', len(must) + len(comp), 'MUST CHANGE'))
    print()
    print('%-6s %-5d %s' % ('', len(safe), 'unchanged (4 KB pages survive)'))
    print('%-6s %-5d %s' % ('', len(look), 'need individual inspection'))
    print()
    by = defaultdict(Counter)
    for s in must:
        by[s['value']][s['module']] += 1
    for v in sorted(by):
        print('shift %-4d %s' % (v, '  '.join('%s %d' % (m, c)
              for m, c in by[v].most_common())))


if __name__ == '__main__':
    main()
