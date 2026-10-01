#!/usr/bin/env python3
"""Compare two Hercules runs of the same test and say whether the engines agree.

Added 1 October, when SDL Hercules 4.9.1 joined 3.13 as a second test engine
(`claude/HERCULES-4.md`).  3.13 remains the build machine; 4.9.1 exists to answer
a question 3.13 cannot: **is what we are building actually ESA/390, or merely
something Hercules's ESA/390 mode accepts?**

`WHAT-31BIT-NEEDS.md` carried that as an assumption.  It is no longer one: in
4.9.1's ESA/390 mode, `facility query enabled` lists thirteen facilities,
including

    bit   0  N3 Instructions are installed
    bit   7  Store-Facility-List-Extended Facility
    bit  16  Extended-Translation Facility 2
    bit  24  ETF2-Enhancement Facility
    bit  52  Interlocked-Access Facility 2      <- z/Architecture, z196 (2010)

So the risk is real, it is listed, and `facility disable` can narrow it.

## Two engines, two message formats

The whole reason this file exists rather than a `diff` is that 4.x renumbered and
reformatted almost everything.  The same three facts print like this:

    3.13   PSW=000E0000 00000004
           R:0000008C:K:06=00040012 00000000 ...
           GR00=000541B8  GR01=01000000

    4.9.1  HHC02278I Processor CP00 PSW: 000E0000 00000004
           HHC02290I R:00000080                   00040012              ....
           HHC02269I GR00=000541B8 GR01=01000000 GR02=000007E0 GR03=00FFFFFC

A raw diff of two such logs is almost entirely noise, and -- worse -- a parser
written for one engine silently finds **nothing** in the other.  That happened on
the first dual run: 4.9.1 behaved identically and this tool reported
`DIFF ... 4.9x: --` on every line, which reads like a disagreement and is not
one.  So `no data` is now its own verdict, never folded into `differs`.

Storage is compared by **address**, not by line, because 4.x prints the
containing 16-byte line with the requested bytes offset inside it.  Ask for
aligned ranges (`r 80.20`, not `r 8C.10`) and both engines print whole lines.

    python3 dualdiff.py <log-3.13> <log-4.x>
"""
import re
import sys

# --- PSW: 3.13 bare, 4.x behind a message id
PSW = re.compile(r'(?:^PSW=|PSW: )([0-9A-F]{8}) ([0-9A-F]{8})', re.M)
# --- storage: a base address then 8-hex-digit words, either engine
STORE = re.compile(r'R:([0-9A-F]{8})(?::K:[0-9A-F]*=|\s\s)(.*)$', re.M)
WORD = re.compile(r'\b([0-9A-F]{8})\b')
GPR = re.compile(r'GR(\d\d)=([0-9A-F]{8})')
PGM = re.compile(r'(\w+ exception)\s+CODE=([0-9A-F]+)\s+ILC=(\d)')
INST = re.compile(r'INST=([0-9A-F]+)')
CPMSG = re.compile(r'(DMK[A-Z]{3}\d{3}[A-Z].*?)\s*$', re.M)

# Registers that vary run to run on the SAME engine, so a difference in them is
# not evidence about the engines.  GR07 was 00000031 then 00000033 on two
# consecutive 3.13 runs before 4.x was involved at all; treating it as signal
# would manufacture a disagreement.
VOLATILE = {'07'}


def memory(t):
    """{address: word} from either engine's storage display."""
    mem = {}
    for base, rest in STORE.findall(t):
        a = int(base, 16)
        # 4.x pads leading slots with spaces when the range starts mid-line, so
        # position matters: each slot is 9 columns wide after the address.
        for m in WORD.finditer(rest):
            slot = m.start() // 9
            mem[a + slot * 4] = m.group(1)
    return mem


def facts(path):
    try:
        t = open(path, errors='replace').read()
    except OSError as e:
        return {'error': str(e)}
    mem = memory(t)
    gprs = GPR.findall(t)[-16:]
    return {
        'psw': PSW.findall(t)[-1:],
        'x8C': mem.get(0x8C, None),
        'x28': (mem.get(0x28), mem.get(0x2C)) if 0x28 in mem else None,
        'gpr': [(n, v) for n, v in gprs if n not in VOLATILE],
        'volatile': [(n, v) for n, v in gprs if n in VOLATILE],
        'pgm': PGM.findall(t),
        'inst': INST.findall(t),
        'cp': [m.strip() for m in CPMSG.findall(t)],
        'arch': (re.findall(r'architecture mode ([A-Za-z0-9/]+)', t) or [None])[-1],
    }


class Cmp:
    def __init__(self):
        self.agree, self.nodata, self.differ = 0, 0, 0

    def __call__(self, name, a, b, fmt=str):
        if a is None and b is None:
            print('  --   %-26s neither run reported it' % name)
            self.nodata += 1
        elif a is None or b is None:
            which = '3.13' if a is None else '4.9x'
            print('  NO   %-26s %s did not report it -- NOT a disagreement, '
                  'missing data' % (name, which))
            print('       %-26s the other said: %s'
                  % ('', fmt(b if a is None else a)))
            self.nodata += 1
        elif a == b:
            print('  ok   %-26s %s' % (name, fmt(a)))
            self.agree += 1
        else:
            print(' DIFF  %-26s 3.13: %s' % (name, fmt(a)))
            print('       %-26s 4.9x: %s' % ('', fmt(b)))
            self.differ += 1


def main():
    if len(sys.argv) != 3:
        print(__doc__)
        return 2
    a, b = facts(sys.argv[1]), facts(sys.argv[2])
    for f in (a, b):
        if 'error' in f:
            print('### cannot compare: %s' % f['error'])
            return 2

    print('Hercules 3.13 vs 4.9.1 -- same nucleus, same test, same starting state')
    print()
    c = Cmp()
    c('architecture mode', a['arch'], b['arch'])
    c('final PSW', a['psw'], b['psw'],
      lambda v: ' '.join('%s %s' % p for p in v) if v else 'none')
    c("prog int id (X'8C')", a['x8C'], b['x8C'])
    c("program old PSW (X'28')", a['x28'], b['x28'], lambda v: '%s %s' % v)
    c('program interrupts', a['pgm'] or None, b['pgm'] or None,
      lambda v: '; '.join('%s code=%s ilc=%s' % x for x in v))
    c('interrupt instructions', a['inst'] or None, b['inst'] or None,
      lambda v: ' '.join(v[:6]))
    c('general registers', a['gpr'] or None, b['gpr'] or None,
      lambda v: ' '.join('R%s=%s' % x for x in v[:6]) + (' …' if len(v) > 6 else ''))
    c('CP console output', a['cp'] or None, b['cp'] or None,
      lambda v: '%d message(s): %s' % (len(v), v[0][:70] if v else ''))

    if a['volatile'] or b['volatile']:
        print()
        print('  (ignored as run-variable: %s vs %s)'
              % (' '.join('R%s=%s' % x for x in a['volatile']) or '-',
                 ' '.join('R%s=%s' % x for x in b['volatile']) or '-'))

    print()
    print('%d agree, %d differ, %d not reported by one or both'
          % (c.agree, c.differ, c.nodata))
    print()
    if c.differ:
        print('VERDICT: the engines DISAGREE, and that is the interesting outcome.')
        print('One is accepting something the other refuses.  Find out which before')
        print('building anything further on top of it.')
        return 1
    if c.agree == 0:
        print('VERDICT: NOTHING was compared.  This is a harness failure, not a')
        print('result -- fix the runs before reading anything into it.')
        return 2
    print('VERDICT: the engines AGREE on all %d compared facts.' % c.agree)
    print('That is evidence the conversion is ESA/390 and not merely')
    print('Hercules-3.13-shaped.  Weaker than real hardware would give, but it is')
    print('the first evidence of the kind this project has had.')
    return 0


if __name__ == '__main__':
    sys.exit(main())
