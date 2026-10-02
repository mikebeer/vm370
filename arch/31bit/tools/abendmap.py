#!/usr/bin/env python3
"""abendmap.py -- address -> module, from CP's own ABEND tags in a storage image.

ABEND.MACRO generates, for every  ABEND n  in a CP module:

        SVC   0
        DC    CL3'&MODNAM',AL1(&CODE)      &MODNAM SETC '&SYSECT'(4,3)

so DMKFRE's  ABEND 13  is the literal byte string  0A 00 C6 D9 C5 0D  in the
nucleus.  The tag is the module name's 4th-6th characters, the fourth byte is
the abend number, and both halves are checkable against the source: a hit is
reported only when that module's source really contains that ABEND code.

That makes the map self-validating and dense -- most modules carry several
abends -- so an address identified through it cites a literal byte sequence
plus the source line that generated it, never an offset calculation.

Note: when the AP global &LOCK is 1 the macro emits 'LOK' instead of the
module tag, so those sites identify as LOK rather than their module.

Usage:  abendmap.py IMAGE [ADDR ...]       addresses in hex
        abendmap.py IMAGE --map            print the whole map
"""
import os
import re
import sys

SRC = '/home/claude/vmce/source/cp'

A2E = {}
for _a, _e in (('ABCDEFGHI', 0xC1), ('JKLMNOPQR', 0xD1), ('STUVWXYZ', 0xE2),
               ('0123456789', 0xF0)):
    for _i, _c in enumerate(_a):
        A2E[_c] = _e + _i

# ABEND takes a self-defining decimal code; a few sites use a symbol, which
# cannot be resolved here and is skipped rather than guessed.
ABEND = re.compile(r'^(?:\S+)?\s+ABEND\s+(\d{1,3})\s*(?:$|\s)')


def expected():
    """(tag, code) -> [source line refs], for every ABEND the sources define."""
    out = {}
    for f in sorted(os.listdir(SRC)):
        m = re.match(r'^(DMK([A-Z0-9]{3}))\.ASSEMBLE$', f)
        if not m:
            continue
        tag = m.group(2)
        with open(os.path.join(SRC, f), 'r', errors='replace') as fh:
            for n, line in enumerate(fh, 1):
                if line.startswith('*'):
                    continue
                g = ABEND.match(line[:71])
                if g:
                    out.setdefault((tag, int(g.group(1))), []).append(
                        '%s:%d' % (f, n))
    return out


def build(img):
    """Confirmed ABEND sites in address order: (addr, tag, code, srcrefs)."""
    exp = expected()
    pat = {}
    for (tag, code) in exp:
        key = b'\x0a\x00' + bytes(A2E[c] for c in tag) + bytes([code])
        pat.setdefault(key, (tag, code))
    out = []
    for key, (tag, code) in pat.items():
        i = 0
        while True:
            i = img.find(key, i)
            if i < 0:
                break
            out.append((i, tag, code, exp[(tag, code)]))
            i += 1
    out.sort()
    return out


def lookup(m, addr):
    before = after = None
    for e in m:
        if e[0] <= addr:
            before = e
        elif after is None:
            after = e
            break
    return before, after


def main():
    if len(sys.argv) < 3:
        sys.exit(__doc__)
    img = open(sys.argv[1], 'rb').read()
    m = build(img)
    if sys.argv[2] == '--map':
        for a, tag, code, refs in m:
            print('X%06X  DMK%-3s ABEND %-3d  %s' % (a, tag, code, refs[0]))
        print('-- %d confirmed abend sites, %d distinct modules'
              % (len(m), len(set(e[1] for e in m))))
        return
    for h in sys.argv[2:]:
        addr = int(h, 16)
        b, a = lookup(m, addr)
        print("X'%X'" % addr)
        for lbl, e in (('at/before', b), ('after    ', a)):
            if e is None:
                print('   %s  (none)' % lbl)
            else:
                print('   %s  X%06X  DMK%-3s ABEND %-3d %+8d  %s'
                      % (lbl, e[0], e[1], e[2], e[0] - addr, e[3][0]))
        if b and a and b[1] == a[1]:
            print('   => inside DMK%s -- same module both sides' % b[1])
        elif b and a:
            print('   => between DMK%s and DMK%s' % (b[1], a[1]))


if __name__ == '__main__':
    main()
