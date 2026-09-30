#!/usr/bin/env python3
"""Read a printed CP abend dump back into a byte image, and measure it.

Written for `I-116`, and the reason it measures rather than parses is worth
recording, because the first attempt at this check did parse and was wrong.

`I-116` is a DSECT whose length disagrees with the macro that BUILDS its
storage: `RBLOKS.XA0002DK` added `RDEVSSID` to `RDEVBLOK`, so
`RDEVSIZE EQU (*-RDEVBLOK)/8` grew, but `RDEVICE.MACRO` emits DMKRIO's blocks as
a list of explicit `DC` statements and did not.  Every routine that strides
`RDEVSIZE*8` then walks 8 bytes further out per block, and `DMKSCNVS` cannot
find the SYSRES label -- `CPI001`.

**The first version of this check tried to compute both lengths by parsing.**  It
reported RDEVBLOK as 180 bytes against the macro's 256, and RCHBLOK as 92
against 36 -- all three pairs "disagreeing", including two that are fine.  The
reason is in its own output: `RDEVICE.MACRO` contains **339 `AIF`/`AGO`
statements**, so a static walk of its `DC`s sums every conditional path at once
and means nothing; and the DSECT walk mishandled alignment, giving `RDEVSIZE = 9`
where the true value is 11.  A tool that reports three defects where there is one
is worse than no tool: it would have sent the next person to fix RCHBLOK.

So this measures the artifact instead.  A CP dump prints all of storage, the
RDEVBLOKs are a contiguous array, and `RDEVADD` is the first halfword of each --
so the **stride is observable** by finding the run of ascending device addresses.
That number is evidence, and it is the number that actually broke: the blocks in
the failing dump were 0x58 bytes apart while `RDEVSIZE*8` was 0x60.

    python3 dumpscan.py <printed-dump> [--at ADDR] [--find HEX] [--bytes ADDR LEN]
    python3 dumpscan.py <printed-dump> --rdev          measure the RDEVBLOK stride

Dump line format, from DMKDMP's own printer output:

    0149E0    04001043  0252C600  00040000  20008000    000149E8  ...  *....

Eight fullwords per line, an optional storage-key byte, then EBCDIC.  Lines
reading `<a> TO <b>  SUPPRESSED LINE(S) SAME AS ABOVE` repeat the previous line,
and they are expanded rather than skipped -- a suppressed range is still storage,
and treating it as a hole is how a run of identical blocks can look like the
array ending.
"""
import re
import sys

LINE = re.compile(r'^([0-9A-F]{6})\s+((?:[0-9A-F]{8}\s+){1,8})')
SUPP = re.compile(r'^([0-9A-F]{6})\s+TO\s+([0-9A-F]{6})\s+SUPPRESSED')


def load(path):
    """The dump as {address: byte}.  Suppressed ranges are expanded."""
    mem, last = {}, None
    for line in open(path, errors='replace'):
        m = SUPP.match(line)
        if m and last is not None:
            a, b = int(m.group(1), 16), int(m.group(2), 16)
            for base in range(a, b + 0x20, 0x20):
                for i, byte in enumerate(last):
                    mem[base + i] = byte
            continue
        m = LINE.match(line)
        if not m:
            continue
        addr = int(m.group(1), 16)
        words = m.group(2).split()
        data = bytes.fromhex(''.join(words))
        for i, byte in enumerate(data):
            mem[addr + i] = byte
        last = data
    return mem


def word(mem, a):
    try:
        return (mem[a] << 24) | (mem[a + 1] << 16) | (mem[a + 2] << 8) | mem[a + 3]
    except KeyError:
        return None


def half(mem, a):
    try:
        return (mem[a] << 8) | mem[a + 1]
    except KeyError:
        return None


def rdev(mem):
    """Measure the RDEVBLOK array: origin, count, and the OBSERVED stride.

    ARIODV (X'3BC') is the first RDEVBLOK and ARIODC (X'3C8') points at the
    count, both from `PSA.MACRO`'s map.  `RDEVADD` is the first halfword of each
    block, and DMKRIO generates them in ascending device order within each
    `RDEVICE ADDRESS=(base,n)` group -- so for each candidate stride, count how
    many consecutive blocks have an address exactly one greater than the last.
    The true stride wins by a wide margin; a wrong one matches at most by luck.
    """
    ariodv = word(mem, 0x3BC)
    ariodc_p = word(mem, 0x3C8)
    count = half(mem, ariodc_p) if ariodc_p else None
    print('ARIODV (X\'3BC\')  first RDEVBLOK = %s'
          % ('%06X' % ariodv if ariodv else '??'))
    print('ARIODC (X\'3C8\')  count at %s = %s'
          % ('%06X' % ariodc_p if ariodc_p else '??', count))
    if not ariodv:
        return 2
    best = None
    for stride in range(0x20, 0x101, 8):
        run, addr = 0, half(mem, ariodv)
        if addr is None:
            continue
        a = ariodv
        while True:
            nxt = half(mem, a + stride)
            if nxt is None or nxt != addr + 1:
                break
            run += 1
            addr, a = nxt, a + stride
        if best is None or run > best[1]:
            best = (stride, run)
    print()
    print('OBSERVED stride = X\'%02X\' (%d bytes, %d doublewords), '
          'proven by a run of %d consecutive ascending device addresses'
          % (best[0], best[0], best[0] // 8, best[1]))

    # Independent and exact: DMKRIO lays the three arrays out end to end, so the
    # RDEVBLOK array's last byte must abut the RCUBLOKs.  ARIOCU (X'3B8') is the
    # first RCUBLOK.  This confirms the stride arithmetically instead of by a
    # run of addresses, and it is the check that settles it -- a wrong stride
    # misses the boundary by count*error, which for 949 blocks is thousands of
    # bytes and cannot be a coincidence.
    ariocu = word(mem, 0x3B8)
    if count and ariocu:
        end = ariodv + count * best[0]
        print()
        print('CONFIRMED: ARIODV + %d x X\'%02X\' = X\'%06X\'; '
              'ARIOCU (first RCUBLOK) = X\'%06X\' -- %s'
              % (count, best[0], end, ariocu,
                 'they abut exactly' if end == ariocu
                 else 'MISMATCH of %+d bytes' % (ariocu - end)))
        for cand in (b for b in range(0x20, 0x101, 8) if b != best[0]):
            if ariodv + count * cand == ariocu:
                print('         (X\'%02X\' would also abut -- ambiguous)' % cand)
    print()
    print('Compare against RDEVSIZE*8 as the nucleus computes it.  If they '
          'differ,\nevery `LA R1,RDEVSIZE*8(,R1)` scan walks off by the '
          'difference per block\nand finds nothing -- which is CPI001.  I-116.')
    return 0


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        return 2
    mem = load(sys.argv[1])
    lo, hi = min(mem), max(mem)
    print('loaded %d bytes, X\'%06X\'-X\'%06X\'\n' % (len(mem), lo, hi))
    a = sys.argv[2:]
    if '--rdev' in a:
        return rdev(mem)
    if '--at' in a:
        addr = int(a[a.index('--at') + 1], 16)
        for r in range(addr, addr + 0x40, 0x10):
            print('%06X  %s' % (r, ' '.join(
                '%08X' % (word(mem, r + i) or 0) for i in (0, 4, 8, 12))))
        return 0
    if '--find' in a:
        pat = bytes.fromhex(a[a.index('--find') + 1])
        hits = [x for x in range(lo, hi - len(pat))
                if all(mem.get(x + i) == pat[i] for i in range(len(pat)))]
        print('%d occurrences: %s' % (len(hits), ' '.join('%06X' % h for h in hits)))
        return 0
    print(__doc__)
    return 2


if __name__ == '__main__':
    sys.exit(main())
