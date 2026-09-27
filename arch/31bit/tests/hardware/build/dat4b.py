#!/usr/bin/env python3
"""
DAT step 4b -- an above-the-line REAL frame.

4a proved the virtual side: virtual 01005000 translated through segment
entry 16 to real frame 7, below the line.  This moves the real frame above
the line as well, which is the last hardware question.

    virtual 01005000  ->  real 01100000        (17 MB)

Checking it needs care.  With DAT off in 24-bit mode, real 01100000 is not
addressable at all -- the address truncates.  So the checks run in 31-bit
mode with DAT OFF, where addresses are real and bits 1-31 wide.  That
means entering 31-bit mode BEFORE clearing the frames, not after.

A distinct fourth check earns its place: write 55 to real 01100000 and
read it back, in 31-bit real mode, BEFORE any translation is involved.
If real storage above the line is simply not usable, that is a different
and more basic failure than translation failing to reach it, and without
this check the two would produce the same answer.
"""
import sys
sys.path.insert(0, ".")
from asm import Asm, psw

VIRT      = 0x01005000     # above the line, segment 16 page 5
REAL      = 0x01100000     # above the line, 17 MB -- MAINSIZE 64 covers it
SEGTAB    = 0x3000
PAGETAB0  = 0x3080
PAGETAB16 = 0x30C0
CR1       = SEGTAB | 0x01  # STL 1 -> 32 entries, so entry 16 exists

assert REAL & 0x7FFFF000 == REAL, "frame must be 4 KB aligned for PAGETAB_PFRA"

a = Asm()
a.base = 0x2002

a.label("START")
a.insn(2, lambda s: bytes([0x05, 0xF0]), "BALR  15,0", "")
a.insn(4, lambda s: bytes([0x41, 0xF0]) + s.bd(15, "START", 2), "LA    15,0(0,15)",
       "Mandatory before any AMODE 31 code: BALR leaves ILC, CC and")
a.insn(6, lambda s: bytes([0xD2, 0x07, 0x00, 0x68]) + s.bd(15, "PCPSW"),
       "MVC   X'68'(8,0),PCPSW", "the program mask in bits 0-7")
a.insn(4, lambda s: bytes([0xB7, 0x01]) + s.bd(15, "CRVALS"), "LCTL  0,1,CRVALS", "")
a.insn(4, lambda s: bytes([0x58, 0x20]) + s.bd(15, "A5000"), "L     2,A5000",
       "R2 = 00005000, where a truncated store would land")
a.insn(4, lambda s: bytes([0x58, 0x30]) + s.bd(15, "AREAL"), "L     3,AREAL",
       "R3 = 01100000, the real frame ABOVE the line")
a.insn(4, lambda s: bytes([0x58, 0x60]) + s.bd(15, "AVIRT"), "L     6,AVIRT",
       "R6 = 01005000, the virtual address above the line")
a.insn(4, lambda s: bytes([0x58, 0x40]) + s.bd(15, "A31"), "L     4,A31", "")
a.insn(2, lambda s: bytes([0x0B, 0x04]), "BSM   0,4",
       "31-bit mode FIRST, and DAT still off: real 01100000 is not")
a.align(4)
a.label("N31")
a.insn(2, lambda s: bytes([0x1B, 0x11]), "SR    1,1",
       "N31: addressable in 24-bit mode, so the clearing needs 31-bit")
a.insn(2, lambda s: bytes([0x0B, 0x10]), "BSM   1,0", "")
a.insn(2, lambda s: bytes([0x12, 0x11]), "LTR   1,1", "")
a.insn(4, lambda s: bytes([0x47, 0xB0]) + s.bd(15, "FAIL1"), "BNM   FAIL1",
       "still 24-bit: nothing below would mean anything")

a.insn(4, lambda s: bytes([0x92, 0x55, 0x30, 0x00]), "MVI   0(3),X'55'",
       "Is real storage above the line usable AT ALL?  31-bit,")
a.insn(4, lambda s: bytes([0x95, 0x55, 0x30, 0x00]), "CLI   0(3),X'55'",
       "DAT off, so this is plain real addressing with no")
a.insn(4, lambda s: bytes([0x47, 0x70]) + s.bd(15, "FAIL4"), "BNE   FAIL4",
       "translation involved.  A separate, more basic failure")

a.insn(4, lambda s: bytes([0x92, 0x00, 0x20, 0x00]), "MVI   0(2),X'00'",
       "Clear both, DAT still off")
a.insn(4, lambda s: bytes([0x92, 0x00, 0x30, 0x00]), "MVI   0(3),X'00'", "")
a.insn(4, lambda s: bytes([0xAD, 0x04]) + s.bd(15, "MASKSAVE"),
       "STOSM MASKSAVE,X'04'", "DAT on")
a.insn(4, lambda s: bytes([0x92, 0xAA, 0x60, 0x00]), "MVI   0(6),X'AA'",
       "THE TEST.  Virtual 01005000 above the line, translating to")
a.insn(4, lambda s: bytes([0xAC, 0xFB]) + s.bd(15, "MASKSAVE"),
       "STNSM MASKSAVE,X'FB'", "a real frame also above the line.  DAT off again")
a.insn(4, lambda s: bytes([0x95, 0xAA, 0x30, 0x00]), "CLI   0(3),X'AA'",
       "real 01100000 -- did it arrive?")
a.insn(4, lambda s: bytes([0x47, 0x70]) + s.bd(15, "FAIL2"), "BNE   FAIL2", "")
a.insn(4, lambda s: bytes([0x95, 0x00, 0x20, 0x00]), "CLI   0(2),X'00'",
       "real 5000 -- or was the address truncated?")
a.insn(4, lambda s: bytes([0x47, 0x70]) + s.bd(15, "FAIL3"), "BNE   FAIL3", "")
a.insn(4, lambda s: bytes([0x82, 0x00]) + s.bd(15, "PASSPSW"), "LPSW  PASSPSW", "")
for n, p in (("FAIL1","F1PSW"), ("FAIL2","F2PSW"),
             ("FAIL3","F3PSW"), ("FAIL4","F4PSW")):
    a.label(n)
    a.insn(4, (lambda p: lambda s: bytes([0x82,0x00]) + s.bd(15, p))(p),
           "LPSW  %s" % p, "%s:" % n)

for name, ia in (("PASSPSW", 0x006005), ("F1PSW", 0x000B31),
                 ("F2PSW", 0x000BA6), ("F3PSW", 0x000BA7),
                 ("F4PSW", 0x000BA8), ("PCPSW", 0x000DED)):
    a.data(name, (lambda ia: lambda s: psw(ia))(ia), "", align=8)
a.data("CRVALS",
       lambda s: (0x00B00000).to_bytes(4,"big") + CR1.to_bytes(4,"big"),
       "CR0 = 1M/4K format; CR1 = STO 3000, STL 1", align=4)
a.data("A5000", lambda s: (0x5000).to_bytes(4,"big"), "truncation control", align=4)
a.data("AREAL", lambda s: REAL.to_bytes(4,"big"), "real 01100000", align=4)
a.data("AVIRT", lambda s: VIRT.to_bytes(4,"big"), "virtual 01005000", align=4)
a.data("A31", lambda s: (0x80000000 | s.addr("N31")).to_bytes(4,"big"),
       "bit 0 set = 31-bit", align=4)
a.data("MASKSAVE", lambda s: b"\x00", "", align=1)

a.layout().assemble(size=0x1100)   # must reach PAGETAB16 at 30C0

# The two invalid bits are NOT the same, and using one for both is a real bug
# rather than a cosmetic one.  A segment-table entry is invalid when X'20' is
# set; a PAGE-table entry is invalid when X'400' is set.  Filling unused page
# table entries with X'20' leaves bit 0x400 CLEAR, so the hardware reads them
# as VALID entries whose page-frame real address is zero -- every unmapped page
# in the segment quietly aliased real page 0.  Harmless here only because the
# test touches one entry.  See docs/13-ISSUES.md I-06.
STE_INVALID = (0x20).to_bytes(4, "big")    # segment-table entry: bit 26
PTE_INVALID = (0x400).to_bytes(4, "big")   # page-table entry:    bit 21

for i in range(32):
    a.put(SEGTAB + 4*i, STE_INVALID)
a.put(SEGTAB + 4*0,  PAGETAB0.to_bytes(4, "big"))
a.put(SEGTAB + 4*16, PAGETAB16.to_bytes(4, "big"))
for i in range(16):
    a.put(PAGETAB0 + 4*i, (i * 0x1000).to_bytes(4, "big"))
    a.put(PAGETAB16 + 4*i, PTE_INVALID if i != 5 else REAL.to_bytes(4, "big"))

a.check_align(("CRVALS",4,"LCTL"), ("A5000",4,"L"), ("AREAL",4,"L"),
              ("AVIRT",4,"L"), ("A31",4,"L"),
              *[(n,8,"LPSW") for n in ("PASSPSW","F1PSW","F2PSW","F3PSW","F4PSW")],
              ("PCPSW",8,"program new PSW"))
assert SEGTAB % 4096 == 0 and PAGETAB0 % 64 == 0 and PAGETAB16 % 64 == 0
assert a.end <= 0x3000

a.print_listing()
print("\n  virtual %08X -> segment %d page %d -> real %08X"
      % (VIRT, VIRT >> 20, (VIRT >> 12) & 0xFF, REAL))
print("  SEGTAB[16]   = %08X" % int.from_bytes(a.read(SEGTAB+64, 4), "big"))
print("  PAGETAB16[5] = %08X" % int.from_bytes(a.read(PAGETAB16+20, 4), "big"))
print("  N31 = %06X, no return to 24-bit: the checks need 31-bit real mode"
      % a.addr("N31"))
print("  ends %06X" % a.end)

end = (a.end + 7) & ~7
cmds = a.pokes((0x2000, end, 8), (SEGTAB, SEGTAB+128, 16),
               (PAGETAB0, PAGETAB0+64, 16), (PAGETAB16, PAGETAB16+64, 16))
open("dat4b.cmds","w").write("\n".join(cmds) + "\n")
print("\n%d poke commands" % len(cmds))
