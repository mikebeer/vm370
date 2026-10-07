#!/usr/bin/env python3
"""mkg390.py <prog.bin> <out.aws>: a tape-IPLable ESA/390 test guest (M7).

Record 1 (24 bytes): IPL PSW 00080000 80000400 (EC/ESA format, AMODE 31,
start X'400') and one CCW reading record 2 to X'400'.  Record 2 is the
program, assembled with `s390x-linux-gnu-as -m31 -mesa` and flattened with
objcopy (see Makefile-free recipe in README.md)."""
import struct, sys
prog = open(sys.argv[1], 'rb').read()
prog += b'\x00' * (-len(prog) % 8)
assert len(prog) <= 0xC00, 'program must stay below X1000 (results area)'
rec1 = bytes.fromhex('00080000' '80000400')
rec1 += struct.pack('>BBHBBH', 0x02, 0, 0x0400, 0x20, 0, len(prog))  # read, SILI
rec1 += bytes(8)
def aws(records):
    out = bytearray(); prev = 0
    for r in records:
        out += struct.pack('<HHBB', len(r), prev, 0xA0, 0) + r
        prev = len(r)
    out += struct.pack('<HHBB', 0, prev, 0x40, 0)
    out += struct.pack('<HHBB', 0, 0, 0x40, 0)
    return bytes(out)
open(sys.argv[2], 'wb').write(aws([rec1, prog]))
print('%s: %d-byte program, IPL PSW 00080000 80000400' % (sys.argv[2], len(prog)))
