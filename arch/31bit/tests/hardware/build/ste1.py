#!/usr/bin/env python3
"""
The segment-table flag collision -- does the invariant hold, and what breaks?

03-CP-INVENTORY.md found that two of CP's segment-table flags collide with
ESA/390 meanings:

    CP / S/370                    ESA/390
    SEGINV  = X'01'               invalid = X'20'
    SEGMIG  = X'10'               collides with the COMMON SEGMENT bit
    SEGENQ  = X'40'               collides with the lowest PTO bit

and argued they are "survivable but fragile: CP sets SEGMIG and SEGENQ only
when the pointer is zero, and the hardware does not examine other fields of an
invalid entry.  That needs to become an explicit invariant rather than an
accident, because an entry that is invalid to CP but valid to the hardware
would translate to X'000000x0'."

That was reasoning, not measurement.  This measures it, in two directions.

CASE A -- the invariant holding.  A segment-table entry with the ESA/390
invalid bit set AND both CP flags set:

    X'20' invalid  |  X'10' SEGMIG  |  X'40' SEGENQ  =  X'00000070'

LRA on an address in that segment must report cc=1, segment-translation
exception.  If it does, the hardware really does ignore the rest of an invalid
entry and CP's flags are safe to leave where they are.

CASE B -- the invariant broken, which is the part worth knowing.  The same two
CP flags WITHOUT the invalid bit:

    X'10' SEGMIG  |  X'40' SEGENQ  =  X'00000050'

To ESA/390 that is a perfectly VALID entry: a common segment whose page-table
origin is X'40'.  So the hardware walks a page table at real address X'40' --
inside lowcore, on top of the CSW and CAW -- and translates through whatever
bytes happen to be there.

The assertion for case B is simply that cc is NOT 1: the hardware did not
report segment-invalid, so it followed the entry.  What it then finds depends
on lowcore contents and does not matter; that it followed at all is the
finding.

WHY THIS IS WORTH A TEST RATHER THAN A COMMENT.  It turns "fragile, needs an
explicit invariant" into a demonstrated consequence: if any path in CP ever
sets SEGMIG or SEGENQ without SEGINV, translation silently proceeds through a
page table in lowcore.  No exception, no diagnostic -- the same failure shape
as CR6 in test 7.  That is an argument for asserting the invariant in code, not
in a comment.
"""
import sys
sys.path.insert(0, ".")
from asm import Asm, psw

CR0 = 0x00B00000
SEGTAB, PAGETAB0 = 0x3000, 0x3080
CR1 = SEGTAB | 0x01          # STL 1 -> 32 entries, so 17 and 18 exist

STE_INVALID = 0x20           # ESA/390 segment-invalid
CP_SEGMIG   = 0x10           # collides with COMMON SEGMENT
CP_SEGENQ   = 0x40           # collides with the lowest PTO bit

STE_CASE_A = STE_INVALID | CP_SEGMIG | CP_SEGENQ    # X'70' -- invalid + flags
STE_CASE_B = CP_SEGMIG | CP_SEGENQ                  # X'50' -- flags, NOT invalid

VIRT_A = 0x01100000          # segment 17
VIRT_B = 0x01200000          # segment 18

assert VIRT_A >> 20 == 17 and VIRT_B >> 20 == 18

a = Asm()
a.base = 0x2002


def lra(r1, b2):
    return bytes([0xB1, (r1 << 4), (b2 << 4), 0x00])


# ------------------------------------------------------------------- code
a.label("START")
a.insn(2, lambda s: bytes([0x05, 0xF0]), "BALR  15,0", "")
a.insn(4, lambda s: bytes([0x41, 0xF0]) + s.bd(15, "START", 2), "LA    15,0(0,15)", "")
a.insn(6, lambda s: bytes([0xD2, 0x07, 0x00, 0x68]) + s.bd(15, "PCPSW"),
       "MVC   X'68'(8,0),PCPSW", "")
a.insn(4, lambda s: bytes([0xB7, 0x01]) + s.bd(15, "CRVALS"), "LCTL  0,1,CRVALS",
       "CR0 format and CR1 origin.  DAT stays OFF -- LRA translates anyway")

# 31-bit mode: both test addresses are above the line, and in 24-bit mode the
# operand address would be truncated before translation (see 08-lra.rc).
a.insn(4, lambda s: bytes([0x58, 0x40]) + s.bd(15, "A31"), "L     4,A31", "")
a.insn(2, lambda s: bytes([0x0B, 0x04]), "BSM   0,4", "")
a.align(4)
a.label("N31")
a.insn(4, lambda s: bytes([0x58, 0x60]) + s.bd(15, "AVA"), "L     6,AVA", "N31:")
a.insn(4, lambda s: bytes([0x58, 0x70]) + s.bd(15, "AVB"), "L     7,AVB", "")

# --- CASE A: invalid bit set, plus both CP flags.  Must be cc=1 ---
a.insn(4, lambda s: lra(2, 6), "LRA   2,0(0,6)",
       "CASE A: segment 17, STE = X'70' -- invalid, SEGMIG and SEGENQ all set")
a.insn(4, lambda s: bytes([0x47, 0xB0]) + s.bd(15, "FAILA"), "BC    11,FAILA",
       "cc must be 1: the hardware ignores the rest of an invalid entry")

# --- CASE B: the same CP flags WITHOUT the invalid bit.  Must NOT be cc=1 ---
a.insn(4, lambda s: lra(3, 7), "LRA   3,0(0,7)",
       "CASE B: segment 18, STE = X'50' -- the CP flags alone.  To ESA/390")
a.insn(4, lambda s: bytes([0x47, 0x40]) + s.bd(15, "FAILB"), "BC    4,FAILB",
       "that is a VALID common segment with page-table origin X'40', so cc")
#                                                    must NOT be 1
a.insn(4, lambda s: bytes([0x82, 0x00]) + s.bd(15, "PASSPSW"), "LPSW  PASSPSW",
       "must not be 1 -- the hardware followed it into lowcore")

for n, p in (("FAILA","FAPSW"), ("FAILB","FBPSW")):
    a.label(n)
    a.insn(4, (lambda p: lambda s: bytes([0x82,0x00]) + s.bd(15, p))(p),
           "LPSW  %s" % p, "%s:" % n)

# ------------------------------------------------------------------- data
for name, ia in (("PASSPSW", 0x00600D),
                 ("FAPSW", 0x001301),    # case A: invalid entry NOT honoured
                 ("FBPSW", 0x001302),    # case B: hardware rejected it after all
                 ("PCPSW", 0x000DED)):
    a.data(name, (lambda ia: lambda s: psw(ia))(ia), "", align=8)

a.data("CRVALS", lambda s: CR0.to_bytes(4,"big") + CR1.to_bytes(4,"big"), "", align=4)
a.data("AVA", lambda s: VIRT_A.to_bytes(4,"big"), "segment 17", align=4)
a.data("AVB", lambda s: VIRT_B.to_bytes(4,"big"), "segment 18", align=4)
a.data("A31", lambda s: (0x80000000 | s.addr("N31")).to_bytes(4,"big"), "", align=4)

a.layout().assemble(size=0x1100)

for i in range(32):
    a.put(SEGTAB + 4*i, STE_INVALID.to_bytes(4, "big"))
a.put(SEGTAB + 4*0,  PAGETAB0.to_bytes(4, "big"))
for i in range(16):
    a.put(PAGETAB0 + 4*i, (i * 0x1000).to_bytes(4, "big"))
a.put(SEGTAB + 4*17, STE_CASE_A.to_bytes(4, "big"))
a.put(SEGTAB + 4*18, STE_CASE_B.to_bytes(4, "big"))

a.check_align(("CRVALS",4,"LCTL"), ("AVA",4,"L"), ("AVB",4,"L"), ("A31",4,"L"),
              ("PASSPSW",8,"LPSW"), ("FAPSW",8,"LPSW"), ("FBPSW",8,"LPSW"),
              ("PCPSW",8,"program new PSW"))
assert a.end <= SEGTAB

a.print_listing()
print("\n  CASE A  segment 17  STE = %08X  invalid|SEGMIG|SEGENQ  expect cc 1"
      % STE_CASE_A)
print("  CASE B  segment 18  STE = %08X  SEGMIG|SEGENQ only      expect cc NOT 1"
      % STE_CASE_B)
print("          to ESA/390 that is a common segment with PTO = %02X --"
      % (STE_CASE_B & 0x7FFFFFC0))
print("          a page table inside lowcore, on top of the CSW and CAW")
print("  ends %06X" % a.end)

end = (a.end + 7) & ~7
cmds = a.pokes((0x2000, end, 8), (SEGTAB, SEGTAB+128, 16),
               (PAGETAB0, PAGETAB0+64, 16))
open("ste1.cmds", "w").write("\n".join(cmds) + "\n")
print("\n%d poke commands" % len(cmds))
