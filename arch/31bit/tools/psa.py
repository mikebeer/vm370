#!/usr/bin/env python3
"""The PSA fields that say who was running and why, read from a savecore image,
with every PSW address resolved through CP's own symbol table.

    python3 psa.py <core.bin>

Why this exists: on 2 and 3 October the question "where is CP stuck" was
answered four times from a decoded `ia=` line in a Hercules panel dump, and the
answer was wrong or unusable every time.  The panel's `psw` command prints a
decoded line and a hex line from two separate reads of a RUNNING cpu, so they
disagree and neither is a measurement of a moment.  The old PSWs in the PSA are
different in kind: they were stored by the hardware at a defined instant and
they do not move.  `X20` says which instruction issued the SVC -- that is the
identity of DMKPTRAN's caller, which no amount of sampling the current PSW will
give.  Pair it with `symtab.py` and the answer is a name and an offset.

A worked example, from the image that found I-183:

    X20 SVC old   000C1000 00063906   ->  DMKPGS + 2310
    X38 I/O old   020C0000 000338CE   ->  DMKDSPQS + 306, sm=02, so the I/O
                                          mask WAS set and the interrupt WAS
                                          taken, in the dispatcher
    XBC IOINTPRM  000006A1            ->  I-174's device address, arriving
"""
import os
import subprocess
import sys

SYMTAB = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'symtab.py')

# name, offset.  ESA/390 assigned storage locations -- note that the S/370
# interval timer at X50 and the CSW at X40 are NOT here: they do not exist in
# this architecture, which is the whole subject of this conversion.  PoO
# Appendix F.
FIELDS = [
    ('X00 restart new', 0x00), ('X08 restart old', 0x08),
    ('X18 external old', 0x18), ('X20 SVC old', 0x20),
    ('X28 program old', 0x28), ('X30 mach-check old', 0x30),
    ('X38 I/O old', 0x38),
    ('X58 external new', 0x58), ('X60 SVC new', 0x60),
    ('X68 program new', 0x68), ('X70 mach-check new', 0x70),
    ('X78 I/O new', 0x78),
    ('X88 SVC int code', 0x88), ('X8C program int code', 0x8C),
    ('XB8 IOSSID', 0xB8), ('XBC IOINTPRM', 0xBC),
    ('X348 CPSTATUS', 0x348),
]


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        return 2
    img = sys.argv[1]
    b = open(img, 'rb').read()
    if len(b) < 0x400 or not any(b[:0x400]):
        print('### page 0 is empty -- this image is of a machine that never')
        print('### IPLed.  `--bare` omits the ipl as well as the dialogue.')
        return 1

    def w(o):
        return int.from_bytes(b[o:o + 4], 'big')

    want = set()
    for name, off in FIELDS:
        hi, lo = w(off), w(off + 4)
        print(f'{name:22} {hi:08X} {lo:08X}')
        if 'old' in name or 'new' in name:
            a = lo & 0x7FFFFFFF
            if 0 < a < len(b):
                want.add(a)

    if want:
        print('\n--- the PSW addresses, through CP\'s own symbol table ---')
        r = subprocess.run(
            [sys.executable, SYMTAB, img] + [f'{a:X}' for a in sorted(want)],
            capture_output=True, text=True)
        print(r.stdout or r.stderr)
    return 0


if __name__ == '__main__':
    sys.exit(main())
