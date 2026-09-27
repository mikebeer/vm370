#!/usr/bin/env python3
"""
Storage-key write protection at PAGE granularity -- CP-67's other half.

09-frame-sharing.rc proved the first half: two address spaces can share a frame
at 4 KB granularity inside a 1 MB segment, so segment size does not dictate
sharing granularity.  That gives SHARING.  It does not give READ-ONLY sharing,
and CP-67 needed both:

    For store protection of the shared pages, the users are run with
    protection key = F.  All shared pages' storage keys are set to zero and
    all other pages belonging to these users have storage keys = F.
        -- CP-67 Program Logic Manual, GY20-0590-2, p.114

and PAGTRANS: "If shared page, get key '0', non-shared pages get key 'F'."

The two mechanisms are independent.  The page tables decide WHAT is shared; the
storage keys decide whether a sharer may WRITE it.  Neither involves the
segment size, which is the entire point of 05-CP67-PRIOR-ART.md.

THE SHAPE.  One address space, two frames, both above the line:

    virtual 01005000  ->  real 01100000   storage key 0   "shared"
    virtual 01006000  ->  real 01200000   storage key F   private

Then SPKA to PSW key F and try three things:

    store to the private page    must SUCCEED   key F PSW vs key F storage
    fetch from the shared page   must SUCCEED   no fetch protection set
    store to the shared page     must FAIL      key F PSW vs key 0 storage

The third is the assertion.  A store is permitted when the PSW key is zero OR
matches the storage key; F against 0 is neither, so it must take a protection
exception -- program interruption code 4.

HOW THE FAULT IS CAUGHT, AND WHY R10 EXISTS.  The program new PSW at X'68'
points at a handler.  Registers survive an interruption, so R10 carries a
marker for which store was in flight: the handler can distinguish "the shared
store faulted, as intended" from "the private store faulted, which is a real
failure".  Storage cannot be used for that marker, because after SPKA almost
every frame is unwritable by design -- which is the situation being tested.

ENCODINGS.  SSKE is B22B, RRE: r1 holds the key, r2 the real frame address.
SPKA is B20A, S-format, and takes the new key from bits 24-27 of its operand
address -- so SPKA 240(0) sets key F.  Both were cross-checked against z390's
opcode table.
"""
import sys
sys.path.insert(0, ".")
from asm import Asm, psw

CR0 = 0x00B00000
SEGTAB, PAGETAB0, PAGE16 = 0x3000, 0x3080, 0x30C0
CR1 = SEGTAB | 0x01

VSHARE, VPRIV = 0x01005000, 0x01006000
FSHARE, FPRIV = 0x01100000, 0x01200000
STE_INVALID, PTE_INVALID = 0x20, 0x400
PGM_PROTECTION = 4

a = Asm()
a.base = 0x2002


def sske(r1, r2):
    return bytes([0xB2, 0x2B, 0x00, (r1 << 4) | r2])


def spka(key):
    """Key comes from bits 24-27 of the operand address."""
    return bytes([0xB2, 0x0A, 0x00, key << 4])


# ------------------------------------------------------------------- code
a.label("START")
a.insn(2, lambda s: bytes([0x05, 0xF0]), "BALR  15,0", "")
a.insn(4, lambda s: bytes([0x41, 0xF0]) + s.bd(15, "START", 2), "LA    15,0(0,15)", "")
a.insn(6, lambda s: bytes([0xD2, 0x07, 0x00, 0x68]) + s.bd(15, "PGMPSW"),
       "MVC   X'68'(8,0),PGMPSW",
       "Program new PSW -> the handler, key 0 so it can act")

# 31-bit first: the frames are above the line and unreachable in 24-bit mode.
a.insn(4, lambda s: bytes([0x58, 0x40]) + s.bd(15, "A31"), "L     4,A31", "")
a.insn(2, lambda s: bytes([0x0B, 0x04]), "BSM   0,4", "")
a.align(4)
a.label("N31")
a.insn(4, lambda s: bytes([0x58, 0x50]) + s.bd(15, "AFSHARE"), "L     5,AFSHARE", "N31:")
a.insn(4, lambda s: bytes([0x58, 0x60]) + s.bd(15, "AFPRIV"), "L     6,AFPRIV", "")
a.insn(4, lambda s: bytes([0x92, 0x00, 0x50, 0x00]), "MVI   0(5),X'00'",
       "Clear both frames while still key 0 and DAT off")
a.insn(4, lambda s: bytes([0x92, 0x00, 0x60, 0x00]), "MVI   0(6),X'00'", "")

# --- set the storage keys.  SSKE takes a REAL address, so DAT is still off ---
a.insn(4, lambda s: bytes([0x41, 0x70, 0x00, 0x00]), "LA    7,0(0,0)",
       "key 0 for the shared frame -- fetch-protect bit left OFF, which is")
a.insn(4, lambda s: sske(7, 5), "SSKE  7,5",
       "what makes it readable by a key F program and not writable")
a.insn(4, lambda s: bytes([0x41, 0x70, 0x00, 0xF0]), "LA    7,240(0,0)",
       "key F for the private frame")
a.insn(4, lambda s: sske(7, 6), "SSKE  7,6", "")

# --- verify the keys took, with ISKE, before relying on them ---
a.insn(4, lambda s: bytes([0xB2, 0x29, 0x00, 0x85]), "ISKE  8,5",
       "Read the shared frame's key back, because a test that assumed SSKE")
a.insn(4, lambda s: bytes([0x54, 0x80]) + s.bd(15, "AKEYMASK"), "N     8,AKEYMASK",
       "worked would pass for the wrong reason.  Isolate the ACCESS KEY:")
a.insn(2, lambda s: bytes([0x12, 0x88]), "LTR   8,8",
       "ISKE also returns fetch-protect, reference and change in bits 4-7")
a.insn(4, lambda s: bytes([0x47, 0x70]) + s.bd(15, "FAILK0"), "BNZ   FAILK0",
       "key must read back as 0")

# --- DAT on, then drop to key F ---
a.insn(4, lambda s: bytes([0x58, 0x80]) + s.bd(15, "AVSHARE"), "L     8,AVSHARE", "")
a.insn(4, lambda s: bytes([0x58, 0x90]) + s.bd(15, "AVPRIV"), "L     9,AVPRIV", "")
a.insn(4, lambda s: bytes([0xB7, 0x01]) + s.bd(15, "CRVALS"), "LCTL  0,1,CRVALS", "")
a.insn(4, lambda s: bytes([0xB2, 0x0D, 0x00, 0x00]), "PTLB", "")
a.insn(4, lambda s: bytes([0xAD, 0x04]) + s.bd(15, "MASKSAVE"), "STOSM MASKSAVE,X'04'",
       "DAT on")
a.insn(4, lambda s: bytes([0x41, 0xA0, 0x00, 0x01]), "LA    10,1",
       "R10 = 1: the private store is in flight.  A register, because after")
a.insn(4, lambda s: spka(0xF), "SPKA  240(0)",
       "SPKA almost no frame is writable -- which is what we are testing")

# --- 1. store to the private page: key F against key F, must work ---
a.insn(4, lambda s: bytes([0x92, 0xE1, 0x90, 0x00]), "MVI   0(9),X'E1'",
       "Private page, key F storage, key F PSW -- permitted")

# --- 2. fetch from the shared page: must work, no fetch protection ---
a.insn(4, lambda s: bytes([0x95, 0x00, 0x80, 0x00]), "CLI   0(8),X'00'",
       "Shared page, key 0 storage, key F PSW -- a FETCH is still allowed")
a.insn(4, lambda s: bytes([0x47, 0x70]) + s.bd(15, "FAILRD"), "BNE   FAILRD",
       "because the fetch-protection bit was left off")

# --- 3. store to the shared page: must take a protection exception ---
a.insn(4, lambda s: bytes([0x41, 0xA0, 0x00, 0x02]), "LA    10,2",
       "R10 = 2: THE store under test is now in flight")
a.insn(4, lambda s: bytes([0x92, 0xC1, 0x80, 0x00]), "MVI   0(8),X'C1'",
       "THE ASSERTION: this must NOT complete.  Key F storing into key 0")
a.insn(4, lambda s: bytes([0x47, 0xF0]) + s.bd(15, "FAILWR"), "B     FAILWR",
       "reaching here means the store was allowed -- no protection at all")

# ------------------------------------------------------- program-check handler
a.label("PGMH")
a.insn(4, lambda s: bytes([0x41, 0xB0, 0x00, 0x02]), "LA    11,2",
       "PGMH: R10 is a VALUE, 1 or 2, not an address -- compare it")
a.insn(2, lambda s: bytes([0x19, 0xAB]), "CR    10,11",
       "Was the SHARED store the one in flight?")
a.insn(4, lambda s: bytes([0x47, 0x70]) + s.bd(15, "FAILEARLY"), "BNE   FAILEARLY",
       "no -- something faulted before the assertion, which is a real failure")
a.insn(4, lambda s: bytes([0x95, PGM_PROTECTION, 0x00, 0x8F]), "CLI   X'8F'(0),X'04'",
       "INTPR is the halfword at X'8E'; its low byte carries the code.")
a.insn(4, lambda s: bytes([0x47, 0x70]) + s.bd(15, "FAILCODE"), "BNE   FAILCODE",
       "4 = protection exception.  Anything else is the wrong fault")
a.insn(4, lambda s: bytes([0x82, 0x00]) + s.bd(15, "PASSPSW"), "LPSW  PASSPSW", "")

FAILS = (("FAILK0","FK0PSW"), ("FAILRD","FRDPSW"), ("FAILWR","FWRPSW"),
         ("FAILEARLY","FEPSW"), ("FAILCODE","FCPSW"))
for n, p in FAILS:
    a.label(n)
    a.insn(4, (lambda p: lambda s: bytes([0x82,0x00]) + s.bd(15, p))(p),
           "LPSW  %s" % p, "%s:" % n)

# ------------------------------------------------------------------- data
for name, ia in (("PASSPSW", 0x00600C),
                 ("FK0PSW",  0x001201),   # SSKE/ISKE: key never set
                 ("FRDPSW",  0x001202),   # fetch from key 0 frame failed
                 ("FWRPSW",  0x001203),   # THE STORE WAS ALLOWED -- no protection
                 ("FEPSW",   0x001204),   # something faulted before the assertion
                 ("FCPSW",   0x001205)):  # faulted, but not with code 4
    a.data(name, (lambda ia: lambda s: psw(ia))(ia), "", align=8)
# The handler runs key 0 and running, not waiting: byte1 = X'08'.
a.data("PGMPSW", lambda s: bytes([0x00, 0x08, 0x00, 0x00])
       + s.addr("PGMH").to_bytes(4, "big"), "key 0 so the handler can act",
       align=8, size=8)

a.data("CRVALS", lambda s: CR0.to_bytes(4,"big") + CR1.to_bytes(4,"big"), "", align=4)
a.data("AVSHARE", lambda s: VSHARE.to_bytes(4,"big"), "", align=4)
a.data("AVPRIV",  lambda s: VPRIV.to_bytes(4,"big"), "", align=4)
a.data("AFSHARE", lambda s: FSHARE.to_bytes(4,"big"), "key 0", align=4)
a.data("AFPRIV",  lambda s: FPRIV.to_bytes(4,"big"), "key F", align=4)
a.data("A31", lambda s: (0x80000000 | s.addr("N31")).to_bytes(4,"big"), "", align=4)
a.data("AKEYMASK", lambda s: (0x000000F0).to_bytes(4,"big"),
       "STORKEY_KEY -- the access key, without fetch/ref/change", align=4)
a.data("MASKSAVE", lambda s: b"\x00", "", align=1)

a.layout().assemble(size=0x1100)

for i in range(32):
    a.put(SEGTAB + 4*i, STE_INVALID.to_bytes(4, "big"))
a.put(SEGTAB + 4*0,  PAGETAB0.to_bytes(4, "big"))
a.put(SEGTAB + 4*16, PAGE16.to_bytes(4, "big"))
for i in range(16):
    a.put(PAGETAB0 + 4*i, (i * 0x1000).to_bytes(4, "big"))
    a.put(PAGE16 + 4*i, PTE_INVALID.to_bytes(4, "big"))
a.put(PAGE16 + 4*5, FSHARE.to_bytes(4, "big"))
a.put(PAGE16 + 4*6, FPRIV.to_bytes(4, "big"))

a.check_align(("CRVALS",4,"LCTL"), ("AVSHARE",4,"L"), ("AVPRIV",4,"L"),
              ("AFSHARE",4,"L"), ("AFPRIV",4,"L"), ("A31",4,"L"), ("AKEYMASK",4,"N"),
              ("PGMPSW",8,"MVC to X'68'"),
              *[(p,8,"LPSW") for _, p in FAILS], ("PASSPSW",8,"LPSW"))
assert a.end <= SEGTAB

a.print_listing()
print("\n  virtual %08X -> real %08X  storage key 0  (shared, read-only to key F)"
      % (VSHARE, FSHARE))
print("  virtual %08X -> real %08X  storage key F  (private, writable)"
      % (VPRIV, FPRIV))
print("  PGMH at %06X, entered via the program new PSW at X'68'" % a.addr("PGMH"))
print("  ends %06X" % a.end)

end = (a.end + 7) & ~7
cmds = a.pokes((0x2000, end, 8), (SEGTAB, SEGTAB+128, 16),
               (PAGETAB0, PAGETAB0+64, 16), (PAGE16, PAGE16+64, 16))
open("key1.cmds", "w").write("\n".join(cmds) + "\n")
print("\n%d poke commands" % len(cmds))
