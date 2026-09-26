#!/usr/bin/env python3
"""
LRA characterisation -- the largest untested dependency in the DAT path.

WHY THIS MATTERS MORE THAN ITS SIZE SUGGESTS.  CP's TRANS macro is invoked
174 times and its core is:

    LCTL  C1,C1,VMSEG -  GET SEGMENT TABLE ORIGIN
    LRA   &RV,0(0,&UR)   AND DO HARDWARE TRANSLATE
    BC    8,TRN&NL       PAGE IS RESIDENT

So every virtual-to-real translation in CP goes through one LRA and a
condition-code test.  And Appendix F of the ESA/390 Principles of Operation
lists "Changes to LOAD REAL ADDRESS" among the differences from S/370 --
without this test, 174 sites rest on an instruction whose ESA/390 behaviour
had been assumed rather than checked.

WHAT THIS TEST FOUND, WHICH WAS NOT WHAT IT WAS LOOKING FOR.

The worry was LRA's RESULT: if it truncated to 24 bits in 24-bit mode,
TRANS could never return an above-the-line real address.  The result is
fine.  From control.c the threshold is 2 GB, not 16 MB, and the addressing
mode does not enter into it:

    if (regs->dat.raddr <= 0x7FFFFFFF)
        regs->GR_L(r1) = regs->dat.raddr;
    else if (cc == 0)
        program_interrupt(PGM_SPECIAL_OPERATION_EXCEPTION);

BUT THE OPERAND ADDRESS IS TRUNCATED, AND THAT IS WORSE.  Running case A
in 24-bit mode with R6 = 01005000 gave cc=0 and R2 = 00005000.  The
effective address was masked to 24 bits BEFORE translation, so LRA was
asked about virtual 005000 -- segment 0, page 5 -- which is validly mapped,
and answered correctly about the wrong address.

    24-bit mode:  LRA 2,0(0,6)  R6=01005000  ->  cc 0, R2 = 00005000
    31-bit mode:  LRA 2,0(0,6)  R6=01005000  ->  cc 0, R2 = 01100000

CONSEQUENCE FOR CP, AND IT IS A HARD REQUIREMENT.  TRANS does
LRA &RV,0(0,&UR) at 174 sites.  While CP runs AMODE 24, those sites CANNOT
ASK ABOUT AN ABOVE-THE-LINE VIRTUAL ADDRESS AT ALL -- the question is
truncated before it is put.  And the failure is silent and plausible: cc=0
with a real address that belongs to a different page.

So converting CP to AMODE 31 is a PREREQUISITE for paging above the line,
not an independent choice that could be deferred.  That reorders the
milestones: M2 cannot translate above-the-line addresses unless the modules
containing TRANS run AMODE 31.

A NOTE ON TEST DESIGN.  A version of case A that checked only cc=0 would
have PASSED, because cc=0 is exactly what a truncated-but-valid translation
returns.  Comparing the returned real address against the expected one is
what caught it.

DAT IS OFF THROUGHOUT.  LRA translates through the tables designated by
CR1 whether or not DAT is enabled in the PSW, and CP relies on that.
Keeping DAT off also means any accidental storage reference would fault
rather than silently translate.

FIVE CASES.  A runs in 24-bit mode; the rest need 31-bit, because their
virtual addresses are above the line and would otherwise be truncated into
a different and validly-mapped part of the address space.

    A   cc=0  24-bit: the operand IS truncated      <-- the finding
    A2  cc=0  31-bit: same LRA, correct answer
    B   cc=1  segment-table entry invalid
    C   cc=2  page-table entry invalid
    D   cc=3  address beyond the segment-table length

A NOTE ON THE FIXTURE.  dat4b.py fills unused page-table entries with
X'00000020'.  That is SEGTAB_INVALID, the SEGMENT invalid bit; in a PAGE
table entry the invalid bit is X'00000400'.  So those entries are actually
VALID, with a page-frame address of zero.  It did not matter to 4b, which
only ever referenced page 5 -- but case C here needs a genuinely invalid
PTE, so this builds one with X'400' explicitly.
"""
import sys
sys.path.insert(0, ".")
from asm import Asm, psw

SEGTAB    = 0x3000
PAGETAB0  = 0x3080
PAGETAB16 = 0x30C0
CR0       = 0x00B00000     # 1 MB segments, 4 KB pages -- checked before any table
CR1       = SEGTAB | 0x01  # STL 1 -> 32 entries, so segments 0-31 exist

VIRT_OK   = 0x01005000     # segment 16, page 5  -> valid, above the line
REAL_OK   = 0x01100000     # 17 MB
VIRT_SEG  = 0x00100000     # segment 1  -> STE invalid          -> cc=1
VIRT_PAGE = 0x01006000     # segment 16, page 6 -> PTE invalid   -> cc=2
VIRT_LEN  = 0x02000000     # segment 32 -> beyond STL 1          -> cc=3

STE_INVALID = 0x20         # segment-table entry invalid bit
PTE_INVALID = 0x400        # PAGE-table entry invalid bit -- NOT 0x20

assert VIRT_OK >> 20 == 16 and (VIRT_OK >> 12) & 0xFF == 5
assert VIRT_SEG >> 20 == 1
assert VIRT_PAGE >> 20 == 16 and (VIRT_PAGE >> 12) & 0xFF == 6
assert VIRT_LEN >> 20 == 32, "must exceed the 32 entries STL 1 gives"

a = Asm()
a.base = 0x2002


def lra(r1, b2):
    """LRA r1,0(0,b2) -- RX, opcode B1, index register 0."""
    return bytes([0xB1, (r1 << 4), (b2 << 4), 0x00])


# ------------------------------------------------------------------- code
a.label("START")
a.insn(2, lambda s: bytes([0x05, 0xF0]), "BALR  15,0", "")
a.insn(4, lambda s: bytes([0x41, 0xF0]) + s.bd(15, "START", 2), "LA    15,0(0,15)",
       "Clear bits 0-7.  Stays 24-bit from here -- that is the point")
a.insn(6, lambda s: bytes([0xD2, 0x07, 0x00, 0x68]) + s.bd(15, "PCPSW"),
       "MVC   X'68'(8,0),PCPSW", "Arm the failure answer first")
a.insn(4, lambda s: bytes([0xB7, 0x01]) + s.bd(15, "CRVALS"), "LCTL  0,1,CRVALS",
       "CR0 format AND CR1 origin.  CR0 is checked before any table read")

a.insn(4, lambda s: bytes([0x58, 0x60]) + s.bd(15, "AVOK"), "L     6,AVOK", "")
a.insn(4, lambda s: bytes([0x58, 0x70]) + s.bd(15, "AVSEG"), "L     7,AVSEG", "")
a.insn(4, lambda s: bytes([0x58, 0x80]) + s.bd(15, "AVPAGE"), "L     8,AVPAGE", "")
a.insn(4, lambda s: bytes([0x58, 0x90]) + s.bd(15, "AVLEN"), "L     9,AVLEN", "")

# --- case A: 24-bit mode.  THE FINDING: the operand is truncated ---
a.insn(4, lambda s: lra(2, 6), "LRA   2,0(0,6)",
       "CASE A: R6 = 01005000, but we are in 24-BIT MODE, so the effective")
a.insn(4, lambda s: bytes([0x47, 0x70]) + s.bd(15, "FAILA1"), "BC    7,FAILA1",
       "address is masked to 005000 BEFORE translation.  cc is still 0 --")
a.insn(4, lambda s: bytes([0x59, 0x20]) + s.bd(15, "ATRUNC"), "C     2,ATRUNC",
       "segment 0 page 5 is validly mapped -- so only comparing the ANSWER")
a.insn(4, lambda s: bytes([0x47, 0x70]) + s.bd(15, "FAILA2"), "BC    7,FAILA2",
       "catches it.  Expect 00005000, the identity mapping, NOT 01100000")

# --- into 31-bit mode.  R15 was cleared with LA at entry, so it survives ---
a.insn(4, lambda s: bytes([0x58, 0x40]) + s.bd(15, "A31"), "L     4,A31", "")
a.insn(2, lambda s: bytes([0x0B, 0x04]), "BSM   0,4", "bit 0 set = 31-bit")
a.align(4)
a.label("N31")

# --- case A2: the identical LRA, now able to see the whole address ---
a.insn(4, lambda s: lra(2, 6), "LRA   2,0(0,6)",
       "CASE A2: N31: same instruction, same register, 31-bit mode.")
a.insn(4, lambda s: bytes([0x47, 0x70]) + s.bd(15, "FAILA3"), "BC    7,FAILA3",
       "Now the operand reaches translation intact")
a.insn(4, lambda s: bytes([0x59, 0x20]) + s.bd(15, "AREAL"), "C     2,AREAL",
       "and R2 is the full 31-bit real address 01100000 = 17 MB, proving")
a.insn(4, lambda s: bytes([0x47, 0x70]) + s.bd(15, "FAILA4"), "BC    7,FAILA4",
       "the RESULT was never the problem -- the question was")

# --- case B: cc=1, segment-table entry invalid ---
a.insn(4, lambda s: lra(3, 7), "LRA   3,0(0,7)",
       "CASE B: segment 1, whose STE carries the invalid bit X'20'")
a.insn(4, lambda s: bytes([0x47, 0xB0]) + s.bd(15, "FAILB"), "BC    11,FAILB",
       "cc must be 1.  Mask 11 = branch on cc 0, 2 or 3")

# --- case C: cc=2, page-table entry invalid ---
a.insn(4, lambda s: lra(4, 8), "LRA   4,0(0,8)",
       "CASE C: segment 16 page 6, PTE X'400' -- the PAGE invalid bit, not")
a.insn(4, lambda s: bytes([0x47, 0xD0]) + s.bd(15, "FAILC"), "BC    13,FAILC",
       "the segment one.  Needs 31-bit or it would truncate to segment 0")

# --- case D: cc=3, beyond the segment-table length ---
a.insn(4, lambda s: lra(5, 9), "LRA   5,0(0,9)",
       "CASE D: segment 32, one past the 32 entries STL 1 provides")
a.insn(4, lambda s: bytes([0x47, 0xE0]) + s.bd(15, "FAILD"), "BC    14,FAILD",
       "cc must be 3.  Mask 14 = branch on cc 0, 1 or 2")

a.insn(4, lambda s: bytes([0x82, 0x00]) + s.bd(15, "PASSPSW"), "LPSW  PASSPSW", "")

FAILS = (("FAILA1","FA1PSW"), ("FAILA2","FA2PSW"),
         ("FAILA3","FA3PSW"), ("FAILA4","FA4PSW"),
         ("FAILB","FBPSW"), ("FAILC","FCPSW"), ("FAILD","FDPSW"))
for n, p in FAILS:
    a.label(n)
    a.insn(4, (lambda p: lambda s: bytes([0x82,0x00]) + s.bd(15, p))(p),
           "LPSW  %s" % p, "%s:" % n)

# ------------------------------------------------------------------- data
for name, ia in (("PASSPSW", 0x006009),
                 ("FA1PSW", 0x000F01),   # case A: cc was not 0
                 ("FA2PSW", 0x000F02),   # case A: 24-bit answer not the
                                         #   truncated one -- READ R2
                 ("FA3PSW", 0x000F11),   # case A2: cc was not 0 in 31-bit
                 ("FA4PSW", 0x000F12),   # case A2: R2 not 01100000 -- READ R2
                 ("FBPSW",  0x000F03),   # case B: cc was not 1
                 ("FCPSW",  0x000F04),   # case C: cc was not 2
                 ("FDPSW",  0x000F05),   # case D: cc was not 3
                 ("PCPSW",  0x000DED)):
    a.data(name, (lambda ia: lambda s: psw(ia))(ia), "", align=8)

a.data("CRVALS", lambda s: CR0.to_bytes(4,"big") + CR1.to_bytes(4,"big"),
       "CR0 = ESA/390 1M/4K format; CR1 = STO 3000, STL 1", align=4)
a.data("AREAL",  lambda s: REAL_OK.to_bytes(4,"big"), "expected real, 17 MB", align=4)
a.data("ATRUNC", lambda s: (0x00005000).to_bytes(4,"big"),
       "what 24-bit mode gets instead: segment 0 page 5, identity-mapped", align=4)
a.data("A31", lambda s: (0x80000000 | s.addr("N31")).to_bytes(4,"big"),
       "bit 0 set = 31-bit", align=4)
a.data("AVOK",   lambda s: VIRT_OK.to_bytes(4,"big"), "valid, above the line", align=4)
a.data("AVSEG",  lambda s: VIRT_SEG.to_bytes(4,"big"), "segment invalid", align=4)
a.data("AVPAGE", lambda s: VIRT_PAGE.to_bytes(4,"big"), "page invalid", align=4)
a.data("AVLEN",  lambda s: VIRT_LEN.to_bytes(4,"big"), "beyond table length", align=4)

a.layout().assemble(size=0x1100)     # must reach PAGETAB16 at 30C0

# --- the tables ---
for i in range(32):
    a.put(SEGTAB + 4*i, STE_INVALID.to_bytes(4, "big"))
a.put(SEGTAB + 4*0,  PAGETAB0.to_bytes(4, "big"))
a.put(SEGTAB + 4*16, PAGETAB16.to_bytes(4, "big"))
for i in range(16):
    a.put(PAGETAB0 + 4*i, (i * 0x1000).to_bytes(4, "big"))
    # Correct PTE invalid bit here, unlike dat4b.py -- see the header.
    a.put(PAGETAB16 + 4*i, PTE_INVALID.to_bytes(4, "big"))
a.put(PAGETAB16 + 4*5, REAL_OK.to_bytes(4, "big"))

a.check_align(("CRVALS",4,"LCTL"), ("AREAL",4,"C"), ("ATRUNC",4,"C"),
              ("A31",4,"L"), ("AVOK",4,"L"),
              ("AVSEG",4,"L"), ("AVPAGE",4,"L"), ("AVLEN",4,"L"),
              *[(p,8,"LPSW") for _, p in FAILS],
              ("PASSPSW",8,"LPSW"), ("PCPSW",8,"program new PSW"))
assert SEGTAB % 4096 == 0 and PAGETAB0 % 64 == 0 and PAGETAB16 % 64 == 0
assert a.end <= SEGTAB, "code must not overlap the tables"

a.print_listing()
print("\n  CASE A  24-bit: virtual %08X TRUNCATED to 00005000 -> real 00005000  cc 0"
      % VIRT_OK)
print("  CASE A2 31-bit: virtual %08X -> segment %2d page %2d -> real %08X  cc 0"
      % (VIRT_OK, VIRT_OK >> 20, (VIRT_OK >> 12) & 0xFF, REAL_OK))
print("  CASE B  virtual %08X -> segment %2d              STE invalid  cc 1"
      % (VIRT_SEG, VIRT_SEG >> 20))
print("  CASE C  virtual %08X -> segment %2d page %2d      PTE invalid  cc 2"
      % (VIRT_PAGE, VIRT_PAGE >> 20, (VIRT_PAGE >> 12) & 0xFF))
print("  CASE D  virtual %08X -> segment %2d              beyond STL   cc 3"
      % (VIRT_LEN, VIRT_LEN >> 20))
print("\n  SEGTAB[0]    = %08X" % int.from_bytes(a.read(SEGTAB, 4), "big"))
print("  SEGTAB[1]    = %08X  (invalid)" % int.from_bytes(a.read(SEGTAB+4, 4), "big"))
print("  SEGTAB[16]   = %08X" % int.from_bytes(a.read(SEGTAB+64, 4), "big"))
print("  PAGETAB16[5] = %08X" % int.from_bytes(a.read(PAGETAB16+20, 4), "big"))
print("  PAGETAB16[6] = %08X  (invalid, X'400')"
      % int.from_bytes(a.read(PAGETAB16+24, 4), "big"))
print("  ends %06X" % a.end)

end = (a.end + 7) & ~7
cmds = a.pokes((0x2000, end, 8), (SEGTAB, SEGTAB+128, 16),
               (PAGETAB0, PAGETAB0+64, 16), (PAGETAB16, PAGETAB16+64, 16))
open("lra1.cmds", "w").write("\n".join(cmds) + "\n")
print("\n%d poke commands" % len(cmds))
