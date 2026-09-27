#!/usr/bin/env python3
"""Per-module conversion status, computed rather than hand-maintained.

The project has registers for risks, issues and milestones but no view of
where each CP module stands. A hand-written table would go stale on the next
deck, so this derives the state from four sources:

  * the nucleus load list          maintenance/files/194/CPLOAD.EXEC
  * what ASMDMK assembles          maintenance/files/194/ASMDMK.EXEC
  * which modules we have changed   arch/31bit/updates/*.AUXLCL
  * which modules the PSA rename    a scan of source/cp for the renamed
    breaks                          symbols

    python3 status.py /path/to/vmce [--all]

Baseline: `ASMDMK DMKHRC` assembled 186 of 186 with 185 clean on 27 September
(docs/21-NUCLEUS-GAP.md). The single exception is recorded below rather than
re-derived, because it is a property of CE's site configuration and not of
any module's source.
"""
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
UPDATES = os.path.join(HERE, '..', 'updates')

# Symbols the PSA lowcore change renamed.  A module referencing any of them
# no longer assembles until it is dealt with.  docs/19-M1-STEP2.md.
RENAMED = ('INTTIO', 'CHANID', 'IOELPNTR', 'ECSWLOG', 'ECSWBYT3')

# Sites where a renamed symbol is a displacement into a GUEST's page 0, not
# into CP's own lowcore.  Guests stay S/370-mode through M4, so these need a
# symbol swap and no semantic change at all.  I-36.
GUEST_PSA = {'DMKDSP': 'INTTIO-PSA-1',
             'DMKPRV': 'CHANID-PSA',
             'DMKCCH': 'ECSWLOG-PSA'}

# Modules whose deck covers every site the PSA rename broke.  This cannot be
# derived from a scan of `source/cp`: the decks are an UPDATE level applied at
# assembly time, so the base source still carries the old symbols and a scan
# still reports the module as broken.  Verified by CE saying
# `NO STATEMENTS FLAGGED IN THIS ASSEMBLY` with a TXTLCL produced.
HANDLED = {
    'DMKDSP': 'run19',
    'DMKPRV': 'run19',
    'DMKIOG': 'run21',
    'DMKEIG': 'run22',
    'DMKCCH': 'run25',
    'DMKVMI': 'run26',
    'DMKIOT': 'run26',
    'DMKCPI': 'run30',
    'DMKSYS': 'run31',
    'DMKCKP': 'run38',
    'DMKDMP': 'run38',
}

# Severity-4 MNOTEs for 3375/3390 in CE's site configuration, not a source
# defect and the TEXT deck is still produced.  I-34.
BASELINE_WARN = {'DMKRIO': 'RDEVICE 3375/3390 UNSUPPORTED DEVICE TYPE, sev 4'}

# What each broken module actually needs, from reading its sites.
NEEDS = {
    'DMKSYS': 'AP=NO so DMKCPI never executes CONCS -- I-50',
    'DMKCPI': 'CR6 subclass mask and subchannel discovery -- M1 step 6',
    'DMKIOT': 'convert: 10 INTTIO sites, interrupt entry -- M1 step 5',
    'DMKCKP': '4 INTTIO plus 25 channel sites -- one pass, bootstrap',
    'DMKDMP': '3 INTTIO plus 22 channel sites -- one pass, bootstrap',
    'DMKDSP': 'guest-PSA symbol swap (G370TIO), no semantic change',
    'DMKPRV': 'guest-PSA symbol swap (S370CHID), STIDC simulation',
    'DMKCCH': 'guest-PSA swap plus 13 channel-logout sites -- R-03',
    'DMKIOG': 'channel logout: CHANID x3, ECSWLOG x2, IOELPNTR x1 -- R-03',
    'DMKEIG': 'channel logout: IOELPNTR x2 -- R-03',
    'DMKVMI': 'IPL device address moves to SYSIPLDV -- I-47',
}


def rollup(docs):
    """Risk and issue counts, read from the registers rather than restated.

    A status snapshot in a document goes stale on the next deck; the registers
    are the source of truth, so count them here and keep one command that
    answers "where are we".
    """
    import collections

    def tally(path, prefix):
        rows = collections.Counter()
        weights = []
        for line in open(path):
            if not line.startswith('| **%s-' % prefix):
                continue
            cells = [c.strip() for c in line.strip().strip('|').split('|')]
            rows[cells[-1].strip('*')] += 1
            if prefix == 'R':
                for c in cells:
                    if c.startswith('**') and c.strip('*').isdigit():
                        weights.append((int(c.strip('*')), cells[0].strip('*')))
        return rows, weights

    for name, prefix, label in (('12-RISKS.md', 'R', 'RISKS'),
                                ('13-ISSUES.md', 'I', 'ISSUES')):
        path = os.path.join(docs, name)
        if not os.path.exists(path):
            continue
        rows, weights = tally(path, prefix)
        print()
        print('%s  (%d)  %s' % (label, sum(rows.values()),
                                '  '.join('%s %d' % (k, v)
                                          for k, v in rows.most_common())))
        if weights:
            top = sorted(weights, reverse=True)[:5]
            print('  heaviest: ' + '  '.join('%s w%d' % (i, w)
                                             for w, i in top))


def listed(path, pattern):
    return [m.group(1) for m in re.finditer(pattern, open(path).read())]


def main():
    root = sys.argv[1] if len(sys.argv) > 1 else '/home/claude/vmce'
    M = os.path.join(root, 'maintenance', 'files', '194')
    src = os.path.join(root, 'source', 'cp')

    nucleus = [m for m in listed(os.path.join(M, 'CPLOAD.EXEC'),
                                 r'&1 &2 &3 (\S+)')
               if m not in ('LOADER', 'LDT')]
    asmdmk = set(listed(os.path.join(M, 'ASMDMK.EXEC'), r'EXEC VMFASM (\S+)'))

    changed = {f.split('.')[0] for f in os.listdir(UPDATES)
               if f.endswith('.AUXLCL')}

    broken = {}
    for name in sorted(os.listdir(src)):
        if not name.endswith('.ASSEMBLE'):
            continue
        mod, text = name[:-9], open(os.path.join(src, name),
                                    errors='replace').read()
        hits = {s: len(re.findall(r'\b%s\b' % s, text)) for s in RENAMED}
        hits = {k: v for k, v in hits.items() if v}
        if hits:
            broken[mod] = hits

    print('CP MODULE STATUS  --  generated by tools/status.py')
    print()
    print('%-8s %-9s %-5s %s' % ('MEMBER', 'STATE', 'IN', 'NOTE'))
    print('-' * 78)

    rows = sorted(set(list(broken) + list(changed) + list(BASELINE_WARN)))
    for mod in rows:
        nucl = 'yes' if mod in nucleus else 'lib'
        if mod in changed and (mod not in broken or mod in HANDLED):
            state = 'CONVERTED'
            note = ('in DMKLCL MACLIB, rebuilt by VMFMAC'
                    if mod not in nucleus else
                    'clean on CE (%s), TXTLCL produced' % HANDLED.get(mod, '?'))
            if mod == 'DMKIOS':
                note = 'SSCH path done; TIO/HDV/TCH sites outstanding'
        elif mod in changed and mod in broken:
            state = 'PARTIAL'
            note = NEEDS.get(mod, '')
            if mod == 'DMKIOS':
                note = ('SSCH path done, clean on CE; TIO/HDV/TCH left. '
                        'Its lone source INTTIO site is absent from CE\'s '
                        'own build -- I-30')
        elif mod in broken:
            state = 'BROKEN'
            note = NEEDS.get(mod, ', '.join('%s x%d' % (k, v)
                                            for k, v in broken[mod].items()))
        else:
            state = 'warn'
            note = BASELINE_WARN[mod]
        print('%-8s %-9s %-5s %s' % (mod, state, nucl, note[:52]))

    if '--all' in sys.argv:
        print()
        print('Untouched and clean (%d in the nucleus):' % (
            len([m for m in nucleus if m not in rows])))
        rest = [m for m in nucleus if m not in rows]
        for i in range(0, len(rest), 9):
            print('  ' + ' '.join('%-8s' % m for m in rest[i:i + 9]))

    print()
    print('%-46s %s' % ('nucleus load-list modules', len(nucleus)))
    print('%-46s %s' % ('  covered by ASMDMK', len([m for m in nucleus
                                                    if m in asmdmk])))
    print('%-46s %s' % ('  no source anywhere (I-35)',
                        ' '.join(m for m in nucleus if m not in asmdmk)))
    print('%-46s %s' % ('converted, assembling clean',
                        len([m for m in changed
                             if m not in broken or m in HANDLED])))
    print('%-46s %s' % ('broken by the PSA rename, awaiting work',
                        len([m for m in broken if m not in changed])))
    print('%-46s %s' % ('  of which guest-PSA swaps only (I-36)',
                        len([m for m in broken
                             if m in GUEST_PSA and m not in HANDLED])))
    print('%-46s %s' % ('untouched by the PSA rename',
                        len([m for m in nucleus if m not in rows])))
    print()
    print('Of those, the ones still holding S/370-only instructions are found')
    print('by tools/s370only.py, which is a separate and larger axis:')
    print('%-46s %s' % ('  nucleus channel-I/O sites (SIO/TIO/HIO/...)', 133))
    print('%-46s %s' % ('  nucleus storage-key sites (ISK/SSK/RRB)', 67))
    print('%-46s %s' % ('  nucleus modules affected', 28))
    rollup(os.path.join(HERE, '..', '..', '..', 'docs'))


if __name__ == '__main__':
    main()
