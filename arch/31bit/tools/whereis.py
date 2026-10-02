#!/usr/bin/env python3
"""Which CP module owns a real address?  A lookup, not a judgement.

On 2 October I identified the module at a faulting address four times and was
wrong three times, every time by matching a number against a plausible owner --
`SHRTABLE` because three offsets fitted its DSECT, `DMKATS` because it was the
only one of four modules I happened to check that used those fields.  The way
out is not more care; it is a table.

CP modules carry their own name as an EBCDIC constant (`DC CL8'DMKPGS'` and the
like).  Not all of them do -- `DMKFRE` does not, it carries `DC C'FREE'` -- so
the map this builds is PARTIAL by construction, and says so.  Combined with the
load order in `CPLOAD EXEC` it still places any address between two known
modules, which is all that is needed to stop the guessing.

The storage image comes from Hercules's own `savecore`:

    build.sh test "herc:stop:6" "herc:savecore /tmp/nuc.bin 0 7FFFF:20"

    python3 whereis.py /tmp/nuc.bin 3DB62 [more addresses...]
    python3 whereis.py /tmp/nuc.bin --map        # every name found, in order
"""
import re
import sys

# EBCDIC -> ASCII for the printable range we care about
E2A = {}
for a, e in zip(
    "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789",
    list(range(0xC1, 0xCA)) + list(range(0xD1, 0xDA)) + list(range(0xE2, 0xEA))
    + list(range(0xF0, 0xFA))):
    E2A[e] = a
NAME = re.compile(r'^DMK[A-Z0-9]{3,5}$')


def names(image):
    """[(offset, name)] for every EBCDIC DMKxxx constant in the image."""
    out = []
    i = 0
    n = len(image)
    while i < n - 8:
        # EBCDIC 'DMK' = C4 D4 D2
        if image[i] == 0xC4 and image[i + 1] == 0xD4 and image[i + 2] == 0xD2:
            s = ''
            for b in image[i:i + 8]:
                c = E2A.get(b)
                if c is None:
                    break
                s += c
            if NAME.match(s.strip()):
                out.append((i, s.strip()))
            i += 8
        else:
            i += 1
    return out


def main():
    if len(sys.argv) < 3:
        print(__doc__)
        return 2
    image = open(sys.argv[1], 'rb').read()
    found = names(image)
    # Keep the FIRST occurrence of each name: a module's own identifier sits
    # near its start, while later hits are adcons and messages referring to it.
    first = {}
    for off, nm in found:
        first.setdefault(nm, off)
    table = sorted((off, nm) for nm, off in first.items())

    if '--map' in sys.argv[2:]:
        print('%d distinct module name(s) in %d bytes of storage'
              % (len(table), len(image)))
        for off, nm in table:
            print('  X%06X  %s' % (off, nm))
        print()
        print('PARTIAL: a module without a self-name constant does not appear.')
        return 0

    for arg in sys.argv[2:]:
        a = int(arg, 16)
        before = [(o, n) for o, n in table if o <= a]
        after = [(o, n) for o, n in table if o > a]
        print('X%05X' % a)
        if before:
            o, n = before[-1]
            print('   after  %-9s at X%06X  (+%d bytes)' % (n, o, a - o))
        if after:
            o, n = after[0]
            print('   before %-9s at X%06X  (-%d bytes)' % (n, o, o - a))
        if not before and not after:
            print('   no named module found in the image')
    return 0


if __name__ == '__main__':
    sys.exit(main())
