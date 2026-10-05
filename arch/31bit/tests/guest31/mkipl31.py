#!/usr/bin/env python3
"""Build G31.AWS: a tape-IPLable test guest that runs in AMODE 31 (M2 step 3).

Record 1 (24 bytes): the IPL PSW -- EC mode, bit 32 ON, start at X'400' --
and one CCW that reads record 2 to X'400'.  Record 2 is the program:

    0400 BALR  R12,0                base register (bit 0 on, AMODE 31)
         L     R2,=A(X'01FF0000')   above 16 MB
         MVC   0(8,R2),=C'AMODE 31' the store a 24-bit guest could not make
         L     R3,=A(X'01000000')   exactly 16 MB
         MVC   0(4,R3),=C'HI31'
         MVC   X'60'(8,0),NEWSVC    SVC new PSW: bit 32 on, handler below
         SVC   1                    an interrupt taken in AMODE 31
    HNDL MVC   16(8,R2),X'20'(0)    the SVC old PSW, for inspection at 1FF0010
         LPSW  WAIT31               000A0000 00000031: 'CP ENTERED; DISABLED WAIT'

What the console then shows (d 1ff0000.20): C1D4D6C4 C5404031 ('AMODE 31')
at 1FF0000 and the old PSW 000C0000 8000041E at 1FF0010 -- bit 32 on, the
address of HNDL -- and (d 1000000.10) C8C9F3F1 ('HI31') at 1000000.
"""
import struct, sys

def ebc(s):
    return s.encode('cp037')

prog = bytearray()
def emit(h):
    prog.extend(bytes.fromhex(h))
emit('05C0')                 # 0400 BALR R12,0
emit('5820C02E')             # 0402 L   R2,=A(01FF0000)     (0430)
emit('D2072000C036')         # 0406 MVC 0(8,R2),LITAM       (0438)
emit('5830C032')             # 040C L   R3,=A(01000000)     (0434)
emit('D2033000C03E')         # 0410 MVC 0(4,R3),LITHI       (0440)
emit('D2070060C046')         # 0416 MVC X'60'(8,0),NEWSVC   (0448)
emit('0A01')                 # 041C SVC 1
emit('D20720100020')         # 041E MVC 16(8,R2),X'20'(0)   HNDL
emit('8200C04E')             # 0424 LPSW WAIT31              (0450)
emit('0700')                 # 0428 BCR 0,0 (pad)
assert len(prog) == 0x2A
prog.extend(b'\x00' * (0x30 - len(prog)))
prog.extend(struct.pack('>I', 0x01FF0000))   # 0430
prog.extend(struct.pack('>I', 0x01000000))   # 0434
prog.extend(ebc('AMODE 31'))                 # 0438
prog.extend(ebc('HI31'))                     # 0440
prog.extend(b'\x00' * 4)                     # 0444
prog.extend(bytes.fromhex('00080000' '8000041E'))  # 0448 NEWSVC
prog.extend(bytes.fromhex('000A0000' '00000031'))  # 0450 WAIT31
prog.extend(b'\x00' * (0x80 - len(prog)))
assert len(prog) == 0x80

rec1 = bytes.fromhex('00080000' '80000400')          # IPL PSW: EC, AMODE 31, 0400
rec1 += bytes.fromhex('02000400' '20000080')          # CCW: read 0x80 to 0400, SILI
rec1 += bytes.fromhex('00000000' '00000000')
assert len(rec1) == 24

def aws(records):
    out = bytearray(); prev = 0
    for r in records:
        out += struct.pack('<HHBB', len(r), prev, 0xA0, 0) + r
        prev = len(r)
    out += struct.pack('<HHBB', 0, prev, 0x40, 0)     # tape mark
    out += struct.pack('<HHBB', 0, 0, 0x40, 0)
    return bytes(out)

open(sys.argv[1] if len(sys.argv) > 1 else 'G31.AWS', 'wb').write(aws([rec1, prog]))
print('G31.AWS: %d-byte program, IPL PSW 00080000 80000400' % len(prog))
