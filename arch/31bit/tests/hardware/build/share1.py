#!/usr/bin/env python3
"""
Frame-level sharing at PAGE granularity, with 1 MB segments.

WHAT THIS IS FOR.  05-CP67-PRIOR-ART.md carries the repository's most
load-bearing conclusion: that the 64 KB -> 1 MB segment change does NOT cost
a 16x loss of sharing granularity, because sharing need not be done by
repointing a segment table entry.  CP-67 ran 4 KB pages in 1 MB segments and
shared at 4 KB, by giving each machine its own page table populated from a
model and sharing the FRAMES.

That conclusion rests on IBM documentation from 1973.  It has never been
executed on ESA/390.  This does that.

    04-SHARED-SEGMENTS.md  measured what VM/370's segment-level sharing
                           costs at 1 MB: CMSOLD forces the whole first
                           megabyte common.
    05-CP67-PRIOR-ART.md   argued from CP-67 that the cost is avoidable.
    THIS TEST              proves the avoidance works on the real hardware.

THE SHAPE.  Two address spaces, A and B, with their own segment tables and
their own page tables.  Identical virtual addresses in both.  One virtual
page is mapped to the SAME real frame in both page tables; another is mapped
to DIFFERENT frames.  Then:

    share     write under A, read under B, at virtual 01005000 -> same frame
    isolate   write under A and under B at virtual 01006000    -> different

If both hold simultaneously, then 4 KB sharing granularity and 4 KB isolation
granularity coexist inside a single 1 MB segment -- which is precisely what
VM/370's SYSHRSG cannot express and what CP-67's FIRSTSP/LASTSP could.

    virtual 01005000  segment 16 page 5  ->  A: 01100000   B: 01100000  SHARED
    virtual 01006000  segment 16 page 6  ->  A: 01200000   B: 01300000  private

Note that all three frames are ABOVE THE LINE, so this also exercises the
case that matters rather than a convenient low-storage one.

THE STEP THAT WILL BITE ANYONE REPEATING THIS: PTLB.  Changing CR1 does not
invalidate the translation lookaside buffer.  Without a PTLB after each
switch, the second address space reads through the first one's cached
translations and the test passes for the wrong reason -- or fails
confusingly.  CP has 4 PTLB sites today and will need more.

Write protection is the OTHER half of CP-67's mechanism -- shared pages at
storage key 0, users running with PSW key F -- and it is a separate test,
because it is a separate mechanism and one change at a time has worked all
day.
"""
import sys
sys.path.insert(0, ".")
from asm import Asm, psw

CR0 = 0x00B00000        # ESA/390 1 MB segments, 4 KB pages

SEGTAB_A   = 0x3000     # 4 KB aligned
PAGETAB0_A = 0x3080     # 64 byte aligned; identity, pages 0-15
PAGE16_A   = 0x30C0     # segment 16's page table for A
SEGTAB_B   = 0x4000
PAGETAB0_B = 0x4080
PAGE16_B   = 0x40C0

CR1_A = SEGTAB_A | 0x01   # STL 1 -> 32 entries, so entry 16 exists
CR1_B = SEGTAB_B | 0x01

VSHARE  = 0x01005000    # segment 16, page 5
VPRIV   = 0x01006000    # segment 16, page 6
FSHARE  = 0x01100000    # 17 MB -- the frame both spaces map
FPRIV_A = 0x01200000    # 18 MB
FPRIV_B = 0x01300000    # 19 MB

STE_INVALID = 0x20
PTE_INVALID = 0x400

assert VSHARE >> 20 == 16 and (VSHARE >> 12) & 0xFF == 5
assert VPRIV >> 20 == 16 and (VPRIV >> 12) & 0xFF == 6
for f in (FSHARE, FPRIV_A, FPRIV_B):
    assert f & 0x7FFFF000 == f, "frame must be 4 KB aligned"

a = Asm()
a.base = 0x2002


def ptlb():
    return bytes([0xB2, 0x0D, 0x00, 0x00])


# ------------------------------------------------------------------- code
a.label("START")
a.insn(2, lambda s: bytes([0x05, 0xF0]), "BALR  15,0", "")
a.insn(4, lambda s: bytes([0x41, 0xF0]) + s.bd(15, "START", 2), "LA    15,0(0,15)",
       "Clear bits 0-7 before 31-bit mode")
a.insn(6, lambda s: bytes([0xD2, 0x07, 0x00, 0x68]) + s.bd(15, "PCPSW"),
       "MVC   X'68'(8,0),PCPSW", "Arm the failure answer first")

# 31-bit mode before anything else: the frames are all above the line, and
# with DAT off they are not addressable in 24-bit mode at all.
a.insn(4, lambda s: bytes([0x58, 0x40]) + s.bd(15, "A31"), "L     4,A31", "")
a.insn(2, lambda s: bytes([0x0B, 0x04]), "BSM   0,4", "31-bit mode, DAT still off")
a.align(4)
a.label("N31")

# Clear the three frames in 31-bit real mode, so residue cannot fake a pass.
a.insn(4, lambda s: bytes([0x58, 0x50]) + s.bd(15, "AFSHARE"), "L     5,AFSHARE",
       "N31:")
a.insn(4, lambda s: bytes([0x58, 0x60]) + s.bd(15, "AFPRIVA"), "L     6,AFPRIVA", "")
a.insn(4, lambda s: bytes([0x58, 0x70]) + s.bd(15, "AFPRIVB"), "L     7,AFPRIVB", "")
a.insn(4, lambda s: bytes([0x92, 0x00, 0x50, 0x00]), "MVI   0(5),X'00'", "")
a.insn(4, lambda s: bytes([0x92, 0x00, 0x60, 0x00]), "MVI   0(6),X'00'", "")
a.insn(4, lambda s: bytes([0x92, 0x00, 0x70, 0x00]), "MVI   0(7),X'00'", "")

# Confirm above-the-line real storage works at all, before translation is
# involved -- otherwise a later failure has two possible causes.
a.insn(4, lambda s: bytes([0x92, 0x5A, 0x50, 0x00]), "MVI   0(5),X'5A'", "")
a.insn(4, lambda s: bytes([0x95, 0x5A, 0x50, 0x00]), "CLI   0(5),X'5A'", "")
a.insn(4, lambda s: bytes([0x47, 0x70]) + s.bd(15, "FAIL0"), "BNE   FAIL0",
       "real storage above the line unusable -- a different, more basic fault")
a.insn(4, lambda s: bytes([0x92, 0x00, 0x50, 0x00]), "MVI   0(5),X'00'", "")

# Registers for the virtual addresses.
a.insn(4, lambda s: bytes([0x58, 0x80]) + s.bd(15, "AVSHARE"), "L     8,AVSHARE", "")
a.insn(4, lambda s: bytes([0x58, 0x90]) + s.bd(15, "AVPRIV"), "L     9,AVPRIV", "")

# ---- address space A ----
a.insn(4, lambda s: bytes([0xB7, 0x01]) + s.bd(15, "CRVALA"), "LCTL  0,1,CRVALA",
       "CR0 format + CR1 = segment table A")
a.insn(4, lambda s: ptlb(), "PTLB", "Purge: CR1 changes do NOT invalidate the TLB")
a.insn(4, lambda s: bytes([0xAD, 0x04]) + s.bd(15, "MASKSAVE"), "STOSM MASKSAVE,X'04'",
       "DAT on")
a.insn(4, lambda s: bytes([0x92, 0xC1, 0x80, 0x00]), "MVI   0(8),X'C1'",
       "'A' to the SHARED page, through A's tables")
a.insn(4, lambda s: bytes([0x92, 0xE1, 0x90, 0x00]), "MVI   0(9),X'E1'",
       "'a' to the PRIVATE page, through A's tables")
a.insn(4, lambda s: bytes([0xAC, 0xFB]) + s.bd(15, "MASKSAVE"), "STNSM MASKSAVE,X'FB'",
       "DAT off")

# ---- address space B ----
a.insn(4, lambda s: bytes([0xB7, 0x01]) + s.bd(15, "CRVALB"), "LCTL  0,1,CRVALB",
       "CR1 = segment table B.  Same virtual addresses, different tables")
a.insn(4, lambda s: ptlb(), "PTLB", "WITHOUT THIS the test reads A's cached translations")
a.insn(4, lambda s: bytes([0xAD, 0x04]) + s.bd(15, "MASKSAVE"), "STOSM MASKSAVE,X'04'", "")
a.insn(4, lambda s: bytes([0x95, 0xC1, 0x80, 0x00]), "CLI   0(8),X'C1'",
       "THE SHARING PROOF: the shared page read through B's tables must")
a.insn(4, lambda s: bytes([0x47, 0x70]) + s.bd(15, "FAILSH"), "BNE   FAILSH",
       "hold what A wrote, because both page tables point at one frame")
a.insn(4, lambda s: bytes([0x95, 0xE1, 0x90, 0x00]), "CLI   0(9),X'E1'",
       "THE ISOLATION PROOF: the private page must NOT hold A's byte,")
a.insn(4, lambda s: bytes([0x47, 0x80]) + s.bd(15, "FAILIS"), "BE    FAILIS",
       "even though it is the same virtual address in the same segment")
a.insn(4, lambda s: bytes([0x92, 0xE2, 0x90, 0x00]), "MVI   0(9),X'E2'",
       "'b' to B's private page")
a.insn(4, lambda s: bytes([0xAC, 0xFB]) + s.bd(15, "MASKSAVE"), "STNSM MASKSAVE,X'FB'", "")

# ---- back to A: isolation must hold in both directions ----
a.insn(4, lambda s: bytes([0xB7, 0x01]) + s.bd(15, "CRVALA"), "LCTL  0,1,CRVALA", "")
a.insn(4, lambda s: ptlb(), "PTLB", "")
a.insn(4, lambda s: bytes([0xAD, 0x04]) + s.bd(15, "MASKSAVE"), "STOSM MASKSAVE,X'04'", "")
a.insn(4, lambda s: bytes([0x95, 0xE1, 0x90, 0x00]), "CLI   0(9),X'E1'",
       "A's private page must still be A's byte, not B's")
a.insn(4, lambda s: bytes([0x47, 0x70]) + s.bd(15, "FAILIS2"), "BNE   FAILIS2", "")
a.insn(4, lambda s: bytes([0xAC, 0xFB]) + s.bd(15, "MASKSAVE"), "STNSM MASKSAVE,X'FB'", "")

# ---- and confirm the real frames directly, DAT off, 31-bit ----
a.insn(4, lambda s: bytes([0x95, 0xC1, 0x50, 0x00]), "CLI   0(5),X'C1'",
       "real 01100000 -- the shared frame")
a.insn(4, lambda s: bytes([0x47, 0x70]) + s.bd(15, "FAILR1"), "BNE   FAILR1", "")
a.insn(4, lambda s: bytes([0x95, 0xE1, 0x60, 0x00]), "CLI   0(6),X'E1'",
       "real 01200000 -- A's private frame")
a.insn(4, lambda s: bytes([0x47, 0x70]) + s.bd(15, "FAILR2"), "BNE   FAILR2", "")
a.insn(4, lambda s: bytes([0x95, 0xE2, 0x70, 0x00]), "CLI   0(7),X'E2'",
       "real 01300000 -- B's private frame")
a.insn(4, lambda s: bytes([0x47, 0x70]) + s.bd(15, "FAILR3"), "BNE   FAILR3", "")
a.insn(4, lambda s: bytes([0x82, 0x00]) + s.bd(15, "PASSPSW"), "LPSW  PASSPSW", "")

FAILS = (("FAIL0","F0PSW"), ("FAILSH","FSPSW"), ("FAILIS","FIPSW"),
         ("FAILIS2","FI2PSW"), ("FAILR1","FR1PSW"), ("FAILR2","FR2PSW"),
         ("FAILR3","FR3PSW"))
for n, p in FAILS:
    a.label(n)
    a.insn(4, (lambda p: lambda s: bytes([0x82,0x00]) + s.bd(15, p))(p),
           "LPSW  %s" % p, "%s:" % n)

# ------------------------------------------------------------------- data
for name, ia in (("PASSPSW", 0x00600A),
                 ("F0PSW",  0x001001),   # above-the-line real storage broken
                 ("FSPSW",  0x001011),   # SHARING failed -- frame not shared
                 ("FIPSW",  0x001012),   # ISOLATION failed -- private page shared
                 ("FI2PSW", 0x001013),   # isolation failed the other way
                 ("FR1PSW", 0x001021),   # shared frame wrong at real address
                 ("FR2PSW", 0x001022),   # A's private frame wrong
                 ("FR3PSW", 0x001023),   # B's private frame wrong
                 ("PCPSW",  0x000DED)):
    a.data(name, (lambda ia: lambda s: psw(ia))(ia), "", align=8)

a.data("CRVALA", lambda s: CR0.to_bytes(4,"big") + CR1_A.to_bytes(4,"big"),
       "CR0 + CR1 for space A", align=4)
a.data("CRVALB", lambda s: CR0.to_bytes(4,"big") + CR1_B.to_bytes(4,"big"),
       "CR0 + CR1 for space B", align=4)
a.data("AVSHARE", lambda s: VSHARE.to_bytes(4,"big"), "shared virtual", align=4)
a.data("AVPRIV",  lambda s: VPRIV.to_bytes(4,"big"), "private virtual", align=4)
a.data("AFSHARE", lambda s: FSHARE.to_bytes(4,"big"), "shared frame", align=4)
a.data("AFPRIVA", lambda s: FPRIV_A.to_bytes(4,"big"), "A's frame", align=4)
a.data("AFPRIVB", lambda s: FPRIV_B.to_bytes(4,"big"), "B's frame", align=4)
a.data("A31", lambda s: (0x80000000 | s.addr("N31")).to_bytes(4,"big"),
       "bit 0 set = 31-bit", align=4)
a.data("MASKSAVE", lambda s: b"\x00", "", align=1)

a.layout().assemble(size=0x2100)     # must reach PAGE16_B at 40C0

# --- the two sets of tables ---
for base, p0, p16, fpriv in ((SEGTAB_A, PAGETAB0_A, PAGE16_A, FPRIV_A),
                             (SEGTAB_B, PAGETAB0_B, PAGE16_B, FPRIV_B)):
    for i in range(32):
        a.put(base + 4*i, STE_INVALID.to_bytes(4, "big"))
    a.put(base + 4*0,  p0.to_bytes(4, "big"))     # PTL 0 -> 16 entries
    a.put(base + 4*16, p16.to_bytes(4, "big"))
    for i in range(16):
        a.put(p0 + 4*i, (i * 0x1000).to_bytes(4, "big"))   # identity 0-FFFF
        a.put(p16 + 4*i, PTE_INVALID.to_bytes(4, "big"))
    a.put(p16 + 4*5, FSHARE.to_bytes(4, "big"))   # page 5 -> THE SAME frame
    a.put(p16 + 4*6, fpriv.to_bytes(4, "big"))    # page 6 -> a different one

a.check_align(("CRVALA",4,"LCTL"), ("CRVALB",4,"LCTL"),
              ("AVSHARE",4,"L"), ("AVPRIV",4,"L"), ("AFSHARE",4,"L"),
              ("AFPRIVA",4,"L"), ("AFPRIVB",4,"L"), ("A31",4,"L"),
              *[(p,8,"LPSW") for _, p in FAILS],
              ("PASSPSW",8,"LPSW"), ("PCPSW",8,"program new PSW"))
for t in (SEGTAB_A, SEGTAB_B):
    assert t % 4096 == 0
for t in (PAGETAB0_A, PAGE16_A, PAGETAB0_B, PAGE16_B):
    assert t % 64 == 0
assert a.end <= SEGTAB_A, "code must not overlap the tables"

a.print_listing()
print("\n  virtual %08X (seg %d page %d)  A -> %08X   B -> %08X   SHARED"
      % (VSHARE, VSHARE >> 20, (VSHARE >> 12) & 0xFF, FSHARE, FSHARE))
print("  virtual %08X (seg %d page %d)  A -> %08X   B -> %08X   private"
      % (VPRIV, VPRIV >> 20, (VPRIV >> 12) & 0xFF, FPRIV_A, FPRIV_B))
print("\n  A: SEGTAB %04X  PAGETAB0 %04X  PAGE16 %04X  CR1 %08X"
      % (SEGTAB_A, PAGETAB0_A, PAGE16_A, CR1_A))
print("  B: SEGTAB %04X  PAGETAB0 %04X  PAGE16 %04X  CR1 %08X"
      % (SEGTAB_B, PAGETAB0_B, PAGE16_B, CR1_B))
print("  A PAGE16[5] = %08X   B PAGE16[5] = %08X   <- must be equal"
      % (int.from_bytes(a.read(PAGE16_A+20,4),"big"),
         int.from_bytes(a.read(PAGE16_B+20,4),"big")))
print("  A PAGE16[6] = %08X   B PAGE16[6] = %08X   <- must differ"
      % (int.from_bytes(a.read(PAGE16_A+24,4),"big"),
         int.from_bytes(a.read(PAGE16_B+24,4),"big")))
print("  ends %06X" % a.end)

end = (a.end + 7) & ~7
cmds = a.pokes((0x2000, end, 8),
               (SEGTAB_A, SEGTAB_A+128, 16), (PAGETAB0_A, PAGETAB0_A+64, 16),
               (PAGE16_A, PAGE16_A+64, 16),
               (SEGTAB_B, SEGTAB_B+128, 16), (PAGETAB0_B, PAGETAB0_B+64, 16),
               (PAGE16_B, PAGE16_B+64, 16))
open("share1.cmds", "w").write("\n".join(cmds) + "\n")
print("\n%d poke commands" % len(cmds))
