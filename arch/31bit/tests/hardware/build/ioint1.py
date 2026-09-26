#!/usr/bin/env python3
"""
Channel subsystem test 3 -- I/O INTERRUPTION, not polling.

Tests 5 and 6 both polled TSCH.  CP does not poll: DMKIOS starts an
operation and returns to the dispatcher, and DMKIOT runs when the machine
takes an I/O interruption.  So until an interruption has actually been
taken and a subchannel identified from lowcore, the I/O route is unproven
in the way that matters.

This test starts a write, loads an ENABLED WAIT PSW, and expects the
machine to wake up in a handler.

THE THIRD SILENT GATE.  Two have already cost time on this project: CR0's
translation format, checked before any DAT table is read, and PMCW5_E,
without which SSCH returns cc=3 with no message.  Here is the third, and
it is worse because the failure is SILENCE rather than a code.

    /* Isolate the interruption subclass */
    i = ((dev->pmcw.flag4 & PMCW4_ISC) >> 3);

    /* Test interruption subclass mask bit in CR6 */
    if ((regs->CR_L(6) & (0x80000000 >> i)) == 0)
        return 0;                       /* interrupt NOT enabled */

CR6 is the I/O-interruption subclass mask.  A subchannel's ISC defaults to
0, so CR6 bit 0 -- X'80000000' -- must be on or the interruption is never
presented.  Not deferred: never presented.  The CPU sits in its enabled
wait forever, Hercules prints nothing because an ENABLED wait is not an
error, and there is no pass code and no failure code to read.

That is why this test loads CR6 explicitly and says so here.  A CP that
converts DMKIOS perfectly and forgets CR6 hangs at IPL with no diagnostic.

HOW TO READ THE RESULT
    006008   pass.  An I/O interruption was taken, lowcore X'B8' held the
             expected subsystem id, and TSCH returned CE|DE.
    SILENCE  the interruption was never presented.  Suspect CR6 first,
             then whether the device is attached at all.  Distinguish them
             at the panel: `cr` shows CR6, `devlist` shows the device.
    000E..   see the table below -- a code means the handler WAS entered,
             which is itself most of what the test is for.

WHAT IT STILL DOES NOT PROVE.  One interruption from one subchannel with
one CCW.  Not interruption while another is pending, not the ISC mechanism
with more than one class in play, and not DMKIOT's queue walk.  Those need
more than one device, which this deliberately minimal config does not
have.

Built on ssch1.py/ssch2.py: same device, same config, same
MSCH-before-SSCH prerequisite.  See those files for why each step is
there.
"""
import sys
sys.path.insert(0, ".")
from asm import Asm, psw


def wait_psw(ia, io=True):
    """Byte 0 is the system mask: PSW_IOMASK is X'02'.  Byte 1 X'0A' is
    bit 12 (ESA/390 requires it) plus bit 14, the wait state."""
    return bytes([0x02 if io else 0x00, 0x0A, 0x00, 0x00]) + ia.to_bytes(4, "big")


def run_psw(ia):
    """Running, not waiting, and I/O DISABLED so the handler cannot be
    re-entered by a second interruption while it is reading the first."""
    return bytes([0x00, 0x08, 0x00, 0x00]) + ia.to_bytes(4, "big")


MSG = "IOINT OK -- I/O INTERRUPTION TAKEN, SUBCHANNEL IDENTIFIED FROM LOWCORE"
msg_ebcdic = MSG.encode("cp037")
assert len(msg_ebcdic) <= 150, "BUFLEN_1052 is 150"

a = Asm()
a.base = 0x2002

# ------------------------------------------------------------------- code
a.label("START")
a.insn(2, lambda s: bytes([0x05, 0xF0]), "BALR  15,0", "")
a.insn(4, lambda s: bytes([0x41, 0xF0]) + s.bd(15, "START", 2), "LA    15,0(0,15)", "")
a.insn(6, lambda s: bytes([0xD2, 0x07, 0x00, 0x68]) + s.bd(15, "PCPSW"),
       "MVC   X'68'(8,0),PCPSW", "Arm the failure answer first")
a.insn(6, lambda s: bytes([0xD2, 0x07, 0x00, 0x78]) + s.bd(15, "IONPSW"),
       "MVC   X'78'(8,0),IONPSW", "I/O NEW PSW -> the handler, I/O disabled")
a.insn(4, lambda s: bytes([0xB7, 0x66]) + s.bd(15, "CR6VAL"), "LCTL  6,6,CR6VAL",
       "CR6 = X'80000000'.  THE THIRD SILENT GATE -- see the header")
a.insn(4, lambda s: bytes([0x58, 0x10]) + s.bd(15, "SSIDW"), "L     1,SSIDW", "")

# --- enable the subchannel (PMCW5_E: gate two) ---
a.insn(4, lambda s: bytes([0xB2, 0x34]) + s.bd(15, "SCHIB"), "STSCH SCHIB", "")
a.insn(4, lambda s: bytes([0x47, 0x70]) + s.bd(15, "FAIL1"), "BC    7,FAIL1", "")
a.insn(4, lambda s: bytes([0x96, 0x80]) + s.bd(15, "SCHIB", 5), "OI    SCHIB+5,X'80'", "")
a.insn(4, lambda s: bytes([0xB2, 0x32]) + s.bd(15, "SCHIB"), "MSCH  SCHIB", "")
a.insn(4, lambda s: bytes([0x47, 0x70]) + s.bd(15, "FAIL2"), "BC    7,FAIL2", "")

# --- start it and go to sleep ---
a.insn(4, lambda s: bytes([0xB2, 0x33]) + s.bd(15, "ORB"), "SSCH  ORB", "")
a.insn(4, lambda s: bytes([0x47, 0x70]) + s.bd(15, "FAIL3"), "BC    7,FAIL3", "")
a.insn(4, lambda s: bytes([0x82, 0x00]) + s.bd(15, "WAITPSW"), "LPSW  WAITPSW",
       "ENABLED wait.  If CR6 were wrong this never returns and there is")
# (nothing follows: control leaves here and comes back at HANDLER)

# ------------------------------------------------------- interrupt handler
# An interruption stores the old PSW and loads the new one; it does not
# touch the general registers.  So R15 is still the base established at
# START and the handler needs no prologue of its own.
a.label("HANDLER")
a.insn(6, lambda s: bytes([0xD5, 0x03, 0x00, 0xB8]) + s.bd(15, "SSIDW"),
       "CLC   X'B8'(4,0),SSIDW",
       "HANDLER: lowcore X'B8' is the I/O interrupt subsystem id.  Proves")
a.insn(4, lambda s: bytes([0x47, 0x70]) + s.bd(15, "FAILID"), "BC    7,FAILID",
       "WHICH subchannel interrupted -- what DMKIOT needs to find its IOBLOK")
a.insn(4, lambda s: bytes([0xB2, 0x35]) + s.bd(15, "IRB"), "TSCH  IRB",
       "Status is pending by definition here, so cc must be 0")
a.insn(4, lambda s: bytes([0x47, 0x70]) + s.bd(15, "FAILTS"), "BC    7,FAILTS", "")
a.insn(4, lambda s: bytes([0x95, 0x0C]) + s.bd(15, "IRB", 8), "CLI   IRB+8,X'0C'",
       "device status exactly CE|DE")
a.insn(4, lambda s: bytes([0x47, 0x70]) + s.bd(15, "FAIL8"), "BC    7,FAIL8", "")
a.insn(4, lambda s: bytes([0x95, 0x00]) + s.bd(15, "IRB", 9), "CLI   IRB+9,X'00'", "")
a.insn(4, lambda s: bytes([0x47, 0x70]) + s.bd(15, "FAIL9"), "BC    7,FAIL9", "")
a.insn(4, lambda s: bytes([0x82, 0x00]) + s.bd(15, "PASSPSW"), "LPSW  PASSPSW", "")

FAILS = (("FAIL1","F1PSW"), ("FAIL2","F2PSW"), ("FAIL3","F3PSW"),
         ("FAILID","FDPSW"), ("FAILTS","FTPSW"),
         ("FAIL8","F8PSW"), ("FAIL9","F9PSW"))
for n, p in FAILS:
    a.label(n)
    a.insn(4, (lambda p: lambda s: bytes([0x82,0x00]) + s.bd(15, p))(p),
           "LPSW  %s" % p, "%s:" % n)

# ------------------------------------------------------------------- data
for name, ia in (("PASSPSW", 0x006008),
                 ("F1PSW", 0x000E01),   # STSCH cc != 0
                 ("F2PSW", 0x000E02),   # MSCH  cc != 0
                 ("F3PSW", 0x000E03),   # SSCH  cc != 0
                 ("FDPSW", 0x000E11),   # wrong subsystem id at X'B8'
                 ("FTPSW", 0x000E12),   # TSCH cc != 0 inside the handler
                 ("F8PSW", 0x000E08),   # device status wrong
                 ("F9PSW", 0x000E09),   # subchannel status nonzero
                 ("PCPSW", 0x000DED)):
    a.data(name, (lambda ia: lambda s: psw(ia))(ia), "", align=8)

# The two PSWs that are not disabled waits.
a.data("WAITPSW", lambda s: wait_psw(0x006FFF, io=True),
       "enabled for I/O + wait.  IA is never reached; it is a marker", align=8)
a.data("IONPSW", lambda s: run_psw(s.addr("HANDLER")),
       "I/O new PSW: running, I/O masked off", align=8, size=8)

a.data("CR6VAL", lambda s: (0x80000000).to_bytes(4, "big"),
       "ISC 0 subclass mask -- X'80000000' >> ISC", align=4)
a.data("SSIDW", lambda s: (0x00010000).to_bytes(4, "big"),
       "X'0001' || subchannel; also compared against lowcore X'B8'", align=4)

a.data("ORB", lambda s: (
    (0).to_bytes(4, "big")              # +00 intparm -- comes back at X'BC'
    + bytes([0x00])                     # +04 flag4: key 0, ISC 0
    + bytes([0x80])                     # +05 flag5: F=1 format-1.  No ORB5_I:
                                        #     this test wants the PRIMARY
                                        #     completion interrupt, which is
                                        #     what DMKIOS actually waits for
    + bytes([0x80])                     # +06 lpm -- must be 80
    + bytes([0x00])                     # +07 flag7
    + s.addr("MYCCW").to_bytes(4, "big")
    + bytes(20)                         # pad to 32 (io.c fetches 31)
), "32 bytes", align=4, size=32)

a.data("SCHIB", lambda s: bytes(52), "STSCH stores 52; MSCH reads 28", align=4)
a.data("IRB", lambda s: bytes(64), "TSCH stores all 64", align=4)

a.data("MYCCW", lambda s: (
    bytes([0x09]) + bytes([0x20])
    + len(msg_ebcdic).to_bytes(2, "big")
    + s.addr("MSG").to_bytes(4, "big")
), "doubleword aligned", align=8, size=8)

a.data("MSG", lambda s: msg_ebcdic, "EBCDIC", align=1)

a.layout().assemble(size=0x1000)

a.check_align(("CR6VAL",4,"LCTL"), ("SSIDW",4,"L"),
              ("ORB",4,"SSCH FW_CHECK"), ("SCHIB",4,"MSCH/STSCH FW_CHECK"),
              ("IRB",4,"TSCH FW_CHECK"), ("MYCCW",8,"CCW doubleword"),
              ("WAITPSW",8,"LPSW"), ("IONPSW",8,"MVC to X'78'"),
              *[(p,8,"LPSW") for _, p in FAILS],
              ("PASSPSW",8,"LPSW"), ("PCPSW",8,"program new PSW"))

a.print_listing()
print("\n  HANDLER at %06X -- the I/O new PSW points here" % a.addr("HANDLER"))
print("  IONPSW  at %06X = %s" % (a.addr("IONPSW"),
      run_psw(a.addr("HANDLER")).hex().upper()))
print("  WAITPSW at %06X = %s  (byte 0 = 02, I/O enabled)"
      % (a.addr("WAITPSW"), wait_psw(0x006FFF).hex().upper()))
print("  CR6VAL  at %06X = 80000000  <-- silence means this is wrong"
      % a.addr("CR6VAL"))
print("  ends %06X" % a.end)

end = (a.end + 7) & ~7
cmds = a.pokes((0x2000, end, 8))
open("ioint1.cmds", "w").write("\n".join(cmds) + "\n")
print("\n%d poke commands" % len(cmds))
