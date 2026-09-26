#!/usr/bin/env python3
"""
A DASD read -- the first test that does what DMKIOS actually does.

WHY THIS IS DIFFERENT FROM TESTS 5, 6 AND 7.  Those drove a 3215 console with
ONE CCW, which proved the channel-subsystem plumbing but not much about
channel programs.  DMKIOS drives DASD, and a DASD read is a CHAIN with
command chaining, a transfer-in-channel that loops, and a device that returns
status you have to care about.  This is the shape of the thing CP's I/O
supervisor exists to issue.

    SEEK              07  CC    6 bytes BBCCHH
    SEARCH ID EQUAL   31  CC    5 bytes CCHHR
    TIC               08        back to the SEARCH
    READ DATA         06  SLI  80 bytes

The SEARCH/TIC pair is the classic CKD idiom and it is worth understanding
rather than copying: when the search matches, the device returns STATUS
MODIFIER, which makes the channel SKIP the next CCW -- the TIC -- and fall
through to the READ.  When it does not match, control reaches the TIC, which
branches back to the search to try the next record on the track.  So the
"loop" is built out of a conditional skip, and the channel program is
genuinely a program.

Tests 5-7 never exercised command chaining, status modifier or TIC at all.

THE TARGET IS A SCRATCH VOLUME, DELIBERATELY.  Earlier notes in this
repository flagged that a DASD test must never point at a CE pack: a
bare-metal test builds its own channel programs with no operating system to
stop it addressing the wrong subchannel, and during development a write
command did reach subchannel 0000 while a writable CE pack was attached, with
only a command reject preventing damage.  So this creates its own volume:

    dasdinit -z scratch.cckd 3350 SCRTCH 10

Ten cylinders, compressed to about 3 KB, containing nothing but the standard
labels.  Nothing on it matters and nothing else is attached.  This resolves
that conflict rather than avoiding it.

WHAT IT READS.  dasdinit writes a standard VOL1 label at cylinder 0, head 0,
record 3 -- verified with cckddiag before writing a line of this test:

    Track 0 COUNT CC=0 HH=0 R=3 KL=4 DL=80
    Track 0 R3 KEY (4 bytes)   E5D6D3F1                      VOL1
    Track 0 R3 DATA (80 bytes) E5D6D3F1 E2C3D9E3 C3C84000... VOL1SCRTCH

So the assertions are that the data begins 'VOL1' AND that the volume serial
is 'SCRTCH' -- the second one matters, because it proves this read reached
THIS volume rather than matching four plausible bytes by luck.

Residual count is checked too: reading 80 of 80 bytes must leave zero.

SUBCHANNEL NUMBERING.  herc.conf lists the 3215 first, so it is subchannel
0000 and the DASD is 0001.  R1 = X'00010001'.  If the config order changes
this is wrong -- check `devlist` at the panel.
"""
import sys
sys.path.insert(0, ".")
from asm import Asm, psw

VOLSER = "SCRTCH"
CYL, HEAD, REC = 0, 0, 3
DATALEN = 80

a = Asm()
a.base = 0x2002

# ------------------------------------------------------------------- code
a.label("START")
a.insn(2, lambda s: bytes([0x05, 0xF0]), "BALR  15,0", "")
a.insn(4, lambda s: bytes([0x41, 0xF0]) + s.bd(15, "START", 2), "LA    15,0(0,15)", "")
a.insn(6, lambda s: bytes([0xD2, 0x07, 0x00, 0x68]) + s.bd(15, "PCPSW"),
       "MVC   X'68'(8,0),PCPSW", "Arm the failure answer first")
a.insn(4, lambda s: bytes([0x58, 0x10]) + s.bd(15, "SSIDW"), "L     1,SSIDW",
       "R1 = X'0001' || subchannel 0001 -- the DASD, not the console")

# --- enable the subchannel (PMCW5_E, the gate from test 5) ---
a.insn(4, lambda s: bytes([0xB2, 0x34]) + s.bd(15, "SCHIB"), "STSCH SCHIB", "")
a.insn(4, lambda s: bytes([0x47, 0x70]) + s.bd(15, "FAIL1"), "BC    7,FAIL1",
       "cc/=0 here usually means the subchannel number is wrong")
a.insn(4, lambda s: bytes([0x96, 0x80]) + s.bd(15, "SCHIB", 5), "OI    SCHIB+5,X'80'", "")
a.insn(4, lambda s: bytes([0xB2, 0x32]) + s.bd(15, "SCHIB"), "MSCH  SCHIB", "")
a.insn(4, lambda s: bytes([0x47, 0x70]) + s.bd(15, "FAIL2"), "BC    7,FAIL2", "")

# --- start the chain ---
a.insn(4, lambda s: bytes([0xB2, 0x33]) + s.bd(15, "ORB"), "SSCH  ORB",
       "Four CCWs, not one: SEEK, SEARCH, TIC, READ")
a.insn(4, lambda s: bytes([0x47, 0x70]) + s.bd(15, "FAIL3"), "BC    7,FAIL3", "")

# --- poll ---
a.insn(4, lambda s: bytes([0x58, 0x20]) + s.bd(15, "POLLMAX"), "L     2,POLLMAX", "")
a.label("POLL")
a.insn(4, lambda s: bytes([0xB2, 0x35]) + s.bd(15, "IRB"), "TSCH  IRB", "POLL:")
a.insn(4, lambda s: bytes([0x47, 0x80]) + s.bd(15, "CHECK"), "BC    8,CHECK", "")
a.insn(4, lambda s: bytes([0x47, 0x30]) + s.bd(15, "FAIL4"), "BC    3,FAIL4", "")
a.insn(4, lambda s: bytes([0x46, 0x20]) + s.bd(15, "POLL"), "BCT   2,POLL", "")
a.insn(4, lambda s: bytes([0x47, 0xF0]) + s.bd(15, "FAIL5"), "B     FAIL5", "")

# --- status ---
a.label("CHECK")
a.insn(4, lambda s: bytes([0x95, 0x0C]) + s.bd(15, "IRB", 8), "CLI   IRB+8,X'0C'",
       "CHECK: device status exactly CE|DE.  A unit check here means the")
a.insn(4, lambda s: bytes([0x47, 0x70]) + s.bd(15, "FAIL6"), "BC    7,FAIL6",
       "chain reached the device and it objected -- read the sense")
a.insn(4, lambda s: bytes([0x95, 0x00]) + s.bd(15, "IRB", 9), "CLI   IRB+9,X'00'",
       "subchannel status zero: no channel program check, no protection")
a.insn(4, lambda s: bytes([0x47, 0x70]) + s.bd(15, "FAIL7"), "BC    7,FAIL7",
       "check, no chaining check")
a.insn(4, lambda s: bytes([0x95, 0x00]) + s.bd(15, "IRB", 10), "CLI   IRB+10,X'00'",
       "residual count high byte -- 80 of 80 bytes must leave zero")
a.insn(4, lambda s: bytes([0x47, 0x70]) + s.bd(15, "FAIL8"), "BC    7,FAIL8", "")
a.insn(4, lambda s: bytes([0x95, 0x00]) + s.bd(15, "IRB", 11), "CLI   IRB+11,X'00'", "")
a.insn(4, lambda s: bytes([0x47, 0x70]) + s.bd(15, "FAIL9"), "BC    7,FAIL9", "")

# --- the data.  This is what makes it a read rather than a status test ---
a.insn(6, lambda s: bytes([0xD5, 0x03]) + s.bd(15, "READBUF") + s.bd(15, "EVOL1"),
       "CLC   READBUF(4),EVOL1",
       "'VOL1' in EBCDIC -- the label identifier")
a.insn(4, lambda s: bytes([0x47, 0x70]) + s.bd(15, "FAILV1"), "BC    7,FAILV1", "")
a.insn(6, lambda s: bytes([0xD5, 0x05]) + s.bd(15, "READBUF", 4) + s.bd(15, "EVOLSER"),
       "CLC   READBUF+4(6),EVOLSER",
       "AND the volume serial 'SCRTCH' -- proves it read THIS volume")
a.insn(4, lambda s: bytes([0x47, 0x70]) + s.bd(15, "FAILV2"), "BC    7,FAILV2",
       "rather than matching four plausible bytes by luck")
a.insn(4, lambda s: bytes([0x82, 0x00]) + s.bd(15, "PASSPSW"), "LPSW  PASSPSW", "")

FAILS = (("FAIL1","F1PSW"), ("FAIL2","F2PSW"), ("FAIL3","F3PSW"),
         ("FAIL4","F4PSW"), ("FAIL5","F5PSW"), ("FAIL6","F6PSW"),
         ("FAIL7","F7PSW"), ("FAIL8","F8PSW"), ("FAIL9","F9PSW"),
         ("FAILV1","FV1PSW"), ("FAILV2","FV2PSW"))
for n, p in FAILS:
    a.label(n)
    a.insn(4, (lambda p: lambda s: bytes([0x82,0x00]) + s.bd(15, p))(p),
           "LPSW  %s" % p, "%s:" % n)

# ------------------------------------------------------------------- data
for name, ia in (("PASSPSW", 0x00600B),
                 ("F1PSW",  0x001101),   # STSCH cc/=0 -- subchannel number?
                 ("F2PSW",  0x001102),   # MSCH  cc/=0
                 ("F3PSW",  0x001103),   # SSCH  cc/=0
                 ("F4PSW",  0x001104),   # TSCH  cc=3
                 ("F5PSW",  0x001105),   # poll exhausted
                 ("F6PSW",  0x001106),   # device status -- READ IRB+8
                 ("F7PSW",  0x001107),   # subchannel status -- READ IRB+9
                 ("F8PSW",  0x001108),   # residual count high
                 ("F9PSW",  0x001109),   # residual count low
                 ("FV1PSW", 0x001111),   # data is not 'VOL1' -- READ READBUF
                 ("FV2PSW", 0x001112),   # volser is not SCRTCH
                 ("PCPSW",  0x000DED)):
    a.data(name, (lambda ia: lambda s: psw(ia))(ia), "", align=8)

a.data("SSIDW", lambda s: (0x00010001).to_bytes(4, "big"),
       "subchannel 0001 = the DASD; 0000 is the console", align=4)
a.data("POLLMAX", lambda s: (400000).to_bytes(4, "big"),
       "higher than the console tests: a seek takes longer", align=4)

a.data("ORB", lambda s: (
    (0).to_bytes(4, "big")              # intparm
    + bytes([0x00])                     # flag4: key 0
    + bytes([0x80])                     # flag5: F=1 format-1 CCWs
    + bytes([0x80])                     # lpm -- must be 80
    + bytes([0x00])                     # flag7
    + s.addr("CCW1").to_bytes(4, "big")
    + bytes(20)
), "32 bytes", align=4, size=32)

a.data("SCHIB", lambda s: bytes(52), "", align=4)
a.data("IRB", lambda s: bytes(64), "", align=4)

# The channel program.  Four CCWs, contiguous, all doubleword aligned
# because the first one is and each is exactly 8 bytes.
a.data("CCW1", lambda s: (
      bytes([0x07, 0x40]) + (6).to_bytes(2, "big")        # SEEK, CC
      + s.addr("SEEKADDR").to_bytes(4, "big")
), "SEEK BBCCHH, command chained", align=8, size=8)
a.data("CCW2", lambda s: (
      bytes([0x31, 0x40]) + (5).to_bytes(2, "big")        # SEARCH ID EQ, CC
      + s.addr("SRCHID").to_bytes(4, "big")
), "SEARCH ID EQUAL CCHHR, command chained", align=8, size=8)
a.data("CCW3", lambda s: (
      bytes([0x08, 0x00]) + (0).to_bytes(2, "big")        # TIC
      + s.addr("CCW2").to_bytes(4, "big")
), "TIC back to the SEARCH -- skipped when the search matches", align=8, size=8)
a.data("CCW4", lambda s: (
      bytes([0x06, 0x20]) + (DATALEN).to_bytes(2, "big")  # READ DATA, SLI
      + s.addr("READBUF").to_bytes(4, "big")
), "READ DATA, suppress incorrect length", align=8, size=8)

a.data("SEEKADDR", lambda s: (
      (0).to_bytes(2, "big")                  # BB, always zero
      + CYL.to_bytes(2, "big") + HEAD.to_bytes(2, "big")
), "BBCCHH", align=2, size=6)
a.data("SRCHID", lambda s: (
      CYL.to_bytes(2, "big") + HEAD.to_bytes(2, "big") + bytes([REC])
), "CCHHR -- cylinder 0, head 0, record 3", align=1, size=5)

a.data("EVOL1", lambda s: "VOL1".encode("cp037"), "EBCDIC 'VOL1'", align=1)
a.data("EVOLSER", lambda s: VOLSER.encode("cp037"), "EBCDIC volume serial", align=1)
a.data("READBUF", lambda s: bytes(DATALEN), "where the label lands", align=1,
       size=DATALEN)

a.layout().assemble(size=0x1000)

a.check_align(("SSIDW",4,"L"), ("POLLMAX",4,"L"), ("ORB",4,"SSCH FW_CHECK"),
              ("SCHIB",4,"STSCH"), ("IRB",4,"TSCH"),
              ("CCW1",8,"CCW doubleword"), ("CCW2",8,"CCW doubleword"),
              ("CCW3",8,"CCW doubleword"), ("CCW4",8,"CCW doubleword"),
              *[(p,8,"LPSW") for _, p in FAILS],
              ("PASSPSW",8,"LPSW"), ("PCPSW",8,"program new PSW"))
# The chain must be contiguous, or the CC flags chain to the wrong place.
for x, y in (("CCW1","CCW2"), ("CCW2","CCW3"), ("CCW3","CCW4")):
    assert a.addr(y) == a.addr(x) + 8, f"{x}->{y} not contiguous"

a.print_listing()
print("\n  chain at %06X:  SEEK -> SEARCH ID EQ -> TIC -> READ DATA"
      % a.addr("CCW1"))
print("  target  cylinder %d head %d record %d, %d bytes"
      % (CYL, HEAD, REC, DATALEN))
print("  expect  READBUF = 'VOL1' + '%s'" % VOLSER)
print("  READBUF at %06X -- dump it by hand if 001111 or 001112"
      % a.addr("READBUF"))
print("  IRB     at %06X  (+8 devstat  +9 substat  +10 residual)"
      % a.addr("IRB"))
print("  SSIDW   at %06X = 00010001 -- subchannel 0001" % a.addr("SSIDW"))
print("  ends %06X" % a.end)

end = (a.end + 7) & ~7
cmds = a.pokes((0x2000, end, 8))
open("dasd1.cmds", "w").write("\n".join(cmds) + "\n")
print("\n%d poke commands" % len(cmds))
