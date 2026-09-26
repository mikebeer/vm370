#!/usr/bin/env python3
"""
Channel subsystem test 2 -- the initial-status-interruption facility, and
the deferred condition code.

THIS IS THE TEST THAT MATTERS MOST, because it is the only one aimed at a
SEMANTIC gap rather than a field layout.

The problem it exists to settle.  S/370 SIO sets a condition code
SYNCHRONOUSLY: cc=1 means "a CSW has been stored, look at it now".  DMKIOS
relies on that about a dozen times --

     988   BC    4,IOSCC1       BRANCH IF CSW STORED
    1017   BC    4,TIOCC1       CC = 1    CSW STORED
    1029   BC    4,HIOCC1       CC = 1 CSW STORED

-- and SSCH gives none of it.  SSCH queues the request and returns.  No
field mapping fixes that; it is a different contract.

IBM added a facility for exactly this problem: initial-status interruption,
requested by ORB5_I (flag5 X'20').  With it set, the subchannel reports
status as soon as the channel program starts, and sets SCSW1_Z, the ZERO
CONDITION CODE flag -- the substitute for SIO's synchronous cc.  The full
mapping is the DEFERRED CONDITION CODE in SCSW byte 0 bits 6-7 (SCSW0_CC),
which is what a program reads instead of the condition code SIO would have
set.

A PREVIOUS VERSION OF THE PROJECT DOCS SAID HERCULES CANNOT PROTOTYPE THIS.
That was wrong, and this test exists partly to prove the retraction.
Hercules's own release notes list "I/O initial status interruption" under
version 1.39, 24 November 1999, so every build since should have it.
Hyperion 4.x implements it with Principles of Operation citations:

    /* Process Initial-Status-Interruption Request           */
    /* SA22-7201-05:  p. 16-11, Zero Condition Code          */
    if (dev->scsw.flag1 & SCSW1_I)
    {
        STORE_FW(dev->scsw.ccwaddr,ccwaddr);
        dev->scsw.flag1 |= SCSW1_Z;
        dev->scsw.flag3 |= (SCSW3_SC_INTER | SCSW3_SC_PEND);
    }

and channel.c's AIPSX() builds the whole of "Figure 16-5, the
Deferred-Condition-Code Meaning for Status-Pending Subchannel".

WHAT PASSING MEANS.  That CP's SIO condition-code contract has a working
ESA/390 equivalent on the emulator the project actually runs on -- which
turns the top technical risk from "cannot be validated before M1" into a
known quantity.

WHAT FAILING ON 3.07 WOULD MEAN.  Not that the approach is wrong -- 4.x
demonstrably has it -- but that the lab has to move to 4.9.1 before the I/O
conversion can be developed against it.  Adrian is already on 4.9.1.  That
is a useful thing to learn from a fifteen-minute test rather than from M1.

ONE HONEST LIMIT.  This polls TSCH rather than taking an I/O interruption,
so it proves the STATUS mechanism, not the interruption delivery.  Status
pending is a subchannel condition and TSCH clears it whether or not
interrupts are enabled, so the SCSW contents are the same either way; but a
test with a real I/O new PSW and handler would prove more, and should come
before CP relies on the interrupt path.

Everything else is test 1's machinery: same device, same config, same
MSCH-before-SSCH prerequisite, and the same reasons.  See ssch1.py.
"""
import sys
sys.path.insert(0, ".")
from asm import Asm, psw

MSG = "ISI OK -- SCSW1_Z SET, DEFERRED CC 0: SIO CONTRACT HAS AN XA EQUIVALENT"
msg_ebcdic = MSG.encode("cp037")
assert len(msg_ebcdic) <= 150, "BUFLEN_1052 is 150"

a = Asm()
a.base = 0x2002

# ------------------------------------------------------------------- code
a.label("START")
a.insn(2, lambda s: bytes([0x05, 0xF0]), "BALR  15,0", "")
a.insn(4, lambda s: bytes([0x41, 0xF0]) + s.bd(15, "START", 2), "LA    15,0(0,15)",
       "Clear bits 0-7 before anything uses R15 as a base")
a.insn(6, lambda s: bytes([0xD2, 0x07, 0x00, 0x68]) + s.bd(15, "PCPSW"),
       "MVC   X'68'(8,0),PCPSW", "Arm the failure answer first")
a.insn(4, lambda s: bytes([0x58, 0x10]) + s.bd(15, "SSIDW"), "L     1,SSIDW",
       "R1 = X'0001' || subchannel")

# --- enable the subchannel (see ssch1.py: cc=3 silently, otherwise) ---
a.insn(4, lambda s: bytes([0xB2, 0x34]) + s.bd(15, "SCHIB"), "STSCH SCHIB", "")
a.insn(4, lambda s: bytes([0x47, 0x70]) + s.bd(15, "FAIL1"), "BC    7,FAIL1", "")
a.insn(4, lambda s: bytes([0x96, 0x80]) + s.bd(15, "SCHIB", 5), "OI    SCHIB+5,X'80'",
       "PMCW5_E")
a.insn(4, lambda s: bytes([0xB2, 0x32]) + s.bd(15, "SCHIB"), "MSCH  SCHIB", "")
a.insn(4, lambda s: bytes([0x47, 0x70]) + s.bd(15, "FAIL2"), "BC    7,FAIL2", "")

# --- start it, with ORB5_I requested this time ---
a.insn(4, lambda s: bytes([0xB2, 0x33]) + s.bd(15, "ORB"), "SSCH  ORB",
       "ORB flag5 = X'A0': F=1 format-1, AND I=1 initial status")
a.insn(4, lambda s: bytes([0x47, 0x70]) + s.bd(15, "FAIL3"), "BC    7,FAIL3", "")

# --- first status.  Poll, because SSCH is still asynchronous ---
a.insn(4, lambda s: bytes([0x58, 0x20]) + s.bd(15, "POLLMAX"), "L     2,POLLMAX", "")
a.label("POLL1")
a.insn(4, lambda s: bytes([0xB2, 0x35]) + s.bd(15, "IRB"), "TSCH  IRB", "POLL1:")
a.insn(4, lambda s: bytes([0x47, 0x80]) + s.bd(15, "GOT1"), "BC    8,GOT1",
       "cc=0: status was pending and is now in the IRB")
a.insn(4, lambda s: bytes([0x47, 0x30]) + s.bd(15, "FAIL4"), "BC    3,FAIL4",
       "cc=3 not operational")
a.insn(4, lambda s: bytes([0x46, 0x20]) + s.bd(15, "POLL1"), "BCT   2,POLL1", "")
a.insn(4, lambda s: bytes([0x47, 0xF0]) + s.bd(15, "FAIL5"), "B     FAIL5", "")

# --- THE ASSERTIONS.  This is the whole point of the test ---
a.label("GOT1")
a.insn(4, lambda s: bytes([0x91, 0x04]) + s.bd(15, "IRB", 1), "TM    IRB+1,X'04'",
       "GOT1: SCSW1_Z, the ZERO CONDITION CODE flag.  THE assertion --")
a.insn(4, lambda s: bytes([0x47, 0x80]) + s.bd(15, "FAILZ"), "BC    8,FAILZ",
       "cc=0 means the bit is clear, so the facility did not fire")
a.insn(4, lambda s: bytes([0x91, 0x08]) + s.bd(15, "IRB", 3), "TM    IRB+3,X'08'",
       "SCSW3_SC_INTER -- intermediate status, which is how ISI reports")
a.insn(4, lambda s: bytes([0x47, 0x80]) + s.bd(15, "FAILI"), "BC    8,FAILI", "")
a.insn(4, lambda s: bytes([0x91, 0x03]) + s.bd(15, "IRB"), "TM    IRB,X'03'",
       "SCSW0_CC, the DEFERRED CONDITION CODE.  Must be 00 = cc 0, the")
a.insn(4, lambda s: bytes([0x47, 0x70]) + s.bd(15, "FAILCC"), "BC    7,FAILCC",
       "direct analogue of the cc SIO would have set")

# Primary status may already be here: a console write can finish before the
# first TSCH.  Both pending at once is legitimate, so tolerate it rather
# than polling for a status that has already been collected.
a.insn(4, lambda s: bytes([0x91, 0x04]) + s.bd(15, "IRB", 3), "TM    IRB+3,X'04'",
       "SCSW3_SC_PRI already set?  Then the write is done too")
a.insn(4, lambda s: bytes([0x47, 0x10]) + s.bd(15, "FINAL"), "BC    1,FINAL",
       "cc=3, bit set -- skip the second poll")

# --- second status: the completion ---
a.insn(4, lambda s: bytes([0x58, 0x20]) + s.bd(15, "POLLMAX"), "L     2,POLLMAX", "")
a.label("POLL2")
a.insn(4, lambda s: bytes([0xB2, 0x35]) + s.bd(15, "IRB"), "TSCH  IRB", "POLL2:")
a.insn(4, lambda s: bytes([0x47, 0x80]) + s.bd(15, "GOT2"), "BC    8,GOT2", "")
a.insn(4, lambda s: bytes([0x47, 0x30]) + s.bd(15, "FAIL6"), "BC    3,FAIL6", "")
a.insn(4, lambda s: bytes([0x46, 0x20]) + s.bd(15, "POLL2"), "BCT   2,POLL2", "")
a.insn(4, lambda s: bytes([0x47, 0xF0]) + s.bd(15, "FAIL7"), "B     FAIL7", "")

a.label("GOT2")
a.insn(4, lambda s: bytes([0x91, 0x04]) + s.bd(15, "IRB", 3), "TM    IRB+3,X'04'",
       "GOT2: SCSW3_SC_PRI -- primary status, the operation ended")
a.insn(4, lambda s: bytes([0x47, 0x80]) + s.bd(15, "FAILP"), "BC    8,FAILP", "")

a.label("FINAL")
a.insn(4, lambda s: bytes([0x95, 0x0C]) + s.bd(15, "IRB", 8), "CLI   IRB+8,X'0C'",
       "FINAL: device status exactly CE|DE, as in test 1")
a.insn(4, lambda s: bytes([0x47, 0x70]) + s.bd(15, "FAIL8"), "BC    7,FAIL8", "")
a.insn(4, lambda s: bytes([0x95, 0x00]) + s.bd(15, "IRB", 9), "CLI   IRB+9,X'00'",
       "subchannel status zero")
a.insn(4, lambda s: bytes([0x47, 0x70]) + s.bd(15, "FAIL9"), "BC    7,FAIL9", "")
a.insn(4, lambda s: bytes([0x82, 0x00]) + s.bd(15, "PASSPSW"), "LPSW  PASSPSW", "")

FAILS = (("FAIL1","F1PSW"), ("FAIL2","F2PSW"), ("FAIL3","F3PSW"),
         ("FAIL4","F4PSW"), ("FAIL5","F5PSW"), ("FAILZ","FZPSW"),
         ("FAILI","FIPSW"), ("FAILCC","FCPSW"), ("FAIL6","F6PSW"),
         ("FAIL7","F7PSW"), ("FAILP","FPPSW"), ("FAIL8","F8PSW"),
         ("FAIL9","F9PSW"))
for n, p in FAILS:
    a.label(n)
    a.insn(4, (lambda p: lambda s: bytes([0x82,0x00]) + s.bd(15, p))(p),
           "LPSW  %s" % p, "%s:" % n)

# ------------------------------------------------------------------- data
# Fail codes are 000Cnn so they cannot be confused with test 1's 000Bnn.
# The three that matter have mnemonic codes rather than sequence numbers.
for name, ia in (("PASSPSW", 0x006007),
                 ("F1PSW", 0x000C01),   # STSCH cc != 0
                 ("F2PSW", 0x000C02),   # MSCH  cc != 0
                 ("F3PSW", 0x000C03),   # SSCH  cc != 0  (ORB5_I rejected?)
                 ("F4PSW", 0x000C04),   # first TSCH cc=3
                 ("F5PSW", 0x000C05),   # first poll exhausted: NO STATUS AT ALL
                 ("FZPSW", 0x000C11),   # SCSW1_Z NOT SET -- the headline failure
                 ("FIPSW", 0x000C12),   # intermediate status not set
                 ("FCPSW", 0x000C13),   # deferred condition code nonzero
                 ("F6PSW", 0x000C06),   # second TSCH cc=3
                 ("F7PSW", 0x000C07),   # second poll exhausted
                 ("FPPSW", 0x000C14),   # primary status never arrived
                 ("F8PSW", 0x000C08),   # device status wrong
                 ("F9PSW", 0x000C09),   # subchannel status nonzero
                 ("PCPSW", 0x000DED)):
    a.data(name, (lambda ia: lambda s: psw(ia))(ia), "", align=8)

a.data("SSIDW", lambda s: (0x00010000).to_bytes(4, "big"),
       "low halfword = subchannel; CHECK IT with devlist", align=4)
a.data("POLLMAX", lambda s: (200000).to_bytes(4, "big"), "poll limit", align=4)

# The ORB, with the one byte that distinguishes this test from test 1.
a.data("ORB", lambda s: (
    (0).to_bytes(4, "big")              # +00 intparm
    + bytes([0x00])                     # +04 flag4: key 0
    + bytes([0xA0])                     # +05 flag5: ORB5_F X'80' format-1
                                        #          | ORB5_I X'20' INITIAL STATUS
                                        #     THIS BYTE IS THE TEST
    + bytes([0x80])                     # +06 lpm -- must be 80, see ssch1.py
    + bytes([0x00])                     # +07 flag7
    + s.addr("MYCCW").to_bytes(4, "big")  # +08 CCW address
    + bytes(20)                         # +12 pad to 32 (io.c:561)
), "flag5 X'A0' -- F and I", align=4, size=32)

a.data("SCHIB", lambda s: bytes(52), "STSCH stores 52; MSCH reads 28", align=4)
a.data("IRB", lambda s: bytes(64), "TSCH stores all 64", align=4)

a.data("MYCCW", lambda s: (
    bytes([0x09])                       # Write with auto carrier return
    + bytes([0x20])                     # SLI
    + len(msg_ebcdic).to_bytes(2, "big")
    + s.addr("MSG").to_bytes(4, "big")
), "doubleword aligned (channel.c:3229)", align=8, size=8)

a.data("MSG", lambda s: msg_ebcdic, "EBCDIC", align=1)

a.layout().assemble(size=0x1000)

a.check_align(("SSIDW",4,"L"), ("POLLMAX",4,"L"),
              ("ORB",4,"SSCH FW_CHECK"), ("SCHIB",4,"MSCH/STSCH FW_CHECK"),
              ("IRB",4,"TSCH FW_CHECK"),
              ("MYCCW",8,"CCW doubleword"),
              *[(p,8,"LPSW") for _, p in FAILS],
              ("PASSPSW",8,"LPSW"), ("PCPSW",8,"program new PSW"))

a.print_listing()
print("\n  ORB flag5 at %06X = A0  (F=format-1, I=initial status)"
      % (a.addr("ORB") + 5))
print("  IRB    at %06X" % a.addr("IRB"))
print("    IRB+0 bits X'03' = deferred condition code   (want 00)")
print("    IRB+1 bit  X'04' = SCSW1_Z zero condition cc (want set)")
print("    IRB+3 bit  X'08' = intermediate status       (want set)")
print("    IRB+3 bit  X'04' = primary status")
print("    IRB+8 / +9       = device / subchannel status (want 0C / 00)")
print("  ends %06X" % a.end)

end = (a.end + 7) & ~7
cmds = a.pokes((0x2000, end, 8))
open("ssch2.cmds", "w").write("\n".join(cmds) + "\n")
print("\n%d poke commands" % len(cmds))
