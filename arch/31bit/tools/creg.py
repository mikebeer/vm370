#!/usr/bin/env python3
"""Every LCTL and STCTL in CP, by which control register it touches.

Two control registers change meaning between S/370 and ESA/390, and both are
load-bearing for I/O:

    CR2   S/370: the channel masks, one bit per channel, X'FFFFFFFF' for all
          ESA/390: the dispatchable-unit-control-table origin
    CR6   S/370: the virtual-machine-assist control register
          ESA/390: the I/O-interruption subclass mask

`XA0013DK` moved the mask from CR2 to CR6 in `DMKCPI`'s `CTLREGS`, which is
where CP's control registers are *initialised*.  That is necessary and not
sufficient, because CP **reloads both at runtime** -- `DMKDSP` reloads CR6 on
every dispatch -- and a register reloaded with an S/370 value is back to being
wrong a few instructions after `CTLREGS` is honoured.  Nothing in the project
would have caught that: the module assembles, and CR6 going to zero presents no
interruption and reports no error.  `I-71`.

So this enumerates them.  A range like `LCTL C1,C14` covers CR2 and CR6 without
naming either, which is exactly the kind of site an eyeball scan misses, so the
range is expanded rather than matched.

    python3 creg.py /path/to/vmce [--reg N] [--all]

Registers are written `C2` or `2`; both forms appear in CP.  Sites in modules
outside the nucleus load list are reported separately, since `DMKAPI`,
`DMKCPP` and `DMKMCT` are attached-processor modules that `AP=NO` keeps out
(`I-50`).
"""
import os
import re
import sys

# What each register means on each side, for the registers where it differs.
MEANING = {
    0: ('translation format, extent and page size',
        'same role, different encoding -- CODEB0 not CODE70 (I-24)'),
    2: ('channel masks, one bit per channel',
        'dispatchable-unit-control-table origin'),
    6: ('virtual-machine-assist control',
        'I/O-interruption subclass mask'),
}
BREAKING = (2, 6)

# Sites a deck has dealt with, and how.  Like `s370only.py`, this tool reads
# base source and cannot see an UPDATE level, so without this it would report
# closed sites as live for ever -- the failure `I-67` is about, on a new axis.
# A site is listed only once its deck assembles clean on CE.
HANDLED = {
    ('DMKCPI', '00461000'): 'CTLREGS carries the mask -- XA0013DK',
    ('DMKCPI', '00608000'): 'loads CPCREG6, which is the mask now -- XA0001DK',
    ('DMKCPI', '00615000'): 'was ZEROES, now CPCREG6 -- XA0013DK',
    ('DMKCPI', '01653000'): 'was TEMPR0, now CPCREG6 -- XA0013DK',
    ('DMKCPI', '01674000'): 'was ZEROES, now CPCREG6 -- XA0013DK',
    ('DMKDSP', '02422000'): 'range split around CR6 -- XA0006DK',
    ('DMKDSP', '02542000'): 'was 0(R6), now CPCREG6 -- XA0006DK',
    ('DMKPRV', '00780000'): 'was VMMICRO, now CPCREG6 -- XA0007DK',
    ('DMKCFO', '00612200'): 'the ST that wrecked CPCREG6 is gone -- XA0019DK',
}

# Sites left alone, with the reason.  A store is not a load: STCTL saves
# whatever is there and can never put a wrong value into a live register, so
# every STCTL is harmless by construction and is listed here as a class.
DECLARED = {
    ('DMKMCH', '00463000'):
        'restores CR0-CR13 from MCFXDLOG+216, the machine-check fixed logout '
        'area the HARDWARE writes -- and ESA/390 lays that area out '
        'differently, so the displacement is probably wrong. Only reachable on '
        'a machine check, which Hercules does not generate. I-72.',
}

OPS = ('LCTL', 'STCTL')


def regs(operands):
    """The register range an LCTL/STCTL covers, expanded.

    `LCTL C1,C14,BALR1` is CR1 through CR14 -- a range that names neither CR2
    nor CR6 and loads both.  Control registers wrap, so C14,C2 is a real and
    legal range meaning 14, 15, 0, 1, 2.
    """
    parts = operands.split(',')
    if len(parts) < 2:
        return []
    def num(t):
        t = t.strip().upper()
        if t.startswith('C'):
            t = t[1:]
        return int(t) if t.isdigit() else None
    a, b = num(parts[0]), num(parts[1])
    if a is None or b is None:
        return []
    out, i = [], a
    while True:
        out.append(i)
        if i == b:
            break
        i = (i + 1) % 16
        if len(out) > 16:
            break
    return out


def scan(src):
    """(module, seq, op, registers, text) for every LCTL/STCTL."""
    hits = []
    for name in sorted(os.listdir(src)):
        if not name.endswith('.ASSEMBLE'):
            continue
        mod = name[:-9]
        for line in open(os.path.join(src, name), errors='replace'):
            if line.startswith('*') or len(line) < 20:
                continue
            body = line[9:71]
            m = re.match(r'(LCTL|STCTL)\s+(\S+)', body)
            if not m:
                continue
            seq = line[72:80].strip()
            hits.append((mod, seq, m.group(1), regs(m.group(2)),
                         body.rstrip()))
    return hits


def main():
    root = sys.argv[1] if len(sys.argv) > 1 else '/home/claude/vmce'
    src = os.path.join(root, 'source', 'cp')
    nucleus = {m.group(1) for m in re.finditer(
        r'(?m)^&1 &2 &3 (\S+)',
        open(os.path.join(root, 'maintenance', 'files', '094',
                          'CPLOAD.EXEC')).read())} - {'LOADER', 'LDT',
                                                      'SLC', 'SPB'}
    hits = scan(src)

    want = BREAKING
    if '--reg' in sys.argv:
        want = (int(sys.argv[sys.argv.index('--reg') + 1]),)

    print('CONTROL REGISTERS THAT CHANGE MEANING  --  tools/creg.py')
    print()
    for r in want:
        s370, esa = MEANING.get(r, ('?', '?'))
        print('CR%d   S/370: %s' % (r, s370))
        print('      ESA/390: %s' % esa)
        rows = [h for h in hits if r in h[3]]
        nuc = [h for h in rows if h[0] in nucleus]
        other = sorted({h[0] for h in rows if h[0] not in nucleus})
        print('      %d sites in %d nucleus modules'
              % (len(nuc), len({h[0] for h in nuc})))
        open_ = 0
        for mod, seq, op, rr, text in nuc:
            span = '' if len(rr) <= 2 else '  [range of %d]' % len(rr)
            if op == 'STCTL':
                mark = 'store'
            elif (mod, seq) in HANDLED:
                mark = 'done'
            elif (mod, seq) in DECLARED:
                mark = 'left'
            else:
                mark = 'OPEN'
                open_ += 1
            print('        %-5s %-9s %-9s %s%s'
                  % (mark, mod, seq, text[:38], span))
        print('      %d loads still open' % open_)
        for (mod, seq), why in sorted(DECLARED.items()):
            if any(h[0] == mod and h[1] == seq and r in h[3] for h in hits):
                print('      left alone: %s %s -- %s' % (mod, seq, why))
        if other:
            print('      not in the nucleus (AP modules, I-50): %s'
                  % ' '.join(other))
        print()

    if '--all' in sys.argv:
        print('Every LCTL/STCTL, by register:')
        for r in range(16):
            rows = [h for h in hits if r in h[3] and h[0] in nucleus]
            if rows:
                print('  CR%-3d %3d sites  %s' % (
                    r, len(rows),
                    ' '.join(sorted({h[0] for h in rows}))))
    return 0


if __name__ == '__main__':
    sys.exit(main())
