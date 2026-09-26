#!/usr/bin/env python3
"""
DAT step 4a -- can a virtual address ABOVE the 16 MB line be translated?

This is the question the project actually needs answered.  Steps 1 to 3
built the ground for it: tables accepted, translation demonstrably walking
the page table, AMODE 31 entered and left, DAT still correct while there.

Target: virtual 01005000, stored to in 31-bit mode with DAT on.

    segment index   01005000 >> 20      = 16      <- past the line
    page index     (01005000 >> 12) & FF = 5
    byte offset                           000

REAL storage stays entirely below the line.  Segment 16's page table
points page 5 at real frame 7, so the whole experiment is whether the
31-bit VIRTUAL address survives translation -- not whether Hercules can
address real storage above 16 MB, which is a separate question and step
4b.

The table has to grow for the first time.  A sixteen-entry segment table
cannot reach segment 16 at all:

    SEGTAB  3000  32 entries, STL 1        (was 16 entries, STL 0)
      [0]   -> PAGETAB0                    identity, pages 0-15
      [16]  -> PAGETAB16                   page 5 -> real frame 7
      rest  invalid
    PAGETAB0   3080   64-byte aligned as SEGTAB_PTO requires
    PAGETAB16  30C0
    CR1 = 00003001                         STO 3000, STL 1

Why real 5000 is the control: if the address were truncated to 24 bits,
01005000 becomes 005000, and PAGETAB0 maps virtual 5000 to real 5000
identically.  So a truncated store lands on real 5000 and nowhere near
frame 7.  Checking both addresses distinguishes the three outcomes --
translated, truncated, or not stored at all -- which one address could
not.
"""
import sys
sys.path.insert(0, ".")
from asm import Asm, psw

HIGH     = 0x01005000      # the virtual address above the line
SEGTAB   = 0x3000
PAGETAB0 = 0x3080
PAGETAB16= 0x30C0
CR1      = SEGTAB | 0x01   # STL 1: two 64-byte units, 32 entries

a = Asm()
a.base = 0x2002

a.label("START")
a.insn(2, lambda s: bytes([0x05, 0xF0]), "BALR  15,0", "")
a.insn(4, lambda s: bytes([0x41, 0xF0]) + s.bd(15, "START", 2), "LA    15,0(0,15)",
       "Clear bits 0-7: BALR left ILC/CC/mask there, and in 31-bit")
a.insn(6, lambda s: bytes([0xD2, 0x07, 0x00, 0x68]) + s.bd(15, "PCPSW"),
       "MVC   X'68'(8,0),PCPSW", "mode those would be address bits")
a.insn(4, lambda s: bytes([0xB7, 0x01]) + s.bd(15, "CRVALS"), "LCTL  0,1,CRVALS",
       "CR1 now carries STL 1 -- 32 segments, so entry 16 exists")
a.insn(4, lambda s: bytes([0x58, 0x20]) + s.bd(15, "A5000"), "L     2,A5000",
       "R2 = 00005000, where a TRUNCATED store would land")
a.insn(4, lambda s: bytes([0x58, 0x30]) + s.bd(15, "A7000"), "L     3,A7000",
       "R3 = 00007000, the real frame segment 16 page 5 points at")
a.insn(4, lambda s: bytes([0x58, 0x60]) + s.bd(15, "AHIGH"), "L     6,AHIGH",
       "R6 = 01005000, above the line")
a.insn(4, lambda s: bytes([0x92, 0x00, 0x20, 0x00]), "MVI   0(2),X'00'",
       "Clear both with DAT off, so nothing left over can be")
a.insn(4, lambda s: bytes([0x92, 0x00, 0x30, 0x00]), "MVI   0(3),X'00'",
       "mistaken for this run's store")
a.insn(4, lambda s: bytes([0xAD, 0x04]) + s.bd(15, "MASKSAVE"),
       "STOSM MASKSAVE,X'04'", "DAT on")
a.insn(4, lambda s: bytes([0x58, 0x40]) + s.bd(15, "A31"), "L     4,A31", "")
a.insn(2, lambda s: bytes([0x0B, 0x04]), "BSM   0,4", "enter 31-bit mode at N31")
a.align(4)
a.label("N31")
a.insn(2, lambda s: bytes([0x1B, 0x11]), "SR    1,1", "N31:")
a.insn(2, lambda s: bytes([0x0B, 0x10]), "BSM   1,0", "report the amode in R1 bit 0")
a.insn(2, lambda s: bytes([0x12, 0x11]), "LTR   1,1", "")
a.insn(4, lambda s: bytes([0x47, 0xB0]) + s.bd(15, "FAIL1"), "BNM   FAIL1",
       "still 24-bit: nothing below would mean anything")
a.insn(4, lambda s: bytes([0x92, 0xAA, 0x60, 0x00]), "MVI   0(6),X'AA'",
       "THE TEST.  Store at virtual 01005000, above the line,")
a.insn(4, lambda s: bytes([0x58, 0x50]) + s.bd(15, "A24"), "L     5,A24",
       "in 31-bit mode, through DAT")
a.insn(2, lambda s: bytes([0x0B, 0x05]), "BSM   0,5", "back to 24-bit at N24")
a.align(4)
a.label("N24")
a.insn(4, lambda s: bytes([0xAC, 0xFB]) + s.bd(15, "MASKSAVE"),
       "STNSM MASKSAVE,X'FB'", "N24: DAT off")
a.insn(4, lambda s: bytes([0x95, 0xAA, 0x30, 0x00]), "CLI   0(3),X'AA'",
       "real 7000 -- did the above-the-line address translate?")
a.insn(4, lambda s: bytes([0x47, 0x70]) + s.bd(15, "FAIL2"), "BNE   FAIL2", "")
a.insn(4, lambda s: bytes([0x95, 0x00, 0x20, 0x00]), "CLI   0(2),X'00'",
       "real 5000 -- or was it truncated to 24 bits?")
a.insn(4, lambda s: bytes([0x47, 0x70]) + s.bd(15, "FAIL3"), "BNE   FAIL3", "")
a.insn(4, lambda s: bytes([0x82, 0x00]) + s.bd(15, "PASSPSW"), "LPSW  PASSPSW", "")
for n, p in (("FAIL1","F1PSW"), ("FAIL2","F2PSW"), ("FAIL3","F3PSW")):
    a.label(n)
    a.insn(4, (lambda p: lambda s: bytes([0x82,0x00]) + s.bd(15, p))(p),
           "LPSW  %s" % p, "%s:" % n)

for name, ia in (("PASSPSW", 0x006004), ("F1PSW", 0x000B31),
                 ("F2PSW", 0x000BA4), ("F3PSW", 0x000BA5),
                 ("PCPSW", 0x000DED)):
    a.data(name, (lambda ia: lambda s: psw(ia))(ia), "", align=8)
a.data("CRVALS",
       lambda s: (0x00B00000).to_bytes(4,"big") + CR1.to_bytes(4,"big"),
       "CR0 = 1M/4K format; CR1 = STO 3000 with STL 1", align=4)
a.data("A5000", lambda s: (0x5000).to_bytes(4,"big"), "", align=4)
a.data("A7000", lambda s: (0x7000).to_bytes(4,"big"), "", align=4)
a.data("AHIGH", lambda s: HIGH.to_bytes(4,"big"), "virtual 01005000", align=4)
a.data("A31", lambda s: (0x80000000 | s.addr("N31")).to_bytes(4,"big"),
       "bit 0 set = 31-bit", align=4)
a.data("A24", lambda s: s.addr("N24").to_bytes(4,"big"),
       "bit 0 clear = 24-bit", align=4)
a.data("MASKSAVE", lambda s: b"\x00", "", align=1)

a.layout().assemble(size=0x1100)   # must reach PAGETAB16 at 30C0

# --------------------------------------------------------------- tables
INVALID = (0x20).to_bytes(4, "big")
for i in range(32):
    a.put(SEGTAB + 4*i, INVALID)
a.put(SEGTAB + 4*0,  PAGETAB0.to_bytes(4, "big"))     # PTL 0, valid
a.put(SEGTAB + 4*16, PAGETAB16.to_bytes(4, "big"))    # PTL 0, valid
for i in range(16):
    a.put(PAGETAB0 + 4*i, (i * 0x1000).to_bytes(4, "big"))   # identity
    a.put(PAGETAB16 + 4*i, INVALID if i != 5 else (0x7000).to_bytes(4, "big"))

a.check_align(("CRVALS",4,"LCTL"), ("A5000",4,"L"), ("A7000",4,"L"),
              ("AHIGH",4,"L"), ("A31",4,"L"), ("A24",4,"L"),
              *[(n,8,"LPSW") for n in ("PASSPSW","F1PSW","F2PSW","F3PSW")],
              ("PCPSW",8,"program new PSW"))
assert SEGTAB % 4096 == 0, "segment table origin must be 4 KB aligned"
for pt in (PAGETAB0, PAGETAB16):
    assert pt % 64 == 0, "page table origin must be 64-byte aligned"
assert SEGTAB + 32*4 <= PAGETAB0, "segment table overruns first page table"
assert PAGETAB0 + 16*4 <= PAGETAB16, "page tables overlap"
assert a.end <= 0x3000, "program overruns the tables"

a.print_listing()
print("\n  virtual %08X -> segment %d, page %d" % (HIGH, HIGH >> 20, (HIGH >> 12) & 0xFF))
print("  CR1 = %08X  (STO %04X, STL 1 = 32 entries)" % (CR1, SEGTAB))
print("  SEGTAB[0]  = %08X -> PAGETAB0" % int.from_bytes(a.read(SEGTAB, 4), "big"))
print("  SEGTAB[16] = %08X -> PAGETAB16" % int.from_bytes(a.read(SEGTAB+64, 4), "big"))
print("  PAGETAB16[5] = %08X -> real frame 7" % int.from_bytes(a.read(PAGETAB16+20, 4), "big"))
print("  N31 = %06X, N24 = %06X, ends %06X" % (a.addr("N31"), a.addr("N24"), a.end))

end = (a.end + 7) & ~7
cmds = a.pokes((0x2000, end, 8), (SEGTAB, SEGTAB + 128, 16),
               (PAGETAB0, PAGETAB0 + 64, 16), (PAGETAB16, PAGETAB16 + 64, 16))
open("dat4a.cmds", "w").write("\n".join(cmds) + "\n")
print("\n%d poke commands" % len(cmds))
