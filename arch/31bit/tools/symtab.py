#!/usr/bin/env python3
"""Read CP's OWN symbol table out of a storage image, and answer "what is at
this address" from it rather than from a guess.

`whereis.py` exists because I identified the module at a faulting address four
times on 2 October and was wrong three times.  It scans for `DC CL8'DMKxxx'`
constants, and its own docstring says the map that produces is partial by
construction: `DMKFRE` carries `DC C'FREE'`, several modules carry no name at
all, and a name constant is wherever the author put it rather than at the
module's entry point.  On 3 October that partiality cost another half hour --
the map placed `X3DA38` "after DMKVSQ, before DMKPTR41" across a seventeen-
kilobyte gap, which is not an answer.

CP already maintains the table I wanted.  `DMKSYM` is a file of nothing but

    SYM   DMKPSAEX
    SYM   DMKSVCIN
    ...

and `SYM.MACRO` expands each one to

    DC    CL8'&MODULE ',V(&MODULE)

-- twelve bytes, an eight-byte blank-padded EBCDIC name followed by the
four-byte address the loader resolved.  Three hundred and fifty-odd entries, in
load-list order, built for exactly this purpose: `DMKCPI 01895000` writes it as
the first record of every dump (`CCW X'05',DMKSYMTB,CC,4096`) so that the dump
processor can print symbols.  It is in the nucleus, so it is in any `savecore`
image, and it names ENTRY POINTS, not just CSECTs -- `DMKPSAEX`, `DMKSVCIN`,
`DMKPRGCT` and the rest -- which is finer than module granularity.

So this reads the real thing.  Nothing here is inferred: an entry is accepted
only if its name is plausible EBCDIC and its address is inside the image, and
the table is accepted only as the longest unbroken run of such entries, which
is what `DMKSYM` is and what random data is not.

    python3 symtab.py <core.bin> 3DA38 F38 C58      # what is at each address
    python3 symtab.py <core.bin> --map              # the whole table
    python3 symtab.py <core.bin> --near DMKPSA      # entries matching a name
"""
import sys

# EBCDIC -> ASCII for the characters a CP symbol can contain.
E2A = {0x40: ' '}
for i, c in enumerate('ABCDEFGHI'):
    E2A[0xC1 + i] = c
for i, c in enumerate('JKLMNOPQR'):
    E2A[0xD1 + i] = c
for i, c in enumerate('STUVWXYZ'):
    E2A[0xE2 + i] = c
for i in range(10):
    E2A[0xF0 + i] = str(i)
E2A[0x4B] = '.'
E2A[0x5B] = '$'
E2A[0x7B] = '#'
E2A[0x7C] = '@'


def name_at(b, off):
    """The 8 bytes at off as a symbol, or None if they cannot be one."""
    out = []
    for i in range(8):
        c = E2A.get(b[off + i])
        if c is None:
            return None
        out.append(c)
    s = ''.join(out)
    # Trailing blanks only: a blank inside a name means this is not an entry.
    t = s.rstrip()
    if not t or ' ' in t:
        return None
    # A symbol starts with a letter and is at most 8 characters.
    if not ('A' <= t[0] <= 'Z' or t[0] in '$#@'):
        return None
    return t


def entries(b, off, limit):
    """The run of 12-byte name+address entries starting at off."""
    out = []
    while off + 12 <= len(b):
        n = name_at(b, off)
        if n is None:
            break
        a = int.from_bytes(b[off + 8:off + 12], 'big')
        if a >= limit:
            break
        out.append((n, a, off))
        off += 12
    return out


def find_table(b):
    """The longest run of entries in the image -- that is DMKSYMTB.

    DMKSYM is PUNCHed with 'SPB', so it starts on a page boundary, but the
    table's first entry is a few bytes in; the scan does not assume either.
    """
    best = []
    off = 0
    n = len(b)
    while off + 12 <= n:
        # Cheap reject: byte 0 must be an EBCDIC letter.
        if E2A.get(b[off], ' ') == ' ':
            off += 1
            continue
        run = entries(b, off, n)
        if len(run) > len(best):
            best = run
        off += max(12 * len(run), 1)
    return best


def main():
    if len(sys.argv) < 3:
        print(__doc__)
        return 2
    b = open(sys.argv[1], 'rb').read()
    tab = find_table(b)
    if len(tab) < 50:
        print(f'### only {len(tab)} entries found -- that is not DMKSYMTB.')
        print('### Is this image a dump of a machine that actually IPLed?')
        return 1
    print(f'DMKSYMTB: {len(tab)} entries at X{tab[0][2]:05X}, '
          f'{tab[0][0]} .. {tab[-1][0]}')
    byaddr = sorted(tab, key=lambda e: e[1])

    args = sys.argv[2:]
    if '--map' in args:
        for n, a, _ in byaddr:
            print(f'  X{a:05X}  {n}')
        return 0
    if '--near' in args:
        pat = args[args.index('--near') + 1].upper()
        for n, a, _ in byaddr:
            if pat in n:
                print(f'  X{a:05X}  {n}')
        return 0

    for s in args:
        want = int(s, 16)
        before = [e for e in byaddr if e[1] <= want]
        after = [e for e in byaddr if e[1] > want]
        print(f'X{want:05X}')
        if before:
            n, a, _ = before[-1]
            print(f'   {n:<8} at X{a:05X}  +{want - a} bytes')
            # Everything sharing that address -- entry points often coincide.
            same = [e[0] for e in before if e[1] == a and e[0] != n]
            if same:
                print(f'   {"":8}    also {", ".join(same)}')
        else:
            print('   below the first symbol')
        if after:
            n, a, _ = after[0]
            print(f'   {n:<8} at X{a:05X}  -{a - want} bytes')
    return 0


if __name__ == '__main__':
    sys.exit(main())
