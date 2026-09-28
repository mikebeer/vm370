#!/usr/bin/env python3
"""Strip CP's spool header and trailing blanks from a punched loader deck.

`VMFLOAD` punches a standalone loader deck, but what reaches the real punch is
wrapped: `CP START 00D` without `NOSEP` prepends five separator cards reading
`MAINT MAINT MAINT`, and even with `NOSEP` a `USERID MAINT CLASS A` header
card survives.  Feed that to `ipl 00c` and the machine reads a banner as its
IPL record and stops with `CSW status=0020`.

The real deck begins with the IPL record -- an IPL PSW followed by two CCWs,
so a card starting X'00' whose successor is an X'02' loader record -- and ends
with the `LDT` card, after which the punch pads with blanks.

    python3 striphdr.py <punched> <stripped>
"""
import sys


def main():
    src, dst = sys.argv[1], sys.argv[2]
    d = open(src, 'rb').read()
    n = len(d) // 80
    start = None
    for i in range(n - 1):
        if d[i * 80] == 0x00 and d[(i + 1) * 80] == 0x02:
            start = i
            break
    if start is None:
        raise SystemExit('no IPL record found: no X00 card followed by an X02')
    end = n
    while end > start and not d[(end - 1) * 80:end * 80].strip(b'\x40'):
        end -= 1
    out = d[start * 80:end * 80]
    open(dst, 'wb').write(out)
    print('%s: dropped %d header and %d trailing cards, kept %d'
          % (src.rsplit('/', 1)[-1], start, n - end, end - start))
    print('  IPL record %s' % out[:16].hex())
    print('  last card  %s' % out[-80:][:16].hex())
    return 0


if __name__ == '__main__':
    sys.exit(main())
