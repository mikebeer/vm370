#!/usr/bin/env python3
"""
Channel subsystem test 1 -- can we drive a device with SSCH?

Writes a line to the 3215 console using MSCH/SSCH/TSCH, on bare ESA/390,
no operating system.  If text appears on the Hercules log, we have done
channel-subsystem I/O and have a working template for what DMKIOS's inner
loop becomes.

DAT is OFF throughout and no control registers are loaded.  This test asks
only about I/O; the five DAT tests asked only about addressing.  Keeping
them apart is the whole method.

THE PREREQUISITE THAT WOULD OTHERWISE COST AN EVENING: a subchannel comes
up with only the valid bit set.  config.c:740 sets PMCW5_V and nothing
ever sets PMCW5_E except MSCH and the IPL path -- and device_reset()
clears it again.  SSCH with E off returns condition code 3 SILENTLY: no
exception, no message, nothing on the log.  So MSCH first, always.

Verified against SDL Hyperion 4.9.1 source.  Field layouts, required bits
and every condition-code path came from esa390.h, io.c, channel.c and
con1052c.c rather than from the Principles of Operation, because the
emulator is what accepts or rejects these control blocks.

SUBCHANNEL NUMBER: assigned sequentially from 0x0000 in CONFIG FILE
ORDER, not by device number (config.c:678). With 0009 as the only device
it is 0x0000, so R1 = X'00010000'. If the config lists other devices
first, this is wrong -- check `devlist` at the panel, or the HHC02198
"... subchannel 0:xxxx attached" messages at startup, and re-poke SSIDW.
"""
import sys
sys.path.insert(0, ".")
from asm import Asm, psw

MSG = "SSCH OK -- CHANNEL SUBSYSTEM I/O ON BARE ESA/390"
msg_ebcdic = MSG.encode("cp037")        # the handler translates EBCDIC->ASCII
assert len(msg_ebcdic) <= 150, "BUFLEN_1052 is 150; longer needs SLI and truncates"

a = Asm()
a.base = 0x2002

# ------------------------------------------------------------------- code
a.label("START")
a.insn(2, lambda s: bytes([0x05, 0xF0]), "BALR  15,0", "")
a.insn(4, lambda s: bytes([0x41, 0xF0]) + s.bd(15, "START", 2), "LA    15,0(0,15)",
       "Clear bits 0-7 -- habit now, and mandatory before any AMODE 31")
a.insn(6, lambda s: bytes([0xD2, 0x07, 0x00, 0x68]) + s.bd(15, "PCPSW"),
       "MVC   X'68'(8,0),PCPSW", "Arm the failure answer first")
a.insn(4, lambda s: bytes([0x58, 0x10]) + s.bd(15, "SSIDW"), "L     1,SSIDW",
       "R1 = X'0001' || subchannel.  Bits 0-15 must be exactly 0001")

# --- enable the subchannel.  Without this, SSCH gives cc=3 and no clue ---
a.insn(4, lambda s: bytes([0xB2, 0x34]) + s.bd(15, "SCHIB"), "STSCH SCHIB",
       "Read the current PMCW.  Safer than hand-building one: cannot get")
a.insn(4, lambda s: bytes([0x47, 0x70]) + s.bd(15, "FAIL1"), "BC    7,FAIL1",
       "flag26/flag27/flag4 reserved bits wrong")
a.insn(4, lambda s: bytes([0x96, 0x80]) + s.bd(15, "SCHIB", 5), "OI    SCHIB+5,X'80'",
       "PMCW5_E.  THE mandatory step -- see the header")
a.insn(4, lambda s: bytes([0xB2, 0x32]) + s.bd(15, "SCHIB"), "MSCH  SCHIB",
       "MSCH reads 28 bytes and copies only E/LM/MM/D, ISC/A, LPM/POM,")
a.insn(4, lambda s: bytes([0x47, 0x70]) + s.bd(15, "FAIL2"), "BC    7,FAIL2",
       "MBI and INTPARM.  It cannot touch pam, which is what SSCH tests")

# --- start the channel program ---
a.insn(4, lambda s: bytes([0xB2, 0x33]) + s.bd(15, "ORB"), "SSCH  ORB",
       "cc=3 not enabled or lpm&pam==0; cc=1 stale status; cc=2 busy")
a.insn(4, lambda s: bytes([0x47, 0x70]) + s.bd(15, "FAIL3"), "BC    7,FAIL3", "")

# --- poll.  SSCH is asynchronous: the CCW has not run yet ---
a.insn(4, lambda s: bytes([0x58, 0x20]) + s.bd(15, "POLLMAX"), "L     2,POLLMAX",
       "Bounded, so a stall gives a diagnosable answer instead of a hang")
a.label("POLL")
a.insn(4, lambda s: bytes([0xB2, 0x35]) + s.bd(15, "IRB"), "TSCH  IRB", "POLL:")
a.insn(4, lambda s: bytes([0x47, 0x80]) + s.bd(15, "CHECK"), "BC    8,CHECK",
       "cc=0: status was pending and has been cleared")
a.insn(4, lambda s: bytes([0x47, 0x30]) + s.bd(15, "FAIL4"), "BC    3,FAIL4",
       "cc=3 not operational (cc=2 is not a TSCH outcome)")
a.insn(4, lambda s: bytes([0x46, 0x20]) + s.bd(15, "POLL"), "BCT   2,POLL",
       "cc=1: nothing pending yet, go round again")
a.insn(4, lambda s: bytes([0x47, 0xF0]) + s.bd(15, "FAIL5"), "B     FAIL5",
       "count exhausted")

# --- did it work? ---
a.label("CHECK")
a.insn(4, lambda s: bytes([0x91, 0x10]) + s.bd(15, "IRB", 3), "TM    IRB+3,X'10'",
       "CHECK: SCSW3_SC_ALERT -- Hercules's own summary bit, set exactly")
a.insn(4, lambda s: bytes([0x47, 0x70]) + s.bd(15, "FAIL6"), "BC    7,FAIL6",
       "when chanstat != 0 or unitstat != CE+DE")
a.insn(4, lambda s: bytes([0x95, 0x0C]) + s.bd(15, "IRB", 8), "CLI   IRB+8,X'0C'",
       "device status must be exactly CSW_CE|CSW_DE")
a.insn(4, lambda s: bytes([0x47, 0x70]) + s.bd(15, "FAIL7"), "BC    7,FAIL7", "")
a.insn(4, lambda s: bytes([0x95, 0x00]) + s.bd(15, "IRB", 9), "CLI   IRB+9,X'00'",
       "subchannel status must be zero")
a.insn(4, lambda s: bytes([0x47, 0x70]) + s.bd(15, "FAIL8"), "BC    7,FAIL8", "")
a.insn(4, lambda s: bytes([0x82, 0x00]) + s.bd(15, "PASSPSW"), "LPSW  PASSPSW", "")

for n, p in (("FAIL1","F1PSW"), ("FAIL2","F2PSW"), ("FAIL3","F3PSW"),
             ("FAIL4","F4PSW"), ("FAIL5","F5PSW"), ("FAIL6","F6PSW"),
             ("FAIL7","F7PSW"), ("FAIL8","F8PSW")):
    a.label(n)
    a.insn(4, (lambda p: lambda s: bytes([0x82,0x00]) + s.bd(15, p))(p),
           "LPSW  %s" % p, "%s:" % n)

# ------------------------------------------------------------------- data
for name, ia in (("PASSPSW", 0x006006),
                 ("F1PSW", 0x000B01),   # STSCH cc != 0
                 ("F2PSW", 0x000B02),   # MSCH  cc != 0
                 ("F3PSW", 0x000B03),   # SSCH  cc != 0
                 ("F4PSW", 0x000B04),   # TSCH  cc = 3
                 ("F5PSW", 0x000B05),   # poll exhausted
                 ("F6PSW", 0x000B06),   # SCSW alert
                 ("F7PSW", 0x000B07),   # device status wrong
                 ("F8PSW", 0x000B08),   # subchannel status nonzero
                 ("PCPSW", 0x000DED)):
    a.data(name, (lambda ia: lambda s: psw(ia))(ia), "", align=8)

a.data("SSIDW", lambda s: (0x00010000).to_bytes(4, "big"),
       "low halfword = subchannel; CHECK IT with devlist", align=4)
a.data("POLLMAX", lambda s: (200000).to_bytes(4, "big"), "poll limit", align=4)

# ORB.  32 bytes, not 12: SSCH fetches sizeof(ORB)-1 = 31 unconditionally
# (io.c:561), whatever the X bit says, so a 12-byte ORB at the end of the
# loaded image takes an addressing exception on a fetch that the
# Principles of Operation says never happens.
a.data("ORB", lambda s: (
    (0).to_bytes(4, "big")              # +00 intparm, comes back at PSA+BC
    + bytes([0x00])                     # +04 flag4: key 0 disables ALL channel
                                        #     key checking, which is what we
                                        #     want with storage keys unset
    + bytes([0x80])                     # +05 flag5: F=1, format-1 CCWs
    + bytes([0x80])                     # +06 lpm -- MUST be 80.  pam is 80 and
                                        #     SSCH tests lpm & pam, so lpm=00
                                        #     is cc=3, NOT "any path"
    + bytes([0x00])                     # +07 flag7: 0x3E reserved, D=operand
                                        #     exception in ESA/390
    + s.addr("MYCCW").to_bytes(4, "big")  # +08 CCW address, bit 0 must be 0
    + bytes(20)                         # +12 pad to 32 -- see above
), "32 bytes deliberately", align=4, size=32)

a.data("SCHIB", lambda s: bytes(52), "STSCH stores 52; MSCH reads 28", align=4)
a.data("IRB", lambda s: bytes(64), "TSCH stores all 64", align=4)

# The CCW must be DOUBLEWORD aligned (channel.c:3229) or it is a channel
# program check -- a different alignment rule from the ORB/SCHIB/IRB, which
# need only a word.
a.data("MYCCW", lambda s: (
    bytes([0x09])                       # Write, auto carrier return: the
                                        # handler appends the newline itself
    + bytes([0x20])                     # SLI -- suppress incorrect length.
                                        # Belt and braces under 150 bytes
    + len(msg_ebcdic).to_bytes(2, "big")
    + s.addr("MSG").to_bytes(4, "big")
), "doubleword aligned", align=8, size=8)

a.data("MSG", lambda s: msg_ebcdic, "EBCDIC -- guest_to_host translates it", align=1)

a.layout().assemble(size=0x1000)

a.check_align(("SSIDW",4,"L"), ("POLLMAX",4,"L"),
              ("ORB",4,"SSCH FW_CHECK"), ("SCHIB",4,"MSCH/STSCH FW_CHECK"),
              ("IRB",4,"TSCH FW_CHECK"),
              ("MYCCW",8,"CCW doubleword, channel.c:3229"),
              *[(n,8,"LPSW") for n in ("PASSPSW","F1PSW","F2PSW","F3PSW",
                                       "F4PSW","F5PSW","F6PSW","F7PSW","F8PSW")],
              ("PCPSW",8,"program new PSW"))

a.print_listing()
print("\n  MSG          %d bytes EBCDIC: %s" % (len(msg_ebcdic), msg_ebcdic.hex().upper()[:32] + "..."))
print("  SSIDW at %06X -- re-poke this if the subchannel is not 0000" % a.addr("SSIDW"))
print("  ORB    at %06X, %d bytes" % (a.addr("ORB"), 32))
print("  MYCCW  at %06X  (%% 8 = %d)" % (a.addr("MYCCW"), a.addr("MYCCW") % 8))
print("  IRB    at %06X -- read IRB+8 and IRB+9 by hand afterwards" % a.addr("IRB"))
print("  ends %06X" % a.end)

end = (a.end + 7) & ~7
cmds = a.pokes((0x2000, end, 8))
open("ssch1.cmds", "w").write("\n".join(cmds) + "\n")
print("\n%d poke commands" % len(cmds))
