#!/usr/bin/env python3
"""Build the AUXLCL update decks for the 31-bit conversion.

The conversion is delivered as CE's own local update level rather than as edits
to base source: `594/DMKLCL.CNTRL` stacks `LCL AUXLCL` over `HRC AUXHRC` over
`TEXT AUXR60`, and the LCL level is empty and reserved for exactly this. See
../../../docs/15-UPDATE-LEVELS.md.

    python3 build.py            # writes the decks next to this file, verified

Then read them onto MAINT's A disk and:

    CPACC
    VMFMAC DMKLCL DMKLCL        rebuild the local MACLIB with the updated PSA
    VMFASM DMKIOS DMKLCL        assemble against it

`DMKLCL MACLIB` is first in the `MACS` record, and `VMFASM` does
`GLOBAL MACLIB &1 &2 ...` in that order, so a `PSA` member there overrides the
one in `DMKMAC` without touching `DMKMAC` at all.
"""
import glob
import os
import re
import sys

TOOLS = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'tools')
sys.path.insert(0, TOOLS)
from mkdeck import Deck, aux, auxcheck, verify, next_seq    # noqa: E402


def auxdrop(path, deck):
    """Remove one deck from an AUXLCL, which is what un-applies it.

    `aux()` merges and never removes -- correct for its job, since two
    generators writing the same module's AUXLCL used to mean whichever ran last
    won (`I-138`).  Bisection needs the opposite: `VMFASM` applies what the
    AUXLCL lists, so dropping the line is how a deck stops being applied
    without deleting the file or editing the table.
    """
    if not os.path.exists(path):
        return
    keep = [l for l in open(path) if l.split(None, 1)[:1] != [deck]]
    with open(path, 'w') as f:
        f.writelines(keep)

# The resolved tree the anchors are measured against.  R-23.
SRC = '/home/claude/vmce/source/cp'
CMSSRC = '/home/claude/vmce/source/cms'      # M5: the CMS decks (DMSxxx)


def srcfile(module, exts=('ASSEMBLE', 'MACRO', 'COPY')):
    """The source a module or member comes from: CP first, then CMS."""
    for d in (SRC, CMSSRC):
        for ext in exts:
            q = os.path.join(d, '%s.%s' % (module, ext))
            if os.path.exists(q):
                return q
    return os.path.join(SRC, '%s.ASSEMBLE' % module)

HERE = os.path.dirname(os.path.abspath(__file__))
XA1 = 'XA0001DK'
XA2 = 'XA0002DK'
XA3 = 'XA0003DK'
XA4 = 'XA0004DK'
XA6 = 'XA0006DK'
XA7 = 'XA0007DK'
XA8 = 'XA0008DK'          # XA0005DK was never issued -- the gap is deliberate
XA9 = 'XA0009DK'
XA10 = 'XA0010DK'
XA11 = 'XA0011DK'
XA12 = 'XA0012DK'
XA13 = 'XA0013DK'
XA14 = 'XA0014DK'
XA15 = 'XA0015DK'
XA16 = 'XA0016DK'
XA17 = 'XA0017DK'
XA18 = 'XA0018DK'
XA19 = 'XA0019DK'
XA20 = 'XA0020DK'
XA21 = 'XA0021DK'
XA22 = 'XA0022DK'
XA23 = 'XA0023DK'
XA24 = 'XA0024DK'
XA25 = 'XA0025DK'
XA26 = 'XA0026DK'
XA27 = 'XA0027DK'
XA28 = 'XA0028DK'
XA29 = 'XA0029DK'
XA30 = 'XA0030DK'
XA31 = 'XA0031DK'
XA32 = 'XA0032DK'
XA33 = 'XA0033DK'
XA34 = 'XA0034DK'
XA35 = 'XA0035DK'
XA36 = 'XA0036DK'
XA37 = 'XA0037DK'
XA38 = 'XA0038DK'
XA39 = 'XA0039DK'
XA40 = 'XA0040DK'
XA41 = 'XA0041DK'
XA42 = 'XA0042DK'
XA43 = 'XA0043DK'
XA44 = 'XA0044DK'
XA45 = 'XA0045DK'
XA46 = 'XA0046DK'
XA47 = 'XA0047DK'
XA48 = 'XA0048DK'
XA49 = 'XA0049DK'
XA50 = 'XA0050DK'
XA51 = 'XA0051DK'
XA52 = 'XA0052DK'
XA53 = 'XA0053DK'   # M4b: real storage above 16 MB


def psa():
    """M1 step 2: ESA/390 lowcore names, and the S/370-only fields marked.

    Anchors are the sequence numbers in the RESOLVED tree (source/cp/PSA.MACRO),
    because the LCL level applies last -- after AUXR60 and AUXHRC. PSA already
    has both, which is why 00175100-00175400 exist at all.
    """
    d = Deck(XA1)

    # --- X'A8', X'AC', X'B0': the three fields with no ESA/390 counterpart.
    d.replace('00173000', '00175000', first='00173100', inc=100, limit='00175100', lines=[
        "*  S/370 ONLY -- NO ESA/390 COUNTERPART.  RENAMED, NOT",
        "*  DELETED, SO A SURVIVING REFERENCE FAILS TO ASSEMBLE",
        "*  RATHER THAN READ LOWCORE THAT NOW MEANS SOMETHING ELSE.",
        "*  STIDC IS GONE, AND THE CHANNEL SUBSYSTEM REPLACES",
        "*  CHANNEL LOGOUT WITH THE ESW AND ERW IN THE IRB PLUS",
        "*  STCRW.  DELETING THEM WOULD LEAVE NO TRACE OF A",
        "*  DECISION A 64-BIT PASS HAS TO MAKE AGAIN.  EXPECTED TO",
        "*  BREAK DMKIOG DMKPRV DMKCCH DMKEIG -- ALL CHANNEL-ERROR",
        "*  AND STIDC-SIMULATION PATHS.  SEE RISK R-03.",
        "S370CHID DS    1F -           STIDC CHANNEL ID, S/370",
        "S370IOEL DS    1F -           IO EXTENDED LOGOUT PTR, S/370",
        "S370ECSW DS    1F -           LIMITED CHANNEL LOGOUT, S/370",
    ])
    d.replace('00175100', first='00175110', inc=10, limit='00175200', lines=[
        "         ORG   S370ECSW",
    ])
    d.replace('00175300', first='00175310', inc=10, limit='00175400', lines=[
        "S370EBY3 DS    1X             3RD BYTE OF LCL, S/370",
    ])

    # --- X'B8' and X'BA': same offset, same width, different meaning.
    d.replace('00177000', '00178000', first='00177100', inc=10, limit='00179000', lines=[
        "*  X'B8' IS THE ESA/390 SUBSYSTEM-IDENTIFICATION WORD,",
        "*  X'BC' THE INTERRUPTION PARAMETER.  CP'S INTKFLIN",
        "*  ALREADY SAT ON THAT EXACT FULLWORD, AND ITS LOW",
        "*  HALFWORD IS THE SUBCHANNEL NUMBER, BECAUSE THE",
        "*  SUBSYSTEM ID IS X'0001' IN THE HIGH HALFWORD.  SO",
        "*  NOTHING MOVES AND NOTHING CHANGES WIDTH; ONLY THE",
        "*  MEANING DOES.  MEASURED IN 07-io-interrupt.rc, WHICH",
        "*  READ X'B8' FOR FOUR BYTES AND MATCHED 00010000.",
        "*",
        "*  INTTIO IS RENAMED WITH NO ALIAS, DELIBERATELY.  19 OF",
        "*  ITS 21 REFERENCES COMPARE IT AGAINST A DEVICE ADDRESS",
        "*  -- WHICH A SUBCHANNEL NUMBER IS NOT -- SO AN ALIAS",
        "*  WOULD LET EVERY ONE KEEP ASSEMBLING AND SILENTLY",
        "*  COMPARE THE WRONG THING.  THAT IS RISK R-02, THE JOINT",
        "*  TOP RISK, AND THIS IS THE CHEAPEST PLACE TO MAKE IT",
        "*  LOUD.",
        "*",
        "*  THESE OFFSETS ARE UNCHANGED IN Z/ARCHITECTURE, SO THE",
        "*  NAMES BELOW CARRY FORWARD WITHOUT EDIT.",
        "IOSSID   DS    1F -           ESA/390 SUBSYSTEM ID WORD",
        "INTKFLIN EQU   IOSSID -       S/370 NAME, SAME FULLWORD",
        "IOSCHNO  EQU   IOSSID+2 -     ESA/390 SUBCHANNEL NUMBER",
        "*",
        "*  AND A GUEST'S PAGE 0 IS NOT CP'S LOWCORE.  PSA SERVES",
        "*  BOTH: CP'S OWN REAL LOWCORE, AND A TEMPLATE FOR A",
        "*  VIRTUAL MACHINE'S PAGE 0 -- EVERY  X-PSA(,R2)  SITE.",
        "*  GUESTS STAY S/370-MODE THROUGH M4, SO A GUEST-PSA",
        "*  DISPLACEMENT KEEPS ITS S/370 MEANING.  DMKDSP BUILDS A",
        "*  GUEST INTERRUPT CODE HERE FROM VDEVADD+VCUADD+VCHADD, A",
        "*  VIRTUAL DEVICE ADDRESS AND NOT A SUBCHANNEL NUMBER, SO IT",
        "*  NEEDS ITS OWN NAME: IOSCHNO WOULD READ AS THE OPPOSITE",
        "*  OF THE TRUTH.  S370CHID AND S370ECSW ALREADY SERVE THE",
        "*  OTHER TWO GUEST-PSA SITES CORRECTLY.",
        "G370TIO  EQU   IOSSID+2 -     GUEST S/370 DEVICE ADDRESS",
    ])

    # --- X'BC': carve the interruption parameter out of the reserved area.
    d.replace('00179000', first='00179010', inc=10, limit='00180000', lines=[
        "IOINTPRM DS    1F -           ESA/390 IO INTERRUPT PARAMETER",
        "         DS    10F -          RESERVED FOR HARDWARE USE",
    ])
    # --- CR6.  `CPCREG6 DC F'0'` is CP's one value for control register 6, and
    #     on S/370 it carried the CP-assist and VM-assist enable bits.  On
    #     ESA/390 CR6 is the I/O-INTERRUPTION SUBCLASS MASK (`esa390.h`: "CR6 is
    #     the I/O interruption subclass mask"), so zero means no I/O
    #     interruption is ever presented -- the same silent gate `XA0013DK`
    #     closed in CTLREGS, reopened by every routine that reloads CR6.
    #
    #     Giving CPCREG6 the mask turns the problem into its own fix: CP
    #     already reloads CR6 from here on the dispatch path, so the value it
    #     keeps re-asserting becomes the correct one.  The `OI CPCREG6,X'02'`
    #     in DMKCPI needs no change at all -- OI addresses byte 0, and X'02' is
    #     already on in X'FF' -- which is luck, but checkable luck.
    #
    #     This generates storage only in DMKPSA: `PSA.MACRO` opens with
    #     `AIF ('&SYSECT' EQ 'DMKPSA').PSA1`, so every other module gets a
    #     DSECT and no DC.  The field keeps its length, so no other module's
    #     offsets move.  I-71.
    # --- CR0's TRANSLATION FORMAT: the bits that were never the tables.
    #
    # `IPL-WALLS.md` attributed `PRG018` to the segment table being in S/370
    # format with bit 0 set in every entry.  The tables WERE wrong and that was
    # a real defect, but it was not the cause of the exception, and converting
    # them did not clear it.  Hercules checks CR0 FIRST, at [3.11.3.2], before
    # it fetches a single table entry:
    #
    #     if ((regs->CR(0) & CR0_TRAN_FMT) != CR0_TRAN_ESA390)
    #         goto tran_spec_excp;
    #
    #     CR0_TRAN_FMT    0x00F80000   bits 8-12, the translation format
    #     CR0_TRAN_ESA390 0x00B00000   1 MB segments, 4 KB pages
    #
    # CE sets `CPCREG0 DC X'81800CC0'` (094/PSA.HRC004DK), and
    # X'81800CC0' & X'00F80000' is X'00800000' -- System/370 for 4 KB pages and
    # **64 KB segments**.  ESA/390 requires X'00B00000'.  Two bits, 10 and 11.
    #
    # Measured on 2 October from a converted nucleus whose tables were verified
    # correct first: CR1 = X'00FFC005' with bit 0 clear and the origin 4096-
    # aligned, STE 0 = X'00FFAC0F' with PTO 64-aligned and PTL 15, and a page
    # table of X'00000000 00001000 00002000 ...' -- textbook ESA/390 entries --
    # and the identical PRG018 at the identical LRA.  Everything the conversion
    # touched was right and the one constant it never touched was wrong.  I-152.
    #
    # X'81B00CC0' keeps bit 7 (CR0_STORKEY_4K, which CE already sets and which
    # 23-STORAGE-KEYS.md depends on) and every external mask in X'0CC0'.
    # The anchor is the RESOLVED sequence, 00242490: HRC004DK replaced record
    # 00242000 with `$ 242490 490`, so 00242000 no longer exists in the tree our
    # decks apply over.  `next_seq` refused the stale number rather than letting
    # it become a NOT FOUND at update time -- I-52's guard working.
    # Seven cards between 00242490 and 00243000 need an increment of 10, not
    # 100: the generator refused 00242500 step 100 because the seventh card
    # would land on 00243100, past CPCREG6.  R-22's check, doing its job.
    d.replace('00242490', first='00242500', inc=10,
              limit=next_seq(SRC + '/PSA.MACRO', '00242490'), lines=[
        "*  CR0 BITS 8-12 ARE THE TRANSLATION FORMAT. S/370 PUT PAGE",
        "*  SIZE IN 8-9 AND SEGMENT SIZE IN 11-12; ESA/390 REQUIRES",
        "*  THE SINGLE PATTERN X'00B00000' -- 1 MB SEGMENTS, 4 KB",
        "*  PAGES. CE'S X'81800CC0' GIVES X'00800000', WHICH IS 64 KB",
        "*  SEGMENTS, AND LRA TAKES A TRANSLATION-SPECIFICATION",
        "*  EXCEPTION BEFORE IT READS ANY TABLE. I-152.",
        "CPCREG0  DC    X'81B00CC0' CP ARCH CONTROL AND EXTERNAL MASK",
    ])

    d.replace('00243000', first='00243010', inc=10, limit='00244000',
              lines=Deck.comment(
        "WAS DC F'0' -- CP ASSIST AND VMA MASK. ON ESA/390 CR6 IS THE I/O "
        "INTERRUPTION SUBCLASS MASK AND ZERO PRESENTS NOTHING. ALL EIGHT "
        "SUBCLASSES ENABLED; SUBCHANNELS DEFAULT TO ISC 0. I-71.") + [
        "*  DS 0F BECAUSE LCTL TAKES A SPECIFICATION EXCEPTION ON A",
        "*  MISALIGNED OPERAND AND DC X DOES NOT ALIGN. THE OLD DC F",
        "*  ALIGNED IMPLICITLY; THIS SAYS IT.",
        "CPCREG6  DS    0F             FULLWORD ALIGNED",
        "         DC    X'FF000000'    CR6 -- IO SUBCLASS MASK",
    ])

    # --- X'41C': the TRANS macro's AMODE 31 LRA, as a stub every module can
    #     reach with base register 0.  The first design (I-208) put six
    #     instructions around every LRA, +16 bytes a site, and DMKMON -- 8
    #     bytes short of its single 4 KB base -- lost its literal pool
    #     (I-216).  A stub here costs a site L + BASSM, +2 bytes.  The PSA is
    #     at real 0 and addressed from R0, so the stub needs no base, and it
    #     is entered in AMODE 31 through ATRL31's bit 0: a 3-byte adcon with
    #     X'80' in front, so the loader relocates only bytes 1-3 and no
    #     question about a bit-0 RLD arises.  TRL31 runs LRA R2,0(0,R1) --
    #     the operands of 139 of CP's 151 TRANS sites -- and BSM 0,R15 goes
    #     back in the caller's mode with LRA's condition code intact.  The
    #     other twelve forms keep the inline wrapper.  Only in DMKPSA is
    #     this storage; everywhere else PSA is a DSECT.  Carved from the 5F
    #     reserved before INSTWRD1, so no later offset moves.
    d.replace('00255600', first='00255610', inc=10, limit='00256000', lines=[
        "*  AMODE 31 STUB FOR THE TRANS MACRO. DOCS/34-AMODE31.",
        "*  TRL31 IS IN DMKPSA'S LIVE CODE NOW (XA0049DK): IT GREW",
        "*  A MODE TEST FOR 31-BIT GUESTS AND NO LONGER FITS HERE, SO",
        "*  THE ADCON IS ONLY RESOLVED WHERE THE CODE IS -- DMKPSA.",
        "         AIF   ('&SYSECT' NE 'DMKPSA').ATRLD",
        "ATRL31   DC    X'80',AL3(TRL31) 31-BIT ENTRY, FOR BASSM",
        "         AGO   .ATRLX",
        ".ATRLD   ANOP",
        "ATRL31   DS    1F -           THE ADCON, SEEN AS A DSECT",
        ".ATRLX   ANOP",
        "         DS    4F -           RESERVED (WAS 5F)",
    ])

    return d


def rbloks():
    """RDEVSSID: the subsystem-identification word, per 20-DMKIOS-DESIGN.md.

    Subchannel numbers are not derivable from device addresses, so CP has to
    learn the mapping with STSCH at initialisation and keep it somewhere.
    RDEVBLOK is the right home -- CP already chains it by device address.

    Stored as a FULLWORD holding X'0001' in the high halfword and the
    subchannel in the low, so each SSCH site becomes one instruction
    (L R1,RDEVSSID) rather than a load, a shift and an OR.

    Inserted immediately before  RDEVSIZE EQU (*-RDEVBLOK)/8  so the size
    symbol grows with the block.  A full DOUBLEWORD is added rather than a
    fullword: the EQU divides by 8 and truncates, so growing by 8 keeps
    whatever alignment the block already had and cannot shrink RDEVSIZE.
    LDEVRDEV DS (RDEVSIZE*8)X grows with it automatically.
    """
    d = Deck(XA2)
    d.insert('00162300', first='00162310', inc=10, limit='00163000',
             lines=Deck.comment(
        "ESA/390 SUBSYSTEM IDENTIFICATION. SUBCHANNEL NUMBERS ARE NOT "
        "DERIVABLE FROM DEVICE ADDRESSES -- THEY ARE ASSIGNED IN "
        "CONFIGURATION ORDER -- SO CP LEARNS THE MAPPING WITH STSCH AT "
        "INITIALISATION AND KEEPS IT HERE. HELD AS A FULLWORD OF "
        "X'0001' || SUBCHANNEL SO THAT EVERY SSCH SITE IS ONE INSTRUCTION, "
        "L R1,RDEVSSID, WITH NO SHIFTING OR MASKING. THE SECOND FULLWORD "
        "KEEPS THE BLOCK A WHOLE DOUBLEWORD LONGER, BECAUSE RDEVSIZE "
        "DIVIDES BY 8 AND TRUNCATES.") + [
        "RDEVSSID DS    1F -           X'0001' || SUBCHANNEL NUMBER",
        "         DS    1F -           RESERVED, KEEPS RDEVSIZE EXACT",
    ])
    return d


def ioblok():
    """IOBORB and IOBIRB: the ORB and IRB, one per outstanding operation.

    Not a global work area.  DMKIOS's own prologue says
    ATTRIBUTES = REENTRANT, RESIDENT and the module contains no STNSM,
    STOSM or SSM anywhere -- it never disables -- so a single shared ORB
    or IRB could be overwritten by a re-entry between being built and
    being used.  The IOBLOK is the right granularity and CP already does
    exactly this with IOBCSW, the real CSW per operation.

    Inserted before  IOBSIZE EQU (*-IOBLOK)/8  so the size symbol grows.
    96 bytes is a whole number of doublewords, so the truncating divide
    in that EQU stays exact.
    """
    d = Deck(XA3)
    # Anchored at the END of the block, immediately before `IOBSIZE EQU
    # (*-IOBLOK)/8`, and NOT after IOBCSW where it first went.  An insert in
    # the middle shifts every field below it -- IOBIOER, IOBSPEC, IOBFLAG and
    # the rest -- by 112 bytes, so every module that reads an IOBLOK, not just
    # those that allocate one, would need reassembling to stay correct.  At the
    # end, only IOBSIZE changes, which narrows the blast radius from "reads an
    # IOBLOK" to "allocates one".  Both still require a full nucleus rebuild;
    # the difference is what a missed module does.  I-76.
    d.insert('00050300', first='00050310', inc=10, limit='00051000',
             lines=Deck.comment(
        "ESA/390 OPERATION REQUEST BLOCK AND INTERRUPTION RESPONSE BLOCK, "
        "ONE PER OUTSTANDING OPERATION. DMKIOS IS REENTRANT AND NEVER "
        "DISABLES -- IT HAS NO STNSM, STOSM OR SSM ANYWHERE -- SO THESE "
        "CANNOT BE A SHARED WORK AREA. MAPPED WITH ORBLOK AND IRBLOK IN "
        "XABLOKS. THE IRB IS SIXTY-FOUR BYTES BECAUSE TSCH ALWAYS STORES "
        "ALL SIXTY-FOUR, EVEN THOUGH M1 READS ONLY THE SCSW.") + [
        "*  DS 0D: SSCH AND TSCH BOTH TAKE A SPECIFICATION",
        "*  EXCEPTION ON A MISALIGNED OPERAND.",
        "         DS    0D             DOUBLEWORD ALIGNED",
        "IOBORB   DS    0XL32          ORB -- SEE ORBLOK IN XABLOKS",
        "IOBOPARM DS    1F             INTERRUPTION PARAMETER",
        "IOBOFL4  DS    1X             KEY AND SUSPEND CONTROL",
        "IOBOFL5  DS    1X             FORMAT, PREFETCH, INIT STATUS",
        "IOBOLPM  DS    1X             LOGICAL PATH MASK",
        "IOBOFL7  DS    1X             LENGTH AND EXTENSION CONTROL",
        "IOBOCCW  DS    1F             CCW ADDRESS FOR THIS OPERATION",
        "         DS    5F             PAD -- SEE ORBLOK",
        "IOBIRB   DS    0XL64          IRB -- SEE IRBLOK IN XABLOKS",
        "IOBISCSW DS    0XL12          SUBCHANNEL STATUS WORD",
        "IOBIFL0  DS    1X             KEY, SUSPEND, DEFERRED CC",
        "IOBIFL1  DS    1X             FORMAT, INIT STATUS, ZERO CC",
        "IOBIFL2  DS    1X             FUNCTION AND ACTIVITY CONTROL",
        "IOBIFL3  DS    1X             ACTIVITY AND STATUS CONTROL",
        "IOBICCW  DS    1F             CCW ADDRESS",
        "IOBIDST  DS    1X             DEVICE STATUS     -- TO CSW+4",
        "IOBISST  DS    1X             SUBCHANNEL STATUS -- TO CSW+5",
        "IOBICNT  DS    1H             RESIDUAL COUNT    -- TO CSW+6",
        "         DS    XL20           EXTENDED STATUS WORD",
        "         DS    XL32           EXTENDED CONTROL WORD",
        "IOBXSAV  DS    4F             R14, R15, R0, R1 IN THE SHIMS",
        "*  PER-IOBLOK, SO THE SHIMS STAY REENTRANT -- XAIO'S STATIC",
        "*  WORK AREA IS NOT, WHICH IS WHY DMKIOS CANNOT USE XAIO.",
    ])
    return d


def dmkios():
    """M1 step 4, first increment: the SSCH path.

    Four edits, per 20-DMKIOS-DESIGN.md.  Deliberately NOT the whole of step
    4: the four TIO sites, two HDV sites and two TCH sites are a second deck,
    because each needs its condition-code flow re-derived rather than
    substituted, and those instructions still assemble as S/370 meanwhile.

    Every access uses a base CP already holds -- R10 for the IOBLOK, R8 for
    the RDEVBLOK, R0 for the PSA -- so no register is borrowed anywhere and
    no USING is added.  That was worth the redesign: at the SSCH site the
    only demonstrably free register is R15, and "demonstrably" rested on a
    trace call twenty lines later.
    """
    d = Deck(XA4)

    # 1. Build the ORB alongside the CAW.  The CAW store STAYS: 1,917 CAW and
    #    CSW references in CP keep reading it, and the shim keeps the CSW
    #    honest, which is the whole premise of the conversion.
    d.replace('01194000', first='01194100', inc=10, limit='01195000',
              lines=['IOSTCAW  ST    R2,CAW         KEPT -- SEE BELOW'] +
              Deck.comment(
        "THE CAW STORE STAYS. 1,917 CAW AND CSW REFERENCES ACROSS CP KEEP "
        "READING BOTH, AND IOSXCC1 BELOW KEEPS THE CSW HONEST. THAT IS THE "
        "PREMISE OF THE WHOLE I/O CONVERSION: CHANGE THE TEN INSTRUCTIONS, "
        "NOT THE 1,917 REFERENCES.") + [
        "         MVC   IOBORB,ORBTMPL BUILD THE ORB -- IMPLICIT L'32",
        "         MVC   IOBOPARM+2(2),IOBRADD  INT PARM = DEVICE ADDR",
        "         ST    R2,IOBOCCW     CCW ADDRESS FOR THIS OPERATION",
    ])

    # 1b. I-174, wall 16.  The ORB's interruption parameter is the ONLY way an
    #     ESA/390 I/O interrupt can carry anything of CP's choosing, and the
    #     template left it zero -- so the hardware handed back zero and
    #     `DMKIOT`'s `CLC IOINTPRM+2(2),IOBRADD` could never match ANY device.
    #     Every asynchronous completion was therefore unroutable and dropped.
    #
    #     DASD hid it completely: its status is normally already pending at
    #     `SSCH`, so cc=1 takes the synchronous `IOSXCC1`/`TSCH` path and never
    #     needs an interrupt at all.  1,474 channel programs of nucleus load
    #     and directory read all went that way.  The console write completes
    #     asynchronously, and it was the first thing in five days that actually
    #     depended on the interrupt path.
    #
    #     Measured: `IOSCHNO` read `X'0056'` -- only a real interrupt stores
    #     that -- and the same interrupt stored `IOINTPRM = 00000000`.
    #
    #     The device address is the right value to carry, not the IOBLOK
    #     address, because it makes all FOUR of DMKIOT's existing comparisons
    #     work unchanged (`MVC 2(2,R14),IOINTPRM+2`, `LH R1,IOINTPRM+2`,
    #     `CLC IOBRADD(2),IOINTPRM+2`, `CLC IOINTPRM+2(2),2(R14)`).  Carrying
    #     the IOBLOK instead would be faster and would mean rewriting all of
    #     them -- against this module's own stated premise, three comments up:
    #     change the ten instructions, not the 1,917 references.

    # 2. SIO -> SSCH.  The operand meaning inverts: SIO takes the device
    #    address in R1 and ignores its operand; SSCH takes the subsystem id
    #    in R1 and the ORB as its operand.  LH R1,IOBRADD upstream is left
    #    alone because IOSQTIO still needs the device address in R1.
    d.replace('01206000', first='01206010', inc=10, limit='01207000',
              lines=Deck.comment(
        "SIO TOOK THE DEVICE ADDRESS IN R1 AND IGNORED ITS OPERAND. SSCH "
        "TAKES THE SUBSYSTEM ID IN R1 AND THE ORB AS ITS OPERAND -- THE TWO "
        "SWAP ROLES. THE LH R1,IOBRADD UPSTREAM IS LEFT ALONE BECAUSE "
        "IOSQTIO STILL WANTS THE DEVICE ADDRESS THERE. A DEVICE DMKRIO "
        "NAMES BUT THE CONFIGURATION LACKS HAS NO SUBCHANNEL AND RDEVSSID "
        "ZERO; SIO ANSWERED CC3 FOR IT, SSCH WITH SID 0 IS AN OPERAND "
        "EXCEPTION (PRG021, I-211). ANSWER CC3 OURSELVES.") + [
        "         L     R1,RDEVSSID    X'0001' || SUBCHANNEL NUMBER",
        "         LTR   R1,R1          IS THERE A SUBCHANNEL AT ALL?",
        "         BNZ   IOSXDOSS       YES",
        "         L     R1,=X'80000000' NO: CC3 NOT OPERATIONAL",
        "         LCR   R1,R1          BY OVERFLOW",
        "         B     IOSXDONE       AS SIO WOULD HAVE SAID",
        "IOSXDOSS SSCH  IOBORB         START SUBCHANNEL",
        "IOSXDONE DS    0H",
    ])

    # 3. cc1 no longer means "CSW stored", so route it through the shim.
    d.replace('01241000', first='01241100', inc=10, limit='01242000', lines=[
        "         BC    4,IOSXCC1      CC 1 = STATUS PENDING, NOT CSW",
    ])

    # 4. The shim and the ORB template, placed out of line between RETYCNT
    #    and IOSNSIO1 -- an area reached only by branch, so nothing falls
    #    into it.  RETYCNT DC F'40000' sitting there already is the
    #    precedent.
    # --- M1 step 4, second increment: the remaining nine sites.
    #
    # Each one goes through a normalising shim, for the same reason XAIO does:
    # the branches after every site test S/370 condition codes, and there are
    # four of them at 01269000 alone -- BC 8,IOSDVFRE / BC 4,TIOCC1 /
    # BC 1,IOSCC3 / B IOSQBSY.  A shim that hands back the code TIO would have
    # set leaves all of them untouched, which in the scheduler is worth a great
    # deal more than the instructions it costs.
    #
    # STM R14,R1 wraps to save R14, R15, R0 and R1 into IOBXSAV, and LM
    # restores them without disturbing the condition code -- the same pattern
    # XAIO uses, but with the save area inside the IOBLOK so it stays
    # reentrant.  R1 comes back holding IOBRADD, which every site still wants.
    # --- The nine remaining sites, in ascending anchor order because UPDATE
    # reads the source once, forward.  Every one is the same four-instruction
    # call: STM R14,R1 wraps to save R14, R15, R0 and R1 into IOBXSAV, BAL to
    # the shim, LM to restore -- and LM does not alter the condition code, so
    # the code the shim set survives into the caller's branches.  R1 comes back
    # holding IOBRADD, which every site still wants.
    def call(seq, first, inc, limit, shim, text, lab=''):
        d.replace(seq, first=first, inc=inc, limit=limit, lines=[
            "%-8s STM   R14,R1,IOBXSAV  %s" % (lab, text),
            "         BAL   R14,%s" % shim,
            "         LM    R14,R1,IOBXSAV",
        ])

    call('01263000', '01263100', 100, '01264000', 'IOSXTIO',
         'ISSUE REQUESTED TEST I/O')
    call('01274000', '01274100', 100, '01275000', 'IOSXHIO',
         'ISSUE REQUESTED HALT I/O', lab='IOSQHIO')

    # 01356000 keeps its IOSTIO label and its own loop, whose BC 2 tested
    # "channel busy".  TSCH never returns CC2, so that loop would never repeat.
    # The wait it wants is "until status is present", which after normalisation
    # is CC1 -- so this is the one site in the module where a mask changes.
    d.replace('01356000', '01357000', first='01356100', inc=100,
              limit='01358000', lines=Deck.comment(
        "THE ONLY MASK CHANGE IN THIS MODULE. BC 2 WAITED ON TIO'S CC2, "
        "CHANNEL BUSY, WHICH TSCH NEVER RETURNS. THE WAIT INTENDED IS UNTIL "
        "STATUS IS PRESENT, AND AFTER NORMALISATION THAT IS CC1 -- SO LOOP "
        "WHILE THE DEVICE STILL READS FREE.") + [
        "IOSTIO   STM   R14,R1,IOBXSAV  YES - CLEAR STATUS",
        "         BAL   R14,IOSXTIO",
        "         LM    R14,R1,IOBXSAV",
        "         BC    8,IOSTIO       WAIT UNTIL STATUS IS THERE",
    ])

    # 01480000 and 01489000: TCH has no counterpart at all.  The channel
    # subsystem exposes no per-channel busy state -- every subchannel is
    # independently addressable -- so both sites force the available path.
    # CR R1,R1 sets CC0 in two bytes and clobbers nothing, which matters
    # because R1 here holds RCHADD, a channel address, not a device address.
    for seq, lab in (('01480000', ''), ('01489000', 'TESTCHAN')):
        d.replace(seq, first=str(int(seq) + 100), inc=100,
                  limit=str(int(seq) + 1000), lines=[
            "%-8s CR    R1,R1          ALWAYS AVAILABLE: SETS CC0" % lab,
        ])

    call('01525000', '01525100', 100, '01526000', 'IOSXHIO',
         'TRY AGAIN TO HALT IT', lab='HIORLOOP')
    d.replace('01563000', first='1563010', inc=10,
              limit=next_seq(SRC + '/DMKIOS.ASSEMBLE', '01563000'),
              lines=Deck.comment("WAS LCTL C2,C2,TEMPSAVE. CR2 IS THE DUCT ORIGIN ON ESA/390, NOT A CHANNEL MASK, AND THERE IS NO PER-CHANNEL MASK TO PUT IT IN INSTEAD. THE STCTL AND THE ARITHMETIC ABOVE ARE HARMLESS AND STAY, SO NO LABEL MOVES. DISABLING A FAILING CHANNEL DURING CHANNEL-CHECK RECOVERY: THE CHANNEL SUBSYSTEM OWNS PATH RECOVERY NOW.") + [
        "         DS    0H             THE LCTL IS GONE. I-73.",
    ])

    d.replace('01585000', first='1585010', inc=10,
              limit=next_seq(SRC + '/DMKIOS.ASSEMBLE', '01585000'),
              lines=Deck.comment("WAS LCTL C2,C2,TEMPSAVE. CR2 IS THE DUCT ORIGIN ON ESA/390, NOT A CHANNEL MASK, AND THERE IS NO PER-CHANNEL MASK TO PUT IT IN INSTEAD. THE STCTL AND THE ARITHMETIC ABOVE ARE HARMLESS AND STAY, SO NO LABEL MOVES. REENABLING IT AFTERWARDS.") + [
        "         DS    0H             THE LCTL IS GONE. I-73.",
    ])

    call('02617000', '02617100', 100, '02618000', 'IOSXTIO',
         "SEE IF IT'S REALLY BUSY")
    call('02627250', '02627260', 10, '02627300', 'IOSXTIO', 'IS IT BUSY ?')

    d.insert('02651100', first='02651105', inc=5, limit='02652000',
             lines=Deck.comment(
        "ORB TEMPLATE. EVERYTHING EXCEPT THE CCW ADDRESS, WHICH IOSTCAW "
        "STORES. LPM MUST BE X'80': SSCH TESTS ORB.LPM AGAINST PMCW.PAM AND "
        "PAM IS X'80', SO A ZERO LPM MEANS NO PATH AVAILABLE RATHER THAN ANY "
        "PATH, AND SSCH THEN RETURNS CONDITION CODE 3 WITH NO DIAGNOSTIC OF "
        "ANY KIND. THAT COST A CYCLE IN THE BARE-METAL TESTS.") + [
        "         DS    0F",
        "ORBTMPL  DC    1F'0'          INTERRUPTION PARAMETER",
        "         DC    X'00'          FLAG4: KEY ZERO",
        "         DC    AL1(ORBCCWFM)  FLAG5: CCW FORMAT -- R-27",
        "         DC    AL1(ORBLPMOK)  LPM -- MUST BE X'80'",
        "         DC    X'00'          FLAG7",
        "         DC    6F'0'          CCW ADDRESS AND PAD",
        "         SPACE 1",
     ] + Deck.comment(
        "IOSXCC1 IS THE CSW SHIM. SIO CONDITION CODE 1 MEANT HERE IS YOUR "
        "CSW, NOW. SSCH CONDITION CODE 1 MEANS STATUS IS PENDING, GO AND "
        "FETCH IT. SO TSCH THE IRB, SYNTHESISE A CSW AT X'40' FROM THE SCSW, "
        "AND JOIN THE ORIGINAL PATH. NO REGISTER IS USED: THE IOBLOK BASE IN "
        "R10 AND THE PSA BASE IN R0 ARE BOTH ALREADY ESTABLISHED.") + [
        "         SPACE 1",
     ] + Deck.comment(
        "CSW BYTE 0 IS SET TO ZERO, WHICH LEAVES THE LOGOUT-PENDING BIT "
        "X'04' ALWAYS OFF, SO EVERY TM CSW,X'04' IN CP FALLS THROUGH. THE "
        "ESA/390 REPLACEMENT FOR CHANNEL LOGOUT IS THE ESW AND ERW IN THE "
        "IRB PLUS STCRW, AND THAT BELONGS TO RISK R-03 AND NOT TO M1. "
        "STUBBING IT THIS WAY LOSES ERROR DETAIL; IT DOES NOT INVENT ANY, "
        "WHICH IS THE SAFE DIRECTION TO FAIL.") + [
        "         SPACE 1",
     ] + Deck.comment(
        "THE CCW ADDRESS IS COPIED STRAIGHT ACROSS. S/370 DEFINED THE CSW "
        "ADDRESS AS EIGHT PAST THE LAST CCW USED; WHETHER THE SCSW USES THE "
        "SAME CONVENTION FOR EVERY STATUS TYPE IS NOT YET CHECKED, AND M1 "
        "READS STATUS BYTES RATHER THAN THIS ADDRESS. TO BE SETTLED BEFORE "
        "ANY CODE RELIES ON THE VALUE.") + [
        "         SPACE 1",
        "IOSXCC1  DS    0H             ESA/390 CC 1: STATUS PENDING",
        "         TSCH  IOBIRB         FETCH IT, CLEAR THE SUBCHANNEL",
        "         MVI   CSW,X'00'      KEY ZERO, LOGOUT NEVER PENDING",
        "         MVC   CSW+4(4),IOBIDST STATUS AND RESIDUAL COUNT",
        "         MVC   CSW+1(3),IOBICCW+1 CCW ADDRESS, LOW 3 BYTES",
        "         B     IOSCC1         NOW PROCEED AS S/370 DID",
        "         SPACE 1",
    ] + Deck.comment("IOSXTIO NORMALISES TSCH BACK TO TIO'S CONDITION CODES. TIO CC"
        "THE DEVICE WAS FREE; TSCH CC1 MEANS NOTHING IS PENDING, WHICH"
        "SAME FACT WITH THE OPPOSITE CODE. WHEN STATUS IS PRESENT A CS"
        "BUILT AT X'40' SO EVERY TM CSW+4 AROUND THE CALL SITES STILL") + [
        "         SPACE 1",
        "IOSXTIO  DS    0H             TSCH, WITH TIO'S CONDITION CODE",
        "         L     R1,RDEVSSID    X'0001' || SUBCHANNEL NUMBER",
        "         LTR   R1,R1          NO SUBCHANNEL: NOT OPERATIONAL",
        "         BZ    IOSXNOP        ...",
        "         TSCH  IOBIRB         TEST SUBCHANNEL",
        "         BC    4,IOSXTIOF     CC1: NOTHING PENDING = FREE",
        "         BC    3,IOSXTIOX     CC2 AND CC3 PASS THROUGH",
        "         MVI   CSW,X'00'      BUILD THE CSW THE CALLER EXPECT",
        "         MVC   CSW+1(3),IOBICCW+1  CCW ADDRESS",
        "         MVC   CSW+4(4),IOBIDST  STATUS AND COUNT",
        "         LA    R15,1          TELL THE CALLER CSW STORED,",
        "         LCR   R15,R15        WHICH IS CC1. LTR WOULD GIVE CC",
        "         BR    R14",
        "IOSXTIOF DS    0H             DEVICE FREE: TIO CALLED THAT CC",
        "         SR    R15,R15        ZERO RESULT, SO CC0",
        "IOSXTIOX DS    0H",
        "         BR    R14",
        "         SPACE 1",
        "IOSXHIO  DS    0H             HSCH REPLACES HIO AND HDV ALIKE",
        "*  THE DISTINCTION WAS BETWEEN HALTING A CHANNEL AND HALTING",
        "*  DEVICE, AND A SUBCHANNEL IS ALWAYS EXACTLY ONE DEVICE. THE",
        "*  CONDITION CODES ALREADY AGREE CLOSELY ENOUGH THAT THE",
        "*  BC 8+2+1 MASKS AT THE CALL SITES ARE LEFT ALONE.",
        "         L     R1,RDEVSSID    X'0001' || SUBCHANNEL NUMBER",
        "         LTR   R1,R1          NO SUBCHANNEL: NOT OPERATIONAL",
        "         BZ    IOSXNOP        ...",
        "         HSCH  0              HALT SUBCHANNEL",
        "         BR    R14",
        "IOSXNOP  L     R1,=X'80000000' DEVICE NOT IN THE CONFIG:",
        "         LCR   R1,R1          CC3 BY OVERFLOW, AS SIO DID",
        "         BR    R14            ANSWERED FOR IT. I-211",
        "         SPACE 1",
        "IOSXSIO  DS    0H             SSCH FOR THE SENSE PATH",
        "         MVC   IOBORB,ORBTMPL BUILD THE ORB",
        "         MVC   IOBOPARM+2(2),IOBRADD  DEV ADDR -- I-174",
        "         MVC   IOBOCCW,CAW    CCW ADDRESS THE CALLER SET",
        "         L     R1,RDEVSSID    X'0001' || SUBCHANNEL NUMBER",
        "         LTR   R1,R1          NO SUBCHANNEL: NOT OPERATIONAL",
        "         BZ    IOSXNOP        ...",
        "         SSCH  IOBORB         START SUBCHANNEL",
        "         BR    R14",
    
    ])

    # 02654000 is the sense SSCH.  It comes after the shims because UPDATE
    # reads the file once, forward, and its anchor is higher than theirs.
    d.replace('02654000', first='02654100', inc=100, limit='02655000', lines=[
        "IOSNSIO  STM   R14,R1,IOBXSAV  ATTEMPT TO DO SENSE",
        "         BAL   R14,IOSXSIO",
        "         LM    R14,R1,IOBXSAV",
    ])


    # 5. XABLOKS for ORB5F and ORBLPMOK.  Placed with the other COPYs so the
    #    DSECTs land after the CSECT, which is where block definitions
    #    already go in this module.
    d.insert('02801000', first='02801500', inc=100, limit='02802000', lines=[
        "         COPY  XABLOKS        ESA/390 CHANNEL SUBSYS BLOCKS",
    ])
    return d


def guest_psa():
    """The two sites where a renamed PSA field is a GUEST lowcore displacement.

    I-36.  PSA serves both CP's own real lowcore and a template for a virtual
    machine's page 0.  Guests stay S/370-mode through M4, so these keep their
    S/370 meaning: there is no semantic change here at all, only a symbol that
    says what the code already does.

    Each clears a whole nucleus module, which is the best ratio available in
    the nine the PSA rename broke.
    """
    dsp = Deck(XA6)
    dsp.replace('01209000', first='01209100', inc=10, limit='01210000',
                lines=Deck.comment(
        "R2 POINTS AT THE GUEST'S PAGE 0, NOT CP'S LOWCORE -- EVERY REFERENCE "
        "HERE IS X-PSA(,R2). THE VALUE IS VDEVADD+VCUADD+VCHADD, A VIRTUAL "
        "DEVICE ADDRESS, AND THE GUEST IS AN S/370 MACHINE, SO THIS FIELD "
        "KEEPS ITS S/370 MEANING. G370TIO NAMES THAT; IOSCHNO WOULD CLAIM A "
        "SUBCHANNEL NUMBER AND BE WRONG. NO SEMANTIC CHANGE.") + [
        "         STCM  R0,7,G370TIO-PSA-1(R2)  GUEST INTERRUPT CODE",
    ])

    # --- CR6 on the dispatch path, two sites, both found only because the
    #     sweep expands register RANGES.  I-71.
    #
    #     02422000 loads the GUEST's control registers 4 through 13 into the
    #     real ones for an EC-mode virtual machine.  CR6 is the third of them,
    #     so a virtual machine's assist word lands in the real I/O-interruption
    #     subclass mask.  The range splits either side of it; ECBLOK's EXTCR4
    #     through EXTCR13 are consecutive fullwords, so EXTCR7 names the second
    #     half exactly.
    dsp.replace('02422000', first='02422100', inc=100,
                limit=next_seq(SRC + '/DMKDSP.ASSEMBLE', '02422000'),
                lines=Deck.comment(
        "WAS LCTL C4,C13,EXTCR4. CR6 IS THE I/O SUBCLASS MASK ON ESA/390 AND "
        "IS NOT THE GUEST'S TO SET, SO THE RANGE SPLITS AROUND IT.") + [
        "         LCTL  C4,C5,EXTCR4   USER'S VALUES, BUT NOT CR6",
        "         LCTL  C7,C13,EXTCR7  THE REST OF THEM",
    ])

    #     02542000 is the unconditional one, and the reason CTLREGS alone was
    #     never going to be enough: it reloads CR6 on EVERY dispatch, from
    #     CPCREG6 by default and from the user's VMMICRO when the assist is on
    #     for both system and user.  With the assist off -- the CE default and
    #     the only possibility on ESA/390, where every ECPS:VM opcode is
    #     S/370-only -- the module's own comment says what happens: "NO - LEAVE
    #     CREG6 ZERO".  CPCREG6 now carries the mask (XA0001DK), so naming it
    #     directly makes the dispatcher re-assert the right value on every
    #     dispatch instead of destroying it.
    dsp.replace('02542000', first='02542100', inc=100,
                limit=next_seq(SRC + '/DMKDSP.ASSEMBLE', '02542000'),
                lines=Deck.comment(
        "WAS LCTL C6,C6,0(R6) -- LOAD APPROPRIATE VMA VALUE, WITH R6 SET TO "
        "CPCREG6 OR VMMICRO ABOVE. NEITHER IS A SUBCLASS MASK, AND THIS RUNS "
        "ON EVERY DISPATCH. I-71.") + [
        "         LCTL  C6,C6,CPCREG6  SUBCLASS MASK, EVERY DISPATCH",
    ])

    prv = Deck(XA7)
    # --- CR6 again, and this one IS guarded -- `TM CPSTAT2,CPMICON` and an
    #     ICM on VMMADDR both have to pass.  On ESA/390 they never will, so
    #     this is belt and braces rather than a live defect; it is converted
    #     anyway because leaving one path that can still write a MICBLOK
    #     pointer into the I/O subclass mask is how I-71 happened in the first
    #     place.  I-71.
    prv.replace('00780000', first='00780100', inc=100,
                limit=next_seq(SRC + '/DMKPRV.ASSEMBLE', '00780000'),
                lines=Deck.comment(
        "WAS LCTL C6,C6,VMMICRO -- RELOAD ASSIST CREG.") + [
        "         LCTL  C6,C6,CPCREG6  IO SUBCLASS MASK, NOT AN ASSIST",
    ])

    prv.replace('01400000', first='01400100', inc=10, limit='01401000',
                lines=Deck.comment(
        "STIDC SIMULATION FOR A VIRTUAL MACHINE. R2 POINTS AT THE GUEST'S "
        "PAGE 0, AND AN S/370 GUEST'S STIDC MUST STILL STORE A CHANNEL ID AT "
        "ITS OWN X'A8'. S370CHID IS THE RIGHT NAME FOR THAT, AND IT IS THE "
        "NAME THE CP LOWCORE RENAME ALREADY PRODUCED -- A PLEASANT ACCIDENT. "
        "NO SEMANTIC CHANGE.") + [
        "         ST    R5,S370CHID-PSA(0,R2) GUEST CHANNEL ID",
    ])
    return dsp, prv


def dmkeig():
    """R-03: the S/370 channel extended logout has no ESA/390 counterpart.

    DMKEIG is the extended-logout analyser for 2860/2870/2880 channels.  It
    walks six words of I/O extended logout looking for a channel that has
    logged out, then reads LW0-LW27 -- the 2880's logout format -- to decide
    whether the failure is retryable.  None of that survives: the channel
    subsystem reports failures as subchannel status in the IRB, with the ESW
    and ERW carrying what little detail there is, and there is no per-channel
    logout area at all.

    So the analysis cannot be converted, only replaced, and replacing it is
    not M1 work.  R-03's recorded mitigation is to stub every logout site to
    a permanent error so the path assembles and fails loudly, and DMKEIG
    already has exactly that path: its own "extended logout pointer is zero"
    exit goes to CLEANUP, which sets ENTSW,TERMSYS -- system termination --
    and returns without dereferencing R1.  Taking it needs one branch.

    The 160 lines of analysis below stay in the module, unreachable, so a
    later pass can re-point them at the ESW and ECW instead of writing them
    again from the principles of operation.
    """
    d = Deck(XA8)

    d.replace('00093000', '00094000', first='00093100', inc=100,
              limit='00095000', lines=Deck.comment(
        "ESA/390 HAS NO CHANNEL EXTENDED LOGOUT, SO THERE IS NOTHING TO "
        "POINT AT AND NOTHING TO ANALYSE. TAKE THE MODULE'S OWN "
        "NO-LOGOUT-AVAILABLE EXIT: CLEANUP SETS ENTSW,TERMSYS AND RETURNS "
        "WITHOUT USING R1, SO A CHANNEL CHECK BECOMES A LOUD SYSTEM "
        "TERMINATION RATHER THAN A SILENT MISREAD OF LOWCORE. R-03.") + [
        "         B     CLEANUP        NO EXTENDED LOGOUT ON ESA/390",
    ])

    d.replace('00101000', first='00101100', inc=100, limit='00102000',
              lines=Deck.comment(
        "UNREACHABLE SINCE 00093000 BRANCHES AWAY. KEPT, WITH THE POINTER "
        "FORCED TO ZERO, SO THE S/370 ANALYSIS BELOW STILL ASSEMBLES AND CAN "
        "BE RE-POINTED AT THE IRB'S ESW AND ECW LATER. R-03.") + [
        "         SR    R1,R1          NO LOGOUT POINTER EXISTS",
    ])
    return d


def dmkiog():
    """DMKIOG's channel survey issues STIDC, which ESA/390 does not have.

    This is the find that justified reading the module instead of renaming
    its six symbols: `STIDC` is `GENx370x___x___` in Hercules' opcode table,
    S/370 mode only, so the survey loop would take an operation exception on
    each of sixteen channels during CP initialisation.  Assembling cleanly
    would have hidden it until the first IPL.

    The fix is again the module's own path.  Before issuing STIDC the code
    sets R0 to F's and the channel-table byte to X'FF' "tentatively ... STIDC
    FAILS", and `BNZ STIDCSAV` takes that path on a non-zero condition code.
    Branching straight there reports every channel as unidentified, which is
    the truth: the channel subsystem does not expose channels this way.  R4
    is recomputed from R5 at the top of the loop, R8 and R9 are dead after
    it, and STIDCSAV stores R0 -- still F's -- into RCHSTIDC.

    One consequence is worth having in writing, because the outstanding
    DMKIOS work depends on it: RCHTYPE's RCH370 flag is only ever reset on
    the 2860/2870/2880 paths, which are now unreachable, so RCH370 stays set
    for every channel.  Both of its consumers are HDV sites in DMKIOS, and
    both now statically take the "let the channel do the work" branch.  That
    is the branch we want under HSCH, so it simplifies M1 step 4 rather than
    complicating it.  I-40.

    The three remaining sites are stores into PSA fields the rename kept, so
    they need the new names and no other change: X'FF' into a reserved byte
    and a zero pointer, neither of which anything reads any more.
    """
    d = Deck(XA9)

    d.replace('00326000', '00332000', first='00326100', inc=100,
              limit='00333000', lines=Deck.comment(
        "STIDC IS AN S/370-ONLY INSTRUCTION: ON ESA/390 IT IS AN OPERATION "
        "EXCEPTION, AND THIS LOOP WOULD TAKE ONE SIXTEEN TIMES DURING CP "
        "INITIALISATION. THE CHANNEL SUBSYSTEM DOES NOT IDENTIFY CHANNELS "
        "THIS WAY AT ALL, SO REPORT EVERY CHANNEL AS UNIDENTIFIED VIA THE "
        "PATH THIS CODE ALREADY HAS FOR IT. R0 IS ALREADY F'S AND THE "
        "CHANNEL-TABLE BYTE ALREADY X'FF' FROM 00323000-00324000.") + [
        "         B     STIDCSAV       NO STIDC: CHANNEL UNIDENTIFIED",
    ])

    d.replace('00416000', first='00416100', inc=100, limit='00417000',
              lines=Deck.comment(
        "RENAMED FIELD, SAME STORE: X'FF' INTO A PSA BYTE NOTHING READS NOW. "
        "THE ECSW IS S/370; SUBCHANNEL STATUS REPLACES IT. R-03.") + [
        "         MVI   S370ECSW,X'FF' INITIALIZE THE ECSW (S/370)",
    ])

    # The next surviving record is 00427300, one hundred away, so this one
    # numbers by ten.  Exactly the R-22 trap the sequence check exists for.
    d.replace('00427200', first='00427210', inc=10, limit='00427300',
              lines=Deck.comment(
        "AS 00416000: RENAMED FIELD, SAME STORE. R-03.") + [
        "         MVI   S370ECSW,X'FF' INITIALIZE THE ECSW (S/370)",
    ])

    d.replace('00536000', first='00536100', inc=100, limit='00537000',
              lines=Deck.comment(
        "RENAMED FIELD, SAME STORE. EVERY PATH THAT REACHES HERE NOW "
        "CARRIES R1 = 0, SO THE LTR BELOW SKIPS THE MVCL THAT WOULD HAVE "
        "PROPAGATED F'S THROUGH A LOGOUT AREA NOBODY ALLOCATES. R-03.") + [
        "         ST    R1,S370IOEL    SAVE THE IOEL POINTER (S/370)",
    ])
    return d


def dmkcch():
    """The channel check handler itself: R-03's last module.

    DMKCCH analyses two different S/370 reporting mechanisms and has a natural
    termination path for each, so almost all of this is renaming rather than
    stubbing.

    `CCHRESTO` (00530000) needs nothing at all beyond the new names.  It loads
    the extended-logout pointer and does `BZ CPTERM` -- put the system down --
    and after XA0009DK that pointer is always zero, because DMKIOG's only
    store into it is `ST R1,S370IOEL` with R1 = 0 on every reachable path.  It
    then dispatches on `MCHMODEL` through `B CCHSEREP(R3)` whose entry 0 is
    also `B CPTERM`, and `MCHMODEL` is NOMODEL under any CPU the model table
    does not list.  Two independent routes to the same correct answer, both
    already written.

    `INTEGRAT` (00340000) is the one that needs a branch.  It tests the Limited
    Channel Logout in the ECSW -- validity bit, log-stored bit, channel-reset
    bit -- and those bits are now stale bytes in a reserved PSA field, so it
    would reach a decision from noise.  Its own `CCHSYSM` sets `ENTSW,TERMSYS`,
    and the code below CCHSYSM then falls through CCHIOER and CCHFAIL to
    `RCUSCN1` -- which is exactly the flow 00327000 uses for a termination
    that has already been decided.  So `B CCHSYSM` reuses the module's own
    path and invents no control flow.  What it copies into the CCH record on
    the way is a record field nobody acts on, not a decision.

    The two sites at 00780400 and 00801000 are GUEST lowcore, like DMKDSP's
    and DMKPRV's: `MVC ECSWLOG-PSA(4,R2)` is commented "ECSW TO USER", and
    00801000 is followed by `TM VMVCR14,VMIOLOG` -- the *user's* control
    register 14 I/O logout mask.  An S/370 guest still has an ECSW and a
    logout pointer at its own X'A8' and X'AC', so these keep their meaning and
    want only the name.  I-36.
    """
    d = Deck(XA10)

    d.replace('00340100', '00342400', first='00340100', inc=100,
              limit='00343000', lines=Deck.comment(
        "THE LIMITED CHANNEL LOGOUT IS S/370. ITS VALIDITY, LOG-STORED AND "
        "CHANNEL-RESET BITS ARE NOW STALE BYTES IN A RESERVED PSA FIELD, SO "
        "TESTING THEM WOULD REACH A DECISION FROM NOISE. TAKE THIS MODULE'S "
        "OWN TERMINATION PATH INSTEAD: CCHSYSM SETS ENTSW,TERMSYS AND FALLS "
        "THROUGH TO RCUSCN1, WHICH IS WHAT 00327000 DOES FOR A TERMINATION "
        "ALREADY DECIDED. THE ANALYSIS BELOW IS LEFT IN PLACE, UNREACHABLE, "
        "FOR A LATER PASS OVER THE IRB'S ESW AND ERW. R-03.") + [
        "         B     CCHSYSM        NO LCL ON ESA/390: TERMINATE",
    ])

    # Unreachable from here on: 00343000's only reference was 00342200, inside
    # the range above.  Renamed so the module assembles and the analysis stays
    # legible to whoever implements ESW handling.
    for seq, first, inc, limit, text in (
        ('00343000', '00343100', 100, '00344000',
         "CCHRESET TM    S370ECSW+3,COMPSYS IS CHANNEL RESET?"),
        ('00347000', '00347100', 100, '00348000',
         "         TM    S370EBY3,CCHIOH  I/O INTERFACE HANG-UP?"),
        ('00354000', '00354100', 100, '00355000',
         "         MVC   FAILECSW+1(3),S370ECSW+1 FAILING ECSW INTO"),
        ('00358100', '00358110', 10, '00359000',
         "         MVC   IOERECSW(4),S370ECSW MOVE IN ECSW"),
        # 00366100 is the next surviving record, one hundred away.
        ('00366000', '00366010', 10, '00366100',
         "         MVI   S370ECSW,X'FF' INITIALIZE THE ECSW (S/370)"),
        ('00367000', '00367100', 100, '00368000',
         "         ICM   R1,15,S370IOEL GET ADDR OF IO EXTENDED LOGOUT"),
        # A fourteenth site I had not catalogued, which CE found: R2 holds
        # SIOADDR, a device address, being stored into what is now IOSCHNO, a
        # subchannel number -- the exact substitution the no-alias rename
        # exists to prevent.  Drop the store rather than translate it.  It is
        # reachable (DMKCCH returns to DMKIOS even with TERMSYS set) but
        # nothing consumes it on the only path out of the module, and leaving
        # IOSCHNO untouched is safer than leaving it wrong.  A correct
        # implementation restores the SSID from RDEVSSID: M1 step 5, DMKIOT.
        # RESTDEV's label is on 00523000 and is undisturbed.  I-43.
        ('00524000', '00524100', 100, '00525000',
         tuple(Deck.comment(
             "STORE DROPPED. R2 HOLDS SIOADDR, A DEVICE ADDRESS, AND THE "
             "FIELD IS NOW IOSCHNO, A SUBCHANNEL NUMBER -- THE ONE "
             "SUBSTITUTION THE RENAME WAS DESIGNED TO MAKE IMPOSSIBLE. A "
             "CORRECT IMPLEMENTATION RESTORES THE SSID FROM RDEVSSID, WHICH "
             "IS M1 STEP 5 WORK IN DMKIOT. UNTIL THEN LEAVE IOSCHNO ALONE: "
             "ON THE ONLY PATH OUT OF THIS MODULE THE SYSTEM IS TERMINATING "
             "AND NOTHING READS IT. I-43."))),
        ('00531000', '00531100', 100, '00532000',
         "         MVC   S370ECSW(4),FAILECSW RESTORE ECSW INFORMATION"),
        ('00536000', '00536100', 100, '00537000',
         "         ICM   R1,15,S370IOEL GET THE POINTER TO THE IOEL"),
        # Guest lowcore, both of these.  R2 addresses the virtual machine's
        # page 0, not CP's.
        ('00780400', '00780410', 10, '00781000',
         "         MVC   S370ECSW-PSA(4,R2),IOERECSW ECSW TO USER"),
        ('00801000', '00801100', 100, '00802000',
         "         L     R1,S370IOEL(R2)  POINTER TO LOGOUT AREA"),
        # WAITCCH's PSW: bit 12 clear, so ESA/390 answers a channel-check
        # wait with a specification exception instead of waiting.  The wait
        # code, X'00000002', is the second half at 00902030 and is unchanged.
        # Same class as I-102, found by sweeping rather than by reading.
        # I-107.
        ('00902020', '00902021', 1, '00902030',
         "         DC    X'000A',X'0000'     EC MODE. I-107."),
    ):
        d.replace(seq, first=first, inc=inc, limit=limit,
                  lines=list(text) if isinstance(text, tuple) else [text])

    return d


def dmkvmi():
    """CP was passing the IPL device address through the architected slot.

    The site is `STH R13,INTTIO  SET IPL DEVICE ADDRESS IN EXT MODE`, and its
    BC-mode sibling one instruction earlier is `STH R13,IPLPSW+2`.  So this is
    CP mimicking the hardware: in BC mode the I/O interruption code lives in
    the PSW, in EC mode at X'BA', and DMKVMI writes the IPL device address into
    whichever one the mode uses so that later code can find it where a real
    I/O interruption would have left it.

    Nothing about ESA/390 requires that, and CP already has the right field:
    `SYSIPLDV DS 1H -  P*3  DEVICE ADDRESS OF SYSTEM IPL DEVICE`, in the PSA,
    set by `DMKCPI` at its seq 00484000 and read by six other places including
    `HDKCQA` and `DMKDMP`.  So this is not a translation at all -- it is a
    redundant copy into hardware-defined storage, and the fix is to write the
    field that means what the value is.  I-47.
    """
    d = Deck(XA11)
    d.replace('00806000', first='00806100', inc=100, limit='00807000',
              lines=Deck.comment(
        "DMKVMI RUNS INSIDE THE VIRTUAL MACHINE (DMKCFP COPIES IT TO THE "
        "GUEST'S X'20000'), SO THIS INTTIO IS THE GUEST'S X'BA': THE PLACE "
        "WHERE A S/370 EC-MODE IPL LEAVES THE IPL DEVICE ADDRESS AND WHERE "
        "AN EC-MODE CMS (DMSINI, M5B) READS IT. THE EARLIER I-47 CARD WROTE "
        "SYSIPLDV HERE, WHICH IN GUEST STORAGE IS NOTHING -- I-241.") + [
        "         STH   R13,G370TIO    GUEST IPL DEVICE, EC MODE",
    ])
    return d
    return d


def dmkiot():
    """M1 step 5: the I/O interrupt entry reads the interruption parameter.

    All ten sites treat `INTTIO` as a 16-bit device address -- compared against
    `IOBRADD` to match a queued IOBLOK, and against the primary and alternate
    console addresses.  ESA/390 presents no device address at interrupt time:
    the hardware stores the subsystem ID at X'B8' and the **interruption
    parameter** at X'BC', and `TSCH` yields the IRB.

    The interruption parameter is CP's to choose, which is the whole trick.
    Hercules shows the flow plainly: `SSCH` copies the ORB's intparm into the
    subchannel (`channel.c`, `memcpy(dev->pmcw.intparm, orb->intparm, ...)`),
    `MSCH` sets it from the SCHIB (`io.c:284`), and every I/O interruption
    presents it from there (`FETCH_FW(*ioparm, dev->pmcw.intparm)`).  It lives
    in the subchannel, so it is delivered on unsolicited interruptions too, not
    only on ones CP started.

    So CP puts the real device address in the low half of each subchannel's
    interruption parameter and reads it back at X'BC'+2.  Ten sites become a
    displacement change, every existing device-address comparison keeps working,
    and `DMKSCNRU` lookups are untouched.

    This deck is therefore only half of step 5: it is correct once something
    sets the parameter, and until then it reads a field nobody writes.  The
    other half is DMKCPI's discovery loop -- `STSCH` each subchannel, then
    `MSCH` to set `PMCW5_E` and the intparm together, filling `RDEVSSID` on the
    way.  Enable and intparm go in one `MSCH` because a subchannel reset clears
    both (`channel.c` zeroes intparm beside `PMCW5_E`), so they must always be
    re-established together.

    A better design exists and is deliberately not taken here: putting the
    RDEVBLOK address in the parameter instead would hand the interrupt handler
    its control block directly and remove a `DMKSCNRU` scan per interruption.
    That changes control flow at each site; the device address is a drop-in.
    Recorded so the cheaper structure is not mistaken for the best one.
    """
    d = Deck(XA12)
    for seq, first, inc, limit, text in (
        ('00278000', '00278100', 100, '00279000',
         "         MVC   2(2,R14),IOINTPRM+2 INTERRUPTING DEVICE ADDR"),
        # --- The interrupt path's CSW, the counterpart of IOSXCC1 on the
        #     SSCH path.  I-175, wall 16's second defect.
        ('00288000', '00288010', 10, '00289000',
         Deck.comment(
        "ESA/390 STORES NO CSW. ON S/370 THE I/O INTERRUPTION ITSELF STORED "
        "ONE AT X'40'; THE CHANNEL SUBSYSTEM KEEPS THE STATUS IN THE "
        "SUBCHANNEL AND MAKES TEST SUBCHANNEL THE ONLY WAY TO FETCH IT. "
        "THIS MODULE READS CSW AT ABOUT FORTY SITES, SO FETCH IT ONCE HERE "
        "AND LET THEM ALL GO ON READING X'40' -- THE SAME BARGAIN IOSXCC1 "
        "MAKES, AND X'40' IS UNASSIGNED IN ESA/390 SO IT IS OURS TO SPEND.")
         + Deck.comment(
        "THE COPY IS EXACT, NOT APPROXIMATE. THE SCSW'S DEVICE-STATUS AND "
        "SUBCHANNEL-STATUS BYTES CARRY THE SAME EIGHT BITS IN THE SAME "
        "ORDER AS THE CSW'S UNIT-STATUS AND CHANNEL-STATUS BYTES, SO THE "
        "FORTY TM AND CLI TESTS DOWNSTREAM NEED NO TRANSLATION. BYTE 0 "
        "GOES TO ZERO: KEY, SLI AND CC HAVE NO ESA/390 COUNTERPART, WHICH "
        "MAKES THE LOGOUT-PENDING TEST AT 00522000 ALWAYS FALSE.")
         + Deck.comment(
        "THE WORK IRB IS STATIC, UNLIKE EVERY OTHER XAIOB AREA, AND HAS TO "
        "BE: DMKSCNRU HAS NOT RUN YET, SO THERE IS NO IOBLOK TO PUT IT IN. "
        "IT IS SAFE BECAUSE THE I/O NEW PSW IS 000C0000 -- I/O MASKED OFF "
        "-- SO NO SECOND I/O INTERRUPT CAN BE TAKEN BEFORE THIS FINISHES.")
         + Deck.comment(
        "R1 IS FREE: THE LAST CARD BELOW LOADS IT ANYWAY. THE SID THE "
        "HARDWARE STORED AT X'B8' IS ALREADY IN THE FORM TSCH WANTS, "
        "X'0001' || SUBCHANNEL NUMBER, SO NO SCAN IS NEEDED. TSCH'S "
        "CONDITION CODE IS DISCARDED: THE LH DOES NOT SET ONE AND "
        "DMKSCNRU SETS ITS OWN BEFORE 00290000 TESTS IT.")
         + [
        "         L     R1,IOSSID      SUBSYSTEM ID OF THIS INTERRUPT",
        "         TSCH  IOTXIRB        FETCH THE STATUS S/370 STORED",
        "         MVI   CSW,X'00'      KEY, SLI AND CC DO NOT SURVIVE",
        "         MVC   CSW+1(3),IOTXIRB+5  CCW ADDRESS",
        "         MVC   CSW+4(4),IOTXIRB+8  STATUS AND COUNT",
        "         LH    R1,IOINTPRM+2  INTERRUPTING UNIT'S ADDRESS",
         ]),
        # Gap of twenty to the next surviving record, so number by five.
        ('00304140', '00304145', 5, '00304160',
         "         CLC   IOBRADD(2),IOINTPRM+2 IS THIS FOR US?"),
        ('00304420', '00304425', 5, '00304440',
         "         CLC   IOBRADD(2),IOINTPRM+2 IS THIS ONE FOR US?"),
        ('00324000', '00324100', 100, '00325000',
         "         LH    R3,IOINTPRM+2  ALSO THE DEVICE ADDRESS."),
        # --- CR2, twice, either side of the interrupt-entry path: the S/370
        #     code masks the failing channel and restores it afterwards.  On
        #     ESA/390 CR2 is the dispatchable-unit-control-table origin and
        #     there is no per-channel mask to put it in instead, so the load
        #     goes.  The STCTL and the arithmetic above each one are harmless
        #     and stay, so no label or branch target moves.  I-73.
        ('00346000', '00346010', 10, None,
         Deck.comment("WAS LCTL C2,C2,TEMPSAVE -- MASK THE FAILING "
                      "CHANNEL. I-73.")
         + ["         DS    0H             THE LCTL IS GONE"]),
        ('00369000', '00369010', 10, None,
         Deck.comment("WAS LCTL C2,C2,TEMPSAVE -- AND RESTORE IT.")
         + ["         DS    0H             THE LCTL IS GONE"]),
        ('00410100', '00410110', 10, '00410200',
         "         CLC   IOINTPRM+2(2),IOBRADD"),
        ('00513000', '00513100', 100, '00514000',
         "         LH    R1,IOINTPRM+2  ADDR. OF INTERRUPTING UNIT"),
        # --- The five channel sites, all `0(R1)` and all on paths that must
        #     WORK rather than merely assemble: this is interrupt entry, and
        #     the console interruption M1 waits for arrives here.  They use
        #     XAIOB rather than XAIO because DMKIOT declares REENTRANT in its
        #     own prologue (seq 00052000) and a static work area cannot be
        #     shared by two concurrent I/Os.  `USING RDEVBLOK,R8` and
        #     `USING IOBLOK,R10` are established at 00187000 and never
        #     dropped, so the subchannel comes from RDEVSSID and the storage
        #     from the IOBLOK.  R1 is left loaded and simply unused; the macro
        #     restores it, so nothing downstream notices.
        ('00514000', '00514010', 10, None,
         ["         XABTIO               IN CASE CHANNEL END WITH IT."]),
        ('00515000', '00515010', 10, None,
         ["RSIO     XABSIO               NOW CLEAR CONTENTION"]),
        ('00846000', '00846100', 100, '00847000',
         "         LH    R4,IOINTPRM+2  SAVE INTERRUPT DEVICE ADDR."),
        ('00864000', '00864100', 100, '00865000',
         "         CLC   IOINTPRM+2(2),2(R14) IS IT PRIMARY CONSOLE?"),
        ('00873000', '00873100', 100, '00874000',
         "         CLC   IOINTPRM+2(2),2(R14) ALTERNATE CONSOLE?"),
        ('01053000', '01053010', 10, None,
         ["         XABTIO               SEE IF IT'S REALLY BUSY"]),
        ('01063300', '01063310', 10, None,
         ["         XABTIO               IS IT BUSY ?"]),
        ('01079000', '01079010', 10, None,
         ["IOTNSIO  XABSIO               ATTEMPT TO DO SENSE"]),
    ):
        d.replace(seq, first=first, inc=inc,
                  limit=limit or next_seq(SRC + '/DMKIOT.ASSEMBLE', seq),
                  lines=text if isinstance(text, list) else [text])

    # --- The work area, before the LTORG at 01160000.  Everything from
    #     01150000 is DC and EQU, so nothing falls into it, and the module has
    #     a single addressability domain -- `USING DMKIOT,R12,R9` at 00192000
    #     with no matching DROP -- so the callers' base registers are the ones
    #     in force here.  I-70.
    d.insert('01159000', first='01159010', inc=10,
             limit=next_seq(SRC + '/DMKIOT.ASSEMBLE', '01159000'),
             lines=Deck.comment(
        "XAIOB WORK AREAS AND SHIMS. REENTRANT BY CONSTRUCTION: THE ORB, "
        "IRB AND REGISTER SAVE AREA ALL LIVE IN THE IOBLOK, AND THE "
        "SUBCHANNEL COMES FROM RDEVSSID RATHER THAN A SCAN.") + [
        "         XAIOBWRK             XAIOB SHIMS",
    ] + Deck.comment(
        "AND THE ONE STATIC EXCEPTION, FOR THE TSCH AT 00288000: THE "
        "FIRST-LEVEL INTERRUPT HANDLER HAS NO IOBLOK YET. DS 16F IS THE "
        "FULL IRB -- SCSW, ESW AND ECW -- AND FULLWORD-ALIGNED, WHICH TSCH "
        "REQUIRES. ONLY THE SCSW IS READ. I-175.") + [
        "IOTXIRB  DS    16F            IRB FOR THE INTERRUPT PATH",
    ])

    # --- XABLOKS last of all, after the other COPYs: it ends in DSECTs, and
    #     ORBCCWFM is used in XAIOBWRK above as a DC operand, which XF resolves
    #     as a forward reference.  I-51.
    d.insert('01170000', first='01170010', inc=10,
             limit=next_seq(SRC + '/DMKIOT.ASSEMBLE', '01170000'),
             lines=["         COPY  XABLOKS        FOR ORBCCWFM"])
    return d


def dmkcpi():
    """M1 step 6: the CR6 gate, and subchannel discovery.

    Two changes, and the first is the more important because nothing would have
    diagnosed it.

    **CR6.**  `CTLREGS` is DMKCPI's control-register image, loaded by
    `LCTL C0,C14,CTLREGS` at seq 00461000.  Its CR2 is `X'FFFFFFFF'` -- the
    S/370 channel-mask register, all thirty-two channels enabled -- and CR6 sits
    inside `DC 11F'0'`, so it is zero.  Under ESA/390 CR6 is the
    **I/O-interruption subclass mask**, and a zero mask means no subclass is
    enabled, which means no I/O interruption is ever presented.  CP would IPL,
    issue a perfectly good SSCH, and wait forever.  Nothing in the assembly or
    the instruction stream hints at it; this is the third of the three silent
    gates.  So the channel mask moves out of CR2 and becomes an ISC mask in CR6.

    CR2 is set to zero rather than left alone, because in ESA/390 it is the
    dispatchable-unit-control-table origin and `X'FFFFFFFF'` is not a value any
    of that wants to see.

    **Discovery.**  The loop probes subchannels 0 upward with `STSCH`, and for
    each one that is provided and valid, takes the device number from the PMCW,
    finds its RDEVBLOK, records the subsystem ID in `RDEVSSID`, and `MSCH`es the
    subchannel to enable it and set the interruption parameter.

    That fills in what `XA0012DK` reads: DMKIOT gets the device address back at
    `IOINTPRM+2` on every interruption, solicited or not.  Enable and parameter
    go in one `MSCH` because a subchannel reset clears both.

    Register choice is dictated by DMKSCNRU's documented conventions -- "GPR 1 =
    DEVICE ADDRESS ... GPR 0, 2-5, & 9-13 ARE NOT USED", and it uses neither
    TEMPSAVE nor BALRSAVE, so it is safe to call this early and safe to call in
    a loop holding state in R2 and R3.

    The probe is bounded rather than stopping at the first gap.  Hercules numbers
    subchannels densely from zero (`config.c`: `dev->subchan =
    sysblk.highsubchan[lcss]++`), so an early exit would work today, but a gap
    would silently truncate the device table and that is not a failure worth
    risking to save a few hundred instructions at IPL.
    """
    d = Deck(XA13)

    # --- the discovery loop, inserted after the last pre-AP instruction.
    d.insert('00480000', first='00480020', inc=20,
             limit=next_seq(SRC + '/DMKCPI.ASSEMBLE', '00480000'),
             lines=Deck.comment(
        "SUBCHANNEL DISCOVERY. ESA/390 REPLACES THE CHANNEL AND UNIT ADDRESS "
        "WITH A SUBCHANNEL NUMBER, AND NOTHING IN THE DIRECTORY KNOWS IT, SO "
        "IT HAS TO BE LEARNED. FOR EACH SUBCHANNEL: STSCH, AND IF IT IS "
        "PROVIDED AND VALID, TAKE ITS DEVICE NUMBER, FIND THE RDEVBLOK, "
        "RECORD THE SUBSYSTEM ID, AND MSCH TO ENABLE IT AND SET THE "
        "INTERRUPTION PARAMETER TO THE DEVICE ADDRESS -- WHICH IS WHAT DMKIOT "
        "READS AT IOINTPRM+2. ENABLE AND PARAMETER GO IN ONE MSCH BECAUSE A "
        "SUBCHANNEL RESET CLEARS BOTH.") + [
        "         LA    R4,CPISCHIB    THE SCHIB WE PROBE INTO",
        "         USING SCHIBLOK,R4                               ",
        "         SR    R2,R2          FIRST SUBCHANNEL NUMBER",
        "         LA    R3,CPINSCH     HOW MANY TO PROBE",
        "CPIDISC  DS    0H                                        ",
        "         L     R1,CPISSID0    X'00010000'",
        "         OR    R1,R2          OR IN THE SUBCHANNEL NUMBER",
        "         STSCH 0(R4)          STORE SUBCHANNEL",
        "         BC    7,CPIDISCN     NOT CC0: NOT PROVIDED, SKIP",
        "         TM    PMCWFLG5,PMCW5V IS THE SUBCHANNEL VALID ?",
        "         BZ    CPIDISCN       NO, NO DEVICE BEHIND IT",
        "         STM   R1,R3,CPIDSAVE SAVE SSID, SCHNO AND COUNT",
        "         LH    R1,PMCWDEV     DEVICE NUMBER FROM THE PMCW",
        "         CALL  DMKSCNRU       FIND THE RCH, RCU AND RDEV",
        "         LM    R1,R3,CPIDSAVE RESTORE -- LM LEAVES THE CC",
        "         BNZ   CPIDISCN       NO RDEVBLOK FOR THIS DEVICE",
        "         USING RDEVBLOK,R8                               ",
        "         ST    R1,RDEVSSID    REMEMBER THIS DEVICE'S SSID",
        "         XC    PMCWPARM,PMCWPARM CLEAR THE PARAMETER",
        "         MVC   PMCWPARM+2(2),RDEVADD DEV ADDR, LOW HALF",
        "         OI    PMCWFLG5,PMCW5E ENABLE THE SUBCHANNEL",
        "         MSCH  0(R4)          MODIFY SUBCHANNEL",
        "         DROP  R8                                        ",
        "CPIDISCN DS    0H             NEXT SUBCHANNEL",
        "         LA    R2,1(0,R2)     BUMP THE SUBCHANNEL NUMBER",
        "         BCT   R3,CPIDISC     PROBE THE WHOLE RANGE",
        "         DROP  R4                                        ",
    ])

    # --- 00593000 and 00594000: the storage-sizing probe.
    #
    # CP measures main storage by pointing the program-new PSW at CPIPINT and
    # walking SSK upward until it takes an ADDRESSING exception; R5 at the
    # exception is the size, stored into DMKSYSRM.  SSK is one of the twelve
    # System/370 instructions 370-XA withdrew -- SA22-7201-08 Appendix F gives
    # it `-` against `B` for SSKE -- so under ESA/390 the FIRST SSK takes an
    # OPERATION exception instead, lands on CPIPINT, which is the loop's own
    # designed exit, and stores R5 = 0.  CP then believes it has no real
    # storage, marks all 4096 pages offline, and FRELOOP runs away over the
    # nucleus.  Nothing reports anything, because the exception IS the exit.
    # I-104.
    #
    # SSKE is the 4 KB counterpart and takes the same two registers, so the
    # instruction is a straight swap and ONE card is the whole change.
    #
    # The 2048 step at 00594000 is deliberately left alone.  ESA/390 has one
    # key per 4 KB block where S/370 had one per 2 KB, so stepping by a page
    # looked tidier -- and `LA R5,4096(,R5)` does not assemble: a
    # base-displacement offset is twelve bits, so X'1000' earns
    # `IFO208 DISPLACEMENT GREATER THAN X'FFF'`.  2048 is the largest step
    # this addressing mode allows, which is presumably why IBM wrote it.
    # Stepping 2048 against 4 KB keys sets each key twice -- redundant rather
    # than wrong, exactly as `23-STORAGE-KEYS.md` found for DMKPTR -- and the
    # `LTR`/`BNZ` wrap test at 16 MB is unaffected, because milestone A runs
    # AMODE 24 so R5 still wraps there.
    #
    # The probe itself is kept rather than replaced by a store of DMKSYSRV.
    # Reading the sysgen constant would be simpler and would be wrong the
    # moment MAINSIZE is smaller than RMSIZE -- which is exactly the case
    # this loop exists to detect.
    d.replace('00593000', first='00593100', inc=100,
              limit=next_seq(SRC + '/DMKCPI.ASSEMBLE', '00593000'),
              lines=Deck.comment(
        "SSK DOES NOT EXIST IN ESA/390, SO THE FIRST ONE TOOK AN OPERATION "
        "EXCEPTION INTO THIS LOOP'S OWN EXIT AND SIZED STORAGE AT ZERO. "
        "SSKE IS THE 4 KB COUNTERPART AND TAKES THE SAME REGISTERS. I-104.") + [
        "KEYLOOP  SSKE  R2,R5          AND SET STORAGE KEYS",
    ])

    # --- I-114.  DMKCPI's own assist probe, at 00613000.  It gets a BRANCH
    #     rather than the six-byte no-op the other twenty sites get, and the
    #     difference matters: no-opping it would fall through to
    #     `OI CPSTAT2,CPASTAVL+CPASTON`, declaring the assists AVAILABLE and ON
    #     on a machine that has none, and skipping `CLEARCPA` entirely.
    #     `B CPIPINT2` is the path CP takes when the probe program-checks, so
    #     this is the same destination reached without the exception.
    #
    #     Padded back to six bytes so nothing downstream shifts.  DMKCPI carries
    #     51 self-relative branches (the second-highest count in CP) and R-26 is
    #     the standing rule; keeping the length identical means it cannot apply.
    #
    #     This is also what makes the ORDERING defect disappear rather than move:
    #     `SCNRU` in DMKSCN faulted before this probe ever ran, so arriving at
    #     CPIPINT2 sooner would not have been enough -- which is why the other
    #     twenty sites are converted statically instead.
    d.replace('00613000', first='00613100', inc=100,
              limit=next_seq(SRC + '/DMKCPI.ASSEMBLE', '00613000'),
              lines=Deck.comment(
        "WAS DC X'E612',S(0(R3),0) -- STORE CP ASSIST LEVEL, THE PROBE. ON "
        "ESA/390 THERE ARE NO ASSISTS, SO TAKE THE NO-ASSIST PATH DIRECTLY "
        "INSTEAD OF PROVOKING AN OPERATION EXCEPTION TO FIND OUT. I-114.") + [
        "         B     CPIPINT2       NO ECPS:VM ON ESA/390",
        "         BCR   0,0            PAD TO THE SIX BYTES E612 HELD",
    ])

    # --- CR6, four sites.  On ESA/390 CR6 is the I/O-interruption subclass
    #     mask, and `XA0001DK` now gives `CPCREG6` the value X'FF000000'.  Every
    #     load of CR6 therefore loads CPCREG6, whatever the S/370 code thought
    #     it was setting -- a uniform rule rather than four judgements.  I-71.
    #
    #     00607000's `OI CPCREG6,X'02'` is deliberately left alone: OI addresses
    #     byte 0, and X'02' is already on in X'FF', so it is a no-op now.
    d.replace('00615000', first='00615100', inc=100,
              limit=next_seq(SRC + '/DMKCPI.ASSEMBLE', '00615000'),
              lines=Deck.comment(
        "WAS LCTL C6,C6,ZEROES -- NO CP ASSIST UNTIL IPL COMPLETE. ZERO IS "
        "NOW NO I/O INTERRUPTIONS AT ALL.") + [
        "         LCTL  C6,C6,CPCREG6  IO SUBCLASS MASK, NOT AN ASSIST",
    ])

    #     00619000 clears the field itself, on the wrong-assist-level path, so
    #     the mask would survive the LCTLs and then be zeroed at the source.
    d.replace('00619000', first='00619100', inc=100,
              limit=next_seq(SRC + '/DMKCPI.ASSEMBLE', '00619000'),
              lines=Deck.comment(
        "WAS MVC CPCREG6,ZEROES -- CLEAR CP ASSIST ENABLE FLAG. CPCREG6 IS "
        "THE IO SUBCLASS MASK NOW AND MUST NOT BE CLEARED; THE ASSIST IS "
        "ALREADY OFF BECAUSE EVERY ECPS:VM OPCODE IS S/370-ONLY.") + [
        "         DS    0H             THE CLEAR IS GONE, NOT MOVED",
    ])

    # --- The twenty live channel sites, all of them `SIO 0(R15)` or
    #     `TIO 0(R15)` in the device-mount loop, every one following the same
    #     shape: the instruction, `BAL R1,TRACESUB` with an inline trace code,
    #     then `BC` masks to labels.  `TRACESUB` already had to preserve the
    #     condition code for the S/370 instruction, so nothing about that
    #     changes; the XAIO macros return the code through `BR R14` and the
    #     `LM` that follows does not disturb it.  R15 survives because the
    #     call-site macro saves and restores R14, R15, R0 and R1.
    #
    #     The twenty-first site, the `SIO` at 00485480, is deliberately NOT
    #     here: it is inside the channel-set-switching probe, which
    #     `CLI N0(R2),YES` at 00483000 skips because `DMKSYSAP` is `N` under
    #     `AP=NO` (XA0014DK).  The unconvertible `CONCS` sits four instructions
    #     before it, so the block is dead as a unit and half-converting an AP
    #     path would be worse than leaving it whole.  Declared in
    #     tools/coverage.py rather than silently skipped.  I-69.
    cpi = lambda seq, line, to=None, extra=(): d.replace(
        seq, to, first=str(int(seq) + 100), inc=100,
        limit=next_seq(SRC + '/DMKCPI.ASSEMBLE', to or seq),
        lines=[line] + list(extra))

    cpi('01045000', "CPIHIO   XAHIO R15            ISSUE HIO")

    # Four consecutive drains for the 3705, with no test between them.
    d.replace('01053000', '01056000', first='01053100', inc=100,
              limit=next_seq(SRC + '/DMKCPI.ASSEMBLE', '01056000'), lines=[
        "         XATIO R15            TO CLEAR HEX 70 STATUS",
        "         XATIO R15            FROM 3705",
        "         XATIO R15            (CODE FOR 3705 ONLY)",
        "         XATIO R15",
    ])

    cpi('01069000', "CPITIO1  XATIO R15            TIO")
    cpi('01096000', 'CHKRSRL2 XASIO R15            ATTEMPT THE "RELEASE"')
    cpi('01111000', "CHKRSRL3 XATIO R15            IF CONDITION-CODE 0,")
    cpi('01154000', "CPISIO1  XASIO R15            ISSUE SIO")
    cpi('01166000', "CPIALLOC XATIO R15            ISSUE TIO")
    cpi('01200000', "CPISIO3  XASIO R15            START THE READ")
    cpi('01225000', "CPSIO1   XASIO R15            SUSPEND IMMEDIATE")
    cpi('01231000', "CPTIO    XATIO R15            CHECK OUT STATUS,CC=0")
    cpi('01239000', "CPIOWNA  XATIO R15            DRAIN FOR CE/DE")
    cpi('01568000', "SNSIO    XASIO R15            ISSUE SENSE COMMAND")
    cpi('01587000', "SNTIO    XATIO R15            CLEAR THE SUBCHANNEL")
    # --- The VM-assist probe's two CR6 loads.  The probe itself is left
    #     running and is correct as it stands: it enters problem state and
    #     issues `SSM`, which the assist microcode would intercept and which
    #     without it raises a privileged-operation exception -- so on ESA/390,
    #     where every ECPS:VM opcode is GENx370x___x___, it lands on CPIPROG
    #     and marks the assist unavailable, which is the right answer arrived
    #     at by the module's own design.  Only the CR6 values are wrong.  The
    #     probe runs with I/O masked in TESTPSW (X'040D0000', bit 6 off), so
    #     CR6's value cannot matter to it either way.
    cpi('01653000', "         LCTL  C6,C6,CPCREG6  IO SUBCLASS MASK, NOT A MICBLOK")

    #     01674000 is the one that decides M1.  `LCTL C6,C6,ZEROES` is the
    #     last instruction before the EJECT whose next comment reads "LOCATE
    #     OPERATOR'S CONSOLE & ATTEMPT TO WRITE SYSTEM MSG" -- so CP zeroed the
    #     I/O-interruption subclass mask immediately before the console write
    #     that M1 exists to produce, and would have waited forever for an
    #     interruption that is never presented.
    d.replace('01674000', first='01674100', inc=100,
              limit=next_seq(SRC + '/DMKCPI.ASSEMBLE', '01674000'),
              lines=Deck.comment(
        "WAS LCTL C6,C6,ZEROES -- RESET ASSIST CONTROL REGISTER. THE VERY "
        "NEXT THING THIS MODULE DOES IS WRITE THE CONSOLE MESSAGE, WHICH "
        "NEEDS AN I/O INTERRUPTION. I-71.") + [
        "         LCTL  C6,C6,CPCREG6  RE-ASSERT THE IO SUBCLASS MASK",
    ])


    cpi('01719000', "         XATIO R15            MAKE SURE IT EXISTS")

    # The module's one backward self-relative branch that spans a converted
    # instruction.  STRTGRF already labels the target, so `*-4` only needs the
    # name it could have used all along.  R-26.
    d.replace('01723000', '01724000', first='01723100', inc=100,
              limit=next_seq(SRC + '/DMKCPI.ASSEMBLE', '01724000'), lines=[
        "STRTGRF  XATIO R15            TEST DEVICE",
        "         BC    2,STRTGRF      LOOP IF BUSY",
    ])

    cpi('01726000', "STRTSIO  XASIO R15            START SENSE TO DEVICE")
    # --- CR2, twice, around an LPSW that waits for a 3277 interruption:
    #     save CR2, load a CHANMASK, wait, restore.  On ESA/390 the wait is
    #     governed by the PSW I/O bit and CR6, both already right, so dropping
    #     both loads leaves it enabled for all I/O -- which is what it wants,
    #     since CHANRET only returns and retries.  I-73.
    for seq, why in (('01749000', 'LOAD OUR NEW MASK'),
                     ('01752000', 'RESTORE CTRL REG')):
        d.replace(seq, first=str(int(seq) + 10).zfill(8), inc=10,
                  limit=next_seq(SRC + '/DMKCPI.ASSEMBLE', seq),
                  lines=Deck.comment(
            "WAS LCTL C2,C2,... -- %s. CR2 IS THE DUCT ORIGIN ON ESA/390. "
            "THE WAIT IS GOVERNED BY THE PSW I/O BIT AND CR6. I-73." % why) + [
            "         DS    0H             THE LCTL IS GONE",
        ])

    cpi('01758000', "TSTGRF   XATIO R15            TEST FOR SENSE END")

    # --- The work area, after TSTGRF's `BR R14` at 01761000 and before the
    #     LTORG.  Placement is forced, not chosen: `DROP R12,R13` at 01767000
    #     ends the DMKCPINT addressability domain and `USING DMKCPIEM,R12,R13`
    #     begins another, so XAIOWORK's OWN references -- `BAL R14,XAIOFIND`,
    #     `MVC XAIOORB+8(4),CAW` -- are assembled against whichever base is
    #     active where the macro expands.  Put it with the other work areas at
    #     01930000 and those displacements would be computed off DMKCPIEM
    #     while every caller runs with R12/R13 holding the DMKCPINT base, which
    #     assembles perfectly and addresses garbage.  Here the USING is the
    #     callers' own.  I-70.
    #
    #     Nothing falls into it: 01761000 is `BR R14`.  And nothing zeroes it
    #     -- DMKCPI's two MVCLs clear CPULOG..PSENDCLR and PSBCLR2..PSECLR2,
    #     which are PSA symbols, not this CSECT.  I-55.
    d.insert('01761000', first='01761010', inc=10,
             limit=next_seq(SRC + '/DMKCPI.ASSEMBLE', '01761000'),
             lines=Deck.comment(
        "XAIO WORK AREAS AND LOOKUP. XABLOKS IS ALREADY COPIED AT 03506100, "
        "AND ORBCCWFM IS USED THERE AS AN MVI IMMEDIATE, WHICH XF RESOLVES "
        "AS A FORWARD REFERENCE -- UNLIKE A LENGTH MODIFIER. I-51.") + [
        "         XAIOWORK             XAIO WORK AREAS AND LOOKUP",
    ])

    # --- 01898000 to 01902100: the six disabled-wait PSWs.
    #
    # `I-102` converted DMKSAV's PSW constants to EC mode and stopped there.
    # The same class is present here and was missed, because DMKSAV was the
    # only module whose PSWs the IPL had reached: every one of DMKCPI's
    # disabled-wait PSWs is `X'0002...'`, bit 12 clear, which ESA/390 refuses
    # with a specification exception.
    #
    # These are CP's error exits -- CAN'T GET TO CONSOLES, REAL MACHINE TOO
    # SMALL FOR VM/370, FAILED TO CONNECT CHANNELS -- so leaving them BC mode
    # does not merely risk a fault later: it means **every initialisation
    # failure reports as a specification exception instead of its own wait
    # code**, which is the difference between a diagnosis and a puzzle.
    # Converting them costs six cards and makes CP able to say what is wrong.
    #
    # `CHANWT` at 01986000 is already `X'020A...'` and is left alone.  IBM
    # converted some of this module's PSWs and not others, exactly the mixed
    # state DMKCKP was in -- which is why a sweep beats reading.  I-107.
    # The label is part of the card and an UPDATE replacement is a whole card,
    # so each one is reproduced: dropping XWAIT1 and friends would leave every
    # `LPSW XWAIT1` in the module unresolved.
    for seq, lbl, code in (('01898000', 'XWAIT1',   '06'),
                           ('01899000', 'XWAIT2',   '05'),
                           ('01900000', 'XWAIT3',   '0D'),
                           ('01901500', 'XWAIT9',   '09'),
                           ('01902000', 'XWAIT4',   '15'),
                           ('01902100', 'XWAITCSS', '16')):
        d.replace(seq, first='%08d' % (int(seq) + 10), inc=10,
                  limit=next_seq(SRC + '/DMKCPI.ASSEMBLE', seq),
                  lines=["%-8s DC    X'000A0000000000%s' EC MODE. I-107."
                         % (lbl, code)])

    # --- CR2 and CR6.  CR2 is one word, CR3-CR13 are the eleven that follow, so
    #     the replacement splits that DC to give CR6 a value of its own.
    d.replace('01928000', '01929000', first='01928100', inc=100,
              limit=next_seq(SRC + '/DMKCPI.ASSEMBLE', '01929000'),
              lines=Deck.comment(
        "CR2 HELD X'FFFFFFFF' AS THE S/370 CHANNEL MASK. ON ESA/390 CR2 IS THE "
        "DISPATCHABLE-UNIT-CONTROL-TABLE ORIGIN AND MUST NOT CARRY THAT, WHILE "
        "CR6 IS THE I/O-INTERRUPTION SUBCLASS MASK AND WAS ZERO -- MEANING NO "
        "I/O INTERRUPTION IS EVER PRESENTED. CP WOULD IPL, ISSUE A GOOD SSCH "
        "AND WAIT FOREVER, WITH NOTHING FLAGGED ANYWHERE. THE MASK THEREFORE "
        "MOVES FROM CR2 TO CR6. ALL EIGHT SUBCLASSES ARE ENABLED; SUBCHANNELS "
        "DEFAULT TO ISC 0.") + [
        "         DC    F'0'           CR2 -- DUCT ORIGIN, NOT A MASK",
        "         DC    3F'0'          CR3, CR4, CR5",
        "         DC    X'FF000000'    CR6 -- IO SUBCLASS MASK",
        "         DC    7F'0'          CR7 THROUGH CR13",
    ])

    # --- the SCHIB, the SSID prefix, the save area and the probe bound.
    d.insert('01930000', first='01930050', inc=50,
             limit=next_seq(SRC + '/DMKCPI.ASSEMBLE', '01930000'),
             lines=Deck.comment(
        "WORK AREAS FOR SUBCHANNEL DISCOVERY. THE SCHIB MUST BE FULLWORD "
        "ALIGNED -- BOTH STSCH AND MSCH TAKE A SPECIFICATION EXCEPTION "
        "OTHERWISE.") + [
        "CPISCHIB DS    13F            52 BYTES = SCHIBSIZ, FULLWORD",
        "*  ALIGNED.  13F RATHER THAN XL(SCHIBSIZ) BECAUSE XABLOKS IS",
        "*  COPIED AFTER THIS POINT AND A LENGTH MODIFIER CANNOT BE A",
        "*  FORWARD REFERENCE -- IFO231.  I-51.",
        "CPIDSAVE DS    3F             SSID, SCHNO, COUNT",
        "CPISSID0 DC    X'00010000'    SUBSYSTEM ID PREFIX, LCSS 0",
        "CPINSCH  EQU   256            SUBCHANNELS PROBED AT IPL",
    ])

    # --- The name, on the console banner.  See the longer note in dmkcns():
    #     CE's System/380 probe zaps a C'8' over the C'7' of "VM/370" in three
    #     places.  We are not taking the /380 route, so the banner is VM/370+.
    d.replace('02140100', first='02140110', inc=10,
              limit=next_seq(SRC + '/DMKCPI.ASSEMBLE', '02140100'),
              lines=Deck.comment(
        "WAS C'VM/370 COMMUNITY EDITION VERSION '. CPIVER, CPIREL AND "
        "CPILEV FOLLOW AS SEPARATE DCs AND STMSGL IS *-STMSG, SO THE EXTRA "
        "BYTE SHIFTS NOTHING THAT IS ADDRESSED BY NAME. THE ONE "
        "FIXED-OFFSET READER WAS THE ZAP REMOVED AT 02287560. I-179.") + [
        "         DC    C'VM/370+ Community Edition Version '",
    ])

    # 02287580 is the next surviving record, twenty away, so number by one.
    d.replace('02287560', first='02287561', inc=1,
              limit=next_seq(SRC + '/DMKCPI.ASSEMBLE', '02287560'),
              lines=Deck.comment(
        "WAS MVI STMSG+7,C'8' -- 'TELL THEM THIS IS SYSTEM/380'. IT IS NOT: "
        "THIS IS A 31-BIT ESA/390 CONVERSION ON THE WAY TO 64-BIT, AND THE "
        "NAME IS VM/370+. THE MVI INSTWRD1,C'8' ABOVE IS LEFT ALONE -- THE "
        "BSM PROBE DID SUCCEED AND THAT IS WORTH RECORDING -- BUT NOTHING "
        "MAY PAINT IT OVER THE BANNER. I-179.") + [
        "         DS    0H             THE ZAP IS GONE",
    ])

    # --- Wall 19.  The interval timer does not exist in 370-XA, and CP
    #     refuses to start without it.  `TIMETEST` reads location X'50',
    #     polls it 40,000 times for a change, writes "Turn on the Interval
    #     Timer" and branches back to poll again -- 181,775 times in one run
    #     before the harness stopped it.
    #
    #     The authority is the same PoO table that justified I-174 and I-175.
    #     Appendix F, "Comparison between System/370 and 370-XA", lists the
    #     assigned-storage locations that differ, and three of this project's
    #     defects are one row each:
    #
    #       Channel-status word         64 (X'40')  ->  gone    I-175
    #       Channel-address word        72 (X'48')  ->  gone    still open
    #       Interval timer              80 (X'50')  ->  gone    this
    #       Subsystem ID                gone -> 184 (X'B8')     I-174
    #       I/O-interruption parameter  gone -> 188 (X'BC')     I-174
    #
    #     CR0 bit 24, the interval-timer subclass mask, goes with it.
    #
    #     So the test cannot be satisfied and must not be run.  Only the
    #     `EQU *` is replaced: `TLOOP1`, `TLOOP` and `NOMPMSG` stay defined
    #     because cards below still branch to them, and the dead loop costs
    #     nothing.  `B TIMETEST` at 02700000 is the only branch in.
    #
    #     This is NOT "timing is gone". The CPU timer and clock comparator
    #     are ESA/390 facilities and CP already uses `STPT`/`SPT` in the
    #     dispatcher. What is gone is the location-X'50' interval timer, and
    #     CP reads it elsewhere -- DMKSCH and DMKDSP most of all -- so the
    #     accounting and time-slicing that depend on it are a separate and
    #     larger piece of work. Clearing the start-up gate does not fix them.
    d.replace('02785000', first='02785010', inc=10,
              limit=next_seq(SRC + '/DMKCPI.ASSEMBLE', '02785000'),
              lines=Deck.comment(
        "WAS TIMETEST EQU * -- THE HEAD OF A POLL ON THE INTERVAL TIMER AT "
        "X'50'. 370-XA DELETED THAT TIMER (PoO APPENDIX F), SO THE VALUE "
        "NEVER CHANGES, THE TEST NEVER PASSES, AND CP SAT IN TLOOP1 WRITING "
        "\'TURN ON THE INTERVAL TIMER\' FOREVER. THE LOOP BELOW IS LEFT IN "
        "PLACE AND UNREACHABLE: TLOOP1, TLOOP AND NOMPMSG ARE STILL BRANCH "
        "TARGETS FURTHER DOWN. THE CPU TIMER AND CLOCK COMPARATOR DO EXIST "
        "AND CP ALREADY USES STPT AND SPT, SO THIS REMOVES A START-UP GATE "
        "AND NOT CP\'S TIMEKEEPING. WALL 19, I-178.") + [
        "TIMETEST DS    0H             NOTHING TO TEST ANY MORE",
        "         B     TIMERON        STRAIGHT PAST THE DEAD POLL",
    ])

    # SCHIBLOK, PMCW* and the subchannel EQUs live in XABLOKS, which until now
    # was copied only into DMKIOS.  Added beside DMKCPI's own COPY list rather
    # than at the point of use, which is where CP keeps its DSECTs.
    d.insert('03506100', first='03506110', inc=10,
             limit=next_seq(SRC + '/DMKCPI.ASSEMBLE', '03506100'),
             lines=["         COPY  XABLOKS"])
    return d


def m4bcpi():
    """M4b.1: CP sizes real storage above 16 MB and builds a CORTABLE for all
    of it, below 16 MB.  docs/38-M4B-REAL2G.md.

    * The probe (`KEYLOOP`, SSKE upward by 2 KB until an addressing
      exception) ran in AMODE 24 -- DMKCPI's initialisation does until its
      first interrupt (I-224) -- so `LA R5,2048(,R5)` wrapped at 16 MB and
      `L R5,=X'01000000'` stored 16 MB whatever Hercules had.  It now runs
      AMODE 31.  The exception's new PSW is `A(CPIPINT)` with bit 32 off, so
      CPIPINT is back in AMODE 24 with the size in R5.
    * The CORTABLE (16 bytes per 4 KB frame) was SYSCOR's static table in
      DMKSYS, sized by RMSIZE (at most 16392K).  DMKCPIB builds one for all
      of real storage at the top of the low 16 MB, stores its origin in
      ACORETBL (the PSA word every module loads it from), marks its own
      frames as system frames and every frame above 16 MB offline ('*OL*',
      as CP marks storage beyond RMSIZE), and stores the low region below
      the table as DMKSYSRV -- the size the rest of DMKCPI lays out free
      storage, the trace table and the dynamic area in.  DMKSYSRM keeps the
      real size: QUERY STORAGE and every bounds check see all of it.  The
      static table and the CP-assist lists that point at it (DMKCCW, DMKFRE,
      DMKPTR) are dead on ESA/390; DMKDMP's DMPCORET still names it (I-201).
    * The dump file is sized from DMKSYSRV, not DMKSYSRM: at 2 GB it would
      be 512K spool records.
    """
    d = Deck(XA53)
    src = SRC + '/DMKCPI.ASSEMBLE'
    d.insert('00592000', first='00592100', inc=100,
             limit=next_seq(src, '00592000'), lines=[
        "         LA    R1,*+16        M4B: PROBE IN AMODE 31",
        "         LA    R0,1           (NO LITERAL: DMKCPI'S POOL",
        "         SLL   R0,31          IS FULL, I-250)",
        "         OR    R1,R0",
        "         DC    X'0B01'        BSM 0,R1",
    ])
    d.replace('00597000', first='00597100', inc=100,
              limit=next_seq(src, '00597000'), lines=[
        "         L     R5,=X'7FFFF000'  M4B: 2 GB",
    ])
    d.insert('00606000', first='00606100', inc=100,
             limit=next_seq(src, '00606000'), lines=[
        "         L     R15,=A(DMKCPIB)  M4B: FULL CORTABLE",
        "         BALR  R14,R15",
    ])
    d.replace('02894000', first='02894100', inc=100,
              limit=next_seq(src, '02894000'), lines=[
        "         L     R10,=A(DMKSYSRV)  M4B: LOW REGION",
    ])
    d.insert('03495800', first='03495801', inc=1,
             limit=next_seq(src, '03495800'), lines=[
        "*",
        "* M4B: THE CORTABLE FOR ALL OF REAL STORAGE, AT THE TOP",
        "* OF THE LOW 16 MB.  BALR R14,R15 IN AMODE 24, REAL SIZE",
        "* IN DMKSYSRM.  RETURNS THE LOW REGION UNDER THE TABLE IN",
        "* DMKSYSRV.  FRAMES ABOVE 16 MB: DMKPGT'S PAGING STORE.",
        "*",
        "DMKCPIB  CSECT",
        "         EXTRN DMKPGTXT",
        "         USING PSA,R0",
        "         STM   R0,R14,CPIBSAVE-DMKCPIB(R15)",
        "         BALR  R11,0",
        "         USING *,R11",
        "         L     R3,=A(DMKSYSRM)",
        "         L     R5,0(,R3)      REAL SIZE",
        "         LR    R6,R5",
        "         SRL   R6,8           16 BYTES PER 4 KB FRAME",
        "         AL    R6,=F'4095'",
        "         N     R6,=X'7FFFF000'  WHOLE PAGES",
        "         L     R10,=X'01000000'  CP BELOW 16 MB",
        "         CLR   R5,R10",
        "         BNL   CPIB1",
        "         LR    R10,R5         UNDER 16 MB: ALL",
        "CPIB1    L     R3,=A(DMKPGTXT)  M4B.2: STORAGE ABOVE 16 MB",
        "         CLR   R5,R10         IS DMKPGT'S PAGING STORE",
        "         BNH   CPIB1A",
        "         ST    R5,0(,R3)      ITS TOP",
        "CPIB1A   LR    R7,R10         TOP OF THE LOW REGION",
        "         SLR   R7,R6          TABLE ORIGIN",
        "         ST    R7,ACORETBL    EVERY MODULE LOOKS HERE",
        "         LR    R8,R7          CLEAR THE TABLE",
        "         LR    R9,R6",
        "         SLR   R14,R14",
        "         SLR   R15,R15",
        "         MVCL  R8,R14",
        "         L     R2,ASYSVM      TABLE FRAMES: SYSTEM",
        "CPIB2    LR    R9,R7",
        "         SRL   R9,8",
        "         AL    R9,ACORETBL",
        "         ST    R2,CORFPNT-CORTABLE(,R9)",
        "         MVI   CORFLAG-CORTABLE(R9),CORCP",
        "         AL    R7,=F'4096'",
        "         CLR   R7,R10",
        "         BL    CPIB2",
        "CPIB3    CLR   R7,R5          FRAMES ABOVE 16 MB: OFFLINE",
        "         BNL   CPIB4",
        "         LR    R9,R7",
        "         SRL   R9,8",
        "         AL    R9,ACORETBL",
        "         MVC   CORFPNT-CORTABLE(4,R9),=C'*OL*'",
        "         AL    R7,=F'4096'",
        "         B     CPIB3",
        "CPIB4    SLR   R10,R6         LOW REGION UNDER TABLE",
        "         L     R3,=A(DMKSYSRV)  DMKCPI LAYS IT OUT",
        "         ST    R10,0(,R3)",
        "         DROP  R11",
        "         BALR  R15,0",
        "         USING *,R15",
        "         LM    R0,R14,CPIBSAVE",
        "         BR    R14",
        "         DROP  R15",
        "CPIBSAVE DS    15F",
        "         LTORG",
    ])
    return d


XSTSLOT = [   # R2 = slot frame address from the CCPD at SWPTABLE R5
    "         SR    R2,R2          SLOT NUMBER = CYL*128",
    "         ICM   R2,B'0011',SWPCYL",
    "         SLL   R2,7",
    "         SR    R0,R0          + PAGE-1",
    "         IC    R0,SWPDPAGE",
    "         BCTR  R0,0",
    "         OR    R2,R0",
    "         SLL   R2,12          FRAME = 16 MB + SLOT*4096",
    "         AL    R2,=X'01000000'",
]


def m4bslots():
    """M4b.2: real storage above 16 MB as CP's paging store.

    Frames above the line hold no guest page and no CP data, so nothing that
    keeps a real address in 24 bits (CCWs, control-block fields with a flag
    in byte 0 -- docs/38-M4B-REAL2G.md) can ever see one.  Instead they are
    page SLOTS, as a paging device's are: DMKPGTPG hands one out before any
    DASD slot, DMKPAG moves the page with MVCL instead of an I/O, and the
    page comes back into a frame below the line on the next page fault.
    This is what VM/XA did with expanded storage.

    A slot's CCPD (SWPCYL/SWPDPAGE/SWPCODE) is CYL = slot/128, PAGE =
    slot//128 + 1 (never 0, which means 'never written'), CODE = X'FF'
    (no OWNDLIST entry; the owned list has at most a few dozen).  Slot n is
    the frame at 16 MB + n*4096.  Allocation pops a free stack threaded
    through the free frames themselves (CP runs AMODE 31) or takes the next
    never-used frame; release pushes.  A slot counts as a drum page
    (VMPDRUM), and every place that finds the device of a slot to keep the
    drum/disk counters -- DMKPGT, DMKPGS, DMKATS, DMKCPP -- or to decide
    on arm optimisation -- DMKPTR -- treats code X'FF' as a drum.
    """
    decks = {}
    src = lambda m: SRC + '/%s.ASSEMBLE' % m

    d = Deck(XA53)
    d.insert('00035000', first='00035100', inc=100,
             limit=next_seq(src('DMKPGT'), '00035000'), lines=[
        "         ENTRY DMKPGTXT       M4B.2: TOP OF THE PAGING STORE",
    ])
    d.replace('00597000', first='00597100', inc=100,
              limit=next_seq(src('DMKPGT'), '00597000'), lines=[
        "SPOOLDEL EQU   *",
        "         CLI   SWPCODE,X'FF'  M4B.2: SLOT ABOVE 16 MB?",
        "         BE    XSTREL",
    ])
    d.insert('01292000', first='01292001', inc=1,
             limit=next_seq(src('DMKPGT'), '01292000'), lines=[
        "*",
        "* M4B.2: THE PAGING STORE ABOVE 16 MB. XSTGET: R2 = CCPD OF A",
        "* FREE SLOT, OR 0.  XSTREL: RELEASE THE SLOT AT SWPTABLE R5.",
        "*",
        "XSTGET   L     R2,XSTFREE     A RELEASED SLOT?",
        "         LTR   R2,R2",
        "         BZ    XSTGET2",
        "         LA    R15,XSTG31     ITS SUCCESSOR, KEPT IN IT:",
        "         O     R15,=X'80000000'  READ IN AMODE 31 (R4B5:",
        "         DC    X'0B4F'        BSM R4,R15  DMKPAG RAN 24-BIT)",
        "XSTG31   L     R0,0(,R2)",
        "         LA    R15,XSTG24",
        "         N     R4,=X'80000000'  BACK TO THE CALLER'S MODE",
        "         OR    R15,R4",
        "         DC    X'0B0F'        BSM 0,R15",
        "XSTG24   DS    0H",
        "         ST    R0,XSTFREE",
        "         B     XSTGET3",
        "XSTGET2  L     R2,XSTHWM      A NEVER-USED SLOT?",
        "         CL    R2,XSTTOP",
        "         BNL   XSTNONE",
        "         LR    R0,R2",
        "         AL    R0,=F'4096'",
        "         ST    R0,XSTHWM",
        "XSTGET3  SL    R2,=X'01000000'  SLOT NUMBER",
        "         SRL   R2,12",
        "         LR    R0,R2",
        "         N     R0,=F'127'     PAGE = SLOT//128 + 1",
        "         AL    R0,=F'1'",
        "         SRL   R2,7           CYL = SLOT/128",
        "         SLL   R2,8",
        "         OR    R2,R0",
        "         SLL   R2,8",
        "         O     R2,=F'255'     DEVICE CODE X'FF'",
        "         BR    R14",
        "XSTNONE  SR    R2,R2",
        "         BR    R14",
        "* DMKPGTPX: DMKPGTPG FOR A USER PAGE-OUT (DMKPTR ONLY).",
        "* DMKPGTPG ITSELF ALSO SERVES DMKCPI, DMKSST AND DMKCDS,",
        "* WHOSE PAGES DMKRPA WRITES WITH ITS OWN CHANNEL PROGRAMS --",
        "* THOSE MUST STAY ON DASD (R4B4: PROGRAM CHECK LOOP AT IPL).",
        "         ENTRY DMKPGTPX",
        "         DROP  R12",
        "         USING *,R15",
        "DMKPGTPX STM   R0,R15,BALRSAVE",
        "         L     R12,=A(DMKPGT)",
        "         DROP  R15",
        "         USING DMKPGT,R12",
        "         CLC   CPID,=C'CPCP'  SYSTEM RUNNING?",
        "         BNE   XSTPX1",
        "         BAL   R14,XSTGET     A SLOT ABOVE 16 MB?",
        "         LTR   R2,R2",
        "         BNZ   XSTGOT         YES",
        "XSTPX1   L     R15,=A(DMKPGTPG)  NO: THE DASD ALLOCATOR",
        "         ST    R15,BALRSAVE+60  (LOADED BEFORE LM: AFTER IT",
        "         LM    R0,R15,BALRSAVE  R12 IS THE CALLER'S BASE)",
        "         BR    R15",
        "XSTGOT   LH    R3,VMPDRUM-VMBLOK(,R11)  COUNTS AS DRUM",
        "         LA    R3,1(,R3)",
        "         STH   R3,VMPDRUM-VMBLOK(,R11)",
        "         B     SETADDR",
        "XSTREL   DS    0H",
    ] + XSTSLOT + [
        "         L     R0,XSTFREE     PUSH IT ON THE FREE STACK",
        "         LA    R15,XSTR31     (STORE IN AMODE 31)",
        "         O     R15,=X'80000000'",
        "         DC    X'0B4F'        BSM R4,R15",
        "XSTR31   ST    R0,0(,R2)",
        "         LA    R15,XSTR24",
        "         N     R4,=X'80000000'",
        "         OR    R15,R4",
        "         DC    X'0B0F'        BSM 0,R15",
        "XSTR24   ST    R2,XSTFREE",
        "         OI    SWPFLAG,SWPRECMP",
        "         XC    SWPCYL(4),SWPCYL",
        "         TM    UCTL,UCTLDR    PAGING ACCOUNTING?",
        "         BZ    XSTREL2",
        "         LR    R4,R11",
        "         TM    UCTL,UCTLSYS   AGAINST THE SYSTEM?",
        "         BZ    *+8",
        "         L     R4,ASYSVM",
        "         LH    R3,VMPDRUM-VMBLOK(,R4)",
        "         S     R3,F1",
        "         BM    XSTREL2",
        "         STH   R3,VMPDRUM-VMBLOK(,R4)",
        "XSTREL2  MVI   UCTL,X'00'",
        "         LM    R0,R15,BALRSAVE",
        "         BR    R14",
        "DMKPGTXT DS    0F",
        "XSTTOP   DC    A(X'01000000')  SET BY DMKCPI: REAL SIZE",
        "XSTHWM   DC    A(X'01000000')  NEXT NEVER-USED SLOT",
        "XSTFREE  DC    A(0)           RELEASED SLOTS",
    ])
    decks['DMKPGT'] = d

    d = Deck(XA53)
    d.insert('00454000', first='00454100', inc=100,
             limit=next_seq(src('DMKPAG'), '00454000'), lines=[
        "         L     R5,CPEXR5      M4B.2: SLOT ABOVE 16 MB?",
        "         CLI   SWPCODE,X'FF'",
        "         BE    XSTIO          YES: MVCL, NO I/O",
    ])
    d.insert('01010000', first='01010001', inc=1,
             limit=next_seq(src('DMKPAG'), '01010000'), lines=[
        "*",
        "* M4B.2: A PAGE WHOSE SLOT IS IN STORAGE ABOVE 16 MB MOVES BY",
        "* MVCL (CP RUNS AMODE 31), AND ITS REQUESTER IS STACKED AS IF",
        "* THE PAGING I/O HAD COMPLETED WITHOUT ERROR.",
        "*",
        "XSTIO    DS    0H",
    ] + XSTSLOT + [
        "         L     R4,CPEXR7      THE FRAME BELOW THE LINE",
        "         SL    R4,ACORETBL",
        "         SLL   R4,8",
        "         L     R3,=F'4096'",
        "         LR    R5,R3",
        "         LR    R7,R3",
        "         LA    R15,XSTIO31    MVCL IN AMODE 31: DMKPAG MAY",
        "         O     R15,=X'80000000'  RUN 24-BIT, AND A 24-BIT",
        "         DC    X'0BEF'        MVCL TO 16 MB WROTE THE PSA",
        "XSTIO31  CLI   CPEXR0+3,X'05' (R4B5) -- WRITE?",
        "         BE    XSTIOW",
        "         LR    R6,R2          READ: SLOT TO FRAME",
        "         MVCL  R4,R6",
        "         B     XSTIOD",
        "XSTIOW   LR    R6,R4          WRITE: FRAME TO SLOT",
        "         LR    R4,R2",
        "         MVCL  R4,R6",
        "XSTIOD   LA    R15,XSTIO24    BACK TO THE CALLER'S MODE",
        "         N     R14,=X'80000000'",
        "         OR    R15,R14",
        "         DC    X'0B0F'        BSM 0,R15",
        "XSTIO24  MVI   CPEXADD,0      NO ERROR",
        "         CALL  DMKSTKCP       THE REQUESTER CONTINUES",
        "         B     GETQ           NEXT REQUEST",
    ])
    decks['DMKPAG'] = d

    d = Deck(XA53)
    d.replace('01533000', first='01533100', inc=100,
              limit=next_seq(src('DMKPTR'), '01533000'), lines=[
        "         CLI   SWPCODE,X'FF'  M4B.2: SLOT ABOVE 16 MB:",
        "         BE    QWRITE         KEEP IT, AS ON A DRUM",
        "         SR    R1,R1          CLEAR VOLUME INDEX",
    ])
    d.replace('01562000', first='01562100', inc=100,
              limit=next_seq(src('DMKPTR'), '01562000'), lines=[
        "         EXTRN DMKPGTPX       M4B.2: STORAGE SLOT FIRST",
        "         CALL  DMKPGTPX       GET NEW DASD PAGE ADDRESS",
    ])
    decks['DMKPTR'] = d

    d = Deck(XA53)
    d.replace('00801000', first='00801100', inc=100,
              limit=next_seq(src('DMKPGS'), '00801000'), lines=[
        "         LA    R15,VMPDRUM-VMBLOK  M4B.2: SLOT ABOVE",
        "         CLI   SWPCODE,X'FF'  16 MB: A DRUM PAGE",
        "         BE    PGSXST",
        "         IC    R2,SWPCODE     GET VOLUME INDEX CODE",
    ])
    d.replace('00812000', first='00812100', inc=100,
              limit=next_seq(src('DMKPGS'), '00812000'), lines=[
        "PGSXST   LH    R0,0(R15,R4)   DECREMENT",
    ])
    decks['DMKPGS'] = d

    d = Deck(XA53)
    d.replace('00547000', first='00547100', inc=100,
              limit=next_seq(src('DMKATS'), '00547000'), lines=[
        "         LA    R14,VMPDRUM-VMBLOK  M4B.2: SLOT ABOVE",
        "         CLI   SWPCODE,X'FF'  16 MB: A DRUM PAGE",
        "         BE    ATSXST",
        "         IC    R1,SWPCODE     GET VOLUME INDEX CODE",
    ])
    d.replace('00559000', first='00559100', inc=100,
              limit=next_seq(src('DMKATS'), '00559000'), lines=[
        "ATSXST   LH    R1,0(R14,R15)  GET OLD OWNERS COUNT",
    ])
    decks['DMKATS'] = d

    d = Deck(XA53)
    d.replace('59400000', first='59410000', inc=10000,
              limit=next_seq(src('DMKCPP'), '59400000'), lines=[
        "         LA    R15,VMPDRUM-VMBLOK  M4B.2: SLOT ABOVE",
        "         CLI   SWPCODE,X'FF'  16 MB: A DRUM PAGE",
        "         BE    DRUM",
        "         IC    R2,SWPCODE     GET VOLUME INDEX CODE",
    ])
    decks['DMKCPP'] = d
    return decks


def dmksys():
    """Run uniprocessor, so DMKCPI's CONCS loop never executes.

    `CONCS` connects a channel set to a processor.  It is S/370-only, it is
    hand-coded as `DC X'B2001000'` so no sweep of the opcode column sees it
    (I-49), and `DMKCPI` executes it in a loop over sixty-four channel-set
    addresses -- but only when `DMKSYSAP` says `Y`.  Which it does, because
    `OPTIONS.COPY` sets `&AP SETB 1` via `HRC035DK` and DMKSYS's
    `AIF (NOT &AP).E1` therefore assembles the `AP=YES` line.  I-50.

    Forcing the flag is the cheapest of the three available levers, and it is
    worth being explicit about why, because the three are often confused:

      * `&AP` in `OPTIONS.COPY` is assembly-wide.  `CALL`, `LOCK`, `SIGNAL`,
        `SWITCH`, `COUNT`, `CHARGE` and `PSA` all declare `GBLB &AP`, so
        changing it re-expands macros in **every** module and invalidates every
        TEXT deck built so far.  Not touched.
      * The load list is chosen at `VMFLOAD` time with no re-assembly at all --
        `CPLOAD` (173) or `APLOAD` (181, which adds DMKCPP and DMKMCT and four
        more CONCS/DISCS sites).
      * `DMKSYSAP` is `DC CL1'&AP1'` -- literally one character, 'Y' or 'N', in
        one module.  This deck replaces the conditional pair with the AP=NO
        line, so one re-assembly of DMKSYS settles it.

    Eight modules read `DMKSYSAP` at runtime -- DMKATS, DMKCDB, DMKCDM, DMKCDS,
    DMKCFG, DMKCPI, DMKCPU, DMKPGS -- so every AP-sensitive path already has a
    uniprocessor branch.  `AP=NO` is a configuration IBM supported, not a
    degradation we are inventing.

    It also matches the machine: CE's Hercules configuration is `NUMCPU 1`, so
    AP support cannot do anything useful today in any case.

    **Reverting** costs one re-assembly of DMKSYS and a nucleus rebuild: drop
    this deck from `DMKSYS AUXLCL`.  Nothing else done for the conversion has to
    be undone.  What re-enabling AP on ESA/390 *would* need is a redesign rather
    than a deck, and that is the honest caveat: channel sets do not exist in the
    channel subsystem, where every CPU can address every subchannel, so CP's
    model of moving I/O ownership between processors is obsolete rather than
    broken.  The processor half survives untouched -- `SIGP`, `SPX`, `STPX`,
    `STAP` and `SPT` are all `GENx370x390x900` -- so multiprocessing is
    reachable later; it is the I/O half that would be new work.
    """
    d = Deck(XA14)
    d.replace('00170000', '00200000', first='00170100', inc=100,
              limit=next_seq(SRC + '/DMKSYS.ASSEMBLE', '00200000'),
              lines=Deck.comment(
        "RUN UNIPROCESSOR. THE AP=YES PATH MAKES DMKCPI EXECUTE CONCS, WHICH "
        "IS S/370-ONLY AND WOULD TAKE AN OPERATION EXCEPTION AT IPL. CHANNEL "
        "SETS DO NOT EXIST IN THE CHANNEL SUBSYSTEM AT ALL -- EVERY CPU CAN "
        "ADDRESS EVERY SUBCHANNEL -- SO THE AP I/O MODEL IS OBSOLETE RATHER "
        "THAN BROKEN, AND RE-ENABLING IT IS A REDESIGN, NOT A DECK. THE "
        "PROCESSOR HALF IS UNAFFECTED: SIGP, SPX, STPX, STAP AND SPT ARE VALID "
        "IN ALL THREE ARCHITECTURES. HERCULES IS NUMCPU 1 REGARDLESS. EIGHT "
        "MODULES ALREADY BRANCH ON DMKSYSAP, SO AP=NO IS A SUPPORTED "
        "CONFIGURATION. TO REVERT: DROP THIS DECK FROM DMKSYS AUXLCL. I-50.") + [
        "         SYSCOR RMSIZE=16384K,AP=NO",
    ])
    return d


def dmkckp():
    """The first bootstrap module: checkpoint and shutdown.

    Twenty-three channel sites, all in polled loops, converted through the XAIO
    macros so the condition-code reasoning stays in one place.  Three separate
    hazard classes meet in this one module, which is why it was worth reading
    rather than pattern-matching:

      * `INTTIO` four times, in both of its roles (I-47): 00208000 reads the IPL
        device address DMKVMI left, 00274370 copies `SYSIPLDV` into the
        architected slot for no reason ESA/390 recognises, and 00772000 and
        01495500 read what the hardware stored.
      * Absolute lowcore three times (I-53): `MVC SAVEDEV(4),184` twice and
        `MVC 184(4),SAVEDEV` once -- a save and restore of the interruption
        information around DMKCKP's own I/O.  X'B8' is four bytes of
        key/flags/device address in S/370 and eight of subsystem ID plus
        interruption parameter in ESA/390, so `SAVEDEV` widens to two fullwords
        and the moves become symbolic.
      * Sixteen backward self-relative branches that span a converted
        instruction (R-26), each becoming a label **in this deck**.  The other
        twenty-six in the module are forward branches over unconverted code and
        are correct as they stand; they belong to the 64-bit pass, which has the
        list in `tools/selfrel.py`.

    Three things deliberately left alone, each worth stating because leaving
    them alone is a decision:

      * The `ST Rx,CAW` stores.  The CAW is now an ordinary word of CP's
        storage, and `XASIO` reads the CCW address straight out of it, so every
        one of those stores keeps working and the diff stays small.
      * The `CLC CSW+4(2),=AL1(CE+DE,0)` tests and `MVC SAVECSW(12),CSW`.
        `XATIO` rebuilds a CSW at the architected location from the IRB, so all
        the status logic is untouched -- which is most of the module.
      * `CCW X'08',*-8-DMKCKP+X'800',0,0` at 00460000, 00467000 and 00475000.
        These are self-relative **CCWs**, not branches, and with format-0 CCWs
        (R-27) the layout and the eight-byte length are both unchanged, so a
        TIC pointing back eight bytes still points at the previous CCW.
    """
    d = Deck(XA15)
    nxt = lambda s: next_seq(SRC + '/DMKCKP.ASSEMBLE', s)

    def one(seq, lines, inc=100, first=None):
        d.replace(seq, first=first or str(int(seq) + inc), inc=inc,
                  limit=nxt(seq), lines=lines)

    # --- 00208000: the IPL device, taken from where the IPL actually left it.
    #
    # The first attempt read SYSIPLDV, on the grounds that DMKVMI (XA0011DK)
    # and DMKCPI (00484000) both put the IPL device address there.  True --
    # and useless here, because DMKCKPT runs AT IPL, before DMKCPI has run at
    # all, so SYSIPLDV is still zero.  XAIOFIND was handed device 0000,
    # scanned all 256 subchannels, found nothing and returned cc3; the machine
    # then spun in the hundred-iteration retry loop above.  Reading XAIO's own
    # work area out of storage is what showed it: XAIODEV = 0000.  I-88.
    #
    # What the IPL does leave is the subsystem-identification word at X'B8',
    # dumped as 00010056 on the real machine -- and in S/370 the device
    # address at X'BA', dumped as 06A1.  So the bootstrap needs no lookup at
    # all: it already holds the answer XAIOFIND exists to compute.  Seeding
    # the cache rather than calling it also removes up to 256 STSCHs from the
    # IPL path.
    #
    # R0 and R1 are both free here: R0 is the only output the next statement
    # wants, and 00212000 clears R1 four statements later.
    one('00208000', Deck.comment(
        "DMKCKPT RUNS AT IPL, BEFORE DMKCPI EXISTS, SO SYSIPLDV IS STILL "
        "ZERO AT THIS POINT -- THAT READ ASKED XAIOFIND FOR DEVICE 0000 AND "
        "GOT CC3. THE IPL LEAVES THE SUBSYSTEM ID AT X'B8'. I-88.") + [
        "         L     R1,IOSSID      SSID LEFT BY THE IPL",
        "         ST    R1,XAIOSSID    SEED THE LOOKUP -- NO SCAN",
        "         STSCH XAIOSCHB       PMCW HAS THE DEVICE NUMBER",
        "         LH    R0,XAIOSCHB+6  WHICH IS WHAT SYSRES MEANS",
        "         STH   R0,XAIODEV     SO THE CACHE HITS FIRST TIME",
    ])

    # --- 00269000 and 00319000/01498000: the interruption information.
    one('00269000', Deck.comment(
        "X'B8' WAS FOUR BYTES OF KEY, FLAGS AND DEVICE ADDRESS. IT IS NOW THE "
        "SUBSYSTEM ID WORD FOLLOWED BY THE INTERRUPTION PARAMETER -- EIGHT "
        "BYTES -- SO SAVE AND RESTORE BOTH, SYMBOLICALLY. I-53.") + [
        "         MVC   IOSSID(8),SAVEDEV RESTORE INTERRUPT INFO",
    ])

    # --- L1, the IPL read: 00274370 through 00274520.
    d.replace('00274370', '00274520', first='00274371', inc=1,
              limit=nxt('00274520'), lines=Deck.comment(
        "THE COPY INTO THE ARCHITECTED INTERRUPT CODE IS GONE: THE VALUE CAME "
        "FROM SYSIPLDV ON THE LINE ABOVE AND NOTHING READS X'BA' NOW. THE "
        "WAIT LOOP KEEPS ITS SHAPE -- BC 7 MEANS \"UNTIL THE DEVICE IS CLEAR\", "
        "AND XATIO CONSUMES STATUS WITH TSCH JUST AS TIO DID, SO THE LOOP "
        "STILL TERMINATES. *-4 BECOMES A LABEL. R-26.") + [
        "         XASIO R1                  Issue the read ipl CCW",
        "         BC    4,LOADCK            CSW stored; check status",
        "         BC    7,IPLLOAD           Error on SIO, wait PSW",
        "CKPWT1   XATIO R1                  Loop for i/o completion",
        "         BC    7,CKPWT1            Keep trying",
    ])

    # --- L2: 00307000 through 00312000.  TIOSYS1 at 00306000 already labels
    #     the first test, so BNZ *-4 simply names it.
    d.replace('00307000', '00312000', first='00307100', inc=100,
              limit=nxt('00312000'), lines=Deck.comment(
        "TIOSYS1 ALREADY LABELS THE FIRST TEST, SO BNZ *-4 ONLY NEEDS ITS "
        "NAME. R-26.") + [
        "         XATIO R2             CLEAR DEVICE",
        "         BNZ   TIOSYS1",
        "         XASIO R2             START",
        "         BNZ   TIOSYS         CLEAR DEVICE AGAIN",
        "CKPWT2   XATIO R2             TEST",
        "         BC    6,CKPWT2       LOOP IF BUSY OR STATUS STORED",
    ])

    # --- 00319000: the other half of the save/restore pair.
    one('00319000', [
        "SAVESTAT MVC   SAVEDEV(8),IOSSID SAVE INTERRUPT INFORMATION",
    ])

    # --- L3: 00323000 through 00327000.
    d.replace('00323000', '00327000', first='00323100', inc=100,
              limit=nxt('00327000'), lines=[
        "CKPCL3   XATIO R2             CLEAR IT",
        "         BC    6,CKPCL3       LOOP IF BUSY OR STATUS STORED",
        "         XASIO R2             START IO (SENSE)",
        "CKPWT3   XATIO R2             TEST IO",
        "         BC    6,CKPWT3       LOOP IF BUSY OR STATUS STORED",
    ])

    # --- L4: 00331000 through 00336000.  Note 00334000 branches back to the
    #     SIO itself, not to a test.
    d.replace('00331000', '00336000', first='00331100', inc=100,
              limit=nxt('00336000'), lines=Deck.comment(
        "00334000 BRANCHED BACK ONTO THE SIO, NOT ONTO A TEST, SO ITS LABEL "
        "GOES ON THE XASIO. R-26.") + [
        "CKPCL4   XATIO R2             DRAIN ANYTHING PENDING",
        "         BC    7,CKPCL4       KEEP TRYING",
        "CKPST4   XASIO R2             READ R0",
        "         BC    7,CKPST4       TAKE ERROR PATH",
        "CKPWT4   XATIO R2             TEST FOR COMPLETION",
        "         BC    7,CKPWT4       TRY AGAIN",
    ])

    # --- L5: 00684000/00685000 and 00690000/00691000, separated by live code.
    # --- CR2 and CR3 together.  `LCTL C2,C3,X8FF` loads X'FFFFFFFF' into
    #     both from a field of FFs, to "enable all channels" before the
    #     checkpoint write.  On ESA/390 CR2 is the dispatchable-unit-control-
    #     table origin and CR3 is the PSW-key mask and secondary ASN, so it
    #     would set two registers wrong at once -- the kind of site a scan for
    #     `C2` never sees, because it names a range.  I-73.
    # The work area goes among the CONSTANTS at 00517500, and the reason is
    # the IPL, not the assembler.  Two earlier placements were wrong for two
    # different reasons and the second one only shows up on a real machine.
    #
    # Inside CLR1 was the first attempt; CE rejected it with IFO224 LENGTH
    # ERROR because 250-odd bytes took CLR1SIZE past the 256-byte limit of the
    # XC that clears it.  The length error was the lucky part -- CLR1 is
    # *zeroed at startup* and XAIOWORK holds the executable lookup subroutine,
    # so it would have been erased at runtime with no diagnostic at all.  I-55.
    #
    # After CLR1SIZE was the second, and it assembled clean, linked clean and
    # died at IPL.  DMKCKPT is one CSECT addressed by TWO base registers --
    # `USING DMKCKPT,R12,R13`, R12 = X'800' and R13 = X'1800' -- and the IPL
    # record reads only the FIRST 4096 bytes.  The second 4096 arrive later,
    # via `LDCCW  CCW 6,0+X'1800',CC+SILI,4096` at 00476000 -- a read that is
    # itself driven by XAIO.  So XAIO above offset X'1000' cannot work: the
    # code that performs the read needs a subroutine that only exists after
    # the read.  Measured in the punched deck, the bodies sat at X'16F2'
    # through X'179A' and `BAL R14,X'752'(R13)` branched to X'1752', 1,618
    # bytes past anything ever loaded -- into zeros, which decode as an
    # operation exception.  I-86.
    #
    # 00517500 is WAIT16, measured at offset X'05B0' in the deck, inside the
    # constants block that runs to the LTORG at 00537000.  Nothing falls
    # through it -- every neighbour is a DC -- and it leaves XAIOWORK entirely
    # below X'1000' with room to spare.
    # 00517600, NOT 00517500.  WAIT16 is an eight-byte PSW built from TWO
    # four-byte DCs -- X'000A0000' at 00517500 and X'00000016' at 00517600 --
    # and `./ I 00517500` inserts AFTER the first of them, landing XAIOWORK
    # between the halves.  That splits the PSW, so `MVC IPLPSW(8),WAIT16` at
    # 00234600 copied four bytes of WAIT16 and four bytes of work area into
    # the restart PSW, and it displaced everything after it -- which is how
    # the assembler noticed, complaining that `LPSW WAIT17` at 00349100 had
    # lost its doubleword alignment.  It named the neighbour, not the victim.
    # I-77 again: a sequence number is not a safe anchor until you have
    # looked at what it is in the middle of.  I-97.
    d.insert('00517600', first='00517610', inc=10,
             limit=nxt('00517600'),
             lines=Deck.comment(
        "BELOW OFFSET X'1000' ON PURPOSE: THE IPL RECORD READS ONLY THE FIRST "
        "4096 BYTES OF DMKCKPT, AND XAIO IS WHAT DRIVES THE READ THAT FETCHES "
        "THE REST. ALSO OUTSIDE CLR1 AND ALLOCBUF, WHICH ARE ZEROED AT "
        "RUNTIME. I-55, I-86.") + [
        "         DS    0D             ORB AND IRB WANT ALIGNMENT",
        "         XAIOWORK             XAIO WORK AREAS AND LOOKUP",
    ])

    d.replace('00546000', first='00546010', inc=10,
              limit=next_seq(SRC + '/DMKCKP.ASSEMBLE', '00546000'),
              lines=Deck.comment(
        "WAS LCTL C2,C3,X8FF -- ENABLE ALL CHANNELS. NEITHER REGISTER IS A "
        "CHANNEL MASK ON ESA/390; CR6 CARRIES THE I/O SUBCLASS MASK AND "
        "ALREADY HAS ALL EIGHT. I-73.") + [
        "         DS    0H             THE LCTL IS GONE",
    ])

    one('00684000', ["CKPST5   XASIO R1             SLAM IT TO THE MSC"])
    one('00685000', ["         BC    2,CKPST5       BUSY, KEEP TRYING..."])
    one('00690000', ["CKPWT5   XATIO R1             CHECK OUT STATUS"])
    one('00691000', ["         BC    2,CKPWT5       BUSY, KEEP TRYING."])

    # --- L6: the two halts.  HSCH covers HIO and HDV alike.
    one('00713000', ["         XAHIO R1             HALT IO"])
    one('00726000', ["         XAHIO R1             HALT IO"])

    # --- L6a: the two sites this deck left INSIDE the loop it converted.
    #     00726000's halt was converted and these two were not, so the drain
    #     loop would have taken an operation exception on its own next
    #     instruction.  Found by auditing the punched deck rather than the
    #     source -- tools/deckscan.py and tools/coverage.py.  I-67.
    #     Every branch around both is to a label, so no mask and no
    #     self-relative target changes: BC 2/1/4 after the TIO keep meaning
    #     busy, not operational and CSW stored, which is what XATIO restores,
    #     and TSTUC's `TM CSW+4,UC` reads the CSW XATIO rebuilds.
    one('00733000', ["NONGRAF  XATIO R1             CLEAR OUTSTANDING STATUS"])
    one('00742000', ["SNSIO    XASIO R1             START I/O SENSE OPERATION"])

    # --- L7: 00772000 through 00774000.
    d.replace('00772000', '00774000', first='00772100', inc=100,
              limit=nxt('00774000'), lines=Deck.comment(
        "THE INTERRUPTING DEVICE ADDRESS COMES FROM THE INTERRUPTION "
        "PARAMETER NOW, WHICH DMKCPI SET WITH MSCH. I-47, XA0013DK.") + [
        "         LH    R3,IOINTPRM+2  GET THE INTERRUPTING DEV ADDR",
        "CKPST7   XASIO R3             ISSUE SENSE TO IT",
        "         BC    2,CKPST7       BETTER NOT BE BUSY",
    ])

    # --- 01488000: a lone start with no adjacent self-relative branch.
    one('01488000', ["         XASIO R2             START IO"])

    # --- 01495500 and 01498000.
    one('01495500', [
        "         CH    R2,IOINTPRM+2       RIGHT DEVICE ?",
    ], inc=10)
    one('01498000', [
        "         MVC   SAVEDEV(8),IOSSID SAVE INTERRUPT INFORMATION",
    ])

    # --- L9: 01503000 through 01507000.
    d.replace('01503000', '01507000', first='01503100', inc=100,
              limit=nxt('01507000'), lines=[
        "CKPCL9   XATIO R2                  CLEAR IT",
        "         BC    6,CKPCL9            LOOP IF BUSY OR STATUS",
        "         XASIO R2                  START IO",
        "CKPWT9   XATIO R2                  TEST IO",
        "         BC    6,CKPWT9            LOOP IF BUSY OR STATUS",
    ])

    # --- L10: 01511000 through 01516000.
    d.replace('01511000', '01516000', first='01511100', inc=100,
              limit=nxt('01516000'), lines=[
        "CKPCLA   XATIO R2             DRAIN ANYTHING PENDING",
        "         BC    7,CKPCLA       KEEP TRYING",
        "CKPSTA   XASIO R2             READ R0",
        "         BC    7,CKPSTA       TAKE ERROR PATH",
        "CKPWTA   XATIO R2             TEST FOR COMPLETION",
        "         BC    7,CKPWTA       TRY AGAIN",
    ])

    # --- SAVEDEV widens, and the work area goes next to it so that whatever
    #     base register already reaches SAVEDEV reaches XAIOWORK too.
    one('01647000', Deck.comment(
        "EIGHT BYTES NOW: SUBSYSTEM ID AND INTERRUPTION PARAMETER. THIS SITS "
        "INSIDE CLR1, WHICH 00541000 ZEROES WITH XC CLR1(CLR1SIZE), SO THE "
        "REGION GROWS BY FOUR BYTES -- FROM ABOUT 136 TO 140, WELL INSIDE THE "
        "XC LENGTH LIMIT OF 256.") + [
        "SAVEDEV  DS    2F             ERROR DEVICE: SSID AND PARM",
    ])

    # XAIO's subroutines take the CCW format from ORBCCWFM in XABLOKS, so the
    # module needs that COPY.  It goes here, with DMKCKP's own COPY list just
    # before END, and nowhere else: XABLOKS ends in DSECTs, so anything placed
    # after it lands in the last DSECT instead of the CSECT.
    d.insert('01723000', first='01723100', inc=100, limit='01724000',
             lines=["         COPY  XABLOKS"])
    return d


def dmkdmp():
    """The abend dump writer: the last module the PSA rename broke.

    Twenty-two channel sites, seventeen backward self-relative branches and three
    `INTTIO` sites.  Structurally the same as DMKCKP, with two differences worth
    noting.

    **Five of the seventeen branches are free.**  `TIOIPL`, `DRAINEND`,
    `DOMONSIO`, `DOTIO` and `GOTIO` already label the instruction their `*-4`
    targets, so the branch only needs the name it could have used all along.

    **Placement is easy here.**  DMKDMP's only clears are `XC SENSDATA(24)` --
    a named field -- and an `MVCL` over real pages 1 to 3, which is storage
    rather than the module.  So `XAIOWORK` goes at the end of the data, after the
    closing `ORG`, with none of the `CLR1` trouble DMKCKP gave (I-55).

    The lookup's `STSCH` scan rather than `RDEVSSID` earns its keep in exactly
    this module: DMKDMP runs *after an abend*, when CP's control blocks are the
    one thing that cannot be trusted, and a dump that needs a healthy RDEVBLOK
    to write itself is no use on the occasion you need it.
    """
    d = Deck(XA16)
    nxt = lambda s: next_seq(SRC + '/DMKDMP.ASSEMBLE', s)

    def one(seq, lines, inc=100):
        d.replace(seq, first=str(int(seq) + inc), inc=inc,
                  limit=nxt(seq), lines=lines)

    def blk(frm, to, lines, first=None, inc=100):
        d.replace(frm, to, first=first or str(int(frm) + inc), inc=inc,
                  limit=nxt(to), lines=lines)

    d.replace('00295000', first='00295010', inc=10,
              limit=next_seq(SRC + '/DMKDMP.ASSEMBLE', '00295000'),
              lines=Deck.comment("WAS LCTL C2,C2,ALLONES -- RE-ENABLE CHANNEL 0. THERE IS NO CHANNEL MASK ON ESA/390; CR6 CARRIES THE I/O SUBCLASS MASK AND IS ALREADY ALL EIGHT SUBCLASSES. I-73.") + [
        "         DS    0H             THE LCTL IS GONE. I-73.",
    ])

    # --- I-109.  Four ISK sites, and they are in the abend handler, which is
    #     why they are on the critical path at all.  DMKDMP is the instrument:
    #     on 30 September CP reported PRG018 and then died taking the dump,
    #     `DMKDMP905W SYSTEM DUMP FAILURE; PROGRAM CHECK`, at 52084 where
    #     `0934` sits -- ISK R3,R4, one of the twelve instructions 370-XA
    #     withdrew.  So the cause of PRG018 is unknowable until these are gone.
    #
    #     ISKE is a drop-in for all four, and that is checked rather than
    #     assumed.  SA22-7201-08: ISKE inserts "the seven-bit storage key in
    #     bit positions 24-30 of general register R1, and bit 31 is set to
    #     zero.  The contents of bit positions 0-23 of the register remain
    #     unchanged" -- the same result format ISK produces, so every
    #     following `STC` is unaffected.  (Not to be confused with IVSK on the
    #     facing page, which returns only ACC and F in bits 24-28.)  The
    #     operand differs only in granularity: in 24-bit mode ISKE takes
    #     "bits 8-19 of general register R2" and ignores bits 20-31, where ISK
    #     reads a 2 KB block, so an address anywhere in a page answers for the
    #     page.
    #
    #     Every one of these four loops walks storage in 2 KB steps and stores
    #     one key byte per step.  Under ISKE both halves of a page return that
    #     page's key, so each pair of slots holds the same value -- which is
    #     the truth under 4 KB keys, and CE already runs with them on
    #     (`CPCREG0 DC X'81800CC0'`).  Redundant, not wrong: exactly I-104's
    #     finding about DMKCPI's SSK.  So the steps, the loop counts and the
    #     SAVKEY layout are all left alone, and each site is ONE card.
    #     Widening the steps would change the dump's own key table, which is a
    #     format change masquerading as an architecture fix.
    #
    #     Knowing deviation: Hercules marks ISKE GENx370x390x900 and so accepts
    #     it in S/370 mode, but a real S/370 would not -- ISKE arrived with
    #     370-XA.  These cards are therefore unconditional, with no architecture
    #     probe, and the converted nucleus is an ESA/390 artifact that happens
    #     to also run under Hercules's S/370.  That is the standing
    #     Hercules-is-permissive risk pointing the other way for once.

    one('00412000', Deck.comment(
        "WAS ISK -- THE KEYS OF REAL PAGES 0-3, READ 2 KB AT A TIME INTO "
        "SAVKEY(8). UNDER 4 KB KEYS EACH PAIR NOW REPEATS, WHICH IS WHAT THE "
        "HARDWARE MEANS. I-109.") + [
        "NXTKEY   ISKE  R9,R3          GET KEYS OF INITIAL 4 PAGES",
    ])

    one('00500000', ["         ISKE  R0,R3          GET STORAGE KEY -- I-109"])

    one('00505000', ["         ISKE  R0,R3          GET STORAGE KEY -- I-109"])

    one('00710300', ["         XASIO R15            START IO"])

    one('00722000', Deck.comment(
        "THE INTERRUPTING DEVICE ADDRESS IS IN THE INTERRUPTION PARAMETER NOW, "
        "PUT THERE BY DMKCPI'S MSCH. I-47.") + [
        "         CH    R15,IOINTPRM+2 INTERRUPT FOR DUMP DISK ?",
    ])

    blk('00731000', '00735000', Deck.comment(
        "R-26: BOTH *-4 BRANCHES SPANNED A TIO AND NOW NAME IT.") + [
        "DMPCL1   XATIO R15            TEST IO",
        "         BC    6,DMPCL1       CLEAR DEVICE",
        "         XASIO R15            START IO (SENSE)",
        "DMPWT1   XATIO R15            WAIT FOR IT",
        "         BC    6,DMPWT1       BRANCH IF BUSY OR STATUS",
    ])

    blk('00738030', '00738080', [
        "DMPCL2   XATIO R15            DRAIN ANY INTERRUPTS",
        "         BC    7,DMPCL2       LOOP UNTIL READY",
        "DMPST2   XASIO R15            READ R0 FOR ALT TRACK ADDR",
        "         BC    7,DMPST2       LOOP UNTIL STARTED",
        "DMPWT2   XATIO R15            TEST FOR COMPLETION",
        "         BC    7,DMPWT2       TRY AGAIN",
    ], first='00738031', inc=1)

    # --- Two sites this deck left inside loops it converted, found by
    #     auditing the punched deck.  I-67.  00769000 is the SIO whose own
    #     cc0 target TIOIPL was converted at 00775000, so the IPL re-read
    #     started with an S/370 instruction and finished with an ESA/390 one.
    one('00769000', ["SIOIPL   XASIO R15            RE-READ THE IPL RECORD"])

    # TIOIPL already labels the target, so the branch just names it.  00776500
    # and 00776600 sit between these two, so they are separate edits.
    one('00775000', ["TIOIPL   XATIO R15            TEST"])
    one('00776000', ["         BNZ   TIOIPL         WAIT"])
    one('00777000', Deck.comment(
        "SYSIPLDV IS CP'S OWN FIELD FOR THE IPL DEVICE ADDRESS, SET BY DMKCPI "
        "AND READ IN SIX PLACES. X'BA' NEVER MEANT IT. I-47.") + [
        "         STH   R15,SYSIPLDV   SAVE IPL DEVICE ADDRESS",
    ])

    blk('00779000', '00782000', [
        "DMPST3   XASIO R15            START",
        "         BNZ   DMPST3         WAIT",
        "DMPWT3   XATIO R15            TEST",
        "         BNZ   DMPWT3         WAIT",
    ])

    blk('00804000', '00807000', [
        "DMPST4   XASIO R15            START",
        "         BNZ   DMPST4         WAIT",
        "DMPWT4   XATIO R15            TEST",
        "         BNZ   DMPWT4         WAIT",
    ])

    blk('00976000', '00977000', [
        "DRAINEND XATIO R15            DRAIN LAST INTERRUPT",
        "         BNZ   DRAINEND       WAIT",
    ])

    blk('01005000', '01006000', [
        "DMPCL5   XATIO R1             CLEAR PENDING INTS",
        "         BC    2,DMPCL5       STILL BUSY, KEEP TRYING",
    ])

    blk('01012000', '01013000', [
        "DOMONSIO XASIO R1             START THE DEVICE",
        "         BC    2,DOMONSIO     BUSY, KEEP TRYING",
    ])

    blk('01016000', '01017000', [
        "DOTIO    XATIO R1             CLEAR THE STATUS",
        "         BC    2,DOTIO        BUSY, KEEP TRYING",
    ])

    # The dump PRINTER's key, shown once per 2 KB boundary.  Under 4 KB keys
    # the two lines of a page now show the same key, which is true.  The
    # `N R2,=F'2047'` boundary test above is deliberately left alone: making it
    # 4095 would halve the number of key lines in the printed dump, and that is
    # a change to the dump's format, not to its correctness.  I-109.
    one('01054000', ["         ISKE  R3,R4          GET STORAGE KEY -- I-109"])

    # 01130000's BC 8+4+2,*+8 is a FORWARD branch over the following BAL, and
    # neither it nor the BAL changes length, so it is correct as it stands.
    one('01129000', ["         XATIO R15            IS THE PATH FREE ?"])

    blk('01144000', '01145000', [
        "DMPCL6   XATIO R15            DRAIN INTERRUPT",
        "         BC    2,DMPCL6       LOOP ON BUSY",
    ])

    one('01151000', [
        "WAITRET  CH    R15,IOINTPRM+2 INTERRUPT FROM RIGHT DEVICE ?",
    ])

    blk('01157000', '01158000', [
        "DMPWT7   XATIO R15            TEST",
        "         BC    2,DMPWT7       CC=2; CHANNEL STILL BUSY",
    ])

    # PRSIO sat between DMPWT7 and GOTIO, both converted.  Its own following
    # branch is `BC 8+4+2,*+8`, which is FORWARD over a BAL and so still skips
    # the same eight bytes after conversion -- left alone deliberately.  I-67.
    one('01161000', ["PRSIO    XASIO R15            START"])

    blk('01169000', '01170000', [
        "GOTIO    XATIO R15            ISSUE TIO TO 'DUMP' DEVICE",
        "         BC    2,GOTIO        CC=2, CHANNEL STILL BUSY",
    ])

    # After the closing ORG and before END.  DMKDMP clears only SENSDATA and
    # real pages 1-3, so unlike DMKCKP there is no cleared region to avoid.
    d.insert('01556000', first='01556100', inc=100, limit=nxt('01556000'),
             lines=Deck.comment(
        "AFTER THE CLOSING ORG. DMKDMP'S ONLY CLEARS ARE XC SENSDATA(24) AND "
        "AN MVCL OVER REAL PAGES 1 TO 3, SO NOTHING ZEROES THIS. I-55.") + [
        "         XAIOWORK             XAIO WORK AREAS AND LOOKUP",
        "         COPY  XABLOKS        FOR ORBCCWFM, THE CCW FORMAT",
    ])
    return d


def dmksav():
    """The saved-system reader and writer: the simplest of the four.

    **Only six of its eleven channel sites are converted, and that is the whole
    point of the module.**  DMKSAV has two entry points that run in different
    architectures:

        00129000  DMKSAV   CSECT      IPL entry -- reads the saved nucleus
        00205000  DMKSAVRS BALR R3,0  restore path
        00380000  DMKSAVNC DS   0H    the LDT target -- WRITES it at build time

    `CPLOAD.EXEC`'s last card is `LDT DMKSAVNC`, so `DMKSAVNC` is entered by the
    standalone loader deck while the nucleus is being built -- on the build
    machine, in S/370 mode.  Its five sites (00426000, 00429000, 00601000,
    00613100, 00613300) must therefore stay `SIO` and `TIO`, and `00430000`'s
    `BC 7,*-4` stays with them because the instruction it spans is unchanged.

    The six sites at 00149100 to 00166090 are on the IPL and restore side, which
    runs on the **target** machine in ESA/390 mode, and those are converted.  A
    module holding both is not a contradiction: the two paths are never executed
    in the same IPL.  I-59.

    No `INTTIO`, no absolute lowcore, and **no `XC` or `MVCL` anywhere in the
    module** -- so unlike `DMKCKP` there is no cleared region for `XAIOWORK` to
    avoid (I-55).  It has
    `USING PSA,R0` and `COPY EQU`, so `CAW`, `CSW` and the register equates all
    resolve and no `XAIOWORK` parameters are needed.

    Four sites were invisible to a first scan because the label in columns 1-8 is
    the mnemonic itself -- `SIO SIO 0(R10)`, `QDISK`, `SNSRTSIO`, `SNSRTTIO`.  A
    scan keyed on the operation field finds them; one keyed on leading whitespace
    does not.  Three of those four turn out to be DMKSAVNC's and are left alone;
    the `SIO` label survives conversion unchanged, and `BC 7,*-4` becomes
    `BC 7,SIO`, which reads oddly and is correct.

    The one thing to watch is size.  `USING DMKSAV,R3` is a **single** base
    register, so the module has 4 KB of addressability rather than the 8 KB that
    `DMKDMP` had when it overflowed (I-56).  Eleven sites at fourteen bytes plus
    the work area is about 550 bytes of growth; the module is small, so it should
    fit, but this is the module where a compact call site matters most.
    """
    d = Deck(XA17)
    nxt = lambda s: next_seq(SRC + '/DMKSAV.ASSEMBLE', s)

    def blk(frm, to, lines, first=None, inc=100):
        d.replace(frm, to, first=first or str(int(frm) + inc), inc=inc,
                  limit=nxt(to), lines=lines)

    def one(seq, lines, inc=100):
        blk(seq, None, lines, inc=inc)

    # --- 00145000: clear the cached architecture BEFORE any I/O.
    #
    # DMKSAV is the one module whose RUNTIME STATE ends up in the nucleus it
    # writes.  The build runs it on a real S/370, so XAIOPROB caches X'01' in
    # XAIOMODE -- and then DMKSAVNC writes the nucleus to disk INCLUDING its
    # own data area, baking that answer in.  The ESA/390 IPL then trusts it
    # and issues SIO.  The trace showed exactly that:
    #
    #     CLI XAIOMODE,X'00'   -> already non-zero, probe skipped
    #     CLI XAIOMODE,X'01'   -> says S/370
    #     SIO 0(1)             -> on an ESA/390 machine
    #
    # One MVI fixes it: reset the cache at entry so the probe always runs
    # fresh.  It goes AFTER 00145000 rather than before, because STCAW is a
    # branch target -- `BC 15,8(0,3)` reaches it from DMKSAVRS -- and anything
    # placed ahead of the label is simply skipped on that path.  I-100.
    d.insert('00145000', first='00145100', inc=100, limit=nxt('00145000'),
             lines=Deck.comment(
        "DMKSAVNC WRITES THIS MODULE'S OWN STORAGE INTO THE NUCLEUS, SO A "
        "CACHED PROBE RESULT WOULD PERSIST FROM THE S/370 BUILD INTO THE "
        "ESA/390 IPL. CLEAR IT AND LET XAIOPROB ASK AGAIN. I-100.") + [
        "         MVI   XAIOMODE,X'00' RE-PROBE, DO NOT INHERIT",
    ])

    # --- 00149100 and 00150000.  The label is literally SIO.
    d.replace('00149100', '00150000', first='00149200', inc=100,
              limit=nxt('00150000'), lines=Deck.comment(
        "THE LABEL HERE IS SIO, WHICH IS ALSO A MNEMONIC -- THAT HAS ALWAYS "
        "BEEN TRUE IN THIS MODULE AND STILL ASSEMBLES. R-26: *-4 NAMES IT.") + [
        "SIO      XASIO R10",
        "         BC    7,SIO",
    ])

    # --- 00151000 to 00156000: the first of the two enabled waits.
    #
    # An enabled wait for an I/O interrupt is the ONE place DMKSAV does not
    # poll, and three separate things break it under ESA/390, not one:
    #
    #   * XWAIT is a BC-mode PSW (see the constants below -- but that is only
    #     the first of the three).
    #   * Interrupt delivery is gated by CR6, the I/O-interruption subclass
    #     mask.  DMKSAV instead builds a channel mask from the device address
    #     and sets CR2 (00418300-00418600, @VA11715) -- the S/370 EC-mode
    #     channel-mask register, which in ESA/390 is not that register at all.
    #     The tC trace shows CR6 = 00000000, so the interrupt would never
    #     arrive and a corrected XWAIT would have waited for ever.
    #   * `CH 10,IOOPSW+2` tests the device address the BC-mode hardware
    #     leaves in the I/O old PSW's interruption-code field at X'3A'.  EC
    #     mode puts it at X'BA' and ESA/390 does not supply one at all -- an
    #     I/O interruption gives a subsystem ID at X'B8' and an IRB via TSCH.
    #
    # So the interrupt-driven shape needs four coupled changes to work.
    # Polling needs none: XATIO already handles both architectures, and its
    # shim rebuilds a CSW at the architected location from the IRB, so the
    # `CLC CSW+4(2)` that follows each wait keeps working untouched.  It is
    # also what the rest of DMKSAV already does -- the wait is the odd one
    # out, not the pattern.
    #
    # XATIO's condition codes are S/370 TIO's: cc0 available, cc1 CSW stored,
    # cc2 busy, cc3 not operational.  Status arrives as cc1, so loop on
    # everything else -- mask 8+2+1 = 11.  I-102.
    d.replace('00151000', '00156000', first='00151100', inc=100,
              limit=nxt('00156000'), lines=Deck.comment(
        "AN ENABLED WAIT FOR AN I/O INTERRUPT NEEDS A CR6 SUBCLASS MASK AND A "
        "DEVICE ADDRESS IN THE I/O OLD PSW, AND ESA/390 HAS NEITHER. POLL, "
        "WHICH IS WHAT THE REST OF THIS MODULE DOES. I-102.") + [
        "WAITX    DS    0H",
        "         XATIO R10            POLL FOR COMPLETION",
        "         BC    11,WAITX       ANY CC BUT 1: NO STATUS YET",
        "IOINT    DS    0H             CC1: THE CSW IS BUILT",
    ])

    # --- 00163000 to 00166000.
    d.replace('00163000', '00166000', first='00163100', inc=100,
              limit=nxt('00166000'), lines=[
        "SAVST1   XASIO R10            START SENSE IO",
        "         BNZ   SAVST1         ..",
        "SAVCL1   XATIO R10            CLEAR IO",
        "         BNZ   SAVCL1         ..",
    ])

    # --- 00166050 to 00166100.  The gap to 00166110 is ten, so number by one.
    d.replace('00166050', '00166100', first='00166051', inc=1,
              limit=nxt('00166100'), lines=[
        "SAVCL2   XATIO R10            DRAIN ANY INTERRUPTS",
        "         BC    7,SAVCL2",
        "SAVST2   XASIO R10            START IT UP",
        "         BC    7,SAVST2       UNTIL FREE",
        "SAVWT2   XATIO R10            TEST FOR COMPLETION",
        "         BC    7,SAVWT2       TRY AGAIN",
    ])

    # --- 00236000 to 00334000, then 00630000: the PSWs.
    #
    # DMKSAV states the problem in its own source.  Its IPL data is
    #
    #     IPLDATA  DC  X'000C000000000800'  EXTENDED PSW FOR IPL
    #
    # -- bit 12 on, EC mode, and IBM's comment says so.  That is the PSW
    # DMKSAV WRITES, and it is why CP runs in EC mode at all (I-82).  Every
    # PSW DMKSAV *itself* loads is BC mode:
    #
    #     XWAIT    X'7E06'      enabled wait for an I/O interrupt
    #     IONP     X'00040000'  I/O new
    #     MCNP     X'00020000'  machine check new
    #     WSC10    X'01060000'  wait code 010
    #     WSC11    X'00020000'  wait code 011
    #     DISAWT0  X'00020000'  wait code 012
    #     EXTINT   X'00040000'  external new, restarts at DMKSAVNC
    #     LBIOPN   X'00040000'  I/O new for the second wait
    #
    # The module builds an EC-mode system with BC-mode code.  On a S/370 that
    # is legal; in ESA/390 bit 12 must be 1 and LPSW raises a SPECIFICATION
    # EXCEPTION without it -- reported with ILC 0, because the exception is
    # recognised while loading the PSW rather than while decoding.  That is
    # the 0006/ILC=0 the tC trace caught at 00071032.
    #
    # DISAWT0 is the one to notice.  Wait code 012 is `NUCLEUS LOAD ON
    # 'LABEL'` -- SUCCESS, and the gate every run in this project tests for.
    # Left alone, a fully working conversion would have program-checked at
    # the finishing line and read as the I/O still being broken.
    #
    # Seven of the eight are one nibble: OR in X'08'.  XWAIT is not, because
    # X'7E' sets PSW bits 2-4, which are the BC-mode channel masks 2-4 and
    # MUST BE ZERO in EC mode -- so bit 12 alone would trade one
    # specification exception for another.  DMKCKP, converted by IBM at
    # @V407429, already has the right constant for exactly this job:
    #
    #     IWAIT    DC  X'020E0000'      ENABLE
    #
    # byte 0 = X'02', the EC-mode I/O mask.  Use it.  I-102.
    for seq, old, new, what in (
            ('00236000', "X'7E06'",     "X'020E'",     'XWAIT'),
            ('00239000', "X'00040000'", "X'000C0000'", 'IONP'),
            ('00241000', "X'00020000'", "X'000A0000'", 'MCNP'),
            ('00328000', "X'01060000'", "X'010E0000'", 'WSC10'),
            ('00330000', "X'00020000'", "X'000A0000'", 'WSC11'),
            ('00332000', "X'00020000'", "X'000A0000'", 'DISAWT0'),
            ('00334000', "X'00040000'", "X'000C0000'", 'EXTINT'),
    ):
        # The label sits in columns 1-8 for the named ones and is blank for
        # LBIOPN's and for the second word of a pair, so reproduce the card
        # rather than patching it: an UPDATE replacement is a whole card.
        lbl = '' if what == 'LBIOPN' else what
        # '%08d', not str(): a sequence number is an EIGHT-COLUMN field and
        # str(int('00236000') + 10) is '236010', which UPDATE would place at
        # columns 73-78 and compare as a different, out-of-order key.
        d.replace(seq, first='%08d' % (int(seq) + 10), inc=10, limit=nxt(seq),
                  lines=["%-8s DC    %-14s EC MODE. I-102." % (lbl, new)])

    # --- 00603000 to 00605000: the second enabled wait, same reasoning.
    #
    # R15 is live across this one -- `BR R15` at 00609000 returns on it -- and
    # XATIO's STM/LM pair saves R14 through R1 without disturbing the
    # condition code, so that return survives the poll.  I-102.
    d.replace('00603000', '00605000', first='00603100', inc=100,
              limit=nxt('00605000'), lines=Deck.comment(
        "AS AT WAITX ABOVE. I-102.") + [
        "WAITL    DS    0H",
        "         XATIO R10            POLL FOR COMPLETION",
        "         BC    11,WAITL       ANY CC BUT 1: NO STATUS YET",
        "LBIOINT  DS    0H             CC1: THE CSW IS BUILT",
    ])

    # --- 00630000: LBIOPN, the I/O new PSW for the wait just removed.  Dead
    #     now, and converted anyway: it is still MVC'd into IONPSW at 00599000
    #     and would be a live trap the moment anything enabled I/O.  I-102.
    d.replace('00630000', first='00630010', inc=10, limit=nxt('00630000'),
              lines=["         DC    X'000C0000'    EC MODE. I-102."])

    # --- The work area, immediately before END.  XABLOKS must come after
    #     XAIOWORK and last of all, because it ends in DSECTs.
    # --- Anchored at 00684000, which is `COPY EQU`, and NOT at 00685000,
    #     which is the `PSA` macro call.  `./ I 00685000` inserts AFTER that
    #     record, so XAIOWORK expanded inside `PSA DSECT` -- where DS and DC
    #     generate no storage and the subroutines generate no object code at
    #     all.  The module still assembled clean, because every symbol was
    #     defined: XAIOSIO and friends simply became OFFSETS INTO THE PSA.
    #     With `USING PSA,R0` in force, `BAL R14,XAIOSIO` then branched to
    #     absolute low storage, and the first IPL of the converted nucleus
    #     took an operation exception at X'000208' -- inside TEMPSAVE, on a
    #     stored TOD clock value.  I-77.
    d.insert('00684000', first='00684100', inc=100, limit=nxt('00684000'),
             lines=Deck.comment(
        "NO XC OR MVCL EXISTS ANYWHERE IN DMKSAV, SO NOTHING ZEROES THIS AND "
        "THE PLACEMENT NEEDED NONE OF DMKCKP'S CARE. XABLOKS LAST: IT ENDS IN "
        "DSECTS. I-55.") + [
        "         XAIOWORK             XAIO WORK AREAS AND LOOKUP",
        "         COPY  XABLOKS        FOR ORBCCWFM, THE CCW FORMAT",
    ])
    return d


def dmkvsj():
    """The guest's CLEAR CHANNEL, which stops being passed through to hardware.

    `DMKVSJ` simulates the guest's `HIO` and `CLCH`.  When the virtual channel is
    **dedicated** -- `VCHSTAT` has `VCHDED`, set only by `DMKVCH`'s
    `ATTACH CHANNEL` at seq 00570000 -- CP hands the guest's `CLCH` straight to
    the hardware as a real `CLRCH`, hand-assembled because Assembler XF has no
    such mnemonic:

        00169000  BNO   CLCHEXIT       NO, TREAT CLCH AS A TCH
        00170000  SWITCH               MAKE SURE WE ARE ON I/O PROC
        00171000  LH    R1,VCHADD      GET CHANNEL ADDR - REAL=VIRTUAL
        00172000* CLRCH 0(R1)          ISSUE REAL CLRCH INSTRUCTION
        00173000  DC    X'9F01'        ISSUE REAL CLRCH INSTRUCTION
        00174000  DC    S(0(1))        FOR SPECIFIED CHANNEL

    This is the last live DC-encoded channel instruction in the nucleus, the
    other being `DMKCPI`'s `CONCS`, which `AP=NO` already makes dead (`I-50`).
    It is also the one site in the whole conversion where the right answer is to
    **delete the function rather than convert it**, and it took three findings
    to be sure of that.

    **`RCHP` is not the successor of `CLRCH`.**  X'B23B' is `GENx___x390x900`, so
    it exists exactly where `CLRCH` does not, which makes it look like the
    substitution.  It is not: it resets a *channel path*, which in ESA/390 is a
    shared resource the channel subsystem owns, not a channel a guest can be
    given.  VM/XA dropped dedicated channels for this reason.

    **The obvious conversion program-checks.**  `RCHP` takes its CHPID in R1
    bits 24-31 and takes an operand exception if bits 0-23 are non-zero
    (`io.c`: `if(regs->GR_L(1) & 0xFFFFFF00) program_interrupt(OPERAND)`).
    `VCHADD` is a channel address in device-number form -- X'0300' for channel
    3 -- so `LH R1,VCHADD` followed by `RCHP` is an operand exception every
    time.  A shift would silence that, and Hercules even assigns
    `chpid = devnum >> 8` (`config.c:724`), so it would appear to work.

    **And appearing to work is the trap.**  `chp_reset` calls `device_reset` on
    every device on the path, and `device_reset` is the one thing that clears
    `PMCW5_E` and the interruption parameter (`docs/24-INTTIO.md`).  CP sets both
    exactly once, at IPL, in `XA0013DK`, and has no code anywhere that re-enables
    a subchannel -- so a single guest `CLCH` would permanently disable every
    device on that channel, and SSCH would return cc3 for the rest of the IPL
    with no diagnostic.  `chp_reset` then queues a channel report
    (`build_chp_reset_chrpt`), and CP has no channel-report machinery at all.

    So the pass-through goes.  `CLCH` is now always simulated as a `TCH`, which
    is what this module already did for every channel that was not dedicated --
    the `BNO CLCHEXIT` one instruction earlier.  `DMKVSICH` documents its entry
    contract as "ALL OTHER REGISTERS CONTAIN THE SAME VALUES THAT THEY HAD IN
    DMKVSJ", and nothing between 00165000 and 00169000 alters a register, so
    taking that branch unconditionally is state-identical to taking it on the
    `BNO`.  `I-62`.

    The whole block 00168000-00195000 is replaced rather than left dead, so no
    `CLRCH` remains in the nucleus for a later reader to find.  Three things make
    that safe: `CCTRACE` at 00177000 is referenced from nowhere in CP -- it is
    already a dead label -- `CLRCHNOT` is referenced only from inside the block,
    and the `AIF`/`ANOP` pair at 00175000/00188000 is entirely within the range,
    so the conditional assembly is removed as a unit.  `&TRACE(9) SETB 1` in
    `OPTIONS.COPY`, so it was live code, not skipped text.

    `DMKVSJCC` at 00162000 keeps counting virtual `CLCH`s, so nothing a monitor
    or `Q STAT` reads changes.  The module has no renamed PSA symbol and no
    column-scan channel instruction, so this deck is the whole of its work.
    """
    d = Deck(XA18)
    nxt = lambda s: next_seq(SRC + '/DMKVSJ.ASSEMBLE', s)

    d.replace('00168000', '00195000', first='00168100', inc=100,
              limit=nxt('00195000'), lines=Deck.comment(
        "THE DEDICATED-CHANNEL PASS-THROUGH IS GONE. IT ISSUED A REAL CLRCH, "
        "DC X'9F01', FOR A GUEST WHOSE CHANNEL WAS ATTACHED WHOLE. ESA/390 HAS "
        "NO CHANNEL TO CLEAR: RCHP B23B RESETS A CHANNEL PATH, WHICH THE "
        "CHANNEL SUBSYSTEM OWNS AND SHARES, AND IS A DIFFERENT OPERATION.") +
        Deck.comment(
        "CONVERTING IT WOULD BE WORSE THAN LEAVING IT. RCHP TAKES A CHPID IN "
        "R1 BITS 24-31 AND PROGRAM-CHECKS ON BITS 0-23, AND VCHADD IS X'0300' "
        "FOR CHANNEL 3. WORSE, CHP_RESET CALLS DEVICE_RESET ON EVERY DEVICE ON "
        "THE PATH, WHICH CLEARS PMCW5E AND THE INTERRUPTION PARAMETER -- SET "
        "ONCE AT IPL BY XA0013DK AND NEVER AGAIN. ONE GUEST CLCH WOULD DISABLE "
        "THE WHOLE CHANNEL FOR GOOD.") +
        Deck.comment(
        "SO CLCH IS ALWAYS A TCH NOW, AS IT ALREADY WAS FOR EVERY CHANNEL THAT "
        "WAS NOT DEDICATED. DMKVSICH WANTS THE REGISTERS DMKVSJ HELD AND "
        "NOTHING SINCE 00165000 TOUCHED ONE, SO THE BRANCH IS UNCONDITIONAL "
        "AND STATE-IDENTICAL. DMKVSJCC STILL COUNTS. I-62.") + [
        "         B     CLCHEXIT       SIMULATE CLCH AS A TCH",
    ])

    # --- 00324000.  The module's OTHER S/370 instruction, missed the first
    #     time round because the scan that cleared the module was an ad-hoc
    #     one-liner with a bug in it.  I-67.
    #
    #     This one is a real conversion, not a deletion: `HDV` halts a device,
    #     `HSCH` halts a subchannel, and a subchannel is exactly one device.
    #     Unlike `DMKIOS`'s `IOSXHIO`, a bare pass-through will not do here,
    #     because the cc1 path at `HIOSTCSW` does `CLC CSW+4(2),ZEROES` and
    #     `LH R5,CSW+4` -- it reads the architected CSW and hands the status to
    #     the guest.  `HSCH` cc1 means status *pending*, not stored, so a bare
    #     `HSCH` would give the guest whatever was in the CSW beforehand.
    #
    #     Two registers make this cheap.  R3 still points at the RDEVBLOK from
    #     00308000 (nothing between reassigns it), so `RDEVSSID` is in hand and
    #     no subchannel scan is needed; and R10 is the active IOBLOK, verified
    #     non-zero and equal to `VDEVIOB` at 00312000, so the IRB has somewhere
    #     per-IOBLOK to live and the module stays REENTRANT, which its own
    #     header at seq 00015000 requires.  R1, R14 and R15 are all dead here:
    #     R1 was the mask stored to `VMIOACTV` at 00319000, and R14/R15 were
    #     the `BAL` linkage to `SCANALL`.  R5 must survive and does.
    #     Numbered by ten: the next surviving record is 00325000, which
    #     leaves nine slots at the usual increment and this needs sixteen.
    d.replace('00324000', first='00324010', inc=10,
              limit=nxt('00324000'), lines=Deck.comment(
        "HSCH FOR HDV. THE CC0/CC2/CC3 PATHS FALL THROUGH WITH THE "
        "CONDITION CODE INTACT, SINCE BC DOES NOT DISTURB IT. ONLY CC1 "
        "NEEDS WORK: HSCH LEAVES STATUS PENDING WHERE HDV STORED A CSW, "
        "AND HIOSTCSW READS CSW+4. I-67.") + [
        "         L     R1,RDEVSSID-RDEVBLOK(R3)  SUBSYSTEM ID",
        "         HSCH  0              HALT THE SUBCHANNEL",
        "         BC    4,VSJHDV1      CC1: GO MAKE THE CSW REAL",
        "         B     VSJHDV2        CC0, CC2, CC3 STAND AS THEY ARE",
        "VSJHDV1  L     R1,RDEVSSID-RDEVBLOK(R3)  AGAIN, TSCH WANTS IT",
        "         TSCH  IOBIRB-IOBLOK(R10)  CLEAR THE PENDING STATUS",
        "         MVI   CSW,X'00'      REBUILD THE CSW HDV LEFT",
        "         MVC   CSW+1(3),IOBICCW+1-IOBLOK(R10)",
        "         MVC   CSW+4(4),IOBIDST-IOBLOK(R10)",
        "         LA    R1,1           AND GIVE BACK CC1. LA THEN LCR:",
        "         LCR   R1,R1          LTR ON 1 WOULD SET CC2. I-44.",
        "VSJHDV2  DS    0H",
    ])
    return d


def dmkopr():
    """The operator console writer -- and therefore CP's only voice.

    `DMKOPR` is `DMKOPRWT`, the routine every other module calls to put a line
    on the operator's console.  Three channel sites, all in one routine:

        00142000  TIO 0(R3)   CLEAR ANY OUTSTANDING STATUS
        00149000  SIO 0(R3)   ISSUE SIO
        00153000  TIO 0(R3)   WAIT FOR DEVICE END STATUS

    This is the module to convert next for a reason beyond its size.  Every
    bootstrap failure so far has been diagnosed by instruction trace, because
    `I-94` left CP unable to report anything: the error paths in `DMKCKP` and
    `DMKCPI` call `DMKOPRWT`, and `DMKOPRWT` could not drive the device.  A
    working console turns the next wall from a PSW and a storage dump into a
    message with a number on it.

    The condition-code contract is the reason `XATIO` drops in unchanged.
    The code reads `TIO`'s S/370 codes directly -- `BO SETCC3` for cc3 not
    operational, `BC 4+2,TESTLOOP` for cc1 or cc2 -- and then reads the CSW
    with `TM CSW+4,UC`.  `XATIO` presents exactly those four codes and its
    shim rebuilds the CSW at the architected location from the IRB, so both
    survive.  `SIO`'s condition code is never tested here at all.

    `USING DMKOPRWT,R15` is a **single** base, so the module has 4 KB of
    addressability and the work area has to fit inside it -- the same
    constraint that `I-56` hit in `DMKDMP` and that `dmksav` notes.  If it
    does not fit the assembler says so, which is the cheap failure.

    Placement sharpens `I-77`.  That issue said to anchor before the `PSA`
    macro, and copying that rule here put the work area at `COPY EQU`
    (00277000) and earned **81** `IFO209 ADDRESSABILITY ERROR`s.  The tail of
    this module is

        00274000  LTORG
        00275000  EJECT
        00276000  COPY RBLOKS      <- RCHBLOK DSECT, and it never returns
        00277000  COPY EQU
        00278000  COPY DEVTYPES
        00279000  PSA
        00280000  END DMKOPR

    `COPY RBLOKS` opens a DSECT and does not close it, so everything after it
    -- `COPY EQU`, `COPY DEVTYPES`, the `PSA` macro and anything inserted
    among them -- is already inside a dummy section.  The real rule is
    therefore **anchor before the first COPY that opens a DSECT**, not before
    the `PSA` macro; in `DMKSAV` those happened to be the same statement,
    which is why the narrower rule survived.  The anchor here is the `EJECT`
    at 00275000, the last statement still in the CSECT.  I-105.

    The two `XC`s in this module -- `XC CSW,CSW` and `XC MSGBUF(160),MSGBUF`
    -- are both bounded and neither reaches the work area, so `I-55` does not
    apply.
    """
    d = Deck(XA23)
    nxt = lambda s: next_seq(SRC + '/DMKOPR.ASSEMBLE', s)

    d.replace('00142000', first='00142100', inc=100, limit=nxt('00142000'),
              lines=Deck.comment(
        "THE CALLER READS TIO'S OWN CONDITION CODES -- BO FOR CC3 AND "
        "BC 4+2 FOR CC1 OR CC2 -- AND THEN THE CSW. XATIO PRESENTS BOTH. "
        "I-105.") + [
        "         XATIO R3             CLEAR ANY OUTSTANDING STATUS",
    ])

    d.replace('00149000', first='00149100', inc=100, limit=nxt('00149000'),
              lines=["         XASIO R3             ISSUE THE CHANNEL PROGRAM"])

    d.replace('00153000', first='00153100', inc=100, limit=nxt('00153000'),
              lines=["         XATIO R3             WAIT FOR DEVICE END STATUS"])

    d.insert('00275000', first='00275100', inc=100, limit=nxt('00275000'),
             lines=Deck.comment(
        "BEFORE COPY RBLOKS, WHICH OPENS RCHBLOK DSECT AND NEVER RETURNS TO "
        "THE CSECT. ANCHORING AT COPY EQU PUT THIS INSIDE THAT DSECT AND "
        "EARNED 81 IFO209 ADDRESSABILITY ERRORS. I-105, SHARPENING I-77.") + [
        "         XAIOWORK             XAIO WORK AREAS AND LOOKUP",
        "         COPY  XABLOKS        FOR ORBCCWFM, THE CCW FORMAT",
    ])
    return d


def dmkpsa():
    """The last module on the M1 path, and the only one that is lowcore itself.

    `USING DMKPSA,R0` and `PSA EQU DMKPSA`: the module *is* the prefix storage
    area, addressed from absolute zero.  It declares REENTRANT, and unlike
    `DMKIOT` and `DMKCNS` it has **no** `USING IOBLOK`, so `XAIOB`'s
    IOBLOK-resident storage is not available and neither macro set fits.

    What the two sites actually need turns out to be much less than either
    macro provides.

    **The `HIO` at 00646000 needs no storage at all.**  `HSCH` takes its
    subchannel in R1 and writes nothing, so it is two instructions and is
    reentrant by construction.  R1 is safe to clobber: `CALL DMKSCNRD` set it
    before the loop, nothing between here and `EXTEXIT` reads it, and each
    iteration reloads it from `RDEVSSID` anyway.

    **The `TIO` at 00651000 has no CSW test and no condition-code test after
    it** -- `BCT R15,HALTCON` is the next instruction.  Its whole purpose is to
    consume pending status, so the IRB `TSCH` stores into is **write-only**:
    nothing ever reads it.  That is what makes a shared scratch area correct
    here rather than merely convenient, because two paths racing on it would
    both be discarding what they wrote.  It is the one case in this conversion
    where reentrancy costs nothing to satisfy.

    `BC 2,*-4` at 00647000 spans the converted `HIO`, and `HALTCON` at 00645000
    already labels the target, so it only needs the name it could have used
    all along.  `R-26`.

    No `COPY XABLOKS` is needed: there is no `SSCH` here, so `ORBCCWFM` never
    comes into it.
    """
    d = Deck(XA22)
    nxt = lambda q: next_seq(SRC + '/DMKPSA.ASSEMBLE', q)

    # ---------------------------------------------------- I-192, wall 21
    # The five storage-key reads.  CP's OWN use of the keys, not a guest's --
    # R-12 and DMKPRV are the place where a guest's 2 KB view has to be
    # simulated, and none of that applies here.  So these are mechanical:
    # ISK -> ISKE, same operands, and every mask below them survives, because
    # the result layout did not move.  ISK returns bits 24-27 access control,
    # 28 fetch-protect, 29 reference, 30 change; so does ISKE.  The three masks
    # these routines use -- F8 for fetch, F240 for the key, F2 for change --
    # therefore read the right bits of an ISKE result unchanged.
    #
    # X2048BND, "GET MASK FOR BITS 8-20", also stays.  ISKE takes its block
    # from bits 1-19 of the operand and IGNORES bits 20-31, where S/370's ISK
    # required bits 29-31 to be zero or took a specification exception.  So a
    # 2 KB-aligned address is still a legal operand; it just names the 4 KB
    # page that contains it.
    for seq in ('00386000', '00401000', '00410000'):
        d.replace(seq, first=seq[:-3] + '100', inc=100, limit=nxt(seq),
                  lines=["         ISKE  R15,R15       GET THE REAL STORAGE KEY"])

    # DMKPSACC checks the change bit in both 2 KB halves of a page: 00438000
    # reads the first, and on a zero result 00441000-00446000 recomputes the
    # address plus 2048 and reads "the last half page".  Under ESA/390 there is
    # ONE key for the whole 4 KB, so the second read returns the same byte and
    # the same condition code, and the routine's answer is unchanged either
    # way.  Both are converted and the redundant pair is LEFT IN PLACE rather
    # than deleted: the change set on the critical path stays five identical
    # one-word edits, which can be reviewed in full, and removing dead cards is
    # a separate change with its own way of going wrong.  I-177 collapsed the
    # equivalent SSK pair in DMKPTR, so the precedent for tidying it exists.
    for seq in ('00438000', '00444000'):
        d.replace(seq, first=seq[:-3] + '100', inc=100, limit=nxt(seq),
                  lines=["         ISKE  R15,R15       GET THE REAL STORAGE KEY"])

    d.replace('00646000', '00647000', first='00646100', inc=100,
              limit=nxt('00647000'), lines=Deck.comment(
        "HSCH FOR HIO. NO STORAGE AND NO CONDITION-CODE WORK: THE "
        "BC 8+1,EXTEXIT BELOW MEANS THE SAME THING UNDER HSCH. R1 IS FREE "
        "-- NOTHING READS IT AGAIN, AND EACH RETRY RELOADS IT.") + [
        "         L     R1,RDEVSSID    SUBSYSTEM ID FROM THE RDEVBLOK",
        "         HSCH  0              HALT ACTIVE I/O",
        "         BC    2,HALTCON      CC = 2, BURST OPERATION HALTED",
    ])

    d.replace('00651000', first='00651100', inc=100, limit=nxt('00651000'),
              lines=Deck.comment(
        "TSCH FOR TIO. THE NEXT INSTRUCTION IS BCT, SO NEITHER THE CSW NOR "
        "THE CONDITION CODE IS EVER LOOKED AT -- THIS ONLY CONSUMES PENDING "
        "STATUS. THE IRB IS THEREFORE WRITE-ONLY AND A SHARED SCRATCH AREA "
        "IS CORRECT, NOT JUST CONVENIENT. I-75.") + [
        "         L     R1,RDEVSSID    SUBSYSTEM ID FROM THE RDEVBLOK",
        "         TSCH  PSAXIRB        DRAIN IT; THE IRB IS DISCARDED",
    ])

    # After DMKPSANX and before the LTORG: data, so nothing falls into it.
    d.insert('00665000', first='00665010', inc=10, limit=nxt('00665000'),
             lines=Deck.comment(
        "WRITE-ONLY IRB FOR THE TSCH ABOVE. SIXTY-FOUR BYTES, FULLWORD "
        "ALIGNED -- TSCH TAKES A SPECIFICATION EXCEPTION OTHERWISE. "
        "NOTHING READS IT, SO NO PATH CAN BE HARMED BY ANOTHER WRITING "
        "IT.") + [
        "PSAXIRB  DS    16F            IRB, WRITTEN AND DISCARDED",
    ])
    return d


def dmkcns():
    """The console driver: the last must-work module on the M1 path.

    `DMKQCNWT` -> `DMKCNSIC` -> `DMKIOS` -> interrupt -> `DMKCNSIN` is M1's
    target, so these five sites have to be right rather than merely assemble.
    They are also the only place in the nucleus that issues `CLRIO`.

    It uses `XAIOB` for the same reason `DMKIOT` does -- `USING RDEVBLOK,R8`
    and `USING IOBLOK,R10` from the prologue, and every caller takes its device
    from `CALL DMKSCNRD`, which returns R8's own address.

    **The base registers needed checking and the answer was not obvious.**  The
    module drops R13 twice and establishes `USING DMKCNSIN,R12` and
    `USING DMKCNSEN,R12`, which looks like three addressability domains with
    the five sites split across two of them -- and one `XAIOBWRK` can only be
    assembled against one base (`I-70`).  It is not: each of those entry points
    reloads R12 and R13 from `CNSBASE` within two instructions and
    re-establishes `USING DMKCNS,R12,R13`, so the alternative `USING` covers
    only its own prologue and every site sees the same base.  The same shape as
    `DMKCPI`'s `DMKCPIEM`.

    Placement is before the `LTORG` at 01735000, after the `DC` constants at
    01709000-01724000, so nothing falls into it and it sits between the sites
    and the module's end rather than past it -- `USING DMKCNS,R12,R13` gives
    8 KB and the module already fits inside that, but the five call sites and
    the work area add roughly 280 bytes to it.  If that tips it over, CE says
    `IFO209` and the fix is to move the block, not to rethink it (`I-56`).
    """
    d = Deck(XA21)
    nxt = lambda q: next_seq(SRC + '/DMKCNS.ASSEMBLE', q)

    d.replace('00393000', first='00393100', inc=100, limit=nxt('00393000'),
              lines=Deck.comment(
        "HSCH FOR HDV. THE BC 8/2/1 MASKS BELOW ARE UNCHANGED: CNSEXIT ON "
        "CC0, RETRY ON CC2, CNSICC3 ON CC3, ALL TO LABELS.") + [
        "         XABHIO               .......SCREEEECCCCHHHH.......",
    ])

    d.replace('00567000', first='00567100', inc=100, limit=nxt('00567000'),
              lines=Deck.comment(
        "TSCH FOR TIO, CONDITION CODES NORMALISED. CC0 STILL MEANS NOTHING "
        "PENDING AND BRANCHES TO EBCOMPT BEFORE ANY CSW IS READ; THE "
        "TM CSW+4,ATTN BELOW IS ONLY REACHED ON CC1, WHERE XABTIO HAS "
        "BUILT THE CSW.") + [
        "         XABTIO               CLEAR PENDING STATUS, IF ANY",
    ])

    # --- The name.  CE's HRC370DK probes for System/380 and, when the probe
    #     succeeds, zaps a C'8' over the C'7' in three "VM/370" literals so the
    #     system announces itself as VM/380.  We are NOT taking the /380 route:
    #     this is a 31-bit ESA/390 conversion on the way to 64-bit, so the name
    #     is VM/370+.  The probe itself is left alone -- it records a true fact
    #     about the machine in INSTWRD1 byte 0 -- but nothing may overwrite the
    #     banner with it.  Byte 0 is display-only; bytes 1-3 are the LDEVCTL
    #     pointer that DMKCFP, DMKGRF and HDKD7C use, and MVI touches only
    #     byte 0, so removing these readers changes no behaviour.
    d.replace('01523100', first='01523110', inc=10, limit=nxt('01523100'),
              lines=Deck.comment(
        "WAS MVC EBCLMSG+8(1),INSTWRD1 -- ZAP THE '7' OF VM/370 WITH THE "
        "'7' OR '8' CE'S SYSTEM/380 PROBE LEFT IN THE PSA. THE LITERAL "
        "BELOW NOW READS VM/370+ AND MUST NOT BE OVERWRITTEN. I-179.") + [
        "         DS    0H             THE ZAP IS GONE",
    ])

    # Records here are spaced by seven, so number by one.
    d.replace('01624147', first='01624148', inc=1, limit=nxt('01624147'),
              lines=Deck.comment(
        "SSCH. BC 13 BELOW IS UNTOUCHED.") + [
        "         XABSIO               ATTEMPT TO START THE I/O",
    ])

    d.replace('01624196', '01624203', first='01624197', inc=1,
              limit=nxt('01624203'), lines=Deck.comment(
        "HSCH AND CSCH. THIS CLRIO IS THE ONLY ONE IN THE NUCLEUS. CSCH "
        "SETS CC0 -- CLEARED -- OR CC3 -- NOT VALID, NOT ENABLED OR NOT "
        "THERE -- AND NOTHING ELSE, WHICH IS EXACTLY THE PAIR CNSTSIO1 "
        "TESTS WITH BCR 8,R2 AND BC 1,CNSICC3.") + [
        "         XABHIO               CLEAR UCW",
        "         XABCIO               CLEAR CC=3 CONDITION",
    ])

    d.replace('01701000', first='01701100', inc=100, limit=nxt('01701000'),
              lines=Deck.comment(
        "WAS C' VM/370 ONLINE '. EBCLMSGL IS COMPUTED AS *-EBCLMSG SO THE "
        "EXTRA BYTE NEEDS NO OTHER CHANGE, AND THE ONLY FIXED-OFFSET "
        "READER OF THIS MESSAGE WAS THE ZAP REMOVED AT 01523100. I-179.") + [
        "EBCLMSG  DC    X'151515',C' VM/370+ Online '",
    ])

    d.insert('01724000', first='01724010', inc=10, limit=nxt('01724000'),
             lines=Deck.comment(
        "XAIOB WORK AREAS AND SHIMS, BEFORE THE LTORG AND AFTER THE DC "
        "CONSTANTS, SO NOTHING FALLS INTO IT AND THE CALLERS' OWN "
        "USING DMKCNS,R12,R13 IS THE ONE IN FORCE. I-70.") + [
        "         XAIOBWRK             XAIOB SHIMS",
    ])

    d.insert('01971000', first='01971010', inc=10, limit=nxt('01971000'),
             lines=["         COPY  XABLOKS        FOR ORBCCWFM"])
    return d


def dmkfre():
    """Three CR2 loads that meant "disable channel zero while we are extending".

        TS    XTNDLOCK-PSA(R14)  TEST & SET 'EXTEND LOCK'
        BNZ   ERROR10            EXTEND WHILE EXTENDING -- DIE NOW
        ...
        STCTL C2,C2,TEMPSAVE     GET CURRENT EXTENDED IO MASKS
        NI    TEMPSAVE,X'7F'     DISABLE CHANNEL ZERO
        LCTL  C2,C2,TEMPSAVE     WHILE WE ARE EXTENDING

    On ESA/390 CR2 is the dispatchable-unit-control-table origin, so the load
    writes a channel mask into a register that is not one.  What to put there
    instead is the interesting question, and the answer is nothing.

    **The mutual exclusion does not depend on it.**  `TS XTNDLOCK` two
    instructions earlier is the real lock, and it aborts on re-entry.  The CR2
    masking is belt and braces for channel 0 alone -- devices on other channels
    could always interrupt -- so removing it weakens a guard that was already
    partial rather than removing the guard.

    **And the obvious substitute would be worse.**  The nearest ESA/390
    equivalent is masking the I/O-interruption subclass in CR6, but every
    subchannel is ISC 0 here, so that would mask *all* I/O -- and the extend
    calls `DMKPTRFR`, which does paging I/O and waits for it.  A faithful-
    looking conversion would deadlock the very path it was protecting.  `I-73`.
    """
    d = Deck(XA20)
    for seq in ('00645000', '00698000', '00723000'):
        d.replace(seq, first=str(int(seq) + 10).zfill(8), inc=10,
                  limit=next_seq(SRC + '/DMKFRE.ASSEMBLE', seq),
                  lines=Deck.comment(
            "WAS LCTL C2,C2,TEMPSAVE -- DISABLE CHANNEL ZERO WHILE "
            "EXTENDING. TS XTNDLOCK IS THE REAL LOCK AND IS UNCHANGED; "
            "MASKING CR6 INSTEAD WOULD DEADLOCK THE DMKPTRFR CALL INSIDE "
            "THE EXTEND. I-73.") + [
            "         DS    0H             THE LCTL IS GONE",
        ])
    return d


def dmkcfo():
    """The `SET CPASSIST` command's CR6 store, which is the last way in.

    `SETCPAC6` is reached from the `SET CPASSIST ON|OFF` command path with R7
    holding X'02000000' or zero, and it does

        SETCPAC6 ST    R7,CPCREG6     RESET CP ASSIST ENABLE MASK
                 LCTL  C6,C6,CPCREG6  AND RESET CREG. 6 FOR CP ASSIST

    -- so it overwrites `CPCREG6` itself rather than merely loading it.  Since
    `XA0001DK` makes that field the I/O-interruption subclass mask, the store
    would destroy the mask at its source and the `LCTL` would then commit the
    damage, and no amount of fixing the loads elsewhere would help.

    The store goes and the `LCTL` stays, so the command still reloads CR6 with
    the correct value.  CP's own record of whether the assist is on lives in
    `CPSTAT2` (`CPASTAVL`, `CPASTON`), not in this word, so nothing that reads
    the assist state is affected.  The label is kept -- it is a branch target.
    `I-71`.
    """
    d = Deck(XA19)
    d.replace('00612100', first='00612110', inc=10,
              limit=next_seq(SRC + '/DMKCFO.ASSEMBLE', '00612100'),
              lines=Deck.comment(
        "WAS ST R7,CPCREG6 -- RESET CP ASSIST ENABLE MASK, WITH R7 HOLDING "
        "X'02000000' OR ZERO. CPCREG6 IS THE I/O SUBCLASS MASK NOW AND THIS "
        "WOULD OVERWRITE IT AT SOURCE. THE LCTL BELOW STAYS AND NOW LOADS "
        "THE RIGHT VALUE. LABEL KEPT: IT IS A BRANCH TARGET. I-71.") + [
        "SETCPAC6 DS    0H             THE STORE IS GONE, NOT MOVED",
    ])
    return d



# --------------------------------------------------------------------- I-114
# CP's twenty-one ECPS:VM assist sites, statically no-opped.
#
# `pgmtrace` found the wall in one run and even named it: two operation
# exceptions in the whole IPL, both ECPS:VM assists.
#
#     PSW=000C3000 0003F52E INST=E60E100003B0 SCNRU  ecpsvm_locate_rblock
#     PSW=000C1000 0006A1CE INST=E61230000000 STEVL  ecpsvm_store_level
#
# The second is DMKCPI's own probe at 00613000, which is DELIBERATE: it arms
# `PRNPSW+4` at `CPIPINT2` first, and `CPIPINT2` walks `CPATABLE` replacing
# every assist instruction with `MVC 0(6,R6),=X'0700,47000000'` -- six bytes of
# no-op -- so that the software path following each assist runs instead.  That
# recovery works, and it worked here on the first try.
#
# The FIRST exception is the defect, and it is an ORDERING defect: `SCNRU` sits
# at DMKSCNRU's entry (X'3F528') and DMKCPI calls it, looking up device 00C
# (GR1 = 0000000C), BEFORE it has probed.  GR5 = 0 dates it -- the storage
# sizing had not run yet.  On real hardware the order is irrelevant, because CE
# runs ECPSVM YES and the assists simply work; under ESA/390 they do not exist,
# and CP executes one before asking whether they are there.
#
# Two counts worth keeping straight, because both were got wrong first:
#
#   * 21 SOURCE SITES, not 24.  `DC X'E610'` with no operand appears in DMKGRT,
#     DMKRGA and DMKRGF and is the card-reader DEVICE TYPE constant -- data, and
#     its own comment says so.  An assist is `DC X'E6nn',S(a,b)`: six bytes,
#     opcode plus two S-type constants, which is what the trace disassembled.
#     Grepping a byte pattern without the operand test over-counts by three.
#   * 30 INSTRUCTIONS in the nucleus, not 21.  DMKCCW generates its assists from
#     macros -- `X'E608'` expands to DMKCCWB1..B8 and `X'E609'` to L1..L5 -- so
#     five source lines become sixteen instructions.  `CPATABLE` is the
#     authority, and it has exactly 30 entries.  08-MACRO-UNDERCOUNT again.
#
# CPATABLE covers all 30, so CP's runtime recovery is COMPLETE and only its
# timing is wrong.  That invites a one-module fix -- no-op DMKSCN's two sites and
# let CLEARCPA handle the other 28 -- and that is refused on purpose: it is the
# "fix the instance, miss the class" pattern this register already records three
# times, and it would leave 28 illegal instructions in the nucleus that merely
# happen not to be reached on this path.
#
# So every site is no-opped at ASSEMBLY time with the same six bytes CP writes at
# RUN time.  Labels are reproduced -- DMKDSP0, DMKDSP1, DMKDSP2, DMKVATZP,
# DMKVATZS, DMKCCW0, DMKCCW1, DMKCCWGN and the macros' `&ENTRYPT` are entry
# points, and I-107 is the reminder that a replacement card that drops its label
# leaves every reference unresolved.  Length is unchanged at six bytes, so no
# self-relative branch can span a site and shift -- R-26 does not apply.
#
# DMKCPI is the one exception and gets a BRANCH, not a no-op: no-opping its probe
# would fall through to `OI CPSTAT2,CPASTAVL+CPASTON`, declaring the assists
# available and ON and skipping CLEARCPA entirely.  `B CPIPINT2` takes the
# correct path, padded to six bytes so nothing shifts.
#
# DMKAPI's E612 is deliberately NOT converted: with AP=NO (I-50) it is not in
# CPLOAD's list.  If AP is ever re-enabled it needs the same treatment.
ECPS = {
    'DMKSCN': (XA24, [('00160000', '', 'E60E', 'SCNRU'),
                      ('00321000', '', 'E606', 'SCNVU')]),
    'DMKDSP': (XA25, [('00328000', 'DMKDSP0', 'E60D', 'DISPATCH 0'),
                      ('01572000', 'DMKDSP1', 'E607', 'DISPATCH 1'),
                      ('01635000', 'DMKDSP2', 'E611', 'DISPATCH 2')]),
    'DMKFRE': (XA26, [('00281500', '', 'E614', 'FREE'),
                      ('01099500', '', 'E615', 'FRET')]),
    'DMKPTR': (XA27, [('01772000', '', 'E603', 'UNLOCK PG'),
                      ('01851000', '', 'E602', 'LOCK PG')]),
    'DMKUNT': (XA28, [('00109400', '', 'E610', 'UNTRANSLATE'),
                      ('00220050', '', 'E605', 'UNTRANS FRE')]),
    'DMKVAT': (XA29, [('00391000', 'DMKVATZP', 'E60B', 'INVAL PAGE'),
                      ('00408700', 'DMKVATZS', 'E60A', 'INVAL SEG')]),
    'DMKVMA': (XA30, [('00172000', '', 'E613', 'SHADOW TBL')]),
    'DMKCCW': (XA31, [('00239000', '&ENTRYPT', 'E608', 'TRANBRNG'),
                      ('00259000', '&ENTRYPT', 'E609', 'TRANLOCK'),
                      ('00561000', 'DMKCCW0', 'E604', 'CCWTRANS'),
                      ('00630000', 'DMKCCW1', 'E60C', 'CCWTRANS1'),
                      ('00909000', 'DMKCCWGN', 'E60F', 'CCWGEN')]),
}


def ecps(module):
    """One deck of six-byte no-ops for `module`'s ECPS:VM assist sites."""
    ident, sites = ECPS[module]
    d = Deck(ident)
    src = SRC + '/%s.ASSEMBLE' % module
    first = True
    for seq, label, op, what in sites:
        lines = []
        if first:
            lines = Deck.comment(
                "ECPS:VM ASSISTS DO NOT EXIST ON ESA/390. EACH SITE BECOMES THE "
                "SAME SIX-BYTE NO-OP CP'S OWN CLEARCPA WRITES AT RUN TIME, SO "
                "THE SOFTWARE PATH BELOW IT RUNS. I-114.")
            first = False
        lines.append('%-8s DC    X\'0700\',X\'47000000\'  WAS %s %s'
                     % (label, op, what))
        d.replace(seq, first=str(int(seq) + 10).zfill(8), inc=10,
                  limit=next_seq(src, seq), lines=lines)
    return d



def rdevice():
    """I-116.  Make the generator emit the block the DSECT describes.

    `RBLOKS.XA0002DK` added `RDEVSSID` and a reserved fullword after `RDEVIOBL`,
    the DSECT's last field, so `RDEVSIZE EQU (*-RDEVBLOK)/8` went from 11
    doublewords to 12.  But DMKRIO's blocks are not cut from the DSECT --
    `RDEVICE.MACRO` emits them as a list of explicit `DC` statements and ends at
    `DC F'0' RESERVED FOR IBM USE`, which IS `RDEVIOBL`.  So the array stayed at
    88 bytes a block while every scanner started striding 96:

        VSERNEXT LA    R1,RDEVSIZE*8(,R1)  POINT TO NEXT REAL DEVICE BLOCK

    `DMKSCNVS` therefore walks 8 bytes further out per block, cannot find the
    SYSRES volume label, and DMKCPI takes `ABEND 1 -- SYSRES DEVICE NOT FOUND OR
    INCORRECT`, reported as `CPI001`.

    **Measured, not argued.**  `tools/dumpscan.py` reads the printed abend dump
    back into a byte image and reports:

        ARIODV = 0149E8, ARIODC count = 949
        OBSERVED stride = X'58' (11 doublewords)
        CONFIRMED: 0149E8 + 949 x X'58' = 029020 = ARIOCU -- they abut exactly

    949 blocks at 88 bytes land precisely on the first RCUBLOK, which settles the
    stride beyond coincidence.  Over 949 blocks the 8-byte error accumulates to
    7592 bytes, so the scan is not slightly off, it is off the end of the array.

    **Why nothing caught it.**  Both halves are correct in isolation, they live in
    different files, and neither mentions the other -- so all 201 modules
    assemble with NO STATEMENTS FLAGGED and the only symptom is a scan reading
    the wrong addresses.  The deck's own comment said *"RESERVED, KEEPS RDEVSIZE
    EXACT"*: care was taken that `RDEVSIZE` stayed a whole number of doublewords,
    and the question of whether anything BUILT blocks to a different length was
    never asked.

    **The rejected alternative.**  `ORG`-ing `RDEVSSID` onto `RDEVIOBL` -- unused
    under AP=NO (I-50) -- would need no generator change at all and no length
    change anywhere.  It is refused because it overloads a field a future AP
    revival needs, and `dmksys()` deliberately keeps that door open: *"the
    processor half survives untouched ... multiprocessing is reachable later"*.
    Paying eight bytes a block (7592 bytes of nucleus) to keep the DSECT honest
    is the cheaper of the two debts.
    """
    d = Deck(XA32)
    src = SRC + '/RDEVICE.MACRO'
    d.insert('00583000', first='00583010', inc=10,
             limit=next_seq(src, '00583000'),
             lines=Deck.comment(
        "ESA/390 SUBSYSTEM IDENTIFICATION, MATCHING THE TWO FULLWORDS "
        "RBLOKS.XA0002DK ADDED TO THE RDEVBLOK DSECT AFTER RDEVIOBL. WITHOUT "
        "THESE THE DSECT SAYS 12 DOUBLEWORDS AND THIS MACRO EMITS 11, SO EVERY "
        "LA R1,RDEVSIZE*8(,R1) SCAN WALKS OFF BY 8 BYTES A BLOCK -- 7592 BYTES "
        "OVER 949 DEVICES -- AND DMKSCNVS CANNOT FIND THE SYSRES LABEL. I-116.") + [
        "         DC    F'0' -         RDEVSSID, FILLED BY XAIOFIND",
        "         DC    F'0' -         RESERVED, KEEPS RDEVSIZE EXACT",
    ])
    return d



def dmkbld():
    """DMKBLDRT and DMKBLDRL: build and release ESA/390 tables, aligned.

    This is the module the conversion exists for.  `DMKBLDRT` writes the segment
    and page tables CP gives itself at IPL, and `TRANS`'s `LRA` reads them --
    which is `wall 11`, `PRG018`, a translation-specification exception against a
    System/370 table.  `DMKBLDRL` is its inverse and has to stay in step, which
    is most of why this deck is one deck and not two.

    `asmerr.py` says the assembler flags **37** statements here.  This deck has
    more cards than that for three reasons, and each is a class the assembler
    cannot see (`I-124`):

      * the **alignment** arithmetic -- `AL R0,F7` and the rounding it pays for
      * the **packed-pointer masks** -- `L Rn,VMSEG` followed by `LA Rn,0(,Rn)`,
        which stripped the length when it lived in the ignored high byte and
        strips nothing now that STL is bits 25-31 (`I-128`)
      * the **ABI split** -- `SRL R8,20`, `SLL R1,4+4` and five more literals
        that divide a page number into a segment and a page

    The ABI itself does not change, and the source says why.  Sequence 00523000:

        *        GPR 1 = BEGINING AND ENDING ADDRESS TO RELEASE
        *        BYTE 0-1 = FIRST ADDRESS TO RELEASE
        *             FIRST 4 BITS = 0, NEXT 8 BITS = SEGMENT, NEXT 4 = PAGE

    Twelve bits of page number, split 8+4 for 64 KB segments and 4+8 for 1 MB
    ones.  **The field keeps its width and its meaning; only the split moves.**
    `SLL R1,4+4  SEGMENT COUNT * 16` is written as a sum because the two shifts
    mean different things -- units to segments, then segments to pages -- so only
    the second becomes 8.  Written as `SLL R1,8` it would have been impossible to
    convert by reading, and `R01-SHIFT-SITES.md`'s "4 -> 8" rule would have
    changed the wrong half.
    """
    d = Deck(XA34)
    src = SRC + '/DMKBLD.ASSEMBLE'

    def one(seq, lines, to=None):
        """Replace a record, choosing the largest increment that fits.

        Hand-picking the increment is how the sequence guard gets tripped: the
        room between two records varies (10 here, 100 there, 5 at 00246090) and
        a block that grows by one card outgrows it silently in the generator and
        loudly, in the wrong place, in UPDATE.  `_seqcheck` catches it, but
        catching it four times in one deck is a sign the caller should not be
        choosing.  So: ask for the biggest step that leaves room.
        """
        limit = next_seq(src, to or seq)
        base = int(seq)
        for inc in (100, 10, 1):
            last = base + inc * len(lines)
            if limit is None or last < int(limit):
                d.replace(seq, to, first=str(base + inc).zfill(8), inc=inc,
                          limit=limit, lines=lines)
                return
        raise ValueError('no room after %s for %d cards before %s -- the lines '
                         'must go somewhere else' % (seq, len(lines), limit))

    # ---------------------------------------------------------- DMKBLDRT
    # Pages -> units, the inverse of the units -> segments -> pages conversion
    # made at 00222700 below, and missed when that one was made.  I-188: this is
    # the card that made the segment table sixteen times longer than the machine,
    # which let DMKPGS's PGOUT2 scan run past VMSIZE, where DMKPTRAN's
    # `LA R1,0(,R1)  STRIP HIGH BYTE` turned 16 MB into 0 and the loop closed.
    #
    # I-221.  The page range arrives packed, start page in the high halfword
    # and end page in the low one, and the end page was masked with F4095 --
    # twelve bits, 4096 pages, 16 MB.  DEF STOR 32M therefore built a 16-entry
    # segment table (STL 0; CR1 = 00FFD000 in the w59 trace) and every LRA
    # above 16 MB took CC3.  The halfword is the real limit: 65,536 pages,
    # 256 MB, which is I-185/I-203's ceiling and the mask that was hiding it.
    one('00197000', [
        "         N     R5,=A(X'FFFF') END PAGE IS A HALFWORD I-221",
    ])
    one('00207000', Deck.comment(
        "WAS SRDL R0,8. R0 ARRIVES AS A PAGE COUNT AND LEAVES AS A COUNT OF "
        "64-BYTE UNITS, WHICH IS WHAT STL COUNTS AND WHAT 00262000 STORES "
        "AFTER A BCTR. THE PROJECT'S OWN CARDS SETTLE THE UNITS: 00249000 "
        "DOES LR R7,R3 AND 00250000 SLL R7,6 -- TIMES 64 BYTES PER TABLE -- "
        "AND 00222500 READS LA R1,1(,R1)  SEGMENT COUNT/16.") + Deck.comment(
        "A 64-BYTE UNIT IS SIXTEEN FULLWORD STES IN BOTH ARCHITECTURES, "
        "BECAUSE AN STE IS A FULLWORD IN BOTH. WHAT MOVED IS WHAT SIXTEEN "
        "ENTRIES COVER: 16 TIMES 64 KB IS 1 MB, 16 TIMES 1 MB IS 16 MB. SO "
        "THE SAME TABLE LENGTH NOW SPANS SIXTEEN TIMES THE ADDRESS SPACE AND "
        "THE SHIFT THAT DIVIDES PAGES BY A UNIT GROWS BY FOUR. IT IS WRITTEN "
        "8+4 BECAUSE 00222700 IS ITS EXACT INVERSE, SLL R1,4+8.") + Deck.comment(
        "DMKVAT'S OWN GEOMETRY TABLE IS THE CITATION. CODEB0 -- LARGE PAGE, "
        "LARGE SEG, FULLWORD ENTRIES, WHICH IS THIS ARCHITECTURE -- CARRIES "
        "PAGINCR H'64', THE UNIT, AND MAXSEGS H'127', A SEVEN-BIT STL. 128 "
        "UNITS OF 16 MB IS 2 GB, WHICH IS THE WHOLE 31-BIT SPACE, SO THE "
        "FIELD IS WIDE ENOUGH AND ONLY THIS SHIFT WAS WRONG.") + [
        "         SRDL  R0,8+4         SHIFT TO OBTAIN NUMBER OF UNITS",
    ])
    # The segment-table length, read from the STD.  S/370 keeps it in bits 0-7,
    # ESA/390 in bits 25-31, so the byte moves from 0 to 3.  Both sites clear the
    # register first (SR R4,R4 / SR R1,R1), so IC alone leaves it clean.
    one('00215000', [
        "         IC    R4,VMSEG+3     STL IS BITS 25-31 NOW, NOT 0-7",
        "         N     R4,=A(SEGSTLM) WITHOUT THE S BIT",
    ])
    one('00222300', [
        "         IC    R1,VMSEG+3     STL IS BITS 25-31 NOW, NOT 0-7",
        "         N     R1,=A(SEGSTLM) WITHOUT THE S BIT",
    ])
    # Units -> segments -> pages.  Only the second shift changes: a segment holds
    # 256 pages, not 16.  See the docstring.
    one('00222700', [
        "         SLL   R1,4+8         SEGMENTS, THEN PAGES PER SEG",
    ])

    # The alignment.  The idiom is already here for 64 bytes; ESA/390 wants the
    # segment table on a 4096-byte boundary, so the slack goes from 7 doublewords
    # to 511 and the rounding mask from X'FFFFC0' to the architected STO mask.
    # 4095 is the largest displacement LA can encode, and the requirement happens
    # to be exactly that.
    one('00241000', Deck.comment(
        "4088 BYTES OF SLACK, NOT 56: AN ESA/390 SEGMENT TABLE MUST BE ON A "
        "4096-BYTE BOUNDARY BECAUSE THE STD'S ORIGIN IS BITS 1-19 WITH TWELVE "
        "ZEROS APPENDED. DMKBLDRL'S F15 BECOMES F519 TO MATCH, AND THE TWO MUST "
        "BE CHANGED TOGETHER OR FRET RETURNS THE WRONG LENGTH.") + [
        "         AL    R0,=F'511'     PLUS 511 FOR 4096-ALIGNMENT",
    ])
    one('00243000', [
        "         LA    R6,4095(,R1)   ROUND UP -- 4095 IS THE MOST",
        "*                             AN LA CAN ENCODE",
    ])
    one('00244000', [
        "         N     R6,=A(SEGSTOM)      (IN R6)",
    ])

    # The quiesce loop.  L Rn,VMSEG / LA Rn,0(,Rn) stripped the length when it
    # lived in the ignored high byte.  It strips nothing now.  I-128.
    one('00246090', [
        "         N     R8,=A(SEGSTOM) STL IS IN THE LOW BITS, SO LA",
        "*                             NO LONGER STRIPS IT",
    ])
    one('00246230', [
        "         TM    SEGPTO+3,SEGENQ+SEGINVAL AVAILABLE?",
    ])
    # ICM of bytes 1-2 tested the S/370 page-table origin.  The ESA/390 origin is
    # bits 1-25, so the test is the masked word.
    one('00246270', [
        "         L     R0,SEGPTO      THE WHOLE ENTRY",
        "         N     R0,=A(SEGPTOM) (ONLY IF POINTER = 0)",
    ])
    # A segment is 1 MB now, not 64 KB.  The LA 4(,R8) two lines below is an STE
    # stride and stays 4 -- adjacent lines, opposite answers.  I-124.
    one('00246370', [
        "         A     R1,=A(X'100000') NEXT VIRTUAL SEGMENT",
    ])
    one('00254000', [
        "         N     R8,=A(SEGSTOM) WITHOUT THE LENGTH",
    ])

    # The STD's length.  The VALUE is unchanged -- ESA/390's STL counts 64-byte
    # units minus one, which is what CP already writes -- but the byte moves from
    # 0 to 3.  Saying the value was unchanged and concluding the instruction was
    # cost a retraction: I-129.
    one('00264000', Deck.comment(
        "STL IS BITS 25-31, SO BYTE 3, NOT BYTE 0. THE VALUE IS UNCHANGED: "
        "ESA/390 COUNTS THE SEGMENT TABLE IN 64-BYTE UNITS MINUS ONE, EXACTLY AS "
        "S/370 DID, AND ONLY THE MEANING OF A UNIT MOVES -- 1 MB TO 16 MB. SAFE "
        "IN BYTE 3 BECAUSE THE TABLE IS 4096-ALIGNED, SO BITS 20-31 OF THE "
        "STORED ADDRESS ARE ZERO AND THE S BIT STAYS CLEAR. I-129.") + [
        "         STC   R15,VMSEG+3    AND STORE IN THE STL FIELD.",
    ])

    # An invalid STE is bit 26 now, not bit 31.
    one('00287000', [
        "ALLNG    LA    R15,SEGINVAL   INVALID STE INDICATOR",
    ])

    # The index into the segment table.  L R6,VMSEG carries STL in the low bits,
    # and the LA 0(R3,R6) below cannot strip it.
    one('00297000', [
        "         L     R6,VMSEG       GET SEGTABLE ORIGIN",
        "         N     R6,=A(SEGSTOM) NO LENGTH -- LA CANNOT",
        "*                             STRIP IT FROM THE LOW BITS",
    ])
    # Page number to segment number: 256 pages per segment, not 16.
    one('00299000', [
        "         SRL   R3,8           DROP THE PAGE NUMBER",
    ])

    # ---------------------------------------------------- BLDRPAGE, per segment
    one('00305400', [
        "         LA    R4,256         LOAD R4 WITH CONSTANT 256",
    ])
    one('00308000', [
        "BLDRPAGE LA    R4,256         LOAD THE CONSTANT 256",
    ])
    one('00309100', [
        "         L     R15,SEGPTO     IS THERE A PAGTABLE PTR",
        "         N     R15,=A(SEGPTOM) ...",
    ])
    one('00309305', [
        "         TM    SEGPTO+3,SEGINVAL IF NOT, MAKE SURE IT'S",
    ])
    one('00309700', [
        "         TM    SEGPTO+3,SEGENQ IS SEGMENT ENQUEUED?",
    ])
    # A full page table is PTL 15 in the low nibble of byte 3, where S/370 had
    # X'F0' in byte 0.  TM tests bits, so the branch becomes BO.
    one('00321000', [
        "         TM    SEGPTO+3,SEGPTLF 256 PAGES IN SEG ALREADY?",
    ])
    one('00323000', [
        "         BO    SKIPBLD        YES - THEN NO NEED TO BUILD",
    ])
    one('00325000', [
        "FORCE16  LA    R5,256         BUILD 256 PAGE TABLE ENTRIES",
    ])
    one('00327000', [
        "         N     R2,=A(SEGSTOM) STRIP LENGTH -- LOW BITS",
    ])
    # The ABI split, produced here and consumed in DMKBLDRL.  See the docstring.
    one('00332000', [
        "         SLL   R1,24          MOVE BEG SEG NUM TO FRET.",
    ])
    one('00333000', [
        "         SLL   R2,8           ENDING SEGMENT NUMBER",
    ])

    # The allocation.  PAGBMP is 3112 bytes now, 389 doublewords exactly, and the
    # page table inside it must start on a 64-byte boundary -- which DMKFREE does
    # not promise, so the block is over-allocated by 7 doublewords and rounded.
    one('00342200', Deck.comment(
        "SEVEN MORE DOUBLEWORDS SO PAGPFRA CAN BE ROUNDED TO A 64-BYTE "
        "BOUNDARY. AN ESA/390 PAGE TABLE ORIGIN IS BITS 1-25 WITH SIX ZEROS "
        "APPENDED; DMKFREE PROMISES DOUBLEWORDS AND NOTHING MORE, AND AN S/370 "
        "PAGE TABLE NEEDED ONLY EIGHT, WHICH IS WHY THERE WAS NO ROUNDING HERE "
        "BEFORE.") + [
        "         SRL   R0,3           OBTAIN NUMBER OF DOUBLEWORDS",
        "         AL    R0,F7          PLUS 7 TO ALIGN PAGPFRA TO 64",
    ])
    one('00343600', Deck.comment(
        "ROUND THE BLOCK SO THAT PAGPFRA, NOT THE HEADER, LANDS ON 64. THE "
        "DMKFREE ADDRESS GOES IN PAGORIG BELOW, BECAUSE THE GAP IS NO LONGER "
        "THE CONSTANT 16 THAT DMKBLDRL SUBTRACTS. I-130.") + [
        "         LR    R7,R1          DMKFREE ADDRESS",
        "         AL    R7,=A(PAGPFRA-PAGSTMP+63) ROUND UP",
        "         N     R7,=A(SEGPTOM) TO A 64-BYTE BOUNDARY",
        "         S     R7,=A(PAGPFRA-PAGSTMP) BACK TO HEADER",
    ])
    # XC PAGACT(12) cleared through PAGSWP.  The header is longer now, and the
    # literal 12 becomes a computed length so it stays right.  PAGORIG is stored
    # after the clear, not before.
    one('00346100', [
        "         XC    PAGACT(PAGPFRA-PAGACT),PAGACT CLEAR HDR",
        "         ST    R1,PAGORIG     EXACT DMKFREE ADDRESS, FOR FRET",
    ])
    # 256 fullword entries of X'00000400'.  MVC propagation cannot do it: 255
    # entries is 1020 bytes and MVC's limit is 256.
    one('00346600', Deck.comment(
        "INVALIDATE ALL 256 ENTRIES. THE OLD FORM WAS MVC PAGCORE,F8+2 THEN MVC "
        "PAGCORE+2(15*2),PAGCORE -- A ONE-BYTE-OVERLAP PROPAGATE. 255 FULLWORD "
        "ENTRIES IS 1020 BYTES AND MVC STOPS AT 256, SO IT BECOMES A LOOP. "
        "PAGINVW IS DERIVED FROM PAGINV, SO IF THE INVALID BIT EVER MOVES AGAIN "
        "THE FULLWORD FORM FOLLOWS IT.") + [
        "         LA    R0,256         ENTRIES IN A FULL PAGE TABLE",
        "         LA    R2,PAGPFRA     FIRST ENTRY",
        "         L     R15,=A(PAGINVW) AN INVALID PTE",
        "BLDRPTE  ST    R15,0(,R2)     INVALIDATE ONE ENTRY",
        "         LA    R2,4(,R2)      NEXT ENTRY",
        "         BCT   R0,BLDRPTE     ALL OF THEM",
    ], to='00347100')
    one('00348100', [
        "         LA    R2,PAGPFRA     LOAD ADR OF PTE",
    ])
    # The STE, built in a register and stored once.  Byte 3 holds two PTO bits as
    # well as I, C and PTL, so STC into it would destroy part of the address.
    one('00348600', Deck.comment(
        "BUILD THE WHOLE ENTRY IN A REGISTER AND STORE IT ONCE. BYTE 3 OF AN "
        "ESA/390 STE HOLDS PTO BITS 24-25 AS WELL AS I, C AND PTL, SO A STC "
        "INTO IT WOULD DESTROY PART OF THE PAGE TABLE ADDRESS. THE ADDRESS "
        "NEEDS NO SHIFTING: PTO IS BITS 1-25 WITH SIX ZEROS APPENDED, SO A "
        "64-BYTE-ALIGNED ADDRESS IS ALREADY IN PLACE.") + [
        "         LR    R15,R4         NUMBER OF PAGES LESS ONE",
        "         SRL   R15,4          PTL COUNTS 16 ENTRIES AT A TIME",
        "         OR    R15,R2         PAGE TABLE ORIGIN, 64-ALIGNED",
        "         O     R15,=A(SEGINVAL) NO PAGES IN CORE YET",
        "         ST    R15,SEGPTO     ONE STORE, NO READ-MODIFY-WRITE",
    ], to='00350600')
    one('00351600', [
        "         LA    R8,PAGPFRA+256*L'PAGPFRA SWAP TABLE",
    ])
    one('00372000', [
        "SKIPBLD  LA    R6,SEGPTO+4    POINT TO NXT STE",
    ])
    # F16 here is PAGES PER SEGMENT, not the header size it means at 00632600.
    # Same spelling, same module, opposite conversions.  I-130.
    one('00373000', [
        "         S     R5,=F'256'     SUBTRACT 256 FROM NO. PAGES",
    ])

    # ------------------------------------------------- the VIRT=REAL builder
    one('00396100', ["         USING PAGPFRA,R8"])
    # R4 carries the PTE value.  In S/370 that is pageno<<4, which is what the
    # halfword PTE holds; in ESA/390 the fullword PTE masked with PAGPFRM IS the
    # page's real address, so R4 steps by 4096.  4096 does not fit an LA
    # displacement -- 4095 is the most -- so both sites become AL/L on a literal.
    one('00400000', Deck.comment(
        "R4 IS THE PTE VALUE, NOT A PAGE NUMBER. AN ESA/390 PTE MASKED WITH "
        "PAGPFRM IS THE PAGE'S REAL ADDRESS, SO IT STEPS BY 4096 WHERE THE "
        "S/370 HALFWORD STEPPED BY 16. 4096 WILL NOT FIT AN LA DISPLACEMENT.") + [
        "         L     R4,=F'4096'    PAGE 1'S REAL ADDRESS",
    ])
    one('00404000', [
        "         L     R7,VMSEG       GET SEGMENT TABLE ADDRESS",
        "         N     R7,=A(SEGSTOM) WITHOUT THE LENGTH",
    ])
    one('00404100', [
        "         NI    SEGPTO+3,255-SEGINVAL CLEAR INVALID BIT",
    ])
    one('00405000', [
        "         L     R8,SEGPTO      LOAD ADDRESS OF PAGE TABLE",
    ])
    one('00406000', [
        "         N     R8,=A(SEGPTOM) CLEAR OUT NUMBER OF PAGES",
    ])
    one('00407100', [
        "         LA    R9,PAGPFRA+256*L'PAGPFRA+8 1ST SWAPTABLE",
    ])
    # PTL is the low nibble of byte 3 and counts units of 16 entries, where
    # SEGPLEN was the high nibble of byte 0 and counted pages.
    PTL = lambda r, what: Deck.comment(
        "PTL IS THE LOW NIBBLE OF BYTE 3 AND COUNTS UNITS OF 16 ENTRIES; "
        "SEGPLEN WAS THE HIGH NIBBLE OF BYTE 0 AND COUNTED PAGES. SO THE "
        "VALUE IS (PTL+1)*16-1 WHERE IT USED TO BE A SHIFT.") + [
        "         IC    R%s,SEGPTO+3    %s" % (r, what),
        "         N     R%s,=A(SEGPTLF) KEEP ONLY PTL" % r,
        "         LA    R%s,1(,R%s)      UNITS OF 16 ENTRIES" % (r, r),
        "         SLL   R%s,4           PAGES IN THIS SEGMENT" % r,
        "         BCTR  R%s,0           LESS ONE, AS BEFORE" % r,
    ]
    one('00411000', PTL('5', 'NO. PAGES IN THIS SEG'), to='00412000')
    one('00414100', [
        "         LA    R8,PAGPFRA+L'PAGPFRA SKIP PAGE 0'S ENTRY",
    ])
    one('00423200', [
        "         ST    R4,PAGPFRA     STORE REAL PAGE ADDRESS",
    ])
    one('00428100', [
        "         LA    R8,PAGPFRA+L'PAGPFRA NEXT PAGE TABLE ENTRY",
    ])
    one('00431000', [
        "         AL    R4,=F'4096'    INCREMENT THE PAGE ADDRESS",
    ])
    one('00433100', [
        "         NI    SEGPTO+3,255-SEGINVAL CLEAR INVALID BIT",
    ])
    one('00434000', PTL('5', 'NO. PAGES IN THIS SEG'), to='00435000')
    one('00437000', [
        "         L     R8,SEGPTO      ADDRESS OF THIS PAGE TABLE",
    ])
    one('00438000', [
        "         N     R8,=A(SEGPTOM) CLEAR OUT PAGE NUMBER",
    ])
    # S R9,F4 reaches PAGSWP by assuming it sits four bytes below the page
    # table.  PAGORIG moved PAGPFRA, so the literal becomes the difference the
    # assembler computes.  Both sites are silent: neither names a DAT field.
    one('00440000', [
        "         S     R9,=A(PAGPFRA-PAGSWP) TABLE SO THAT THE SWAP",
    ])
    one('00447000', [
        "         L     R8,SEGPTO      LOAD ADDRESS OF PAGE 0",
    ])
    one('00448000', [
        "         N     R8,=A(SEGPTOM) CLEAR THE FLAG BITS",
    ])
    one('00450000', [
        "         S     R9,=A(PAGPFRA-PAGSWP) PAGE 0.",
    ])
    # SRL R1,8 produced a value used TWICE -- as a CORTABLE index of 16 bytes a
    # page AND as the S/370 PTE, both being address>>8.  The ESA/390 PTE wants
    # the address itself, so the two uses separate.
    one('00454100', Deck.comment(
        "SRL R1,8 SERVED TWO PURPOSES AT ONCE: A CORTABLE INDEX OF 16 BYTES A "
        "PAGE, AND THE S/370 PTE, WHICH IS PAGENO*16. BOTH ARE ADDRESS/256. AN "
        "ESA/390 PTE IS THE ADDRESS ITSELF, SO THE TWO USES SEPARATE AND THE "
        "ADDRESS IS RELOADED HERE. R0 IS SCRATCH -- THE NEXT CARD LOADS IT.") + [
        "         L     R0,=A(DMKSLC-4096)  PAGE 0'S REAL ADDRESS",
        "         ST    R0,PAGPFRA     STORE ADDRESS OF REAL PAGE 0",
    ])

    # ---------------------------------------------------------- DMKBLDRL
    one('00598100', [
        "         N     R6,=A(SEGSTOM) STRIP LENGTH -- LOW BITS NOW",
    ])
    one('00601000', [
        "         LA    R4,SEGINVAL    LOAD UNUSED SEGMENT INDICATOR",
    ])
    # The ABI split: twelve bits of page number, 8+4 for 64 KB segments and 4+8
    # for 1 MB ones.  Four literals, none of them naming a field.
    one('00605300', [
        "         SRL   R8,24          GET STARTING STE NUMBER",
    ])
    one('00607100', [
        "         N     R15,=A(X'FF0000') PAGE WITHIN SEG. = 0?",
    ])
    one('00610600', [
        "         SRL   R9,8           ENDING SEG. NUMBER TO LOW R9",
    ])
    one('00611100', [
        "         N     R9,F15         CLEAR ALL BUT SEGMENT NUMBER",
    ])
    one('00618000', [
        "RELRLOOP L     R7,SEGPTO      LOAD PAGE TABLE ADDRESS",
    ])
    one('00619100', [
        "         N     R7,=A(SEGPTOM) CLEAR THE FLAG BITS",
    ])
    one('00619300', [
        "         L     R15,SEGPTO     IS THERE A PAGETABLE PTR",
        "         N     R15,=A(SEGPTOM) ...",
    ])
    one('00619505', [
        "         TM    SEGPTO+3,SEGINVAL IF NOT, MAKE SURE IT'S",
    ])
    one('00621000', PTL('2', 'PAGE TABLE LENGTH'), to='00622000')
    one('00624100', ["         USING PAGPFRA,R7"])
    one('00625100', [
        "         L     R0,PAGPFRA     PTE",
    ])
    one('00625600', [
        "         N     R0,=A(PAGPFRM) CHECK FOR REAL PAGE ALLOCATED",
    ])
    one('00627600', [
        "         LA    R7,PAGPFRA+L'PAGPFRA NEXT PAGE TABLE ENTRY",
    ])
    one('00630600', [
        "         L     R1,SEGPTO      GET PAGETABLE POINTER",
    ])
    one('00631100', [
        "         ST    R4,SEGPTO      CLEAR STE ENTRY",
    ])
    # The FRET.  PAGORIG holds the exact DMKFREE address, so the arithmetic that
    # assumed a constant 16 -- and the mask that truncated to 24 bits while
    # claiming to clear a flag -- both go.  I-122, I-130.
    one('00632100', [
        "         N     R1,=A(SEGPTOM) THE PAGE TABLE ADDRESS",
    ])
    one('00632600', Deck.comment(
        "PAGORIG HOLDS WHAT DMKFREE RETURNED, SO THE RELEASE IS EXACT RATHER "
        "THAN DERIVED. THIS RETIRES N R1,=A(X'FFFFFE'), WHICH TRUNCATED A PAGE "
        "TABLE ADDRESS TO 24 BITS WHILE ITS COMMENT CLAIMED TO CLEAR A FLAG. "
        "I-122.") + [
        "         S     R1,=A(PAGPFRA-PAGORIG) BACK UP TO PAGORIG",
        "         L     R1,0(,R1)      THE DMKFREE ADDRESS, EXACTLY",
    ], to='00633100')
    one('00634100', [
        "         SRL   R0,3           OBTAIN NUMBER OF DOUBLEWORDS",
        "         AL    R0,F7          AND THE ALIGNMENT SLACK",
    ])
    one('00643000', [
        "RELRNEXT LA    R6,SEGPTO+4    POINT TO NEXT STE",
    ])
    one('00649000', [
        "         N     R1,=A(SEGSTOM) STRIP THE LENGTH,",
    ])
    one('00651000', [
        "         N     R0,=A(SEGSTLM) NO. OF SEGMENT TABLES (LESS 1)",
    ])
    one('00653000', [
        "         AL    R0,=F'519'     PLUS 8, PLUS 511 FOR ALIGNMENT",
    ])
    return d


# ---------------------------------------------------------------------------
# ESA/390 storage keys at 4 KB.  I-177, wall 18.
#
# System/370 keys cover 2 KB, so CP keys a 4 KB page as TWO halves and keeps
# TWO key bytes per page in the swap table -- `SWPKEY1  VIRTUAL STORAGE KEY,
# 1ST 2048 BYTES` and `SWPKEY2 ... 2ND 2048 BYTES`.  The ESA/390 PoO gives the
# 370-XA facilities "key-controlled protection on only 4K-byte blocks", so each
# pair of `SSK`s becomes one `SSKE` and the arithmetic that moved from one key
# byte to the other goes with it.  That is I-128's structural law again: S/370
# packed two things where ESA/390 has one slot.
#
# This is a SEPARATE deck from the DAT work even though DMKPTR carries both,
# because the two axes fail differently and a bisect wants them apart: DAT
# errors give a plausible wrong address, a missed key gives an operation
# exception at a named instruction.
#
# `ISKE`, `SSKE` and `RRBE` are already in XAOPS.MACRO and already proven by
# execution in `11-storage-keys.rc`, and `DMKCPI.XA0013DK` has been running an
# `SSKE` since I-104.  So this is not new ground, only unfinished ground.
KEYMODS = {

    # The abend that opened wall 18, and the one site where the two keys can
    # genuinely DIFFER -- they are the guest's own keys for the two halves.
    # Collapsing them has to choose, and the choice is guest-visible through
    # ISKE, which is R-12 and belongs with M4.  SWPKEY1 is kept: it is the
    # first half's key, so a guest that set both halves the same -- which is
    # every guest CP itself creates -- sees no change at all.
    'DMKPTR': [
        ('00643000', '00645000', Deck.comment(
            "WAS SSK R3,R8 / SRL R3,8 / SSK R3,R6 -- THE 2ND HALF PAGE'S KEY "
            "THEN THE 1ST. AN ESA/390 KEY COVERS THE WHOLE 4 KB PAGE, SO THE "
            "PAIR BECOMES ONE SSKE AND THE SHIFT BETWEEN THEM IS NOW THE "
            "SELECTION OF WHICH KEY SURVIVES. SWPKEY1 IS KEPT, THE FIRST "
            "HALF'S. A GUEST THAT SET ITS TWO HALVES DIFFERENTLY CANNOT BE "
            "REPRESENTED AT ALL -- THAT IS R-12, GUEST-VISIBLE THROUGH ISKE, "
            "AND BELONGS WITH M4. RECORDED HERE SO THE CHOICE IS NOT MISTAKEN "
            "FOR AN EQUIVALENCE. R8 STILL CARRIES THE 2ND-HALF ADDRESS FROM "
            "00640000 AND IS NOW UNUSED; THE LA IS LEFT ALONE SO NO OTHER "
            "REGISTER STATE CHANGES. I-177.") + [
            "         SRL   R3,8           SWPKEY1, THE FIRST HALF'S KEY",
            "         SSKE  R3,R6          ONE KEY FOR THE WHOLE PAGE",
        ]),
        # Here both halves get the SAME key -- `SR R6,R6  SET KEY TO ZERO` two
        # cards up -- so the collapse is exact and loses nothing.  R5 keeps the
        # second half's address and goes unused, same as R8 above.
        ('00939000', '00940000', Deck.comment(
            "WAS SSK R6,R7 / SSK R6,R5 -- FIRST 2K THEN SECOND 2K, BOTH WITH "
            "THE KEY ZEROED BY SR R6,R6 AT 00937000. ONE KEY, ONE "
            "INSTRUCTION, AND NOTHING IS LOST BECAUSE BOTH HALVES WERE "
            "ALREADY BEING SET THE SAME. I-177.") + [
            "         SSKE  R6,R7          ZERO KEY, WHOLE 4 KB PAGE",
        ]),
        # DMKPTR's four ISK sites are both READ pairs, so they convert the
        # same way as everyone else's and do NOT wait for the RRB work.  In
        # each, the mask below the pair tests the same bit in both byte
        # positions -- SWPREF2*256+SWPREF2 at 01016000, =A(X'00000202') at
        # 02069260 -- and with one key the register holds it twice, so both
        # masks still test exactly what they say.  I-192.
        ('01012000', Deck.comment(
            "ISK PAIR, READ. THE LA R14,2048(,R6) BETWEEN THEM STILL NAMES "
            "THIS PAGE, SO BOTH ISKES RETURN ITS ONE KEY AND 01016000'S "
            "SWPREF2*256+SWPREF2 MASK FINDS IT IN BOTH BYTES. I-192.") + [
            "         ISKE  R15,R6         GET STORAGE KEY",
        ]),
        ('01015000', [
            "         ISKE  R15,R14        GET OTHER STORAGE KEY",
        ]),
        # ------------------------------------------------- the eleven RRBs
        # R-12 decided (23-STORAGE-KEYS.md): one real reference/change pair for
        # 4 KB, reported for BOTH half-page back-up keys.  Over-reporting a
        # reference or a change costs a page write; under-reporting would lose
        # data, and cannot happen here.
        #
        # What makes these tractable after all is that the branch targets are
        # LABELS -- STKEY2, STKEY2+4, TSTRRB2, NONZERO -- so the assembler
        # recomputes them when instructions disappear.  The six `*+8` offsets
        # are the exception, and each becomes a named label, which is R-26's
        # standing instruction rather than a nicety: a `*+8` that skipped one
        # OI must skip two now.
        #
        # RRB is S-format and four bytes; the RRBE macro emits four.  So a
        # first RRB is a same-length swap and only the SECOND of each pair
        # goes, because with one key it would read the state the first one just
        # reset -- which would under-report, the direction that matters.
        ('01021000', '01026000', Deck.comment(
            "WAS RRB 0(R6) / BZ *+8 / OI SWPKEY1,4 / RRB 2048(R6) / BZ *+8 / "
            "OI SWPKEY2,4. ONE KEY, SO ONE RRBE, AND ITS RESULT GOES TO BOTH "
            "BACK-UP KEYS. THE BZ NOW HAS TWO OIS TO SKIP INSTEAD OF ONE, SO "
            "*+8 BECOMES THE LABEL NOBKUP1 RATHER THAN *+12 -- R-26. I-192.") + [
            "         RRBE  0,R6           ONE KEY FOR THE WHOLE PAGE",
            "         BZ    NOBKUP1        NO BITS TO BACK UP",
            "         OI    SWPKEY1,4      VIRT. BACK-UP KEY",
            "         OI    SWPKEY2,4      BOTH HALVES, ONE REAL KEY",
            "NOBKUP1  DS    0H                                   ",
        ]),
        # DORRB.  A page is selectable only if the reference bit was off AND no
        # back-up reference bit is set; the change bits are OR'd for the later
        # test.  With one key the first RRBE answers for the whole page, so the
        # second RRB and the BC that tested it both go.  STKEY2 stays ON the
        # OI SWPKEY2 card so that STKEY2+4 still names the NI below it -- two
        # branches reach that address, 01306000's (which goes) and 01323000's
        # (which stays).
        ('01302000', '01308000', Deck.comment(
            "WAS RRB 0(R6) / BC 8+4,TSTRRB2 / OI SWPKEY1,4 / RRB 2048(R6) / "
            "BC 8+4,STKEY2+4 / STKEY2 DS 0H / OI SWPKEY2,4. THE SECOND RRB "
            "AND ITS BC GO; THE FALL-THROUGH NOW BACKS UP BOTH HALVES FROM "
            "THE ONE RESULT. STKEY2 MOVES ONTO THE OI SO STKEY2+4 STILL "
            "NAMES THE NI AT 01309000, WHICH 01323000 BRANCHES TO. I-192.") + [
            "         RRBE  0,R6           ONE KEY FOR THE WHOLE PAGE",
            "         BC    8+4,TSTRRB2    REF OFF, PAGE IS A CANDIDATE",
            "         OI    SWPKEY1,4      REF. BIT TO VIRT. BACK-UP KEY",
            "STKEY2   OI    SWPKEY2,4      AND THE SECOND HALF, ONE KEY",
        ]),
        # TSTRRB2's second RRB tested the other half's reference bit, which
        # cannot be set here: the BC that reached this label established that
        # the page's reference bit was off, and there is only one now.  So the
        # RRB and the BC 2+1 both go, and BALR R15,R0 parks the SAME condition
        # code R14 already holds -- which is what OR R14,R15 at 01323100 then
        # combines, idempotently.
        ('01318000', '01321000', Deck.comment(
            "WAS BALR R14,0 / RRB 2048(R6) / BC 2+1,STKEY2 / BALR R15,R0. "
            "THE RRB READ THE SECOND HALF'S REFERENCE BIT AND THE BC ACTED "
            "ON IT; WITH ONE KEY THE BRANCH THAT REACHED HERE ALREADY PROVED "
            "IT OFF, SO NEITHER CAN FIRE. BOTH BALRS STAY AND NOW PARK THE "
            "SAME CONDITION CODE, WHICH IS WHAT OR R14,R15 COMBINES. "
            "I-192.") + [
            "         IPM   R14            SAVE C.C. FOR CHANGE TEST I-228",
            "         IPM   R15            ONE KEY, SO THE SAME C.C.",
        ]),
        ('01461000', '01466000', Deck.comment(
            "BCHNGE. WAS RRB 0(R6) / BC 8+2,*+8 / OI SWPKEY1,2 / RRB "
            "2048(R6) / BC 8+2,*+8 / OI SWPKEY2,2 -- WHICH OF THE TWO KEYS "
            "WAS CHANGED. THERE IS ONE, AND ITS CHANGE BIT APPLIES TO BOTH "
            "HALVES. THE *+8 BECOMES NOCHGBK, R-26. I-192.") + [
            "         RRBE  0,R6           ONE KEY FOR THE WHOLE PAGE",
            "         BC    8+2,NOCHGBK    NOT CHANGED",
            "         OI    SWPKEY1,2      BACK-UP CHANGE BITS",
            "         OI    SWPKEY2,2      BOTH HALVES, ONE REAL KEY",
            "NOCHGBK  DS    0H                                   ",
        ]),
        ('01987000', '01994000', Deck.comment(
            "WAS RRB 0(R1) / BALR R14,0 / BC 8+4,*+8 / OI SWPKEY1,4 / RRB "
            "2048(R1) / BALR R15,0 / BC 8+4,*+8 / OI SWPKEY2,4. BOTH BALRS "
            "STAY AND PARK THE SAME CONDITION CODE, WHICH IS WHAT OR R14,R15 "
            "AT 01998000 COMBINES AND SPM R14 AT 02001000 RESTORES. THE TWO "
            "*+8 OFFSETS BECOME ONE LABEL, NOREFBK, R-26. I-192.") + [
            "         RRBE  0,R1           ONE KEY FOR THE WHOLE PAGE",
            "         IPM   R14            SAVE CONDITION CODE, I-228",
            "         IPM   R15            ONE KEY, SO THE SAME C.C.",
            "         BC    8+4,NOREFBK    REF WAS OFF, NOTHING TO BACK UP",
            "         OI    SWPKEY1,4      REF. BIT RESET, BACK-UP TO VIRT",
            "         OI    SWPKEY2,4      BOTH HALVES, ONE REAL KEY",
            "NOREFBK  DS    0H                                   ",
        ]),
        ('02019000', '02024000', Deck.comment(
            "WAS RRB 0(R1) / BC 8+2,*+8 / OI SWPKEY1,2 / RRB 2048(R1) / BC "
            "8+2,*+8 / OI SWPKEY2,2. SAME SHAPE AS 01461000, REACHED FROM "
            "THE OTHER SIDE OF SPM R14 AT 02015000. THE *+8 BECOMES "
            "NOCHGB2, R-26. I-192.") + [
            "         RRBE  0,R1           ONE KEY FOR THE WHOLE PAGE",
            "         BC    8+2,NOCHGB2    NOT CHANGED",
            "         OI    SWPKEY1,2      REAL CHANGE BIT TO VIRT. BACKUP",
            "         OI    SWPKEY2,2      BOTH HALVES, ONE REAL KEY",
            "NOCHGB2  DS    0H                                   ",
        ]),
        ('02069220', Deck.comment(
            "ISK PAIR, READ, IN THE DMKVMA SCAN ADDED BY VA07230. SAME "
            "SHAPE AND SAME REASONING AS 01012000. I-192.") + [
            "         ISKE  R0,R2          LOAD FIRST KEY",
        ]),
        ('02069250', [
            "         ISKE  R0,R2          LOAD SECOND KEY",
        ]),
    ],

    # Wall 21's likely next stop.  CHKFETCH at 01157000 runs on every channel
    # program that touches fetch-protected storage, and CCWCHKEY at 03631000 on
    # every one that has a CAW key at all -- so these are reached as soon as a
    # virtual machine does I/O, which is the next thing AUTOLOG1 will do.
    # I-192.
    'DMKCCW': [
        # The two SSK pairs are the WRITE case, so the pair cannot simply be
        # left in place the way DMKPSACC's read pair was: the two SSKs come
        # from two DIFFERENT bytes.  SWPFLAG holds a packed halfword of two
        # keys -- masked X'F8F8' one card up -- and the original sets the low
        # byte into the second half, shifts right eight, and sets the high byte
        # into the first.  One key now, so the shift stops being a reposition
        # and becomes the choice of which byte survives: SWPKEY1, the first
        # half's, exactly as I-177 chose in DMKPTR.
        ('00973000', '00979000', Deck.comment(
            "WAS N R15,=A(X'F8F8') / N R14,XPAGNUM / LA R14,2048(,R14) / SSK "
            "R15,R14 / SRL R15,8 / N R14,XPAGNUM / SSK R15,R14 -- THE SECOND "
            "HALF PAGE'S KEY FROM THE LOW BYTE, THEN THE FIRST FROM THE HIGH "
            "BYTE. ONE ESA/390 KEY COVERS THE WHOLE PAGE, SO THE SHIFT NOW "
            "SELECTS RATHER THAN REPOSITIONS AND SWPKEY1 IS KEPT. R14 STILL "
            "ENDS ON THE PAGE START, WHICH 00980000'S LR R10,R14 NEEDS. THE "
            "X'F8F8' MASK IS LEFT AS IT IS: IT CLEARS REFERENCE AND CHANGE IN "
            "BOTH BYTES AND ONLY ONE OF THEM IS READ NOW, SO IT IS HARMLESS "
            "AND IT KEEPS THE SWAP TABLE'S FORMAT INTACT. I-192.") + [
            "         N     R15,=A(X'F8F8') CLEAR CHANGE/REFERENCE BITS",
            "         N     R14,XPAGNUM    CLEAR DISPLACEMENT",
            "         SRL   R15,8          SWPKEY1, THE FIRST HALF'S KEY",
            "         SSKE  R15,R14        ONE KEY FOR THE WHOLE PAGE",
        ]),
        # CHKFETCH.  Mnemonic only: N R15,F8 below it isolates the
        # fetch-protect bit, which ISKE returns in the same place, and
        # X2048BND above it stays because ISKE takes its block from bits 1-19
        # and ignores bits 20-31 -- where ISK demanded zeros or took a
        # specification exception.
        ('01157000', [
            "         ISKE  R15,R15       GET THE REAL STORAGE KEY",
        ]),
        # CKSHRCHG reads the change bit in each half and branches the same way
        # on either.  With one key the second read returns the same byte and
        # sets the same condition code, so the pair is left in place: it is
        # behaviour-preserving, and NXTKEY is a branch target at 01190000 that
        # collapsing would have to re-aim.  Both reads converted.
        ('01180000', [
            "         ISKE  R15,R15       GET THE REAL STORAGE KEY",
        ]),
        ('01192000', [
            "         ISKE  R15,R15       GET THE REAL STORAGE KEY",
        ]),
        ('03584000', '03589000', Deck.comment(
            "THE SAME PACKED-HALFWORD PAIR AS 00973000, IN THE OTHER COPY OF "
            "THIS ROUTINE. R14 ARRIVES AS THE PAGE START AND MUST LEAVE AS "
            "ONE -- 03592000'S OR R1,R14 BUILDS THE REPLACEMENT PAGE ADDRESS "
            "FROM IT -- SO THE N R14,XPAGNUM IS KEPT EVEN THOUGH THE LA THAT "
            "MADE IT NECESSARY IS GONE. I-192.") + [
            "         N     R15,=A(X'F8F8') CLEAR CHANGE/REFERENCE BITS",
            "         SRL   R15,8          SWPKEY1, THE FIRST HALF'S KEY",
            "         N     R14,XPAGNUM    BACK TO BEGINING ADDRESS",
            "         SSKE  R15,R14        ONE KEY FOR THE WHOLE PAGE",
        ]),
        # CCWCHKEY.  Mnemonic only; N R15,F240 isolates the access-control
        # key, which ISKE returns in bits 24-27 exactly as ISK did.
        ('03631000', [
            "         ISKE  R15,R15       GET THE REAL STORAGE KEY",
        ]),
    ],

    # -------------------------------------------------------------------
    # The mnemonic-only sites, and the reason there are so many of them.
    #
    # The half-page idiom is always `op Rx,Ry` / `LA Ry,2048(,Ry)` /
    # `op Rx,Ry`.  The second operand still names the SAME 4 KB page -- 2048
    # is inside it -- and ISKE and SSKE take their block from bits 1-19 and
    # IGNORE bits 20-31, where ISK and SSK required bits 29-31 to be zero or
    # took a specification exception.  So under ESA/390 the second operation
    # reads or writes the same key byte as the first.
    #
    # For a READ pair that makes the second ISKE a redundant repeat: it returns
    # the same key and sets the same condition code, so the pair is
    # behaviour-preserving with nothing but the mnemonic changed, and any mask
    # that tests both byte positions -- DMKVMA's CHGBITS of X'00000202',
    # DMKMCH's =A(X'202') -- still works, because the register now holds the
    # same key in both halves.  For a WRITE pair it depends on where the two
    # written values come from: if they are the same byte, as in DMKCDS, the
    # second SSKE rewrites what the first wrote; if a shift sits between them,
    # as in DMKCCW and DMKDGD, they are DIFFERENT bytes of a packed halfword
    # and the pair must genuinely collapse.
    #
    # That is why these are one-word edits and DMKCCW's and DMKDGD's are not.
    # Leaving the redundant operation in place is deliberate: it keeps each
    # site reviewable in isolation, and removing dead instructions shifts the
    # `BZ *+8` offsets around them, which is its own way of going wrong.
    'DMKCFH': [
        # Reads two keys into a halfword to hand to the guest, which is the
        # display format DMKCFH's buffer wants.  One key, shown for both.
        ('00350000', Deck.comment(
            "ISK PAIR, READ. THE A R15,=F'2048' BETWEEN THEM STILL NAMES THIS "
            "PAGE, SO BOTH ISKES RETURN ITS ONE KEY AND THE OR AT 00354000 "
            "BUILDS THE SAME HALFWORD SHAPE AS BEFORE. I-192.") + [
            "         ISKE  R14,R15       GET THE PRESENT KEY",
        ]),
        ('00353000', [
            "         ISKE  R14,R15       GET PRESENT KEY FOR THAT HALF",
        ]),
    ],
    'DMKDIB': [
        ('01145000', [
            "         ISKE  R1,R1          GET THE REAL STORAGE KEY",
        ]),
    ],
    'DMKUNT': [
        ('00473000', [
            "         ISKE  R15,R15       GET REAL STORAGE KEY",
        ]),
    ],
    'DMKVCA': [
        ('01634000', [
            "         ISKE  R1,R1          GET REAL STORAGE KEY",
        ]),
    ],
    'DMKVMA': [
        ('00209000', Deck.comment(
            "ISK PAIR, READ. CHGBITS IS X'00000202' AND TESTS THE CHANGE BIT "
            "IN BOTH BYTE POSITIONS; WITH ONE KEY R0 HOLDS IT TWICE, SO THE "
            "MASK IS STILL CORRECT AND STILL TESTS WHAT IT SAYS. I-192.") + [
            "         ISKE  R0,R2          TAKE A LOOK AT THE KEY",
        ]),
        ('00212000', [
            "         ISKE  R0,R2          TAKE A LOOK AT THIS HALF",
        ]),
    ],
    'DMKVMD': [
        ('00909000', Deck.comment(
            "ISK PAIR, READ, BUILDING THE KEY HALFWORD DMKVMD DISPLAYS. R1 "
            "ENDS WITH THIS PAGE'S ONE KEY IN BOTH BYTES, WHICH IS THE "
            "HONEST ANSWER: THE 4 KB KEY GOVERNS BOTH 2 KB HALVES. I-192.") + [
            "         ISKE  R1,R2          PUT STORAGE KEY INTO R1",
        ]),
        ('00912000', [
            "         ISKE  R1,R14         SAME KEY, R1 LOW ORDER",
        ]),
    ],
    'DMKMCH': [
        ('00612000', Deck.comment(
            "ISK PAIR, READ. =A(X'202') AT 00615000 TESTS THE CHANGE BIT IN "
            "BOTH BYTES AND R1 NOW HOLDS THE ONE KEY TWICE, SO IT STILL "
            "ANSWERS THE QUESTION IT ASKS. I-192.") + [
            "         ISKE  R1,R2          GET THE FIRST KEY FROM STORAGE",
        ]),
        ('00614000', [
            "         ISKE  R1,R3          GET SECOND KEY FROM STORAGE",
        ]),
        # The SPF exercise loop: set a key and read it back, five times for
        # each of sixteen key values, to decide whether a storage-protection
        # failure is intermittent.  Both halves of the pair act on R3 and
        # neither is the other's source, so each converts on its own.
        ('00829000', [
            "         SSKE  R4,R3          EXECERCISE THE",
        ]),
        ('00830000', [
            "         ISKE  R4,R3          FAILING STORAGE LOCATION",
        ]),
        ('00861000', [
            "         SSKE  R8,R3          RESTORE THE PROPER KEY TO THE",
        ]),
    ],
    'DMKCDS': [
        # A WRITE pair whose two writes come from the SAME byte: R0 is re-read
        # by the second ISKE and masked identically, so the second SSKE writes
        # back exactly what the first wrote.  Mnemonic only.
        ('00882000', Deck.comment(
            "ISK/SSK PAIR. THE SECOND TRIPLE AT 00886000-00888000 RE-READS "
            "AND REWRITES THE SAME KEY BYTE NOW, SO IT IS REDUNDANT RATHER "
            "THAN WRONG, AND =A(X'FFFFF8') STILL CLEARS REFERENCE AND CHANGE "
            "AND KEEPS ACCESS CONTROL AND FETCH-PROTECT. I-192.") + [
            "         ISKE  R0,R14         GET REAL STORAGE KEY",
        ]),
        ('00884000', [
            "         SSKE  R0,R14         SET HARDWARE KEY",
        ]),
        ('00886000', [
            "         ISKE  R0,R14         GET REAL STORAGE KEY",
        ]),
        ('00888000', [
            "         SSKE  R0,R14         SET IN NEW STORAGE KEY",
        ]),
    ],
    'DMKDGD': [
        # The third instance of DMKCCW's packed-halfword write pair, and it
        # has to collapse for the same reason: SRL R5,8 between the two SSKs
        # means they write DIFFERENT bytes.  SWPKEY1 is kept.  R4 must leave as
        # the page start -- 00526000's OR R1,R4 builds the replacement page
        # address from it -- so the N R4,XPAGNUM stays even though the LA that
        # made it necessary is gone.
        ('00519000', '00523000', Deck.comment(
            "WAS LA R4,2048(,R4) / SSK R5,R4 / SRL R5,8 / N R4,XPAGNUM / SSK "
            "R5,R4 -- THE SECOND HALF PAGE'S KEY FROM SWPFLAG'S LOW BYTE, "
            "THEN THE FIRST FROM ITS HIGH BYTE. THE SHIFT NOW SELECTS RATHER "
            "THAN REPOSITIONS AND SWPKEY1 IS KEPT, AS IN DMKCCW 00973000 AND "
            "I-177'S DMKPTR. I-192.") + [
            "         SRL   R5,8           SWPKEY1, THE FIRST HALF'S KEY",
            "         N     R4,XPAGNUM     BACK TO BEGINING ADDRESS",
            "         SSKE  R5,R4          ONE KEY FOR THE WHOLE PAGE",
        ]),
    ],
}


# ---------------------------------------------------------------------------
# The S/370 channel instructions that are left in the NUCLEUS.  I-192, wall 22.
#
# There is exactly one, and finding that out took a corrected instrument.  A
# sweep for `^\s+(TCH|TIO|SIO|...)` reported none anywhere, which was wrong in
# the way `I-168` warns about: the card is
#
#     TCHLOOP  TCH   0(R2)            CHANNEL STATUS?
#
# and a labelled card does not start with whitespace.  Allowing an optional
# label found 33 sites the first pattern had been silently missing, and the
# useful half of that is what it did NOT find: 64 of the 65 are `SIO` and `TIO`
# in DMKDDR, DMKDIR, DMKFMT, DMKLD00E, DMKSAV and DMKSSP, which are STANDALONE
# programs -- they run without CP, in S/370 mode, and the nucleus does not
# contain them.  The 65th is this one.
CHANMODS = {

    # DMKENTTI is VM/MONITOR's I/O utilisation sampler, driven by a timer
    # request block.  It walks the sixteen channel numbers testing each with
    # TCH and counting how many are busy, and the count goes into monitor
    # record MN602CHB and nowhere else -- no control flow anywhere depends on
    # it.  SYSMON AUTO=YES in DMKSYS starts the monitor at every IPL, which is
    # why "MONITOR AUTO STARTING" appears in every boot log and why this is
    # reached within seconds.
    #
    # ESA/390 has no channel to test.  The channel subsystem has subchannels,
    # and "channel busy" is not an observable of the same kind: a path can be
    # busy, a subchannel can be status-pending, but the S/370 notion the
    # sampler counts does not exist.  So the honest conversion is to stop
    # sampling and leave the counters at zero, which reports accurately that
    # the measurement is unavailable -- rather than inventing a number from
    # STSCH across every subchannel, which would be a different measurement
    # wearing this one's name.
    #
    # One card, and it is the same length.  TCH is S-format and four bytes; an
    # unconditional branch is RX and four bytes.  So nothing shifts, the
    # BC 9,NOINCR below it becomes four unreachable bytes, and the loop still
    # steps R1 through the sample fields and ends on C R2,F4096 -- the record's
    # shape and its sample count are untouched.
    'DMKENT': [
        ('00242450', Deck.comment(
            "WAS TCH 0(R2) -- TEST CHANNEL, WHICH ESA/390 DOES NOT HAVE AND "
            "WHICH ABENDED CP WITH PRG001 AT DMKENT+294 WITHIN SECONDS OF "
            "THE MONITOR STARTING. THE LOOP COUNTS BUSY CHANNELS FOR MONITOR "
            "RECORD MN602CHB AND NOTHING ELSE READS IT, SO BRANCHING PAST "
            "THE INCREMENT LEAVES THE COUNTERS AT ZERO AND REPORTS THAT THE "
            "MEASUREMENT IS NOT AVAILABLE. A CHANNEL SUBSYSTEM HAS NO "
            "CHANNEL TO TEST; SYNTHESISING ONE FROM STSCH ACROSS EVERY "
            "SUBCHANNEL WOULD BE A DIFFERENT MEASUREMENT UNDER THIS ONE'S "
            "NAME. B IS FOUR BYTES AND SO IS TCH, SO NOTHING SHIFTS. THE "
            "LABEL TCHLOOP STAYS ON THE CARD -- 00242770 BRANCHES BACK TO "
            "IT, AND REPLCHK CAUGHT ITS LOSS BEFORE THIS EVER ASSEMBLED. "
            "I-192.") + [
            "TCHLOOP  B     NOINCR         NO CHANNEL TO TEST IN ESA/390",
        ]),
    ],
}

# ---------------------------------------------------------------------------
# The name.  I-179.
#
# CE's `HRC370DK` probes for System/380 -- a program-check trap around a `BSM`
# -- and when the probe succeeds it zaps a C'8' over the C'7' of "VM/370" in
# three separate literals, so the system announces itself as VM/380.
#
# This project is not taking that route.  It is a 31-bit ESA/390 conversion on
# the way to 64-bit, so the name is **VM/370+**.  The probe is left in place
# because it records a true fact about the machine in `INSTWRD1` byte 0, but
# nothing may paint that byte over a banner.  Byte 0 is display-only; bytes 1-3
# hold the LDEVCTL pointer used by DMKCFP, DMKGRF and HDKD7C, and `MVI` writes
# only byte 0, so removing the three readers changes no behaviour at all.
#
# DMKCPI's console banner and DMKCNS's "VM/370 Online" are handled in their own
# decks, where the literal and its zap sit in one module.  DMKGRF is different:
# its two zaps write into 3270 logo SCREEN DATA at fixed displacements rather
# than into a named literal, so they are removed and the logo keeps whatever the
# screen tables already say.  Putting the `+` into the logo itself needs the
# FMT77 screen layout and is deliberately left for later -- the point here is
# that nothing says /380 any more, not that everything says /370+.
NAMEMODS = {
    'DMKGRF': [
        ('01705990', Deck.comment(
            "WAS MVC 748(R1,1),INSTWRD1 -- ZAP THE 'VM/370 ONLINE' SCREEN "
            "WITH THE '7' OR '8' CE'S SYSTEM/380 PROBE LEFT IN THE PSA. "
            "THIS IS NOT SYSTEM/380. THE SCREEN TABLES ARE UNTOUCHED, SO "
            "THE LOGO KEEPS ITS OWN TEXT. I-179.") + [
            "         DS    0H             THE ZAP IS GONE",
        ]),
        ('01708960', Deck.comment(
            "AND THE SAME ZAP ON THE BIG LOGO SCREEN. I-179.") + [
            "         DS    0H             THE ZAP IS GONE",
        ]),
    ],
}


def datdeck(module, cards, ident=None):
    """One table-driven deck, with the increment chosen for each replacement.

    Every module after `DMKBLD` and `DMKCPI` is the same shape of work -- rename
    a field, mask a pointer, widen a shift -- so it is a table of replacements
    rather than a routine of its own.  `cards` is a list of
    `(seq, [lines])` or `(seq, to, [lines])`, in ascending anchor order, which
    `UPDATE` requires and `Deck._anchor` enforces.
    """
    d = Deck(ident or XA36)
    src = srcfile(module)
    for item in cards:
        seq, to, lines = (item if len(item) == 3 else (item[0], None, item[1]))
        limit = next_seq(src, to or seq)
        base = int(seq)
        for inc in (100, 10, 1):
            if limit is None or base + inc * len(lines) < int(limit):
                d.replace(seq, to, first=str(base + inc).zfill(8), inc=inc,
                          limit=limit, lines=lines)
                break
        else:
            raise ValueError('%s: no room after %s for %d cards before %s'
                             % (module, seq, len(lines), limit))
    return d


# The small modules, read with block.py and converted by the same rules DMKBLD
# established.  Each entry carries only what it needs; the reasoning common to
# all of them is in docs/27-STE-DESIGN.md.
GUESTMODS = {

    # I-199 / wall 26.  The guest's first instruction under this CP was CMS's
    # IPL text issuing SIO, and it looped on program interrupts.  On S/370 a
    # problem-state SIO is a PRIVILEGED-OPERATION exception (code 2); DMKPRG
    # sends code 2 to DMKPRVLG, GETINST sees opcode 9C-9F and hands it to the
    # virtual I/O executive.  ESA/390 has no SIO: the opcode is undefined and
    # the exception is OPERATION (code 1).  DMKPRG sends code 1 to DMKPRV too,
    # but there `BCT R3,GETINST` routes it to OPSIM, which simulates CS, CDS
    # and EX and otherwise reflects an operation exception to the guest -- whose
    # program-new PSW is zero at IPL time, so PSW 0, opcode 00, and the loop.
    #
    # IBM left the pattern for this at CHEKPROB: SPKA and IPK, which an older
    # machine reports as operation exceptions, are taken "AS IF PRIV OP".  The
    # same door, wider: every S/370 privileged opcode ESA/390 dropped goes the
    # way a privileged-operation exception went, with S/370's semantics kept
    # exactly -- a guest in ITS OWN problem state gets code 2 reflected, not
    # code 1, because that is what the real machine told it.  The set:
    #     08 SSK   09 ISK   B213 RRB   9C SIO/SIOF   9D TIO/CLRIO
    #     9E HIO/HDV   9F TCH/CLRCH
    # INTPR is rewritten to 2 so anything downstream that re-reads the code
    # agrees with the path it is on.  DMKVSIEX and the key simulation then run
    # unchanged; SSK/ISK simulation is the software-key path (R-12), not the
    # real-key one.
    'DMKPRV': [
        ('00535000', [
            "CHEKPROB CLI   VMINST,X'9C'   S/370 I/O OPCODE, 9C-9F?",
            "         BL    CHEKPRB1       NO",
            "         CLI   VMINST,X'9F'   ...",
            "         BNH   S370PRIV       YES, ESA/390 CALLS IT OPERATION",
            "CHEKPRB1 CLI   VMINST,X'08'   SSK?",
            "         BE    S370PRIV       PRIVILEGED ON S/370",
            "         CLI   VMINST,X'09'   ISK?",
            "         BE    S370PRIV       PRIVILEGED ON S/370",
            "         CLC   =X'B213',VMINST RRB?",
            "         BE    S370PRIV       PRIVILEGED ON S/370",
            "         TM    VMPSW+1,PROBMODE VIRTUAL PROBLEM STATE?",
        ]),
        ('00541000', [
            "         B     OPEREXCP       REFLECT OPERATION EXCEPTION",
            "S370PRIV TM    VMPSW+1,PROBMODE GUEST'S OWN PROBLEM STATE?",
            "         BO    PRIVEXCP       YES: S/370 SAID PRIVILEGED OP",
            "         MVI   INTPR+1,X'02'  SO DOES THE REST OF CP, NOW",
            "         B     GETINST        SIMULATE AS A PRIVILEGED OP",
            "PRIVEXCP LA    R0,X'02'       PRIVILEGED-OPERATION EXCEPTION",
            "         B     ERREFLCT       REFLECT IT",
        ]),
        # I-200 / wall 27.  The guest key simulation (ISK, SSK, RRB) finds the
        # page's swap-table entry from the virtual address with S/370 geometry:
        # byte 1 of the address is the 64 KB segment index, the high nibble of
        # byte 2 the page within it.  For CMS's SSK on X'3F000' that is STE 3,
        # which is not built, so the "swap table pointer" is loaded from -12
        # and the key byte X'F0' lands in the PSA -- at X'7A' for the even half
        # page and X'7B' for the odd: the I/O new PSW's bits 16-31.  The next
        # I/O interrupt then loads 000CF0F0 00006698, an early specification
        # exception, PRG006.  Measured at CMS's first instruction (w35): R9=F0,
        # R14=3F000, real X'7A' already F0.
        #
        # 1 MB segments: segment index = address>>20; page within segment =
        # bits 12-19; swap entries are PAGSWPE=8 bytes.  The half-page test on
        # bit 20 (TM 2(R3),X'08') and SWPKEY1/SWPKEY2 are the software 2 KB
        # keys and stay.  The two real key instructions on the same path are
        # the deferred R-12 sites: ISK/SSK become ISKE/SSKE on the 4 KB frame
        # (23-STORAGE-KEYS.md, "R-12 decided"); the SWPKEY1=SWPKEY2 detector
        # is still to come.
        ('00915000', '00917000', [
            "         L     R7,0(,R3)      VIRTUAL ADDRESS",
            "         SRL   R7,20          1 MB SEGMENT INDEX",
            "         SLL   R7,2           SEGMENT TABLE ENTRY INDEX",
        ]),
        ('00924000', '00926000', [
            "         L     R4,0(,R3)      VIRTUAL ADDRESS",
            "         SRL   R4,12          PAGE NUMBER",
            "         N     R4,F255        WITHIN ITS 1 MB SEGMENT",
            "         SLL   R4,3           TIMES PAGSWPE, THE ENTRY SIZE",
        ]),
        ('00937000', [
            "         ISKE  R4,R2          GET REAL KEY, 4 KB FRAME",
        ]),
        ('00974000', [
            "         SSKE  R9,R2          SET REAL KEY, 4 KB FRAME",
        ]),
    ],
}

# M3: named systems shared at FRAME granularity (docs/05 section 3, CP-67's
# way).  VM/370 shared the PAGE TABLE: at the first IPL of a named system
# DMKCFG adopted the user's own page table for each shared 64 KB segment as
# the shared one, later users swapped theirs for it, and the segment table
# entry was the unit of sharing.  With 1 MB segments that would make the
# whole megabyte common -- CMS keeps private nucleus pages in the same
# megabyte as its shared ones (F00000-F7FFFF private, F80000-FAFFFF shared)
# -- which is wall 24, I-195.  Here the SHRTABLE's page tables are MODELS,
# never placed in a user's STE: each user keeps a private 256-entry table
# for the segment, and DMKCFG copies the model's 16 PTEs and 16 swap entries
# per shared 64 KB group into it.  The model's frames are brought in once,
# through the first user's address space with the model in the STE for the
# duration of sixteen TRANS BRING+LOCK, and stay locked (CORIOLCK) while the
# named system is resident, so no sharer's PTE copy can go stale; they are
# owned by SYSTEM.  The ESA/390 common-segment bit is never used.
# M2, AMODE 31, first step (I-208): CP runs AMODE 24, and LOAD REAL ADDRESS
# forms its operand address in the current mode, so every `TRANS` asked about
# a virtual address above 16 MB was answered about the address modulo 16 MB
# -- correctly, about the wrong page (README "AMODE 31 is a prerequisite").
# The fix that does not need the 215 LA-strip sites (I-126) first: switch to
# AMODE 31 for the LRA alone with BSM, and switch back.  R15 is the scratch
# register, because the macro's own non-resident path -- CALL DMKPTRAN -- has
# always returned with R15 clobbered, so no site can have depended on it.
# OR sets the condition code but runs before the LRA; LA and BSM leave it,
# so the BC that follows still sees LRA's.  In AMODE 31 LA yields bit 0 = 0,
# which is exactly what BSM needs to return to AMODE 24.  While real storage
# stays below 16 MB every CP address is a 24-bit address, so nothing else in
# CP notices; this unlocks VIRTUAL storage above the line.
# M2 step 3: a guest with PSW bit 32 on.  The dispatcher already copies an
# EC-mode guest's VMPSW+4 whole into the real PSW, so the guest RUNS in
# AMODE 31; what remains is CP's own idea of a guest address.  Every place
# that forms or checks one gets the one test `TM VMPSW+4,X'80'` (R11 is the
# VMBLOK everywhere CP simulates a guest): a 24-bit guest's address is bits
# 8-31, a 31-bit guest's is bits 1-31.  The GADR31 macro (XAOPS) says it in
# five instructions; the three PSW gatekeepers admit bit 32 in EC mode.
# docs/34-AMODE31.md, step 3.
SWEEP_EXCEPT = {('DMKPRV', '00395100'), ('DMKPRV', '00903000'),
                ('DMKPSA', '00272000'), ('DMKPSA', '00279000'),
                ('DMKHVC', '00617000'), ('DMKHVC', '00789000')}
G31MODS = {
    # M5c: a guest that switches mode natively (BSM/BASSM) is invisible to
    # the PSW gatekeepers, so VMAM31 stays stale and the next simulated
    # privileged op (SSK above 16 MB, DIAG with a high address) is decoded
    # as 24-bit.  Every such simulation enters through DMKPRG, which copies
    # the real program old PSW's address word into VMPSW+4 here: take the
    # mode from the same word (EC-mode guests only; BC has no bit 32).
    'DMKPRG': [
        ('00290000', ["         ST    R1,VMPSW+4     SAVE PSW ADDRESS",
                      "         NI    VMFSTAT,255-VMAM31 MODE FROM THE REAL PSW",
                      "         LTR   R1,R1          BIT 32 = AMODE 31 ?",
                      "         BNM   *+8            NO",
                      "         OI    VMFSTAT,VMAM31 YES (M5C, NATIVE BSM)"]),
    ],
    'DMKPSA': [
        # TRL31, the TRANS macro's AMODE 31 LRA, out of the PSA's reserved
        # words (where it no longer fits) into the live code at X'800'.
        # Base register 0 covers it (USING DMKPSA,R0 THROUGHOUT); the VMBLOK
        # is addressed explicitly because USING VMBLOK,R11 comes later.
        ('00171000', [
            "         DC    (X'800'-(*-DMKPSA))X'0'  CLEAR TO X'800'",
            "*  TRL31: THE TRANS MACRO'S LRA IN AMODE 31. ATRL31 AT X'41C'",
            "*  POINTS HERE. A 31-BIT GUEST OWNS BITS 1-31 (M2 STEP 3).",
            "TRL31    LR    R2,R1          THE GUEST ADDRESS",
            "         TM    VMFSTAT-VMBLOK(R11),VMAM31  31-BIT GUEST ?",
            "         BO    TRL31A         YES: ONLY BIT 0 GOES",
            "         N     R2,XRIGHT24    24-BIT GUEST: BYTE 0 GOES",
            "TRL31A   SLL   R2,1           BIT 0 OFF",
            "         SRL   R2,1           ...",
            "         LRA   R2,0(0,R2)     TRANSLATE, IN AMODE 31",
            "         BSM   0,R15          BACK TO THE CALLER'S MODE",
        ]),
        # DMKPSARX: the effective address of a guest RX operand.  LA in
        # AMODE 31 sums to 31 bits; a 24-bit guest's registers may carry
        # flags in byte 0 (BALR's ILC/CC), so its sum wraps to 24 bits as
        # the hardware would.  No CC contract at this exit.
        ('00232000', [
            "         LA    R1,0(R1,R15)   ADD BASE/INDEX REGISTERS",
            "         TM    VMFSTAT,VMAM31 31-BIT GUEST ?",
            "         BO    *+8            YES: THE 31-BIT SUM IS RIGHT",
            "         N     R1,XRIGHT24    24-BIT GUEST: WRAP AT 16 MB",
        ]),
        # DMKPSARR / PSAMVCL: the guest's register as an address, with the
        # CC = 2 contract restored by CLI *,0 as PSAMVCL already does.
        ('00272000', [
            "         GADR31 R1             GUEST ADDRESS, EITHER MODE",
            "         CLI   *,X'00'        SET CC = 2 (THE CONTRACT)",
        ]),
        ('00279000', [
            "         GADR31 R1             ...ADDRESS ONLY, EITHER MODE",
        ]),
    ],
    'DMKDSP': [
        # PSWCKSUB sees every PSW an interrupt reflection or a slow LPSW
        # installs: the mode flag is recomputed here -- off, then on for
        # an EC PSW with bit 32 (CKEXTPSW).  BC mode leaves it off.
        ('01314100', ["         NI    VMDSTAT,255-VMDSP NOT RUN USER",
                      "         NI    VMFSTAT,255-VMAM31 ASSUME 24-BIT (M2 STEP 3)"]),
        ('01342000', ["         TM    VMPSW+4,X'7F'  BAD BITS IN WORD 2 (32 = AMODE)",
                      "         BNZ   BADPSW         ILLEGAL PSW IF BIT SET",
                      "         TM    VMPSW+4,X'80'  AMODE 31 ?",
                      "         BZ    *+8            NO",
                      "         OI    VMFSTAT,VMAM31 YES: GUEST RUNS AMODE 31"]),
        ('01343000', ["         DS    0H             (BNZ BADPSW MOVED UP)"]),
    # I-238.  DMKPAG marks a paging I/O error by storing X'FF' into byte 0
    # of the CPEXBLOK's CPEXADD (STC R9,CPEXADD, R9 = -1), and the
    # dispatcher hands it on as the CONDITION CODE of LTR R15,R15 before
    # branching: in AMODE 24 the byte was invisible to BR.  In AMODE 31
    # it is an instruction fetch at FF03EB84 (w122).  The CC is still
    # the contract, so the byte is stripped with shifts, which set none.
        ('01943000', ["         SLL   R15,8          THE FLAG BYTE IS THE CC ABOVE,",
                      "         SRL   R15,8          NOT AN ADDRESS (I-238)",
                      "         BR    R15            AND GO ..."]),
    ],
    'DMKPRV': [
        ('00395100', ["         GADR31 R1             THE PSW ADDRESS, EITHER MODE"]),
        # PRLPSWEC's fast dispatch bypasses DMKDSP, so the flag is kept
        # here as well; the status-difference test below is untouched.
        ('00741000', ["         TM    VMPSW+4,X'7F'  BITS 33-39 = 0? (32 = AMODE)",
                      "         BNZ   VPSWCHK        NO, -> DMKDSP",
                      "         NI    VMFSTAT,255-VMAM31 MODE FROM THE NEW PSW",
                      "         TM    VMPSW+4,X'80'  AMODE 31 ?",
                      "         BZ    *+8            NO",
                      "         OI    VMFSTAT,VMAM31 YES (M2 STEP 3)"]),
        ('00742000', ["         DS    0H             (BNE VPSWCHK MOVED UP)"]),
        ('00903000', ["         GADR31 R6             GUEST ADDRESS, EITHER MODE"]),
    ],
    'DMKSVC': [
        # the SVC fast reflection loads the guest's new PSW without DMKDSP
        ('00419000', ["         TM    VMPSW+4,X'7F'  MUST-BE-ZERO BITS (32 = AMODE)",
                      "         BNZ   REFSVCA        IF NOT, MAKE DISPATCH CHECK IT",
                      "         NI    VMFSTAT,255-VMAM31 MODE FROM THE NEW PSW",
                      "         TM    VMPSW+4,X'80'  AMODE 31 ?",
                      "         BZ    *+8            NO",
                      "         OI    VMFSTAT,VMAM31 YES (M2 STEP 3)"]),
        ('00420000', ["         DS    0H             (BNE REFSVCA MOVED UP)"]),
    ],
    'DMKHVC': [
        ('00617000', ["         LR    R1,R5          FIRST DOUBLE-WORD TO R1",
                      "         GADR31 R1             GUEST ADDRESS, EITHER MODE"]),
        ('00789000', ["         GADR31 R1             GUEST ADDRESS, EITHER MODE"]),
    ],
}

AMODEMODS = {
    'TRANS': [
        # The common form goes through the PSA stub (+2 bytes a site, I-216),
        # which masks the address to 24 bits first: every guest is a 24-bit
        # machine today and CP's callers hand TRANS CCW and CAW words with
        # the command code or key still in byte 0 (DMKDGD 'L R1,RCWADDR',
        # DMKVSP 'L R1,VSPCAW', ...) -- w53 lost every CMS minidisk to that.
        # OPT=AMODE31 says the address is a clean 31-bit one -- the console
        # ST/D path -- and takes the inline wrapper, unmasked, and passes
        # the flag on to DMKPTRAN.  The other register forms also stay
        # inline (+16), masked by nothing, as the original macro left them.
        ('00004110', [
            "         LCLB  &IERR,&SYST,&LOCK,&BRNG,&DEFR,&VFLT,&A31",
        ]),
        ('00028300', [
            "         AIF   ('&OP(&X)' EQ 'VFAULT').VFT",
            "         AIF   ('&OP(&X)' EQ 'AMODE31').A31",
        ]),
        ('00030860', [
            "         AGO   .ADDOP",
            ".A31     AIF   (&A31).OPERR",
            "&A31     SETB  1              CLEAN 31-BIT ADDRESS (I-208)",
            "         AGO   .ADDOP",
        ]),
        ('00062100', [
            "         AIF   (&A31).TRINL   31-BIT: INLINE, NO MASK",
            "         AIF   ('&RV' NE 'R2' OR '&UR' NE 'R1').TRINL",
            "         L     R15,ATRL31     THE LRA IN AMODE 31: PSA STUB",
            "         BASSM R15,R15        LRA R2,0(0,R1), AND BACK",
            "         AGO   .TRDONE",
            ".TRINL   LA    R15,TR&NL.L    THE LRA, TO RUN IN AMODE 31",
            "         O     R15,=X'80000000' (CP ITSELF RUNS AMODE 24)",
            "         BSM   0,R15          ...",
            "TR&NL.L  LRA   &RV,0(0,&UR)   AND DO HARDWARE TRANSLATE",
            "         LA    R15,TR&NL.B    BIT 0 OFF: BACK TO AMODE 24",
            "         BSM   0,R15          CC STILL LRA'S",
            "TR&NL.B  DS    0H",
            ".TRDONE  ANOP",
        ]),
    ],
    # DMKPTRAN's own LRA -- and its FIRST instruction, which is the I-208
    # alias itself: 'LA R1,0(,R1)  STRIP HIGH BYTE - 24 BIT ADDRESSING
    # ONLY' took every virtual address modulo 16 MB before the TRANS stub
    # had a chance (w51: st s1ff0000 landed at ff0000 with the stub in).
    # Bit 0 is stripped, nothing else; a caller that still hands over a
    # byte of flags in bits 0-7 now gets CC2 from the VMSIZE compare -- a
    # visible failure, not a silent alias -- and that is the I-126 audit.
    # No literal here: this is the entry instruction, before ENTER sets up
    # R10, and the literal pool sits in R10's half of the module -- the
    # first try, N R1,=X'7FFFFFFF', was assembled off a base register the
    # caller owned and IPL died in a program-interrupt loop at 1FC8 (w52).
    # Two shifts need no base at all.
    # ...and after ENTER, because SAVER2 is written BY ENTER (STM
    # R0,R11,SAVEREGS): at the entry instruction it still holds the previous
    # caller's R2, which is how the first try stripped every address with the
    # flag set (w57 trace: R2=C2 at entry, R1 masked to FF0000 at the LRA).
    # ENTER keeps R1 (it stores, nothing else).  I-220.
    'DMKPTR': [
        ('00285000', '00287000', [
            "DMKPTRAN ENTER",
            "         TM    SAVER2+3,AMODE31 CLEAN 31-BIT ADDRESS? (I-208)",
            "         BO    PTRA31         YES: KEEP BITS 1-7",
            "         TM    VMFSTAT,VMAM31 A 31-BIT GUEST? (M2 STEP 3)",
            "         BO    PTRA31         ITS ADDRESSES ARE BITS 1-31",
            "         N     R1,XRIGHT24    24-BIT CALLER: STRIP BYTE 0",
            "PTRA31   SLL   R1,1           BIT 0 OFF, NO LITERAL BEFORE",
            "         SRL   R1,1           R10 IS SET UP (I-218)",
            "         XC    SAVEWRK9,SAVEWRK9 CLEAR PAGEIO ERROR SWITCH",
        ]),
        # 'ST R1,SAVEWRK9  CLEAR PAGEIO ERROR SWITCH' cleared the switch --
        # byte 0 of SAVEWRK9, read by 'CLI SAVEWRK9,0  PAGE IN OK??' --
        # only because the stripped address had a zero byte 0.  A 31-bit
        # address put 01 there and every first touch above 16 MB came back
        # DMKPTR410W PAGING ERROR (w60).  Nothing reads the address from
        # SAVEWRK9; the two other references store and test the switch.
        # I-222.
        ('00307000', [
            "         LA    R15,PTRLRA     THE LRA, IN AMODE 31 (I-208)",
            "         O     R15,=X'80000000' ...",
            "         BSM   0,R15          ...",
            "PTRLRA   LRA   R7,0(,R1)      DO HARDWARE TRANSLATE",
            "         LA    R15,PTRLRAB    BACK TO AMODE 24",
            "         BSM   0,R15          ...",
            "PTRLRAB  DS    0H",
        ]),
    ],
}

# M2 step 2, part 2: CP's own PSWs carry the AMODE 31 bit.  Every path into
# CP after initialisation is an interrupt -- external, SVC, program, machine
# check, I/O, restart -- and DMKCPI installs those new PSWs from CPIPSWS, a
# table of A(mask,entry) pairs.  Bit 32 of a PSW is the addressing mode, which
# is bit 0 of the second word, so the entry address goes in as X'80' plus a
# 3-byte adcon -- the form DMKWRM uses for AL1(flags),AL3(DMKRSPPR), which the
# nucleus loader relocates as a 3-byte field with no question about a bit-0
# RLD.  SVC 8/12 need nothing: DMKSVC saves the SVC old PSW's address word in
# SAVERETN and loads it back, mode bit and all.  Dispatching a guest is LPSW
# RUNPSW with the guest's own PSW, bit 32 off, so S/370 guests stay 24-bit.
# The CPEXBLOK unstack's LPSW TEMPSAVE is AP-only (AIF (NOT &AP)); on this UP
# system the unstack is BR R15 in the current mode.  DMKCPI's own init runs
# in AMODE 24 until its first interrupt -- harmless now that part 1 made CP's
# code mode-independent, and every DMKCPI probe that points PRNPSW+4 at a
# local label (six sites) keeps working.  DMKMCH's five PSWs for the
# machine-check paths get the bit too.  The initial machine-check new PSW
# (01914000, a disabled wait) is left as it is.  I-224.
PSWMODS_CPI = [
        ('01911000', ["CPIPSWS  DC    A(MCHEKENB),X'80',AL3(DMKPSAEX) EXT, AMODE 31"]),
        ('01912000', ["         DC    A(MCHEKENB),X'80',AL3(DMKSVCIN) SVC, AMODE 31"]),
        ('01913000', ["         DC    A(MCHEKENB),X'80',AL3(DMKPRGIN) PROG, AMODE 31"]),
        ('01915000', ["         DC    A(MCHEKENB),X'80',AL3(DMKIOTIN) I/O, AMODE 31"]),
        ('01916000', ["MCKPSW   DC    A(XMODEON),X'80',AL3(DMKMCHIN) MCK, AMODE 31"]),
        ('01917000', ["RESTPSW  DC    A(MCHEKENB),X'80',AL3(DMKPSADU) RESTART, 31"]),
]
# I-229.  The trace subroutines are entered with BAL and read the caller's
# condition code out of byte 0 of the LINK register: STCM Rlink,8 into the
# trace entry and SPM Rlink to restore it, then B 2(,Rlink) over the inline
# trace code.  In AMODE 31 BAL stores bit 0 and a 31-bit address, so every
# traced HIO/TIO/SIO came back CC 0: DMKCPI's IPL device check saw every
# DMKRIO device as present, cleared RDEVDISA on the 2701 lines Hercules
# lacks, and the first ENABLE drove an SSCH at subsystem id 0 (PRG021,
# w84).  IPM at entry puts the CC where byte 0 held it; the link is then
# masked wherever it is used as an address -- with N where the CC has
# already been captured, and with the shift pair SLL 8 / SRL 8 after the
# SPM, because N sets the condition code it would have just restored
# (i237: every traced SIO answered 'nonzero', and no DASD label was read).
TRACESUBS = {
    'DMKCPI': [
        ('01593000', ["TRACESUB IPM   R1             CC INTO THE LINK (I-229)"]),
        ('01595000', ["         LR    R14,R1         THE LINK AS AN ADDRESS",
                      "         N     R14,XRIGHT24   WITHOUT THE CC BITS (I-229)",
                      "         IC    R0,N0(,R14)    LOAD THE TRACE CODE"]),
        ('01607000', ["         SPM   R1             RESTORE CONDITION CODE",
                      "         SLL   R1,8           LINK AS AN ADDRESS: SHIFTS",
                      "         SRL   R1,8           LEAVE THE CC ALONE (I-229)"]),
    ],
    'DMKCNS': [
        ('01580000', ["CNTRACE  IPM   R15            CC INTO THE LINK (I-229)"]),
        ('01584100', ["         LR    R4,R15         THE LINK AS AN ADDRESS",
                      "         N     R4,XRIGHT24    WITHOUT THE CC BITS (I-229)",
                      "         IC    R4,0(,R4)      LOAD ENTRY TYPE FLAG"]),
        ('01600000', ["         SPM   R15            RESET COND. CODE",
                      "         SLL   R15,8          LINK AS AN ADDRESS: SHIFTS",
                      "         SRL   R15,8          LEAVE THE CC ALONE (I-229)"]),
    ],
    'DMKIOS': [
        ('01721000', ["TRACESUB IPM   R15            CC INTO THE LINK (I-229)",
                      "         TM    TRACFLG2,TRACBEF     TRACING ACTIVE?"]),
        ('01723000', ["         LR    R4,R15         THE LINK AS AN ADDRESS",
                      "         N     R4,XRIGHT24    WITHOUT THE CC BITS (I-229)",
                      "         IC    R4,0(R4)       R4 GETS TRACE-CODE FROM CALLER"]),
        ('01737000', ["         SPM   R15            RESTORE CONDITION CODE",
                      "         SLL   R15,8          LINK AS AN ADDRESS: SHIFTS",
                      "         SRL   R15,8          LEAVE THE CC ALONE (I-229)"]),
    ],
    'DMKVSJ': [
        ('00363000', ["HIOTRACE IPM   R15            CC INTO THE LINK (I-229)"]),
        ('00377000', ["         SPM   R15            RESET COND CODE",
                      "         SLL   R15,8          LINK AS AN ADDRESS: SHIFTS",
                      "         SRL   R15,8          LEAVE THE CC ALONE (I-229)"]),
    ],
}
# I-236.  CORSWPNT is a fullword whose byte 0 is CORFLAG: the CORTABLE entry's
# status flags share the word with the swap-table pointer ("ORG CORSWPNT /
# CORFLAG DS 1X").  CP reads the pointer with ICM Rx,B'0111',CORSWPNT+1 at
# most sites -- and with a plain L at these thirteen, where AMODE 24 made the
# flag byte invisible.  In AMODE 31 a page on the flush list (CORFLUSH X'20')
# gave DMKPTR's steal path R5 = 20FD94F8 and the page-out completion NI on
# SWPFLAG took an addressing exception (PRG005, w121: IPL 00C of VMFLOAD's
# deck into a 16 MB MAINT, the first workload to page under this CP).  The
# seventh idiom the strip sweep cannot see: a flag-bearing pointer word
# loaded whole.  Found by `grep "L  *R[0-9]*,CORSWPNT"` over the nucleus;
# CORFPNT/CORBPNT/CORPGPNT carry no flags.  DMKVMA 00457000 sits between an
# LTR and its BNZ, so the N moves ahead of the LTR there.
CORSWMODS = {
    'DMKATS': [('00809000', ["         L     R5,CORSWPNT    GET ADDRESS OF SWPTABLE",
                             "         N     R5,XRIGHT24    BYTE 0 IS CORFLAG (I-236)"])],
    'DMKCCW': [('00971000', ["         L     R15,CORSWPNT-CORTABLE(,R15) POINTER TO SWAP",
                             "         N     R15,XRIGHT24   BYTE 0 IS CORFLAG (I-236)"]),
               ('03582000', ["         L     R15,CORSWPNT-CORTABLE(,R15) POINTER TO SWAP",
                             "         N     R15,XRIGHT24   BYTE 0 IS CORFLAG (I-236)"])],
    'DMKCDS': [('00890000', ["         L     R14,CORSWPNT-CORTABLE(,R15) SWAP TABLE ENTRY",
                             "         N     R14,XRIGHT24   BYTE 0 IS CORFLAG (I-236)"])],
    'DMKDGD': [('00516000', ["         L     R5,CORSWPNT-CORTABLE(,R5) POINTER TO SWAP",
                             "         N     R5,XRIGHT24    BYTE 0 IS CORFLAG (I-236)"])],
    'DMKMCH': [('00618000', ["         L     R3,CORSWPNT    THE SWPTABLE ENTRY ADDRESS",
                             "         N     R3,XRIGHT24    BYTE 0 IS CORFLAG (I-236)"])],
    'DMKPTR': [('00371000', ["         L     R5,CORSWPNT    RESTORE SWAP TABLE ADDRESS",
                             "         N     R5,XRIGHT24    BYTE 0 IS CORFLAG (I-236)"]),
               ('00826000', ["         L     R5,CORSWPNT    PICK-UP SWAPTABLE ENTRY",
                             "         N     R5,XRIGHT24    BYTE 0 IS CORFLAG (I-236)"]),
               ('01206000', ["         L     R5,CORSWPNT    SWAP TABLE POINTER",
                             "         N     R5,XRIGHT24    BYTE 0 IS CORFLAG (I-236)"])],
    'DMKRPA': [('00284000', ["         L     R5,CORSWPNT    AND SWPTABLE POINTER",
                             "         N     R5,XRIGHT24    BYTE 0 IS CORFLAG (I-236)"])],
    'DMKUDU': [('00274000', ["         L     R7,CORSWPNT    R7 = SWAPTABLE ENTRY ADDRESS",
                             "         N     R7,XRIGHT24    BYTE 0 IS CORFLAG (I-236)"])],
    'DMKVMA': [('00280100', ["         L     R2,CORSWPNT-CORTABLE(,R2) LOAD SWAP TABLE PTR",
                             "         N     R2,XRIGHT24    BYTE 0 IS CORFLAG (I-236)"]),
               ('00456000', '00458000',
                            ["         L     R14,CORSWPNT   GET ADDRESS OF SWPTABLE ENTRY",
                             "         N     R14,XRIGHT24   BYTE 0 IS CORFLAG (I-236)",
                             "         LTR   R13,R13        ENTERED VIA CPEXBLOK",
                             "         BNZ   RETFRAM2       NO, SKIP RESETTING BITS"])],
}

# M5b.  CMS in EC mode (36-M5-CMS31.md).  Three things change and nothing
# else: (1) every PSW constant takes the EC form -- BC `channels || key AMWP`
# becomes `00000011 || key 1MWP`, so X'FF06' is X'030E', AL2(MCKM,0) is
# X'000C', and a wait is X'0E'/X'0A' in byte 1; (2) the interruption code and
# ILC are read from the fixed locations (external X'86', SVC X'89'/X'8A',
# program X'8D'/X'8E', I/O device X'BA') instead of the old PSW, which in EC
# mode carries neither; (3) every SSM mask: BC byte 0 is six channel masks,
# channels-6-plus and EXTERNAL, EC byte 0 is PER (bit 1), DAT (bit 5), I/O
# (bit 6) and external (bit 7), so X'FF' becomes X'03', X'FE' X'02', X'81'
# X'03', and the six `SSM *+1` tricks that borrowed the next opcode as a
# disable mask become an honest X'00' -- a borrowed X'58' would have set DAT.
# 133 SSM sites in 23 modules, 16 decode sites, PSW constants in 9 modules.
# Command modules (TYPE, LISTFILE, TAPE, ...) are rebuilt with CMSGEND.
# M4c / I-250: ESA/390 has no interval timer.  VM/370 CP time-slices with
# the S/370 interval timer at real X'50' (TIMER, QUANTUM, QUANTUMR); the
# hardware decremented it and an external interrupt (X'0080') ended the
# slice.  Under ESA/390 Hercules leaves X'50' alone, so a compute-bound
# virtual machine was never preempted (CPWATCH starved CMSUSER, w240/w248)
# and virtual interval timers stood still.  Emulation: DMKSCHTE decrements
# TIMER by the TOD time since its last call, in interval-timer units
# (bit 31 = 1/76800 s: TOD * 3 / 160000, remainder carried), at every CP entry that
# snapshots it (the SVC, program, I/O and external FLIHs); a value already
# negative is left alone.  DMKSCHTK, a 10 ms clock-comparator TRQBLOK set
# up by DMKCPI, guarantees those entries while a guest computes; the
# dispatcher then sees TIMER <= 0 exactly as before (VMTSEND).  DMKCPI has
# no room left (CPIATABL past its base), so DMKSCHTI's first 30-second
# sample starts the tick (DMKSCHTS).
TMRMODS = {
    'PSA': [
        ('00301464', ["TSAVSVC  DS    2F             R14-R15 ACROSS TIMEMU, SVC",
                      "TSAVPRG  DS    2F             ... PROGRAM FLIH",
                      "TSAVIOT  DS    2F             ... I/O FLIH"]),
        ('00301500', ["ATIMEMU  DC    V(DMKSCHTE)    INTERVAL TIMER EMULATION"]),
        ('00301545', ["TSAVEXT  DS    2F             ... EXTERNAL FLIH"]),
    ],
    'DMKSVC': [('00335000', ['         STM   R14,R15,TSAVSVC R14-R15 ACROSS THE CALL', '         L     R15,ATIMEMU    INTERVAL TIMER EMULATION', '         BALR  R14,R15        (I-250)', '         LM    R14,R15,TSAVSVC ...'] + ["         MVC   QUANTUMR,TIMER SAVE INTERVAL TIMER"])],
    'DMKPRG': [('00240000', ['         STM   R14,R15,TSAVPRG R14-R15 ACROSS THE CALL', '         L     R15,ATIMEMU    INTERVAL TIMER EMULATION', '         BALR  R14,R15        (I-250)', '         LM    R14,R15,TSAVPRG ...'] + ["         MVC   QUANTUMR,TIMER SAVE INTERVAL TIMER"])],
    'DMKIOT': [('00229000', ['         STM   R14,R15,TSAVIOT R14-R15 ACROSS THE CALL', '         L     R15,ATIMEMU    INTERVAL TIMER EMULATION', '         BALR  R14,R15        (I-250)', '         LM    R14,R15,TSAVIOT ...'] + ["         MVC   QUANTUMR,TIMER SAVE INTERVAL TIMER"])],
    'DMKPSA': [('00466000', ['         STM   R14,R15,TSAVEXT R14-R15 ACROSS THE CALL', '         L     R15,ATIMEMU    INTERVAL TIMER EMULATION', '         BALR  R14,R15        (I-250)', '         LM    R14,R15,TSAVEXT ...'] + ["         MVC   QUANTUMR,TIMER SAVE INTERVAL TIMER"])],
    'DMKSCH': [
        ('00152000', ["         ENTRY DMKSCHMD",
                      "         ENTRY DMKSCHTK,DMKSCHTE,DMKSCHTS  M4C"]),
        ('01358010', [
            "SETTRQ   DS    0H",
            "*  M4C: THE FIRST 30-SECOND SAMPLE STARTS THE 10 MS TICK",
            "         CLI   TKSTARTD,0     TICK RUNNING?",
            "         BNE   SETTRQ1        YES",
            "         MVI   TKSTARTD,1",
            "         L     R15,ATKSTART   DMKSCHTS",
            "         BALR  R14,R15",
            "SETTRQ1  DS    0H"]),
        ('01401000', [
            "OUT      GOTO  DMKDSPCH",
            "*  M4C: 10 MS TICK.  RE-ARMS ITSELF; ITS ONLY JOB IS A CP",
            "*  ENTRY, SO DMKSCHTE RUNS AND THE DISPATCHER SEES TIMER.",
            "DMKSCHTK EQU   *",
            "         USING TRQBLOK,R10",
            "         USING *,R12",
            "         DROP  R13",
            "         LM    R12,R13,ASCHDL",
            "         USING DMKSCHDL,R12,R13",
            "         LR    R1,R10         THE TRQBLOK FOR DMKSCHST",
            "         STCK  TRQBTOD        NOW",
            "         BC    7,OUT          CLOCK NOT SET: NO TICK",
            "         LM    R4,R5,TRQBTOD",
            "         AL    R5,TICKLEN     + 10 MS",
            "         BC    12,*+8",
            "         AL    R4,F1",
            "         STM   R4,R5,TRQBVAL",
            "         CALL  DMKSCHST       TICK",
            "         B     OUT",
            "TKSTARTD DC    X'00'          TICK STARTED",
            "         DS    0F",
            "ATKSTART DC    A(DMKSCHTS)",
            "*  M4C: START THE TICK.  BALR R14,R15; ALL REGISTERS KEPT.",
            "DMKSCHTS DS    0H",
            "         USING *,R15",
            "         STM   R0,R15,TSSAVE",
            "         LR    R12,R15",
            "         DROP  R15",
            "         USING DMKSCHTS,R12",
            "         LA    R0,TRQBSIZE",
            "         L     R15,AFRE52",
            "         BALR  R14,R15        DMKFREE",
            "         LR    R2,R1",
            "         USING TRQBLOK,R2",
            "         XC    TRQBLOK(TRQBSIZE*8),TRQBLOK",
            "         MVC   TRQBUSER,ASYSVM",
            "         MVC   TRQBIRA,ATK",
            "         STCK  TRQBTOD",
            "         LM    R4,R5,TRQBTOD",
            "         AL    R5,TICKLEN",
            "         BC    12,*+8",
            "         AL    R4,F1",
            "         STM   R4,R5,TRQBVAL",
            "         LR    R1,R2",
            "         L     R15,ASCHST",
            "         BALR  R14,R15        DMKSCHST",
            "         DROP  R2",
            "         LM    R0,R15,TSSAVE  (DMKSCHST KEPT R12)",
            "         BR    R14",
            "         DROP  R12",
            "TSSAVE   DS    16F",
            "AFRE52   DC    V(DMKFREE)",
            "TICKLEN  DC    F'40960000'    10 MS IN TOD UNITS",
            "ASCHST   DC    A(DMKSCHST)",
            "ATK      DC    A(DMKSCHTK)",
            "*  M4C: INTERVAL TIMER EMULATION.  BALR R14,R15 FROM A",
            "*  FLIH, DISABLED; CALLER SAVES R14-R15.  R0-R1 KEPT.",
            "DMKSCHTE DS    0H",
            "         DROP  R13",
            "         USING DMKSCHTE,R15",
            "         STM   R0,R1,TESAVE",
            "         STCK  TENOW",
            "         BC    7,TEOUT        CLOCK NOT SET",
            "         LM    R0,R1,TENOW    ELAPSED = NOW - LAST",
            "         SL    R1,TELAST+4",
            "         BC    3,TENB         NO BORROW",
            "         BCTR  R0,0",
            "TENB     SL    R0,TELAST",
            "         MVC   TELAST(8),TENOW",
            "         LTR   R0,R0          OVER 2**31 TOD UNITS",
            "         BNZ   TEBIG          (0.5 S): SATURATE",
            "         LTR   R1,R1",
            "         BM    TEBIG",
            "*  UNITS = (TOD * 3 + REMAINDER) / 160000, REMAINDER KEPT:",
            "*  ENTRIES COME EVERY FEW MICROSECONDS, ONE UNIT IS 13.",
            "         M     R0,TE3",
            "         AL    R1,TEREM",
            "         BC    12,*+8",
            "         AL    R0,TEONE",
            "         D     R0,TE160K",
            "         ST    R0,TEREM",
            "         B     TESUB",
            "TEBIG    L     R1,TEMAX",
            "         XC    TEREM,TEREM",
            "TESUB    L     R0,TIMER",
            "         LTR   R0,R0          ALREADY NEGATIVE:",
            "         BM    TEOUT          LEAVE IT (NO WRAP)",
            "         SR    R0,R1",
            "         ST    R0,TIMER",
            "TEOUT    LM    R0,R1,TESAVE",
            "         BR    R14",
            "         DROP  R15",
            "         DS    0D",
            "TENOW    DS    D",
            "TELAST   DC    XL8'00'",
            "TESAVE   DS    2F",
            "TE3      DC    F'3'",
            "TE160K   DC    F'160000'",
            "TEREM    DC    F'0'",
            "TEONE    DC    F'1'",
            "TEMAX    DC    X'7FFFFFFF'",
            "         USING DMKSCHDL,R12,R13",
        ]),
    ],
}

ECMODS = {
    # M5d: SVC 120 (GETMAIN/FREEMAIN RU, LOC=ANY) from HIGHSTOR.  CE's
    # HRC380DS placeholder returned the fixed X'04100000' for S/380 Hercules
    # to back; on VM/370+ the storage is real and managed (I-245).
    'DMSSVT': [
        ('02667100', '02667450', [
            "*  M5D: GETMAIN/FREEMAIN RU (SVC 120).  R0 = LENGTH, R1 =",
            "*  ADDRESS (FREEMAIN), R15 FLAGS: X'01' = FREEMAIN (GCC380:",
            "*  X'72' GET, X'03' FREE; W209).  ABOVE THE LINE FROM",
            "*  HIGHSTOR FOR LOC=ANY FROM AN AMODE 31 CALLER; ALL ELSE",
            "*  IS AN ORDINARY GETMAIN/FREEMAIN R, HANDED TO DMSSMN10 AS",
            "*  THE SVC 10 DISPATCH WOULD (I-245).",
            "         L     R6,OSTEMP          TEMPSPC (REENTRANT WORK)",
            "         STM   R0,R1,S120R0-TEMPSPC(R6)",
            "         MVC   S120PL-TEMPSPC(8,R6),=CL8'HIGHSTOR'",
            "         MVC   S120PL+16-TEMPSPC(8,R6),S120R0-TEMPSPC(R6)",
            "         TM    EGPR15+3,X'01'     FREEMAIN?",
            "         BZ    S120GET",
            "         CL    R1,=A(X'01000000') ABOVE THE LINE?",
            "         BL    S120LOW            NO: DMSSMN'S STORAGE",
            "         MVC   S120PL+8-TEMPSPC(8,R6),=CL8'RELEASE'",
            "         B     S120HS",
            "S120GET  TM    EGPR15+3,X'20'     LOC=ANY (VIRTUAL)?",
            "         BZ    S120LOWG           NO: BELOW (I-248)",
            "         TM    OLDPSW+4,X'80'     CALLER IN AMODE 31?",
            "         BZ    S120LOWG           NO: BELOW THE LINE",
            "         MVC   S120PL+8-TEMPSPC(8,R6),=CL8'OBTAIN'",
            "S120HS   LA    R1,S120PL-TEMPSPC(,R6)",
            "         SVC   202",
            "         DC    AL4(S120ERR)",
            "         L     R1,S120PL+20-TEMPSPC(R6)  THE ADDRESS",
            "         ST    R1,EGPR1           FOR THE CALLER",
            "         SR    R15,R15",
            "         B     CMSRET",
            "S120ERR  TM    EGPR15+3,X'01'     FAILED FREEMAIN:",
            "         BO    CMSRET             RC 4 (BAD RELEASE)",
            "S120LOWG MVC   EGPR1,=X'80000000' SVC 10 GETMAIN: R1 BYTE 0",
            "S120LOW  L     R1,OSTEMP          AS THE SVC 10 DISPATCH DOES",
            "         L     R3,SAVR14-TEMPSPC(,R1)",
            "         LA    R0,TEMPLNT",
            "         DMSFRET DWORDS=(0),LOC=(1),TYPCALL=BALR",
            "         LR    R14,R3",
            "         LM    R0,R1,EGPR0",
            "         L     R12,=V(DMSSMN10)",
            "         BR    R12",
        ]),
        ('02782000', [
            "S120R0   DS    F                  M5D: SVC 120 WORK",
            "S120R1   DS    F",
            "S120R15  DS    F",
            "S120PL   DS    6F                 HIGHSTOR PLIST",
            "         DS    0D                 TEMPLNT ROUNDS DOWN (I-249)",
            "TEMPSEND EQU   *",
        ]),
    ],
    # I-252: SVC 10 from an AMODE 31 caller.  CMS reads a nonzero byte 0
    # of R1 as GETMAIN, the 24-bit convention; an AMODE 31 FREEMAIN R of
    # an address above the line (GCC380's PDPCLIB FREEPOOL, from a DCB
    # whose BUFCB it never set) became a GETMAIN of 2 MB and abend 80A.
    # From AMODE 31: GETMAIN iff R1 bit 0 is on (the XA rule); FREEMAIN
    # above the line is not DMSSMN's storage and is ignored.
    'DMSSMN': [
        ('00165000', [
            "         TM    OLDPSW+4,X'80'  I-252: CALLER AMODE 31?",
            "         BZ    SMN10A",
            "         TM    EGPR1,X'80'    R1 NEGATIVE: GETMAIN",
            "         BO    GET",
            "         CLI   EGPR1,X'00'    ABOVE THE LINE?",
            "         BE    SMN10A         NO: AN ORDINARY FREEMAIN",
            "         XC    EGPR15,EGPR15  NOT DMSSMN'S STORAGE:",
            "         BR    R14            IGNORED (I-252)",
            "SMN10A   CLI   EGPR1,X'00'    LOOK AT R1'S HIGH-ORDER BYTE",
        ]),
    ],
    'DMSINI': [
        # a reader IPL arrives from the card loader in BC mode: switch here
        ('00133000', ["         LPSW  ECPSW          DISABLED, EC MODE (M5B)",
                      "         CNOP  0,8",
                      "ECPSW    DC    X'000C0000',A(ECPSW+8) RESUME BELOW"]),
        ('00134000', ["         LH    R0,X'BA'       IPL DEVICE ADDRESS (EC: AT BA)"]),
        ('00192000', ["RDERRPSW DC    X'000E0000',X'00',CL3'INI' EC WAIT, BYTE 4 = 0"]),
        ('00246000', ["ENABLED  DC    X'03'          I/O AND EXTERNAL (EC MODE)"]),
        # DMSINIW, the nucleus-loader entry, arrives in BC mode too
        ('00257000', ["         LPSW  ECPSW2         DISABLED, EC MODE (M5B)",
                      "         CNOP  0,8",
                      "ECPSW2   DC    X'000C0000',A(ECPSW2+8) RESUME BELOW"]),
        ('00275000', ["WAKEHERE LH    R13,X'BA'      THE INTERRUPTING DEVICE (EC)"]),
        ('00613000', ["         DC    X'000C0000',V(EXTINT)   EC, MCK ON"]),
        ('00614000', ["         DC    X'000C0000',V(DMSITS1)  EC, MCK ON"]),
        ('00615000', ["         DC    X'000C0000',V(DMSDBGP)  EC, MCK ON"]),
        ('00616000', ["         DC    X'000E0000',A(MCKNPSW-NUCON) EC WAIT"]),
        ('00617000', ["         DC    X'000C0000',V(IOINT)    EC, MCK ON"]),
        ('00619000', ["NIOPSW   DC    X'000C0000',V(IOINT)    EC, MCK ON"]),
        ('00620000', ["WAITPSW  DC    X'020E0000',A(WAKEHERE) EC, I/O, WAIT"]),
        ('00621000', ["WAKEPSW  DC    X'000C0000',A(WAKEHERE) EC, MCK ON"]),
        ('00764900', ["         DC    X'000C0000',A(DMSINIR)    00 EC MODE"]),
        ('00765200', ["         DC    X'000C0000',A(DMSINIR)    68 EC MODE"]),
    ],
    'DMSCRD': [
        ('00392000', ["WAITPSW  DC    X'000E0000',X'00',CL3'CON' EC WAIT, BYTE 4 = 0"]),
    ],
    'DMSINS': [
        ('00699000', ["         DC    X'000C0000'    EC, MCK ON (WAS H'4,0')"]),
        ('00701000', ["ACVTOK   DC    X'000C0000',A(CVTOK)     EC (EXT-PREC.)"]),
        ('00709000', ["NIOPSW   DC    X'000C0000',V(IOINT)     EC, MCK ON"]),
        ('00710000', ["WAKEPSW  DC    X'000C0000',A(WAKEHERE)  EC, MCK ON"]),
        ('00711000', ["WAITPSW  DC    X'020E0000',A(WAKEHERE)  EC, I/O, WAIT"]),
    ],
    'DMSITS': [
        ('00249000', '00250000', [
            "         MVC   SVCOPSW(4),=X'000C0000' EC VIRTUAL OLD PSW",
            "         MVC   X'88'(4),=X'000200CA' ILC 2, SVC 202 (EC)"]),
        ('00268000', ["         CLI   X'8B',201      IS IT SVC 201? (EC CODE)"]),
        # startup PSWs (ITSPSW/RET) must be EC: byte0 03=I/O+EXT, byte1 0C=EC+MCK
        ('00328000', ["         CLI   X'8B',202      IS THIS SVC 202? (EC CODE)"]),
        ('00330000', ["         CLI   X'8B',203      IS THIS SVC 203? (EC CODE)"]),
        # SCBPSW+4 of a nucleus extension carries flags in byte 0 (DMSREX:
        # X'20'); BC ignored it, EC requires bits 32-39 zero
        ('00537200', ["         MVC   ITSPSW+4(4),SCBPSW+4 SET THE ADDRESS",
                      "         MVI   ITSPSW+4,0     AMODE 24, EC BITS 32-39"]),
        ('00537260', ["         STC   R2,ITSPSW+1    SET THE PSW KEY BYTE",
                      "         OI    ITSPSW+1,X'0C' EC MODE, MCK ENABLED (M5B)"]),
        # bytes 2-3 of RET are whatever STM R11,R13,RET left there; BC
        # ignored them on LPSW, EC takes a specification exception (bit 17)
        ('00548000', ["         ST    R15,RET+4      LOWCORE PSW CONSTRUCTION",
                      "         MVI   RET+4,0        AMODE 24, EC BITS 32-39"]),
        ('00549000', ["         MVC   RET(4),=X'030C0000' EC PSW, ENABLED (M5B)"]),
        ('00703000', ["         MVC   OLDPSW,SVCOPSW COPY SVC OLD PSW INTO AREA",
                      "         MVC   OLDPSW+2(2),X'8A' SVC CODE INTO BC POSITION"]),
        ('00706000', ["         TM    X'89',X'04'    EXECUTE (4-BYTE)? ILC AT 89"]),
        ('00749000', ["         IC    XR,X'8B'       GET SVC NUMBER (EC CODE)"]),
        ('00833000', ["         XC    ITSPSW(8),ITSPSW START WITH ZERO PSW",
                      "         MVI   ITSPSW+1,X'0C' EC MODE, MCK ENABLED (M5B)"]),
        ('00839000', ["         MVI   ITSPSW,X'03'   I/O+EXT ENABLED (EC)"]),
        ('00850000', ["         CLI   X'8B',S203     IS THIS AN SVC 203? (EC)"]),
        ('00894000', ["         MVC   SVCSAVE(8),OLDPSW SET RETURN PSW",
                      "         XC    SVCSAVE+2(2),SVCSAVE+2 DROP SVC CODE (EC)"]),
        ('00930000', ["         MVC   SVCSAVE(8),OLDPSW SET FIRST TO OLDPSW",
                      "         XC    SVCSAVE+2(2),SVCSAVE+2 DROP SVC CODE (EC)"]),
        ('01067000', ["         CLI   X'8B',201      SVC 201? (EC CODE)"]),
        ('01069000', ["         CLC   ITSPSW(2),=X'000C' DISABLED EC PSW?     V0211"]),
        ('01292000', ["         MVC   RET(4),=X'000C0000' FORM EC PSW AT RET"]),
        ('01293000', ["         ST    R1,RET+4       BRANCH ADDRESS (FROM A BAL)",
                      "         MVI   RET+4,0        DROP ILC/CC/MASK: EC (I-247)"]),
    ],
    'DMSITE': [
        ('00084000', ["         CLI   X'87',X'80'    INTERRUPT-CODE = TIMER? (EC)"]),
        ('00196150', ["         CLC   X'86'(2),=X'4001' VMCF EXTERNAL INT? (EC)"]),
        ('00199000', ["         STH   R15,X'BA'      CLEAR I/O INT. CODE (EC)"]),
        ('00216600', ["         SSM   =X'00'         DISABLE (NOT *+1: EC MODE)"]),
        ('00231000', ["         CH    R15,X'BA'      WHILE WE WERE OCCUPIED? (EC)"]),
    ],
    'DMSITP': [
        ('00129000', ["         IC    WORDP,X'8F'    GET INTERRUPT CODE (EC)"]),
        ('00142050', '00142200', [
            "         IC    R10,X'8D'      ILC, BITS 5-6 (EC)",
            "         SLL   R10,16         TO BYTE 1 OF INTINFO",
            "         ICM   R10,3,X'8E'    INTERRUPT CODE (EC)"]),
        ('00152000', ["         IC    XR,X'8F'       GET INTERRUPT CODE (EC)"]),
    ],
    'DMSIOW': [
        ('00162000', ["         MVC   X'BA'(2),SAVIOLD+2(R9) DEVICE IN I/O CODE"]),
        ('00199000', ["WAITNG   DC    X'030E0000',A(WAITRTN) EC WAIT, ENABLED"]),
    ],
    'DMSITI': [
        ('00134000', ["         LH    R4,X'BA'       INTERRUPTING DEVICE (EC)",
                      "         N     R4,TRUNCR      11 BITS OF IT"]),
        ('00154000', ["         LM    0,1,IOOPSW     SET UP I/O OLD PSW",
                      "         ICM   R0,3,X'BA'     WITH THE DEVICE, AS BC HAD IT"]),
        ('00156000', ["         MVC   SAVINT(16,R9),IOOPSW     SAVE THE INTERRUPT",
                      "         MVC   SAVINT+2(2,R9),X'BA'     AND THE DEVICE (EC)"]),
    ],
    'DMSSVN': [
        ('00151100', ["         SSM   =X'00'         DISABLE FOR ECB SCAN (EC)"]),
        ('00211000', ["ECBPSW   DC    X'030E0000',A(WAKEUP)  EC WAIT, ENABLED"]),
    ],
    'DMSABN': [('00309600', ["WAITPSW  DC    X'000A0000',A(*-4)  EC DISABLED WAIT"])],
    'DMSFNS': [('00651000', ["DIE      DC    X'000A0000',A(*)  EC DISABLED PSW TO DIE"])],
    'DMSCIT': [('00449000', ["         SSM   =X'00'         GO DISABLED (EC MODE)"])],
    'DMSEDI': [('04052000', ["FE       DC    X'02'          I/O ENABLED (EC MODE)"])],
    'DMSERS': [('00675000', ["         SSM   =X'00'         INHIBIT ALL (EC MODE)"]),
               ('00735000', ["ON       DC    X'03'          I/O AND EXTERNAL (EC)"])],
    'DMSEXC': [
        ('00098475', ["         MVI   0(0),X'03'         SET PSW ENABLED (EC)"]),
        ('00098480', ["         OI    1(0),X'EC'         USER KEY, EC MODE"]),
        # NUCBREXX carries a flag in byte 0 (X'20'); BC put CC/ILC there,
        # EC requires bits 32-39 zero
        ('00098485', ["         MVC   4(4,0),NUCBREXX    SET PSW ADDRESS",
                      "         MVI   4(0),0             AMODE 24, EC BITS 32-39"]),
        ('00098685', ["         SSM   =X'00'         DISABLE INTERRUPTS (EC)"])],
    'DMSEXT': [('02356000', ["ON       DC    X'03'          ENABLE I/O, EXT (EC)"])],
    'DMSINT': [('00253000', ["         SSM   =X'03'         ENABLE I/O AND EXTERNAL"])],
    'DMSLDR': [('01505000', ["         SSM   =AL1(X'03')    TURN ON SYSTEM MASK (EC)"])],
    'DMSRNM': [('00458000', ["         SSM   =X'00'         INHIBIT ALL AGAIN (EC)"]),
               ('00501000', ["ON       DC    X'03'          I/O AND EXTERNAL (EC)"])],
    # command modules: rebuilt with CMSGEND after VMFASM
    'DMSAMS': [('00964600', ["AMSENA   DC    X'03'          I/O AND EXTERNAL (EC)"])],
    'DMSCMP': [('00609000', ["ENABLE   DC    X'03'          FOR SET SYSTEM MASK (EC)"])],
    'DMSFOR': [('00968000', ["OK81     DC    X'03'          I/O AND EXTERNAL (EC)"])],
    'DMSLFN': [('14360000', ["MASKENAB DC    X'03'          I/O AND EXTERNAL (EC)"])],
    'DMSLST': [('00781000', ["OK81     DC    X'03'          I/O AND EXTERNAL (EC)"])],
    'DMSSYN': [('00387500', ["SHOWSYS  SSM   =X'03'         PERMIT INTERRUPTS (EC)"])],
    'DMSTPE': [('00192000', ["         SSM   =X'03'         ENABLE INTERRUPTS (EC)"]),
               ('01789000', ["TPEENA   DC    X'03'          I/O AND EXTERNAL (EC)"])],
    'DMSTYP': [('00148000', ["         SSM   =X'03'         ENABLE INTERRUPTS (EC)"]),
               ('00646600', ["TYPENA   DC    X'03'          I/O AND EXTERNAL (EC)"])],
    'VMFPLC2': [('00246000', ["         SSM   =X'03'         ENABLE INTERRUPTS (EC)"]),
                ('02517000', ["TPEENA   DC    X'03'          I/O AND EXTERNAL (EC)"])],
}

PSWMODS = {
    # I-225.  DMKFREE's FREE08 computed the END of the last larger free block
    # with LA R5,0(R8,R9); for the block that reaches 16 MB that is 01000000,
    # which LA in AMODE 24 made 0, and SR R5,R2 then gave the block's address
    # as a NEGATIVE number -- FFFFF938 -- whose low 24 bits were right.  Every
    # savearea DMKSVC chained at IPL was one of these, and CP's first SVC in
    # AMODE 31 took an addressing exception at 7FFFF938 (w68).  Add, don't LA.
    'DMKFRE': [
        # I-230.  DMKERMSG's callers hand it 'doublewords || address' in one
        # register and it passes the word to DMKFRET as it is ("HIGH-ORDER
        # BYTE IS OK", 00352000): FRET's address arithmetic ignored byte 0
        # in AMODE 24.  In AMODE 31 the FRETRAP compare took an addressing
        # exception (PRG005, w104: DEF STOR after IPL CMS).  The contract
        # is kept at the callee: FRET and FRETR strip byte 0 on entry.
        # Valid until real storage passes 16 MB (M4), where every such
        # packed word has to go anyway.
        ('00495000', [
            "         LR    R5,R8          END OF LAST LARGER BLOCK: ADD,",
            "         ALR   R5,R9          NOT LA: 16 MB IS NOT 0 (I-225)",
        ]),
        ('01087000', ["DMKFRETR STM   R0,R15,FREESAVE ENTER FRETR - SAVE REGS",
                      "         N     R1,XRIGHT24    CALLERS PASS A FLAG BYTE, I-230"]),
        ('01101000', ["         STM   R0,R15,FREESAVE       - SAVE REGISTERS",
                      "         N     R1,XRIGHT24    CALLERS PASS A FLAG BYTE, I-230"]),
    ],
    # I-226.  A CCW's address word carries the command code in byte 0, and
    # CP loads it whole -- L R3,RCWADDR -- then uses the register as a BASE,
    # which AMODE 24 forgave.  DMKDGD's DGUNLOK1 did exactly that (R3 =
    # 06FFCBBC, L R2,0(,R3), addressing exception, PRG005 at AUTOLOG1's IPL
    # CMS, w71).  The strip sweep saw only the LA R2,0(,R3) copy beside it.
    # Every L of RCWADDR in the nucleus that is not followed by its own strip
    # gets one; the CCW address is a 24-bit field by definition.
    'DMKCCW': [
        ('00793000', [
            "         L     R9,RCWADDR     R9 = POINTER TO NEXT CCWS",
            "         N     R9,XRIGHT24    NO COMMAND CODE (I-226)",
        ]),
        ('04086000', [
            "TICSCAN5 L     R9,RCWADDR     SET R9 TO ADDRESS IN CCW",
            "         N     R9,XRIGHT24    NO COMMAND CODE (I-226)",
        ]),
    ],
    'DMKDGD': [
        ('00254000', [
            "         L     R1,RCWADDR     DATA ADDRESS INTO R1, AND",
            "         N     R1,XRIGHT24    NO COMMAND CODE (I-226)",
        ]),
        ('00286000', [
            "         L     R1,RCWADDR     DATA ADDRESS INTO R1, AND",
            "         N     R1,XRIGHT24    NO COMMAND CODE (I-226)",
        ]),
        ('00646000', [
            "DGUNLOK1 L     R3,RCWADDR     ADDRESS INTO R3 (CC STILL SET)",
            "         N     R3,XRIGHT24    R3 IS A BASE BELOW (I-226)",
        ]),
    ],
    # I-232.  More of the I-226 class, found by `grep 'L  *R.*,RCWADDR'`
    # once IPL 190 reached DMKUNT's IDA path (w109, PRG005 at UNT+E2):
    # every load of RCWADDR that is then used as a base without a strip
    # of its own.  DMKVCA is the virtual CTCA, fixed for completeness.
    'DMKUNT': [
        ('00222450', ["         L     R5,RCWADDR     GET DATA ADDRESS IN THE CCW",
                      "         N     R5,XRIGHT24    IDASET USES IT AS A BASE, I-232"]),
        ('00378000', ["UNREL5   L     R5,RCWADDR     RESTORE R5 (IN CASE LOST)",
                      "         N     R5,XRIGHT24    NO COMMAND CODE (I-232)"]),
    ],
    'DMKTRK': [
        ('00360000', ["         L     R15,RCWADDR    GET FILE MASK POINTER.",
                      "         N     R15,XRIGHT24   NO COMMAND CODE (I-232)"]),
        ('00507000', ["         L     R4,RCWADDR     FOLLOW TIC",
                      "         N     R4,XRIGHT24    NO COMMAND CODE (I-232)"]),
    ],
    'DMKVCA': [
        ('00361000', ["         L     R9,RCWADDR     LOAD NEXT CCW ADDRESS",
                      "         N     R9,XRIGHT24    NO COMMAND CODE (I-232)"]),
        ('01171000', ["         L     R9,RCWADDR     TAKE THE CCW TRANSFER",
                      "         N     R9,XRIGHT24    NO COMMAND CODE (I-232)"]),
        ('01604000', ["         L     R1,RCWADDR     GET ADDRESS OF FIRST IDAW",
                      "         N     R1,XRIGHT24    NO COMMAND CODE (I-232)"]),
    ],
    'DMKDIB': [
        ('01063000', [
            "         L     R9,RCWADDR     GET NEXT CCW ADDRESS",
            "         N     R9,XRIGHT24    NO COMMAND CODE (I-226)",
        ]),
    ],
    # I-228.  BALR Rx,0 saved the condition code in AMODE 24 (byte 0 of Rx
    # = ILC, CC, program mask) and SPM Rx restored it.  In AMODE 31 BALR
    # stores bit 0 and a 31-bit address and no condition code, so every
    # such restore gave CC 0: DMKLNK took CC 0 from DMKSCNVU's CC 3 and
    # refused every directory LINK as 'ALREADY DEFINED' (w83 trace).  IPM
    # (XAOPS) puts CC and mask in the same bits in either mode.  The BALR
    # Rx,0 sites that only ESTABLISH ADDRESSABILITY are left: a base
    # register ignores bit 0.  tools/strips.py lists both kinds.
    'DMKCPI': sorted(PSWMODS_CPI + TRACESUBS['DMKCPI'] + [
        ('00510000', ["         IPM   R15            SET CONDITION CODE IN REG"]),
        ('00530000', ["         IPM   R15            SAVE CC IN CASE OF ERROR"]),
    ], key=lambda c: int(c[0])),
    'DMKCNS': TRACESUBS['DMKCNS'],
    'DMKIOS': TRACESUBS['DMKIOS'],
    'DMKVSJ': TRACESUBS['DMKVSJ'],
    'DMKCQR': [
        ('00595000', ["         IPM   R15            CC BITS IN REG (I-228)"]),
    ],
    'DMKCSP': [
        ('00885250', ["         IPM   R0             SAVE CONDITION CODE"]),
    ],
    'DMKEPS': [
        ('00220000', ["PASSCHK1 IPM   R2             SAVE CONDITION CODE"]),
        ('00227300', ["         IPM   R2             SAVE CC - GOOD FOR REJECT"]),
    ],
    'DMKLNK': [
        ('00654200', ["         IPM   R15            PRESERVE COND CODE FROM SCNVU"]),
    ],
    'DMKLOG': [
        ('00616000', ["         IPM   R15            GET THE CONDITION CODE"]),
    ],
    'DMKPAG': [
        ('01153000', ["         IPM   R15            CC BITS IN REG (I-228)"]),
    ],
    'DMKRPA': [
        ('00217000', ["         IPM   R15            SAVE CONDITION CODE"]),
    ],
    'DMKTCS': [
        ('00791000', ["         IPM   R6             SAVE CONDITION CODE"]),
    ],
    'DMKTRC': [
        ('01385520', ["         IPM   R0             SAVE C.C."]),
    ],
    'DMKVSI': [
        ('00208000', ["         IPM   R0             PRESERVE CONDITION CODE"]),
    ],
    # DMKVSJ 00176000 (BALR R0,0 for CLRCH) is inside the block XA0018DK removed.
    'DMKMCH': [
        ('01252000', ["         DC    X'80',AL3(ENBHARD) AMODE 31 (I-224)"]),
        ('01255000', ["         DC    X'80',AL3(MCHTERM2) HARD MCKS IN TERM, 31"]),
        ('01258000', ["         DC    X'80',AL3(SPFMSG)  AMODE 31"]),
        ('01261000', ["         DC    X'80',AL3(SPFTERMA) AMODE 31"]),
        ('01264000', ["         DC    X'80',AL3(TERM)    SECONDARY HANDLER, 31"]),
    ],
}

SHRMODS = {
    'DMKCFG': [
        # PAGBLDTB extends a small machine's tables to reach the saved
        # pages.  `N R1,=X'FFF0FFFF'` rounded the first page to a 64 KB
        # segment, so a 2 MB AUTOLOG1 got a 48-entry table for segment 15
        # (PTL 2) while the saved pages are its pages 128-175: LRA took a
        # segment-translation exception, TRANS answered CC2, and the model
        # could not be loaded (the stage-A failure, I-195, seen again).
        # Round to the megabyte: 256-page tables, whole segments.
        ('00665000', [
            "         N     R1,=X'FF00FFFF' FIRST PAGE TO ITS SEGMENT",
            "         O     R1,F255        LAST PAGE TO ITS SEGMENT'S END",
        ]),
        # SHRTFND falls into SHRCOPY; SHRTBLD reaches SHRCOPY1 after it has
        # built and chained the SHRTABLE (replaces the SHRSLOOP block that
        # stored the shared page table into the user's STE).
        ('00878000', '00916000', [
            "SHRCOPY  DS    0H             R8 -> SHRPAGE, R9 GROUP INDEX",
            "         L     R2,0(,R8)      THE MODEL'S STE-FORM ENTRY",
            "         N     R2,=A(SEGPTOM) THE MODEL'S PTO",
            "         SR    R7,R7          ...",
            "         IC    R7,SYSHRSEG(R9) 64 KB SEGMENT NUMBER",
            "         LR    R1,R7          ...",
            "         SRL   R1,4           ITS 1 MB SEGMENT",
            "         SLL   R1,2           STE INDEX",
            "         L     R10,VMSEG      THE DESIGNATION",
            "         N     R10,=A(SEGSTOM) WITHOUT THE LENGTH",
            "         L     R10,0(R1,R10)  THE USER'S STE",
            "         N     R10,=A(SEGPTOM) THE USER'S PTO",
            "         BZ    MODERR0        NONE -- PAGLOOP BUILT ONE",
            "         N     R7,F15         GROUP WITHIN THE MEGABYTE",
            "         SLL   R7,6           TIMES 16 PTES OF 4",
            "         LA    R1,0(R7,R10)   THE USER'S FIRST PTE",
            "         LA    R14,0(R7,R2)   THE MODEL'S FIRST PTE",
            "         MVC   0(64,R1),0(R14) THE 16 FRAMES",
            "         SLL   R7,1           TIMES 16 SWAP ENTRIES OF 8",
            "         LA    R1,SWPOFF(R7,R10) THE USER'S SWAP ENTRIES",
            "         LA    R14,SWPOFF(R7,R2) THE MODEL'S",
            "         MVC   0(128,R1),0(R14) 16 SWAP ENTRIES, SWPSHR ON",
            "         LA    R8,L'SHRPAGE(,R8) NEXT GROUP",
            "         LA    R9,1(,R9)      ...",
            "         BCT   R3,SHRCOPY     ALL OF THEM",
            "         OI    VMESTAT,VMINVPAG THE TLB HELD THE OLD ENTRIES",
            "         OI    APSTAT2,CPPTLBR ...",
            "         PTLB  ,              ...",
            "         B     SETVMSHR       GO CLEAN UP AND GET OUT",
            "SHRCOPY1 L     R3,SAVEWRK8    GROUPS IN THE SYSTEM",
            "         LR    R14,R3         FIRST SHRPAGE, AS FNDSHRPG",
            "         LA    R8,SHRSEGNM    ...",
            "FNDSHRP1 LA    R8,L'SHRPAGE(,R8) ...",
            "         S     R14,F4         ...",
            "         BP    FNDSHRP1       ...",
            "         SR    R9,R9          FIRST GROUP",
            "         B     SHRCOPY        COPY THE MODELS TO THIS USER",
        ]),
        # SHRTBLD: build the models (replaces SEGLOOP/APSEGLP, which adopted
        # the user's tables).  Falls into the USING pair and COMMON, which
        # chains the SHRTABLE.
        ('00958000', '01064000', [
            "         LA    R14,SHRSEGNM(R7) LOAD ADDRESS OF FIRST SHRPAGE",
            "         ST    R14,SAVEWRK7   ...",
            "         ST    R3,SAVEWRK8    GROUPS IN THE SYSTEM",
            "         SR    R9,R9          FIRST GROUP",
            "MODLOOP  DS    0H             ONE MODEL TABLE PER GROUP",
            "         SR    R7,R7          ...",
            "         IC    R7,SYSHRSEG(R9) 64 KB SEGMENT NUMBER",
            "         SRL   R7,4           ITS 1 MB SEGMENT",
            "         LR    R1,R7          ...",
            "         SLL   R1,24          FIRST PAGE, HIGH HALFWORD",
            "         LR    R2,R7          ...",
            "         SLL   R2,8           ...",
            "         LA    R2,255(,R2)    LAST PAGE OF THE SEGMENT",
            "         OR    R1,R2          DMKBLDRT'S RANGE",
            "         CALL  DMKBLDRT,PARM=PAGTONLY+NEWPAGES R2 = STE",
            "         N     R2,=A(X'FFFFFFFF'-SEGINVAL) VALID FORM",
            "         L     R8,SAVEWRK7    ...",
            "         ST    R2,0(,R8)      SHRPAGE: THE MODEL",
            "         N     R2,=A(SEGPTOM) THE MODEL'S PTO",
            "         LR    R10,R2         ...",
            "         SL    R10,=A(PAGPFRA-PAGSTMP) ITS HEADER",
            "         MVC   PAGACT-PAGTABLE(4,R10),F1 ACTIVE 0, TOTAL 1",
            "         ST    R5,PAGSHR-PAGTABLE(,R10) THE NAMED SYSTEM",
            "         MVC   PAGTSWP+SWPVM-SWPTABLE(4,R10),ASYSVM SYSTEM",
            "*  THE USER'S TABLE HOLDS THE SAVED COPY'S DASD SLOTS AND",
            "*  KEYS (PAGLOOP): COPY THE GROUP'S 16 SWAP ENTRIES OVER.",
            "         SR    R7,R7          ...",
            "         IC    R7,SYSHRSEG(R9) 64 KB SEGMENT NUMBER",
            "         LR    R1,R7          ...",
            "         SRL   R1,4           ...",
            "         SLL   R1,2           STE INDEX",
            "         L     R14,VMSEG      THE DESIGNATION",
            "         N     R14,=A(SEGSTOM) WITHOUT THE LENGTH",
            "         LA    R14,0(R1,R14)  THE USER'S STE",
            "         ST    R14,SAVEWRK2   ...",
            "         L     R14,0(,R14)    ...",
            "         N     R14,=A(SEGPTOM) THE USER'S PTO",
            "         BZ    MODERR0        NONE -- PAGLOOP BUILT ONE",
            "         N     R7,F15         GROUP WITHIN THE MEGABYTE",
            "         SLL   R7,7           TIMES 16 ENTRIES OF 8",
            "         LA    R14,SWPOFF(R7,R14) THE USER'S SWAP ENTRIES",
            "         LA    R10,SWPOFF(R7,R2) THE MODEL'S",
            "         MVC   0(128,R10),0(R14) 16 SWAP ENTRIES",
            "         LA    R1,16          ...",
            "MODFLAG  OI    0(R10),SWPSHR  SHARED",
            "         LA    R10,8(,R10)    ...",
            "         BCT   R1,MODFLAG     ...",
            "*  BRING THE GROUP IN THROUGH THIS USER'S ADDRESS SPACE WITH",
            "*  THE MODEL IN THE STE, LOCKED; THE FRAMES GO TO SYSTEM.",
            "         L     R14,SAVEWRK2   THE USER'S STE",
            "         L     R1,0(,R14)     ...",
            "         ST    R1,SAVEWRK4    TO RESTORE",
            "         L     R2,0(,R8)      THE MODEL",
            "         ST    R2,0(,R14)     IN THE STE FOR NOW",
            "         PTLB  ,              ...",
            "         SR    R7,R7          ...",
            "         IC    R7,SYSHRSEG(R9) 64 KB SEGMENT NUMBER",
            "         SLL   R7,16          ITS VIRTUAL ADDRESS",
            "         LA    R1,16          ...",
            "         ST    R1,SAVEWRK3    PAGES TO GO",
            "BRINGLP  L     R14,0(,R8)     THE MODEL",
            "         N     R14,=A(SEGPTOM) ITS PTO",
            "         LR    R1,R7          THE PAGE",
            "         SRL   R1,12          ...",
            "         N     R1,F255        WITHIN THE SEGMENT",
            "         SLL   R1,3           TIMES PAGSWPE",
            "         ALR   R14,R1         ...",
            "         L     R1,SWPOFF+4(,R14) THE SAVED COPY'S DASD SLOT",
            "         LTR   R1,R1          IS THERE ONE? (GCCLIB: 13 OF 16",
            "         BNZ   BRINGDO        YES",
            "         NI    SWPOFF(R14),X'FF'-SWPSHR NO: PRIVATE ZERO PAGE",
            "         B     BRINGNX        FOR EVERY USER, NOTHING TO READ",
            "BRINGDO  LR    R1,R7          THE PAGE",
            "         TRANS 2,1,OPT=(BRING,DEFER,LOCK)",
            "         BNZ   MODERR         CANNOT READ THE SAVED SYSTEM",
            "         LR    R1,R2          THE FRAME",
            "         SRL   R1,8           A CORTABLE ENTRY IS 16 A PAGE",
            "         AL    R1,ACORETBL    ...",
            "         L     R14,CORFPNT-CORTABLE(,R1) THE OWNER SO FAR",
            "         LH    R0,VMPAGES-VMBLOK(,R14) ...",
            "         BCTR  R0,0           ONE LESS FOR HIM",
            "         STH   R0,VMPAGES-VMBLOK(,R14) ...",
            "         L     R14,ASYSVM     SYSTEM OWNS SHARED FRAMES",
            "         ST    R14,CORFPNT-CORTABLE(,R1) ...",
            "         LH    R0,VMPAGES-VMBLOK(,R14) ...",
            "         AL    R0,F1          ONE MORE FOR IT (I-237)",
            "         STH   R0,VMPAGES-VMBLOK(,R14) ...",
            "BRINGNX  A     R7,F4096       NEXT PAGE",
            "         L     R1,SAVEWRK3    ...",
            "         BCTR  R1,0           ...",
            "         ST    R1,SAVEWRK3    ...",
            "         LTR   R1,R1          ...",
            "         BNZ   BRINGLP        ALL 16",
            "         L     R14,SAVEWRK2   THE USER'S STE",
            "         L     R1,SAVEWRK4    ...",
            "         ST    R1,0(,R14)     HIS OWN TABLE AGAIN",
            "         PTLB  ,              ...",
            "         LA    R9,1(,R9)      NEXT GROUP",
            "         L     R8,SAVEWRK7    ...",
            "         LA    R8,L'SHRPAGE(,R8) ...",
            "         ST    R8,SAVEWRK7    ...",
            "         BCT   R3,MODLOOP     ALL GROUPS",
            "         B     COMMON         CHAIN THE SHRTABLE",
            "MODERR   L     R14,SAVEWRK2   THE USER'S STE",
            "         L     R1,SAVEWRK4    ...",
            "         ST    R1,0(,R14)     HIS OWN TABLE AGAIN",
            "         PTLB  ,              ...",
            "MODERR0  LH    R10,SYSPAGNM   FIRST SAVED PAGE, FOR NAMPERR1",
            "         SLL   R10,12         ...",
            "         B     NAMPERR1       CLEAR UP TABLES AND EXIT",
        ]),
        # COMMON's last card: after chaining, copy the models to this user.
        ('01076000', [
            "         ST    R5,SHRBPNT-SHRTABLE(,R7) CHANGE BKWD POINTER",
            "         B     SHRCOPY1       NOW THIS USER'S OWN COPIES",
        ]),
        # The offset of swap entry 0 from the PTO.  An EQU must follow the
        # DSECTs it names (IFO231 otherwise), so it sits after the COPYs.
        ('01591000', [
            "         COPY  VMBLOK",
            "SWPOFF   EQU   PAGTSWP-(PAGPFRA-PAGSTMP)+(SWPFLAG-SWPVM)",
        ]),
    ],
    # A user's copies of a model are DROPPED on release, not skipped: the
    # frame is SYSTEM's and locked, the DASD slot is the saved system's, but
    # the PTE copy is valid and DMKBLDRL's CHKPAGE abends (BLD002) on any
    # valid PTE when it frees the table at logoff.  PARTIAL keeps them.
    'DMKPGS': [
        # I-223: the release walk's three TRANS take clean page addresses
        # that CP itself computed over the whole machine; without AMODE31
        # DMKPTRAN masked 01000000 to 0 and the walk never left 16 MB (CP
        # looped at RELLOOP on the IPL after a 32M session, w61).
        ('00822500', [
            "         TRANS 2,1,OPT=(DEFER,AMODE31) PAGE NOT IN TRANSIT?",
        ]),
        ('00962000', [
            "         TRANS 7,1,OPT=(DEFER,AMODE31) ENQUEUE ON SEGMENT",
        ]),
        ('01066000', [
            "         BO    SHRDROP        YES -- DROP OUR COPY OF IT",
        ]),
        ('01071000', [
            "         TRANS 7,1,OPT=(DEFER,AMODE31) ENQUEUE ON PAGE",
        ]),
        ('01248000', [
            "         B     RELEXIT        RETURN TO CALLER",
            "SHRDROP  TM    SAVEWRK1,PARTIAL KEEP THE NAMED SYSTEM?",
            "         BO    NEXTPAGE       YES",
            "         MVC   PAGPFRA,=A(PAGINVW) OUR COPY OF THE MODEL PTE",
            "         XC    SWPFLAG(8),SWPFLAG AND OF ITS SWAP ENTRY",
            "*  LEAVE A FRESH ZERO-PAGE ENTRY, AS DMKBLDRT MAKES THEM: A",
            "*  SWAP ENTRY WITH NEITHER SWPRECMP NOR A DASD SLOT IS ONE",
            "*  DMKPGTPR ABENDS ON (PGT005) -- DMKPGSPO RESCANS (REPEAT).",
            "         MVI   SWPFLAG,SWPRECMP ZERO PAGE, NOTHING TO RELEASE",
            "         LR    R0,R1          THE VIRTUAL ADDRESS",
            "         SRL   R0,12          ITS PAGE NUMBER",
            "         STC   R0,SWPVPAGE    WITHIN THE SEGMENT",
            "         OI    VMESTAT,VMINVPAG THE TLB MAY HOLD IT",
            "         OI    APSTAT2,CPPTLBR ...",
            "         B     NEXTPAGE       NOT OURS TO FREE",
        ]),
    ],
    # A named system's DCSS (GCCLIB, segments 242-243) now lives in the same
    # megabyte as CMS's shared pages, so LOADSYS reaches DMKBLDRT for a
    # segment that already has a full table carrying another system's
    # copies.  BLDTHEM "released the old page tables and built new ones" --
    # 16-entry tables, in S/370 -- and DMKBLDRL's CHKPAGE abended (BLD002,
    # AUTOLOG1 at CP init) on the first valid PTE copy.  A 256-entry table
    # is already everything a segment can have: keep it.  And a PTE whose
    # swap entry is SWPSHR is a copy, not an allocation: let it go.
    'DMKBLD': [
        ('00311000', [
            "         TM    SEGPTO+3,SEGPTLF A FULL TABLE ALREADY?",
            "         BO    SKIPBLD        YES - NOTHING TO BUILD",
            "         CLI   SAVER2+3,OLDVMSEG+KEEPSEGS+NEWPAGES+NEWSEGS",
        ]),
        ('00626600', [
            "         L     R1,SEGPTO      THE PTO",
            "         N     R1,=A(SEGPTOM) ...",
            "         LR    R0,R7          THIS PTE",
            "         SR    R0,R1          ITS INDEX TIMES 4",
            "         AR    R0,R0          TIMES 8: THE SWAP ENTRY",
            "         AR    R1,R0          IN R1: BASE R0 MEANS NO BASE",
            "         TM    SWPOFF(R1),SWPSHR A COPY OF A MODEL'S?",
            "         BO    NXTPAGE        YES - NOT AN ALLOCATION",
            "         ABEND 2              ERROR - PAGE NOT RELEASED",
        ]),
        ('00957000', [
            "         COPY  TIMER",
            "SWPOFF   EQU   PAGTSWP-(PAGPFRA-PAGSTMP)+(SWPFLAG-SWPVM)",
        ]),
    ],
    # DMKVMASH scans a user's shared pages for change bits.  SHRSEGNM holds
    # 64 KB segment numbers: the STE is the number's high nibble, the pages
    # are the low nibble's 16 within it (the XA0036DK card scanned the whole
    # megabyte -- private pages too -- and one PTE past it).  A model frame
    # is CORIOLCK'd: unlock it before it is freed, and invalidate the
    # model's PTE (CORPGPNT) as well as this user's copy.  Other sharers'
    # copies are M3's next increment.
    'DMKVMA': [
        ('00192000', '00205000', [
            "         SLR   R8,R8          ...",
            "         IC    R8,SHRSEGNM(R3) 64 KB SEGMENT NUMBER",
            "         LR    R4,R8          ...",
            "         SRL   R8,4           ITS 1 MB SEGMENT",
            "         SLL   R8,2           STE INDEX",
            "         L     R6,VMSEG       THE DESIGNATION",
            "         N     R6,=A(SEGSTOM) WITHOUT THE LENGTH",
            "         ALR   R8,R6          THE STE",
            "         TM    SEGPTO+3,SEGINVAL SEGMENT INVALID",
            "         BO    NXTSEG1        YES, SKIP SCANNING",
            "         L     R6,SEGPTO      THE PTO",
            "         N     R6,=A(SEGPTOM) WITHOUT THE FLAGS",
            "         N     R4,F15         GROUP WITHIN THE MEGABYTE",
            "         SLL   R4,6           TIMES 16 PTES OF 4",
            "         LR    R5,R4          ...",
            "         AR    R5,R5          TIMES 16 SWAP ENTRIES OF 8",
            "         AR    R5,R6          ...",
            "         LA    R5,SWPOFF(,R5) THE GROUP'S FIRST SWAP ENTRY",
            "         ALR   R6,R4          THE GROUP'S FIRST PTE",
            "         LA    R4,16          ITS 16 PAGES",
            "         CNOP  0,8            ALIGN",
            "PAGEISK  TM    0(R5),SWPSHR   A SHARED PAGE AT ALL? (A GROUP",
            "         BZ    INVAL          MAY END SHORT: GCCLIB 13 OF 16)",
            "         TM    PAGPFRA+2,PAGINV IS PAGE IN STORAGE?",
            "         BO    INVAL          NO - GET NEXT PAGE ENTRY",
        ]),
        # XA0036DK made 00206000 load the fullword PTE but left the S/370
        # `SLL R2,8` that turned a halfword PAGCORE into an address: the frame
        # address was shifted off the top, ISKE read some other frame's key,
        # and a stray change bit made DMKVMASH free a frame CMS was using --
        # the first IPL CMS under frame sharing looped on page faults.  Never
        # exercised before because no shared system had ever IPLed here.
        ('00207000', [
            "         N     R2,=A(PAGPFRM) THE FRAME ADDRESS, NO FLAGS",
        ]),
        # 00215000 itself was renumbered by XA0036DK, and UPDATE needs the
        # start of a range to exist: anchor one card earlier.
        ('00214000', '00216000', [
            "         BNZ   PROTVIOL       IF SO - USER BECOMES NON-SHARED",
            "INVAL    LA    R6,PAGPFRA+L'PAGPFRA NEXT PAGE TABLE ENTRY",
            "         LA    R5,8(,R5)      AND ITS SWAP ENTRY",
            "         BCT   R4,PAGEISK     IF MORE PAGES, PROCESS ALL",
        ]),
        ('00465000', [
            "         TM    CORFLAG,CORCFLCK+CORIOLCK FRAME LOCKED?",
        ]),
        ('00489000', [
            "         L     R15,CORPGPNT   THE MODEL'S PTE",
            "         LTR   R15,R15        ...",
            "         BZ    *+10           NONE",
            "         MVC   0(4,R15),=A(PAGINVW) INVALIDATE IT TOO",
            "         SLR   R15,R15        ZIP REG",
        ]),
        ('00576000', [
            "         COPY  SYSTBL",
            "SWPOFF   EQU   PAGTSWP-(PAGPFRA-PAGSTMP)+(SWPFLAG-SWPVM)",
        ]),
    ],
}

CONSMODS = {

    # I-207.  The console could not look above 16 MB in a 32M machine: DISPLAY
    # and STORE take a hexloc of at most six digits (DMKCDB FLDLEN = F6, DMKCDS
    # CL R0,F6 twice), and DISPLAY printed every address through STCM
    # R0,B'0011' -- the low six of DMKCVTBH's eight digits.  Eight digits now:
    # the hexloc may be eight, and the line header is eight digits followed by
    # two blanks, so data still starts at BUFBUF+10 and nothing else moves.
    # The 'addr TO addr text' lines (suppressed, non-addressable, KEY) grow by
    # two: TO at +9, the second address at +12, text at +21 (was +19) or +20
    # their byte counts follow; the KEY = line keeps its two blanks (+21, +27, 29).  DMKCVTHB itself takes any
    # length.  I-207.
    # I-208.  The console's hexloc is a clean 31-bit address whatever mode
    # the guest is in, so STORE's and DISPLAY's TRANS say so (OPT=AMODE31)
    # and reach storage above 16 MB; every other TRANS in CP still masks to
    # 24 bits (34-AMODE31).  Two LA address sums on the way become adds.
    'DMKCDS': [
        ('00408000', [
            "         CL    R0,F8          FIELD LONGER THAN EIGHT CHARS ?",
        ]),
        ('00459000', [
            "         C     R0,F8          ADDRESS FIELD LONGER THAN 8 ?",
        ]),
        ('00511000', [
            "         TRANS 2,1,OPT=(BRING,DEFER,AMODE31),ADEX=CDS164",
        ]),
    ],
    'DMKCDB': [
        ('00657000', [
            "         MVC   FLDLEN(4),F8   SET MAX FIELD LENGTH, 8 DIGITS",
        ]),
        ('00975000', [
            "         TRANS 2,1,OPT=(BRING,DEFER,AMODE31) USER PAGE (31)",
        ]),
        # non-addressable page, 'addr TO addr NON-ADDRESSABLE STORAGE'
        ('00982100', '00983100', [
            "         STCM  R0,B'1111',BUFBUF EIGHT DIGITS",
            "         STCM  R1,B'1111',BUFBUF+4",
        ]),
        ('00985000', '00987000', [
            "         MVC   BUFBUF+9(2),=C'TO'",
            "         MVC   BUFBUF+21(23),=C'NON-ADDRESSABLE STORAGE'",
            "         MVC   BFRCNT,=AL2(21+23) SET BYTE COUNT",
        ]),
        ('00993100', '00994100', [
            "         STCM  R0,B'1111',BUFBUF+12 EIGHT DIGITS",
            "         STCM  R1,B'1111',BUFBUF+16",
        ]),
        ('01000300', [
            "         CALL  DMKPTRAN,PARM=DEFER+AMODE31 LET PTRAN HANDLE",
        ]),
        # I-209.  DISPLAY K (GETKEY) was converted only as far as the STE
        # (XA0036DK); the page half still read a 2-byte PTE, a 16-entry swap
        # table at PTO+40, and ISK -- an operation exception on ESA/390, so
        # `d kff0000` took CP down with PRG001.  The page number is eight bits
        # at 12-19, the swap entry is PAGSWPE bytes at PAGTSWP from the table
        # header, the PTE is a fullword with PAGINV in byte 2, and the real
        # key comes from ISKE on the 4 KB frame (R-12: one key per frame).
        ('01056900', [
            "         TRANS 2,1,OPT=(DEFER,AMODE31) LET PTR CHECK SEGMENT",
        ]),
        ('01062200', '01081000', [
            "         L     R2,0(,R3)      THE STE",
            "         LR    R3,R2          ...",
            "         N     R3,=A(SEGPTOM) PAGE TABLE ORIGIN",
            "         N     R2,=A(SEGPTLF) PTL, UNITS OF 16 ENTRIES",
            "         LA    R2,1(,R2)      ...",
            "         SLL   R2,4           PAGES IN THIS SEGMENT",
            "         SR    R14,R14        ZERO WORK REGISTER",
            "         SLDL  R14,8          PAGE NUMBER, BITS 12-19",
            "         CR    R14,R2         WITHIN THE PAGE TABLE ?",
            "         BNL   INVDKEY        NO - THATS MORE THAN WE HAVE",
            "         SLL   R14,3          TIMES PAGSWPE",
            "         LA    R2,PAGTSWP-(PAGPFRA-PAGSTMP)+8(,R3) SWPFLAG 0",
            "         SRL   R14,1          SET UP FOR 2ND HALF PAGE",
            "         SLDL  R14,1          ADD 1 IF 2ND HALF OF PAGE",
            "         SR    R1,R1          ZERO REGISTER",
            "         IC    R1,SWPKEY1-SWPFLAG(R14,R2) VIRTUAL KEY",
            "         SRL   R14,1          PAGE NUMBER TIMES 4",
            "         LA    R3,0(R14,R3)   LOAD PAGE TABLE ENTRY ADDRESS",
            "         SR    R2,R2          CLEAR FOR ISKE (OR LACK OF IT)",
            "         TM    2(R3),PAGINV   IS THE PAGE IN STORAGE ?",
            "         BO    GOTPART        BRANCH IF NO",
            "         L     R14,0(,R3)     THE PTE",
            "         N     R14,=A(PAGPFRM) REAL PAGE ADDRESS",
            "         ISKE  R2,R14         GET THE REAL STORAGE KEY",
        ]),
        # DISPLAY KEY: 'addr TO addr KEY = kk'
        ('01100000', [
            "         MVC   BUFBUF+21(5),KEYEQ  MOVE 'KEY =' TO BUFFER",
        ]),
        ('01103000', '01104000', [
            "         STCM  R1,B'0011',BUFBUF+27 KEY, ODD OFFSET (I-217)",
            "         LA    R1,29          STANDARD LINE LENGTH",
        ]),
        ('01107000', [
            "         MVC   BUFBUF+21(23),=C'NON-ADDRESSABLE STORAGE'",
        ]),
        ('01112100', '01114000', [
            "         STCM  R0,B'1111',BUFBUF EIGHT DIGITS",
            "         STCM  R1,B'1111',BUFBUF+4",
            "         MVC   BUFBUF+9(2),=C'TO'",
        ]),
        # I-208: 'LA R1,2047(R1)' in AMODE 24 drops bits 0-7, so the end of a
        # key line above 16 MB printed as 00FF07FF.  Add, do not LA.
        ('01116000', [
            "         A     R1,=F'2047'    ADD 2047 (NOT LA) I-208",
        ]),
        ('01118100', '01119100', [
            "         STCM  R0,B'1111',BUFBUF+12 EIGHT DIGITS",
            "         STCM  R1,B'1111',BUFBUF+16",
        ]),
        # suppressed duplicate lines: 'addr TO addr SUPPRESSED ...'
        ('01379100', '01380100', [
            "         STCM  R0,B'1111',BUFBUF EIGHT DIGITS",
            "         STCM  R1,B'1111',BUFBUF+4",
        ]),
        ('01382000', '01384000', [
            "         MVC   BUFBUF+9(2),=C'TO'",
            "         MVC   BUFBUF+21(L'SUPPLMSG),SUPPLMSG MESSAGE TEXT",
            "         MVC   BFRCNT,=AL2(L'SUPPLMSG+21) SET BYTE COUNT",
        ]),
        ('01400100', '01401100', [
            "         STCM  R0,B'1111',BUFBUF+12 EIGHT DIGITS",
            "         STCM  R1,B'1111',BUFBUF+16",
        ]),
        # the ordinary line header: eight digits, data at +10 as before
        ('01408100', '01409100', [
            "         STCM  R0,B'1111',BUFBUF EIGHT DIGITS",
            "         STCM  R1,B'1111',BUFBUF+4",
        ]),
        ('01428000', [
            "         ISKE  R1,R2          GET THE REAL STUFF, 4 KB FRAME",
        ]),
        ('01454000', [
            "         TRANS 2,1,OPT=(BRING,DEFER,AMODE31) ADDRESS OK?",
        ]),
        # 'LA R1,1(R14,R1)' summed the second page's address in 24 bits
        ('01471100', [
            "         ALR   R1,R14         2ND PAGE ADDRESS: ADD, NOT LA",
            "         AL    R1,F1          (31-BIT, I-208)",
        ]),
        ('01471110', [
            "         TRANS 2,1,OPT=(BRING,DEFER,AMODE31)",
        ]),
        # GETKEY now names PAGTSWP, PAGPFRA, PAGSTMP, SWPKEY1 and SWPFLAG,
        # which live in CORE COPY; DMKCDB never copied it (it wrote 16*2+8).
        ('01669000', [
            "         COPY  VMBLOK",
            "         COPY  CORE",
        ]),
    ],
}

STORMODS = {

    # I-203.  DEFINE STORAGE 32M answered STORAGE MISSING OR INVALID -- not the
    # directory maximum (that is message 094, EXCEEDS ALLOWED MAXIMUM) but
    # DMKDEH's own parser: CL R1,F16 for nnM and CL R1,=F'16384' for nnnnnK,
    # and a five-character limit on the K form.  The ceiling the converted CP
    # can actually honour today is 256 MB: DMKBLDRT takes its page range as
    # two 16-bit page numbers (I-185), so 65,536 pages.  That is the number
    # here -- a parameter named in one place, not a guess spread over three --
    # and raising it further is M5 work on the DMKBLD interface, not on this
    # module.  The STORAGE = nnnnnK message grows to six digits with it, since
    # 262144K has six; DMKCVTBD returns eight zero-filled digits in R0:R1 and
    # the original already showed leading zeros below 10 MB.
    # DMKDIR is the DIRECT command -- a standalone CP utility, built into the
    # CMS DIRECT MODULE with LOAD and GENMOD -- and it refused 32M, 64M and
    # 256M at CE's own console: DMKDIR751E INVALID OPERAND.  One compare, the
    # same 16 MB, the same 256 MB ceiling.  UMACMCOR is a fullword and needs
    # nothing.  I-203.
    'DMKDIR': [
        ('01133000', [
            "         CL    R3,=F'268435456' OVER THE MAX, 256M?",
        ]),
    ],
    'DMKDEH': [
        ('00170000', [
            "         C     R0,F6          PARM COUNT OVER 6 ? (000000K)",
        ]),
        ('00178000', [
            "         CL    R1,=F'256'     ASKING FOR MORE THAN 256 MEG?",
        ]),
        ('00183000', [
            "         CL    R1,=F'262144'  ASKING FOR MORE THAN 256 MEG?",
        ]),
        ('00244000', [
            "         STCM  R0,B'0011',SAVEWRK4+1 SIX-DIGIT NUMBER",
        ]),
    ],
}

# SAVEDMODS -- the unshared-CMS stage A for wall 24 -- was built and RETRACTED
# on 4 October (I-195): with SYSHRSG removed, every autologged CMS user whose
# machine is smaller than 16 MB (AUTOLOG1 first) must load pages at 15.5 MB it
# cannot address, and CP initialisation stops after AUTO LOGON AUTOLOG1 with no
# DMKCPI966I.  Only SHARED segments were ever allowed outside the virtual
# machine; the frame-level design in 05 is the fix, not a DMKSNT edit.

DATMODS = {

    # One flagged site and one silent neighbour.  The silent one is the address
    # split: a segment is 1 MB now, so 16 bits of segment number become 20.
    'DMKCFH': [
        ('00334000', [
            "         L     R2,VMSEG       GET SEGTABLE ADDRESS",
            "         N     R2,=A(SEGSTOM) WITHOUT THE LENGTH",
        ]),
        ('00336000', [
            "         SRDL  R0,20          SEGMENT TO LOW ORDER OF R0,",
        ]),
        ('00339000', [
            "         TM    3(R2),SEGINVAL VALID SEGMENT",
        ]),
        ('00344000', [
            "         L     R2,0(,R2)      ADDRESS OF PAGTABLE",
            "         N     R2,=A(SEGPTOM) WITHOUT THE FLAGS",
        ]),
        ('00345000', Deck.comment(
            "AFTER SRDL 20 THE PAGE-WITHIN-SEGMENT FIELD IS R1 BITS 0-7, NOT "
            "0-3, SO IT RIGHT-JUSTIFIES WITH 24 RATHER THAN 28.") + [
            "         SRL   R1,24          SHIFT PAGE TO LOWORDER OF R1",
        ]),
        ('00347000', [
            "         LA    R2,256*L'PAGPFRA+(SWPFLAG-SWPVM)(R1,R2)",
        ]),
    ],

    # The swap-table address computed from the page table, half symbolically:
    # `16*L'PAGCORE` becomes `256*L'PAGPFRA`, and the page-within-segment field
    # widens from four bits to eight.
    'DMKVMD': [
        ('00886000', [
            "         L     R1,VMSEG            SEGMENT TABLE BASE",
            "         N     R1,=A(SEGSTOM)      WITHOUT THE LENGTH",
        ]),
        ('00888000', [
            "         SRDL  R14,20              GET SEGMENT NUMBER ONLY",
        ]),
        ('00892000', [
            "         L     R1,0(,R1)           PAGE TABLE POINTER",
            "         N     R1,=A(SEGPTOM)      WITHOUT THE FLAGS",
        ]),
        ('00893000', [
            "         LA    R1,256*L'PAGPFRA+(SWPFLAG-SWPVM)(,R1)",
        ]),
        ('00896000', [
            "         SLDL  R14,8               MOVE PAGE NUMBER IN",
        ]),
    ],

    # `PAGCORE+1-PAGCORE` is the source's own way of writing "byte 1 of the
    # entry" with symbols instead of a literal 1.  The flag byte is byte 2 now,
    # so the same idiom carries the change for free.
    'DMKCDS': [
        ('00896000', [
            "         OI    PAGPFRA+2-PAGPFRA(R14),PAGINV ENQUEUE ON",
        ]),
        ('00905000', [
            "         NI    PAGPFRA+2-PAGPFRA(R14),X'FF'-PAGINV DEQUEUE",
        ]),
    ],

    # `OI PAGCORE+1,PAGINVAL+PAGREF` sets two flags that shared byte 1.  In
    # ESA/390 the invalid bit is in byte 2 and the referenced flag in byte 3, so
    # ONE instruction becomes TWO at every such site -- six of them, in DMKRPA
    # and DMKPTR.  Nothing about the card hints that it is two operations; the
    # only clue is that the two flags no longer share a byte.
    'DMKRPA': [
        ('00122000', ["         USING PAGPFRA,R9"]),
        ('00157000', Deck.comment(
            "THE PAGE-WITHIN-SEGMENT FIELD IS EIGHT BITS AT 12-19 NOW, AND A PTE "
            "STRIDE IS 4, SO THE MASK WIDENS AND THE SHIFT THAT MADE PAGE*2 "
            "MAKES PAGE*4. THE LATER SLL 2 THAT MADE PAGE*8 BECOMES SLL 1.") + [
            "         N     R1,=A(X'FF000') CLEAR SEG AND DISPLACEMENT",
        ]),
        ('00158000', [
            "         SRL   R1,10          AND GET PAGE NUMBER TIMES 4",
        ]),
        ('00160000', [
            "         S     R2,=A(PAGPFRA-PAGSWP) TO SWPTABLE POINTER",
        ]),
        ('00162000', [
            "         SLL   R1,1           GET PAGE NUMBER TIMES 8",
        ]),
        ('00174000', Deck.comment(
            "PAGINVAL AND PAGREF SHARED BYTE 1. NOW I IS BIT 21, IN BYTE 2, AND "
            "PAGREF IS IN BYTE 3, WHERE THE HARDWARE IGNORES IT. SO ONE OI "
            "BECOMES TWO, AT ALL SIX SITES THAT NAME BOTH FLAGS.") + [
            "         OI    PAGPFRA+2,PAGINV FLAG PAGE INVALID",
            "         OI    PAGPFRA+3,PAGREF AND REFERENCED",
        ]),
        ('00184000', [
            "         ST    R0,PAGPFRA     AND ALSO THE PAGE ENTRY.",
        ]),
        ('00185100', [
            "         OI    PAGPFRA+2,PAGINV FLAG PAGE INVALID",
            "         OI    PAGPFRA+3,PAGREF AND REFERENCED",
        ]),
        ('00253100', [
            "         OI    PAGPFRA+2,PAGINV INVALIDATE ACROSS",
            "         OI    PAGPFRA+3,PAGREF WRITE",
        ]),
        ('00266100', [
            "         NI    PAGPFRA+2,255-PAGINV FINISHED, VALIDATE",
            "         NI    PAGPFRA+3,255-PAGREF ...",
        ]),
    ],

    # The third instance of one pattern, and the one that names it: the S/370
    # halfword PTE value IS the CORTABLE offset, because a page frame number
    # times 16 is both.  An ESA/390 PTE is the frame's real address, so an
    # SRL 8 has to be inserted -- and `A R2,ACORETBL` names no DAT field, so
    # nothing reports it.  DMKPTR 00721000 states the relationship outright:
    # `S R7,ACORETBL  GET PAGE ADDRESS/256`.
    'DMKCPP': [
        ('50900000', [
            "         N     R4,=A(SEGPTOM) LEAVE PGT ADDRESS ONLY",
        ]),
        ('51000000', [
            "         SL    R4,=A(PAGPFRA-PAGSTMP) BACK UP TO HEADER",
        ]),
        ('51700000', Deck.comment(
            "SHRPAGE IS AN STE IN ALL BUT NAME -- SHRTABLE.COPY SAYS SO IN A "
            "COMMENT AND NO SYMBOL JOINS THEM -- SO ITS LENGTH FIELD MOVES WITH "
            "THE STE'S: PTL IS THE LOW NIBBLE AND COUNTS 16 ENTRIES AT A TIME.") + [
            "         N     R9,=A(SEGPTLF) LEAVE ONLY PTL",
            "         LA    R9,1(,R9)      UNITS OF 16 ENTRIES",
            "         SLL   R9,4           NUMBER OF PAGES",
            "         BCTR  R9,0           MINUS ONE, AS BEFORE",
        ]),
        ('52200000', [
            "         LA    R8,PAGPFRA     POINTER TO 1ST PAGE ADDRESS",
        ]),
        ('52400000', ["         USING PAGPFRA,R8"]),
        ('53800000', [
            "         TM    PAGPFRA+2,PAGINV IS PAGE IN CORE?",
        ]),
        ('54000000', '54100000', Deck.comment(
            "THE S/370 PTE VALUE WAS ALSO THE CORTABLE OFFSET: A FRAME NUMBER "
            "TIMES 16 IS BOTH, SO ONE MASK SERVED TWO PURPOSES. AN ESA/390 PTE "
            "IS THE FRAME'S REAL ADDRESS, SO THE INDEX NEEDS AN SRL 8. NOTHING "
            "REPORTS THIS: A R2,ACORETBL NAMES NO DAT FIELD.") + [
            "         L     R2,PAGPFRA     LOAD A PAGE TABLE ENTRY",
            "         N     R2,=A(PAGPFRM) LEAVE ONLY THE FRAME ADDRESS",
            "         SRL   R2,8           A CORTABLE ENTRY IS 16 A PAGE",
        ]),
        ('57400000', [
            "         MVC   PAGPFRA,=A(PAGINVW) INVALIDATE PAGE TABLE",
        ]),
        ('62000000', '62100000', Deck.comment(
            "THE RECORD REPLACED HERE CARRIED AN X IN COLUMN 72 AND 62100000 "
            "WAS ITS CONTINUATION CARD. REPLACING ONLY THE FIRST LEFT THE "
            "CONTINUATION A STANDALONE STATEMENT, AND THE ASSEMBLER READ ITS "
            "OPERAND FIELD AS AN OPCODE: IFO054 INVALID OPERATION CODE. BOTH "
            "RECORDS GO, AND THE REPLACEMENT NEEDS NO CONTINUATION. I-143.") + [
            "         LA    R8,L'PAGPFRA(,R8) ADDRESS THE NEXT ENTRY",
        ]),
        ('76900000', [
            "         N     R14,=A(SEGPTOM) LEAVE PGT ADDRESS ONLY",
        ]),
        ('77000000', [
            "         SL    R14,=A(PAGPFRA-PAGSTMP) BACK UP TO HEADER",
        ]),
    ],

    # Four modules with NO flagged site: everything in them is reached by
    # displacement or by a literal, so the rename cannot see them and they are
    # here only because idiom.py found them.
    #
    # DMKCDB and DMKCDM hold the worst case in the tree:
    #     TM    3(R3),1        IS THE STE INVALID?
    # byte 3 by displacement AND the invalid bit as a bare 1.  No symbol, so the
    # rename is blind; no DAT field on the line, so dattab is blind; the only
    # trace is a VMSEG five cards above.
    'DMKCDB': [
        ('01053500', [
            "         L     R3,VMSEG       OBTAIN STO",
            "         N     R3,=A(SEGSTOM) WITHOUT THE LENGTH",
        ]),
        ('01054000', ["         SRDL  R14,20         GET SEGMENT NUMBER"]),
        ('01056300', ["         TM    3(R3),SEGINVAL IS THE STE INVALID?"]),
        ('01057300', ["         TM    3(R3),SEGINVAL DID PTR CLEAR UP PAGE"]),
    ],
    'DMKCDM': [
        ('00767000', [
            "         L     R3,VMSEG       OBTAIN STO",
            "         N     R3,=A(SEGSTOM) WITHOUT THE LENGTH",
        ]),
        ('00768000', ["         SRDL  R14,20         GET SEGMENT NUMBER"]),
        ('00771000', ["         TM    3(R3),SEGINVAL IS THE STE INVALID?"]),
        ('00776000', ["         TM    3(R3),SEGINVAL DID PTR CLEAR UP PAGE"]),
    ],
    # CP's own system address space, reached through ASYSVM's VMBLOK.  The mask
    # that extracted the segment number is byte 2 of the address -- bits 16-23,
    # which is a 64 KB segment number times 256.
    'DMKDRD': [
        ('01090000', [
            "         L     R10,VMSEG-VMBLOK(,R10)   SYSTEM ADDR SPACE",
            "         N     R10,=A(SEGSTOM) WITHOUT THE LENGTH",
        ]),
        ('01093000', Deck.comment(
            "WAS X'00FF0000'. X'7FF00000' IS DMKVAT'S OWN CODEB0 SEGMENT "
            "MASK -- LARGE PAGE, LARGE SEG, FULLWORD ENTRIES -- AND THE "
            "SRL 18 BELOW IS CODEB0'S SEGSHFT. I-188: X'00F00000' REACHES "
            "ONLY SIXTEEN SEGMENTS, WHICH IS A 16 MB MACHINE AND NOT AN "
            "ARCHITECTURE. R9 HOLDS A(DMKSYM), A CLEAN NUCLEUS ADDRESS, SO "
            "THE WIDER MASK CANNOT PICK UP A DIRTY HIGH BYTE HERE.") + [
            "         L     R8,=A(X'7FF00000') ...TO GET THE SEGMENT NO.",
        ]),
        ('01096000', [
            "         SRL   R8,18(0)       CONVERT TO SEGTABLE INDEX",
        ]),
    ],
    # DMKDSP 02417000 is deliberately NOT here: its `L R1,VMSEG` feeds
    # `ST R1,RUNCR1`, so the hardware wants the whole designation, length and
    # all.  idiom.py marks it; reading rejects it.
    'DMKUSO': [
        ('00518110', [
            "         L     R1,VMSEG       GET STO",
            "         N     R1,=A(SEGSTOM) WITHOUT THE LENGTH",
        ]),
        ('00518560', [
            "         L     R1,VMSEG       RELOAD STO",
            "         N     R1,=A(SEGSTOM) WITHOUT THE LENGTH",
        ]),
    ],
    'DMKCPU': [
        ('00365000', [
            "         N     R7,=A(SEGPTOM) LEAVE PTO ADDRESS ONLY",
        ]),
        ('00366000', [
            "         SL    R7,=A(PAGPFRA-PAGSTMP) BACK UP TO HEADER",
        ]),
    ],
    'DMKPRV': [
        # I-202 / wall 28.  The first version of this card used R6 for the
        # STO -- and R6 is the guest's virtual address, loaded at GETKEYAD and
        # still needed by the two LRAs below (00935000, 00972000).  With R6
        # clobbered, ISK read the key of whatever guest page the STO's value
        # named, and SSK set THAT frame's key; the frame CMS meant kept the
        # key it had at page-in.  DMSREX then stored in key E into a frame
        # still keyed F: DMSITP141T PROTECTION EXCEPTION AT F30CB6.  R4 is
        # free here (00924100 reloads it).
        ('00918000', [
            "         L     R4,VMSEG       THE DESIGNATION",
            "         N     R4,=A(SEGSTOM) WITHOUT THE LENGTH",
            "         ALR   R7,R4          ADD STO, GET STE (R6 IS THE VA)",
        ]),
        ('00920000', [
            "*                             (LA R7,0(0,R7) REPLACED BELOW)",
        ]),
        ('00921000', ["      N    R7,=A(SEGPTOM)      TURN OFF INVALID BIT"]),
        ('00922000', [
            "         S     R7,=A(PAGPFRA-PAGSWP) BACK UP...",
        ]),
    ],
    # Only the unshare loop.  CHEKPTE, LOADPTE, PTEINCR and the whole ARCHTECT
    # table describe the GUEST's tables, indexed by the GUEST's CR0 -- CP has
    # been able to read fullword page-table entries since 1972, because S/370
    # had that format too, and PINVBIT DC X'04' is already the ESA/390 bit
    # position.  That is milestone B's mechanism, not M1's, and it is left alone.
    'DMKVAT': [
        ('00232180', [
            "         IC    R4,VMSEG+3     GET SIZE OF SEGMENT TABLE",
            "         N     R4,=A(SEGSTLM) WITHOUT THE S BIT",
        ]),
        ('00232240', [
            "         L     R5,VMSEG       GET SEGMENT TABLE",
            "         N     R5,=A(SEGSTOM) WITHOUT THE LENGTH",
        ]),
        ('00232300', [
            "         L     R6,0(R5)       IS SEG INVALID OR MIGRATED",
            "         N     R6,=A(SEGPTOM) ...",
            "         BZ    SKPCHG         NO SEGMENT - LOOK AT NEXT",
        ]),
        ('00232360', [
            "         SL    R6,=A(PAGPFRA-PAGSTMP) BACKUP TO HEADER",
        ]),
        ('00232520', ["         SLL   R1,20          FORM VIRTUAL ADDRESS"]),
        ('01044100', ["SEGSIZE  DC    X'00100000'"]),
        ('01044200', [
            "CLRBITS  DC    A(SEGPTOM)     MASK TO CLEAR FLAG BITS - STE",
        ]),
    ],

    # The paging manager.  32 flagged sites, and it holds the THIRD distinct way
    # of reading VMSEG's length -- `SRL R6,24` after `ICM R6,B'1111',VMSEG`,
    # after DMKPGS's `SLDL` pair and everyone else's `IC Rn,VMSEG` -- plus the
    # header offset written as a NEGATIVE literal, `L R5,=F'-16'`, which no scan
    # for `F16` could ever have found.
    #
    # Its ACORETBL sites go BOTH ways and only two of four change:
    #   00638000  S R6,ACORETBL / SLL R6,8   CORTABLE entry -> real address: ok
    #   00825100  SRL R7,8 / AL R7,ACORETBL  real address -> entry:          ok
    #   00721000  S R7,ACORETBL / STH / SLL  the /256 value is STORED as the PTE
    #   01975000  LH / N / LR / A            and used as an index
    'DMKPTR': [
        ('00260000', ["         USING PAGPFRA,R9"]),
        # I-162.  Five instructions in GETENTRY/GETENTR2 have to agree about
        # page geometry, and the first version of this deck converted ONE of
        # them -- 00338000, the swap-table displacement.  The four that feed it
        # kept 64 KB/16-page/2-byte geometry, so R1 could hold only a 4-bit
        # page number and CP looked up the swap entry of a DIFFERENT page.
        #
        # LRA returns the real address of the invalid PTE in R7 on CC=2, so
        # `SR R7,R1` needs R1 = page*L'PAGPFRA to get back to the start of the
        # array, and the swap entry then needs page*8.  With the old shifts
        # R1 was (page AND 15)*2 and then *8.
        #
        # Measured on the live nucleus for virtual X'B7000' (page 183 of
        # segment 0): the code computed R5 = X'FFB30E', which is not even
        # entry-aligned, and read X'61' there -- SWPALLOC set -- so
        # `TM SWPFLAG,SWPTRANS+SWPALLOC / BNZ INTRAN` enqueued the request and
        # waited for an I/O nobody had started.  The correct R5 is X'FFB5B8',
        # whose SWPFLAG is X'40' (SWPRECMP only), and the test falls through to
        # the not-resident path.  A CCW trace over the loop showed zero channel
        # programs, which is what "waiting for an I/O that was never started"
        # looks like from outside.
        #
        # The mask stays a literal, one-for-one with the X'0000F000' it
        # replaces, because it is used once.  The shared constant for the whole
        # class belongs in EQU COPY and is a separate change -- adding it here
        # would reassemble every module that copies EQU for a one-site fix.
        ('00321000', Deck.comment(
            "WAS N R1,=XL4'0000F000'. A 1 MB SEGMENT HAS 256 PAGES, SO THE "
            "PAGE INDEX IS BITS 12-19, NOT THE FOUR BITS A 64 KB SEGMENT "
            "NEEDED. I-162.") + [
            "         N     R1,=XL4'000FF000'   PAGE INDEX, BITS 12-19",
        ]),
        ('00322000', Deck.comment(
            "WAS SRL R1,11 -- PAGE NUMBER*2 FOR A TWO-BYTE ENTRY. THE ENTRY "
            "IS A FULLWORD NOW AND SR R7,R1 BELOW BACKS UP OVER IT.") + [
            "         SRL   R1,10          GET PAGE NUMBER*L'PAGPFRA",
        ]),
        ('00337000', Deck.comment(
            "WAS SLL R1,2 -- PAGE*2 TIMES FOUR. R1 NOW ARRIVES AS PAGE*4 AND "
            "A SWAP ENTRY IS STILL PAGSWPE BYTES, SO THE SHIFT IS ONE.") + [
            "         SLL   R1,1           GET PAGE NUMBER*PAGSWPE",
        ]),
        ('00338000', [
            "         LA    R5,256*L'PAGPFRA+(SWPFLAG-SWPVM)(R1,R7)",
        ]),
        ('00343000', ["         L     R7,PAGPFRA     GET PAGE TABLE ENTRY"]),
        # I-163, the same half-converted shape as I-162 one card further on.
        # An S/370 PTE was a HALFWORD holding the frame address divided by 256
        # in bits 0-11 with flags in 12-15, so `N R7,=A(X'FFF0')` stripped the
        # flags and left page*16 -- which IS the CORTABLE index, because a
        # CORTABLE entry is 16 bytes (CORFPNT, CORBPNT, CORSWPNT, CORPGPNT,
        # with CORFLAG ORG'd over CORSWPNT at +8).  One mask did two jobs.
        #
        # An ESA/390 PTE is a fullword whose PFRA is the real address itself,
        # so that mask leaves X'F000' rather than an index and the following
        # `A R7,ACORETBL` lands on an unrelated entry -- which is then WRITTEN
        # through by `ST R2,CORFPNT-CORTABLE(,R3)`.  Measured: the bogus entry
        # read CORFREE off, `BZ CNTFLR` did flush-list accounting for a page
        # that was never flushed, and DMKPTRUC went 0-1.  DMKPTRUC (R10+X'2CC')
        # was 0 and DMKPTRP2 (R10+X'2EC') was 1 at the abend, so CNTFLR had run
        # exactly once.  That is ABEND PTR020, DMKPTR.ASSEMBLE:412.
        #
        # So the two jobs separate: mask the PFRA, then scale to the index.
        # SRL does not set the condition code, so the `BZ READPAGE` on the next
        # card still tests the N -- that is why the shift goes here and not
        # after the branch.
        ('00344000', Deck.comment(
            "WAS N R7,=A(X'FFF0'), WHICH MASKED A HALFWORD PTE'S FLAGS AND "
            "LEFT PAGE*16 FOR ACORETBL IN ONE STROKE. AN ESA/390 PTE HOLDS "
            "THE REAL ADDRESS, SO THE MASK AND THE SCALING ARE NOW TWO "
            "INSTRUCTIONS. SRL SETS NO CONDITION CODE, SO THE BZ BELOW STILL "
            "TESTS THE N. I-163.") + [
            "         N     R7,=A(PAGPFRM) IS THE PAGE STILL IN CORE ?",
            "         SRL   R7,8           REAL ADDRESS TO CORTABLE INDEX",
        ]),
        ('00721000', '00723000', Deck.comment(
            "THE /256 VALUE WAS STORED AS THE PTE AND THEN SHIFTED TO MAKE THE "
            "REAL ADDRESS. AN ESA/390 PTE IS THAT ADDRESS, SO THE SHIFT MOVES "
            "AHEAD OF THE STORE.") + [
            "         S     R7,ACORETBL     GET PAGE ADDRESS/256",
            "         SLL   R7,8           GET PAGE ADDRESS",
            "         ST    R7,PAGPFRA     UPDATE PAGE TABLE",
        ]),
        ('00746000', [
            "         L     R5,0(,R7)      TEST FOR VALID PTR",
            "         N     R5,=A(SEGPTOM) ...",
        ]),
        ('00748000', [
            "         NI    3(R7),255-SEGINVAL CLEAR INVALID FLAG",
        ]),
        ('00750000', ["         N     R5,=A(SEGPTOM) CLEAR COUNT FIELD"]),
        ('00751000', [
            "         S     R5,=A(PAGPFRA-PAGSTMP) BACK-UP TO HEADER",
        ]),
        ('00771000', [
            "         L     R6,VMSEG       THE DESIGNATION",
            "         N     R6,=A(SEGSTOM) WITHOUT THE LENGTH",
            "         CR    R7,R6          FOR SEGMENT 0?",
        ]),
        # I-196 / wall 25.  SEGEXA is DMKPTRAN's lazy page-table build: on the
        # first fault in a segment it computes the segment's page range and
        # CALLs DMKBLDRT,PARM=PAGTONLY to build the table, then stores the STE
        # it gets back.  The range arithmetic was IBM's 64 KB one, untouched:
        # STE number = address>>16, end = (STE+1)<<16, start page = STE<<20
        # (16 pages per segment into the high halfword).  Measured on IPL 190
        # for virtual X'20000': R1 = X'0020002F', pages 32-47, SIXTEEN pages,
        # built and stored into the STE of 1 MB segment 0 -- PTL 0.  The next
        # touch at page 32 then takes LRA CC3 (page index past PTL), ADDEX
        # turns that into CC2, and DMKRPAGT dies RPA001.  Three shifts: the
        # segment is address>>20, its end (seg+1)<<20, and its first page
        # seg*256 goes to the high halfword as seg<<24.  Nothing else in the
        # block changes -- the clamp to VMSTOR and the >>12/BCTR last-page
        # arithmetic are geometry-free.
        ('00793000', [
            "         SRL   R2,20          STE NO. -- 1 MB SEGMENTS",
        ]),
        ('00796000', [
            "         SLL   R1,20          ENDING SEGMENT ADDRESS + 1",
        ]),
        ('00802000', [
            "         SLL   R2,24          START PAGE = SEG*256, HIGH HALF",
        ]),
        ('00827150', ["         MVC   PAGPFRA,INVLPTE INVALIDATE PTE"]),
        ('00827550', [
            "INVLPTE  DC    A(PAGINVW)     INVALID PTE CONSTANT",
        ]),
        ('01130000', ["         TM    2(R1),PAGINV   TRY TO CATCH CULPRIT"]),
        ('01134000', '01135000', Deck.comment(
            "MVI 0(R1),0 CLEARED BYTE 0 AND THE NI KEPT TWO FLAGS THAT SHARED "
            "BYTE 1. PAGINV IS IN BYTE 2 AND PAGREF IN BYTE 3, SO PAGREF IS "
            "SAVED FIRST AND THE FRAME ADDRESS IS CLEARED AS TWO BYTES PLUS "
            "THE HIGH NIBBLE OF BYTE 2 -- THE NI DOES THAT NIBBLE AND KEEPS I. "
            "AN XC OF THREE BYTES TOOK THE I BIT WITH IT, AND A PTE OF "
            "00000001 IS REAL FRAME 0, VALID: THE GUEST WROTE CP'S PSA. I-240.") + [
            "         NI    3(R1),PAGREF   RETAINING THIS FLAG",
            "         XC    0(2,R1),0(R1)  SET PTE ADDRESS -> 0,",
            "         NI    2(R1),PAGINV   RETAINING THIS ONE (I-240)",
        ]),
        ('01350130', [
            "         SLL   R0,2           MULTIPLY BY 4 FOR PTE SIZE",
        ]),
        ('01350175', [
            "         SL    R1,=A(PAGPFRA-PAGSTMP) BACK UP TO HEADER",
        ]),
        ('01362000', [
            "         OI    PAGPFRA+3,PAGREF NON-RESIDENT PAGE TOUCHED",
        ]),
        ('01402000', [
            "         L     R3,VMSEG       OWNER'S STO",
            "         N     R3,=A(SEGSTOM) WITHOUT THE LENGTH",
        ]),
        ('01403000', [
            "         L     R2,0(R3)       THE STE",
            "         N     R2,=A(SEGPTOM) PTE FOR PAGE 0?",
            "         CR    R9,R2          ...",
        ]),
        ('01434000', [
            "         OI    PAGPFRA+2,PAGINV FLAG PAGE INVALID",
        ]),
        ('01677000', ["         USING PAGPFRA,R2     ADDRESSABILITY"]),
        ('01679000', ["         TM    PAGPFRA+2,PAGINV    CATCH CULPRIT"]),
        ('01683000', '01684000', [
            "         NI    PAGPFRA+3,PAGREF RETAINING THIS FLAG",
            "         XC    PAGPFRA(2),PAGPFRA CLEAR PTE ADDRESS",
            "         NI    PAGPFRA+2,PAGINV RETAINING THIS ONE (I-240)",
        ]),
        ('01719000', [
            "         TM    PAGPFRA+2,PAGINV    IT MUST BE INVALID",
        ]),
        ('01888000', ["         USING SEGPTO,R3"]),
        ('01891000', ["         USING PAGPFRA,R9"]),
        ('01918000', Deck.comment(
            "THE THIRD DISTINCT WAY OF READING VMSEG'S LENGTH IN THIS TREE: "
            "SRL 24 AFTER AN ICM OF THE WHOLE WORD. IT IS A MASK NOW.") + [
            "         N     R6,=A(SEGSTLM) GET SEG LGTH / 16",
        ]),
        ('01921000', [
            "         L     R3,VMSEG       GET SEG ADDR",
            "         N     R3,=A(SEGSTOM) WITHOUT THE LENGTH",
        ]),
        ('01930000', [
            "         TM    SEGPTO+3,SEGINVAL SEGMENT TABLE ENTRY VALID?",
        ]),
        ('01933000', '01934000', [
            "         IC    R8,SEGPTO+3    PAGE TABLE LENGTH",
            "         N     R8,=A(SEGPTLF) RIGHT JUSTIFY",
        ]),
        ('01935000', [
            "         AR    R8,R4          ORIGIN 1",
            "         SLL   R8,4           UNITS OF 16 ENTRIES",
        ]),
        ('01936000', [
            "         L     R9,SEGPTO      PAGE TABLE POINTER",
            "         N     R9,=A(SEGPTOM) ...",
        ]),
        ('01937000', Deck.comment(
            "THE HEADER OFFSET AS A NEGATIVE LITERAL. NO SCAN FOR F16 COULD "
            "FIND IT; IT TURNED UP ONLY BY READING THE BLOCK.") + [
            "         L     R5,=A(-(PAGPFRA-PAGSTMP)) BACK-UP TO HEADER",
        ]),
        ('01965000', ["         TM    PAGPFRA+2,PAGINV PAGE INVALID?"]),
        ('01967000', ["         TM    PAGPFRA+3,PAGREF USED WHILE IN-Q?"]),
        ('01969000', [
            "         NI    PAGPFRA+3,255-PAGREF YES, RESET FLAG",
        ]),
        ('01975000', ["         L     R7,PAGPFRA     REAL PAGE ADDRESS"]),
        ('01976000', ["         N     R7,=A(PAGPFRM) CLEAR ALL BUT ADDRESS"]),
        ('01977000', [
            "         LR    R1,R7          SAVE",
            "         SRL   R7,8           A CORTABLE ENTRY IS 16 A PAGE",
        ]),
        ('01986000', Deck.comment(
            "R1 ALREADY HOLDS THE REAL PAGE ADDRESS.") + [
            "*                             (SLL R1,8 REMOVED)",
        ]),
        ('02002400', [
            "         SLL   R15,2          MULTIPLY BY 4 FOR PTE SIZE",
        ]),
        ('02002700', [
            "         SL    R2,=A(PAGPFRA-PAGSTMP) BACK UP TO HEADER",
        ]),
        ('02007000', [
            "         OI    PAGPFRA+2,PAGINV INVALIDATE PAGE TABLE ENTRY",
        ]),
        ('02034000', [
            "         LA    R9,PAGPFRA+L'PAGPFRA NEXT PTE",
        ]),
        ('02037000', [
            "         OI    SEGPTO+3,SEGINVAL INVALIDATE STE",
        ]),
        ('02041000', ["         LA    R3,SEGPTO+4    POINT TO NEXT STE"]),
        ('02054000', [
            "         L     R9,SEGPTO      LOAD PAGE TBL POINTER",
            "         N     R9,=A(SEGPTOM) ...",
        ]),
        ('02055000', [
            "         L     R5,=A(-(PAGPFRA-PAGSTMP)) BACK UP TO HEADER",
        ]),
        ('02069170', [
            "PAGEISK  TM    PAGPFRA+2,PAGINV    PAGE INVALID",
        ]),
        ('02069190', '02069200', [
            "         L     R2,PAGPFRA     LOAD PTE",
            "*                             (SLL R2,8 REMOVED)",
        ]),
        ('02069210', ["         N     R2,=A(PAGPFRM) CLEAR DISPLACEMENT"]),
        ('02069280', [
            "INVAL    LA    R9,PAGPFRA+L'PAGPFRA POINT TO NEXT PTE",
        ]),
    ],

    # Page and segment table services -- the largest module in the conversion,
    # 31 flagged sites and 31 idiom candidates.  Two of its idioms exist nowhere
    # else: a double shift that splits the designation into length and address
    # (00477000-00479000), and a one-byte compare that tests for the end of a
    # page table because `page<<4` and `(pages-1)<<4` happen to be the same
    # encoding (01217000).  Neither survives.
    'DMKPGS': [
        ('00278400', ["         USING PAGPFRA,R9"]),
        ('00288000', [
            "         IC    R2,VMSEG+3     NUMBER OF SEGMENT TABLES",
            "         N     R2,=A(SEGSTLM) WITHOUT THE S BIT",
        ]),
        ('00290000', Deck.comment(
            "A 64-BYTE SEGMENT TABLE UNIT COVERED 1 MB AND NOW COVERS 16.") + [
            "         SLL   R2,24          ADDR +1 PAGE OF LAST PAGE",
        ]),
        ('00302000', [
            "PURCONT  L     R3,VMSEG       GET ADDRESS OF SEGTABLE",
            "         N     R3,=A(SEGSTOM) WITHOUT THE LENGTH",
        ]),
        ('00303000', [
            "*                             (LA R3,0(,R3) REPLACED ABOVE)",
        ]),
        ('00307000', [
            "         IC    R4,VMSEG+3     NUMBER OF 16 MEG SEGMENTS",
            "         N     R4,=A(SEGSTLM) WITHOUT THE S BIT",
        ]),
        ('00317000', Deck.comment(
            "CLI COMPARED THE WHOLE BYTE AGAINST X'01'. BYTE 3 HOLDS TWO PTO "
            "BITS, C AND PTL AS WELL, SO IT MUST BE A BIT TEST -- AND THE "
            "BRANCH SENSE TURNS OVER WITH IT.") + [
            "         TM    SEGPTO+3,SEGINVAL UNDEFINED SEGMENT?",
        ]),
        ('00318000', ["         BZ    B1             NO"]),
        ('00319000', [
            "         L     R15,SEGPTO     VALID PNTR?",
            "         N     R15,=A(SEGPTOM) ...",
        ]),
        ('00392000', [
            "         IC    R3,VMSEG+3     NUMBER OF SEGMENT TABLES",
            "         N     R3,=A(SEGSTLM) WITHOUT THE S BIT",
        ]),
        ('00415000', [
            "         L     R3,VMSEG       GET ADDRESS OF SEGTABLE",
            "         N     R3,=A(SEGSTOM) WITHOUT THE LENGTH",
        ]),
        ('00417000', [
            "         SRL   R5,20          LEAVE ONLY SEGMENT NUMBER",
        ]),
        ('00421000', '00423000', [
            "         L     R10,SEGPTO     ANY PTE POINTER?",
            "         N     R10,=A(SEGPTOM) ...",
            "         BZ    PROCNEXT       NO, SKIP",
        ]),
        ('00425000', Deck.comment(
            "F8 REACHED PAGSHR FROM PAGCORE -- A GAP OF 8 THEN AND 16 NOW. THE "
            "COMMENT SAYS PAGE HEADER AND MEANS THE SHRTABLE POINTER.") + [
            "         SL    R10,=A(PAGPFRA-PAGSHR) POINT TO PAGSHR",
        ]),
        ('00477000', '00479000', Deck.comment(
            "SLDL R2,8 SHIFTED THE R2:R3 PAIR SO VMSEG'S BYTE 0 -- THE LENGTH -- "
            "LANDED IN R2, THEN SRL R3,8 PUT THE ADDRESS BACK. ONE DOUBLE SHIFT "
            "EXTRACTING BOTH HALVES, WHICH WORKS ONLY BECAUSE THE LENGTH IS THE "
            "HIGH BYTE. IT BECOMES TWO MASKS.") + [
            "         L     R3,VMSEG       THE DESIGNATION",
            "         LR    R2,R3          FOR THE LENGTH",
            "         N     R2,=A(SEGSTLM) NUMBER OF SEGMENTS",
            "         N     R3,=A(SEGSTOM) AND THE ADDRESS",
        ]),
        ('00484000', '00486000', [
            "         L     R9,SEGPTO      ANY PTE POINTER?",
            "         N     R9,=A(SEGPTOM) ...",
            "         BZ    NEXTADDR+6     NO, SKIP",
        ]),
        ('00488000', [
            "         SL    R9,=A(PAGPFRA-PAGSHR) TO SHRTABLE PTR",
        ]),
        ('00493100', [
            "         IC    R2,VMSEG+3     GET NUMBER OF SEGMENTS",
            "         N     R2,=A(SEGSTLM) WITHOUT THE S BIT",
        ]),
        ('00493300', ["         SLL   R2,24          NOW MAKE IT AN ADDRESS"]),
        ('00517100', [
            "         L     R15,VMSEG      SEGMENT TABLE ORIGIN",
            "         N     R15,=A(SEGSTOM) CLEAR LENGTH BITS",
        ]),
        ('00517200', [
            "*                             (LA R15,0(,R15) REPLACED ABOVE)",
        ]),
        ('00529600', [
            "         NI    SEGPTO+3-SEGPTO(R3),X'FF'-SEGINVAL",
        ]),
        ('00570000', [
            "         L     R5,VMSEG       THE DESIGNATION",
            "         N     R5,=A(SEGSTOM) WITHOUT THE LENGTH",
            "         ALR   R9,R5          ADDR SEGTABLE ENTRY",
        ]),
        ('00572000', ["         L     R5,SEGPTO      LOAD ADDRESS OF PTO"]),
        ('00574000', ["         N     R5,=A(SEGPTOM) CLEAR PTE COUNT"]),
        ('00592000', [
            "         SL    R5,=A(PAGPFRA-PAGSTMP) BACKUP TO HEADER",
        ]),
        ('00616000', [
            "         SL    R5,=A(PAGPFRA-PAGSTMP) BACKUP TO HEADER",
        ]),
        ('00643400', [
            "         AL    R1,=A(PAGPFRA-PAGSTMP) GET ADDRESS OF PTO",
        ]),
        ('00643600', [
            "         L     R15,0(R9)      THE CURRENT ENTRY",
            "         N     R15,=A(SEGFLGM) KEEP I, C AND PTL",
            "         OR    R15,R1         WITH THE NEW ORIGIN",
            "         ST    R15,0(R9)      UPDATE STE",
        ]),
        ('00645500', ["         N     R1,=A(SEGPTOM) CLEAR PTE COUNT"]),
        ('00645590', [
            "         SL    R5,=A(PAGPFRA-PAGSTMP) BACKUP TO HEADER",
        ]),
        ('00645650', ["         N     R1,=A(SEGPTOM) CLEAR PTE COUNT"]),
        ('00645660', [
            "         L     R14,VMSEG      ADDR START OF SEGTABLE",
            "         N     R14,=A(SEGSTOM) CLEAR SEGTABLE SIZE",
        ]),
        ('00645670', [
            "*                             (LA R14,0(,R14) REPLACED ABOVE)",
        ]),
        ('00645700', [
            "         SLL   R1,20          FORM VIRTUAL STARTING ADDRESS",
        ]),
        ('00645760', ["         N     R1,=A(SEGPTOM) CLEAR PTE COUNT"]),
        ('00653500', [
            "         L     R15,SEGPTO-SEGTABLE(R9) THE CURRENT ENTRY",
            "         N     R15,=A(SEGFLGM) KEEP I, C AND PTL",
            "         OR    R15,R1         WITH THE NEW ORIGIN",
            "         ST    R15,SEGPTO-SEGTABLE(R9) HOOK STE - PTO",
        ]),
        ('00655000', ["         N     R5,=A(SEGPTOM) CLEAR COUNT"]),
        ('00656000', [
            "         SL    R5,=A(PAGPFRA-PAGSTMP) BACKUP TO HEADER",
        ]),
        ('00658100', [
            "         SL    R5,=A(PAGPFRA-PAGSTMP) BACKUP TO HEADER",
        ]),
        ('00658160', ["         N     R1,=A(SEGPTOM) CLEAR PTE COUNT"]),
        ('00658170', [
            "         L     R14,VMSEG      STARTING ADDR SEGTABLE",
            "         N     R14,=A(SEGSTOM) CLEAR SEGTABLE SIZE",
        ]),
        ('00658180', [
            "*                             (LA R14,0(,R14) REPLACED ABOVE)",
        ]),
        ('00658210', [
            "         SLL   R1,20          FORM VIRTUAL STARTING ADDRESS",
        ]),
        ('00680000', ["         N     R9,=A(SEGPTOM) CLEAR COUNT FIELD"]),
        ('00681000', ["         TM    3(R9),SEGINVAL VALID STE?"]),
        ('00714000', ["         LA    R7,SEGINVAL    INVALID FLAG"]),
        ('00756000', ["         TM    3(R9),SEGINVAL SEGMENT VALID?"]),
        ('00758000', [
            "         NI    3(R9),255-SEGINVAL NO, VALIDATE IT",
        ]),
        ('00774000', [
            "         L     R2,VMSEG       ADDRESS OF 1ST STE",
            "         N     R2,=A(SEGSTOM) CLEAR COUNT FIELD",
        ]),
        ('00775000', [
            "*                             (LA R2,0(,R2) REPLACED ABOVE)",
        ]),
        ('00777000', Deck.comment(
            "R1 IS AN STE DISPLACEMENT, SEGNUM TIMES 4. TIMES 2**14 GAVE SEGNUM "
            "TIMES 64 KB; A SEGMENT IS 1 MB NOW, SO TIMES 2**18.") + [
            "         SLL   R1,18          ADDRESS OF 1ST PAGE IN SEGMENT",
        ]),
        ('00779000', '00781000', Deck.comment(
            "BYTE 0 HELD (PTE COUNT * 16) - 16, SO ADDING 16 AND DIVIDING BY 16 "
            "GAVE THE COUNT. PTL IS THE LOW NIBBLE OF BYTE 3 AND COUNTS "
            "SIXTEENS, SO IT IS A MASK AND A SHIFT.") + [
            "         IC    R7,3(,R9)      THE STE FLAG BYTE",
            "         N     R7,=A(SEGPTLF) PTL",
            "         LA    R7,1(,R7)      UNITS OF 16 ENTRIES",
            "         SLL   R7,4           PTE COUNT",
        ]),
        ('00934000', [
            "         IC    R2,VMSEG+3     NUMBER OF SEGMENT TABLES",
            "         N     R2,=A(SEGSTLM) WITHOUT THE S BIT",
        ]),
        ('00936000', ["         SLL   R2,24          ADDR +1 PAGE OF LAST"]),
        ('00941000', ["         USING PAGPFRA,R9"]),
        ('00947000', [
            "         L     R3,VMSEG       GET SEGMENT TABLE ORIGIN",
            "         N     R3,=A(SEGSTOM) WITHOUT THE LENGTH",
        ]),
        ('00949000', ["         SRL   R14,20         ISOLATE SEGMENT NUMBER"]),
        ('00954000', [
            "         L     R4,SEGPTO      VALID PNTR?",
            "         N     R4,=A(SEGPTOM) ...",
            "         BNZ   B2             YES",
        ]),
        ('00956000', Deck.comment(
            "THE ORIGINAL IS CLI SEGPAGE+3,SEGINV -- AN EQUALITY TEST, NOT A "
            "BIT TEST. BYTE 3 EQUALS SEGINV EXACTLY ONLY WHEN THE PTO'S LOW "
            "BYTE IS ZERO AND THE INVALID FLAG IS SET, WHICH IS THE 'NEVER "
            "BUILT' CASE. THE NEXT TWO CARDS THEN SEPARATE A SECOND CASE -- "
            "BUILT BUT INVALID, MIGRATING -- AND THAT IS THE ONE THE TRANS AT "
            "00962000 EXISTS TO WAIT FOR. CONVERTING THIS TO TM COLLAPSED THE "
            "TWO INTO ONE: ANY INVALID ENTRY TOOK NEXTSEG, SO REACHING 00958000 "
            "MEANT THE BIT WAS CLEAR, BZ WAS ALWAYS TAKEN, AND THE TRANS BECAME "
            "DEAD CODE. THE EQUALITY TEST SURVIVES THE CONVERSION UNCHANGED IN "
            "KIND -- ONLY THE CONSTANT MOVES, BECAUSE AN UNBUILT ESA/390 STE "
            "READS X'20': INVALID WITH PTL ZERO, CONFIRMED BY READING CP'S OWN "
            "SEGMENT TABLE, WHERE UNUSED ENTRIES ARE 00000020. I-159.") + [
            "         CLI   SEGPTO+3,SEGINVAL INVALID STE(NOT BUILT)?",
        ]),
        ('00957000', ["         BE    NEXTSEG        YES, NOTHING TO RELEASE"]),
        ('00958000', [
            "B2       TM    SEGPTO+3,SEGINVAL VALID ADDR, INVALID",
        ]),
        ('00979000', ["         L     R10,0(R3)      GET PAGETABLE ORIGIN"]),
        ('00980000', ["         N     R10,=A(SEGPTOM) STRIP LENGTH"]),
        ('00981000', [
            "         S     R10,=A(PAGPFRA-PAGSHR) TO SHRTABLE PTR",
        ]),
        ('01004000', ["         TM    SEGPTO+3,SEGINVAL VALID STE?"]),
        ('01007000', [
            "         L     R15,SEGPTO     GET PTO",
            "         N     R15,=A(SEGPTOM) WITHOUT THE FLAGS",
        ]),
        ('01010000', ["         N     R14,F255       (WITHOUT SEGMENT NO.)"]),
        # Three cards in PGOUT2's own body, found while fixing I-183 five cards
        # below.  They compute the PTE and SWPTABLE addresses for the page the
        # loop is about to release, so the loop could not reach them while it
        # was spinning -- the fix for I-183 is what exposes them.
        ('01011000', Deck.comment(
            "WAS ALR R14,R14 -- PAGE NUMBER TIMES TWO, THE INDEX OF A "
            "HALFWORD S/370 PTE. AN ESA/390 PTE IS A FULLWORD.") + [
            "         SLL   R14,2          PAGE NO. * 4 -> PTE INDEX",
        ]),
        ('01013000', Deck.comment(
            "WAS SLL R14,2. THE CARD ABOVE NOW LEAVES PAGE*4 WHERE IT LEFT "
            "PAGE*2, AND AN SWPTABLE ENTRY IS STILL EIGHT BYTES, SO THIS "
            "SHIFT DROPS FROM 2 TO 1. THE TWO TOGETHER STILL GIVE PAGE*8.") + [
            "         SLL   R14,1          PAGE NO. * 8 -> SWAPTABLE ENTRY",
        ]),
        ('01015000', Deck.comment(
            "WAS LA R5,16*2+8(R14,R15) -- SIXTEEN HALFWORD PTES PLUS AN "
            "EIGHT-BYTE SWPTABLE HEADER, WRITTEN OUT RATHER THAN TAKEN FROM "
            "CORE.COPY, WHERE CORE.XA0033DK ALREADY MOVED PAGTSWP TO 256 "
            "FULLWORD ENTRIES. R15 HOLDS THE PTO, WHICH POINTS AT PAGPFRA, "
            "SO THE HEADER AHEAD OF IT COMES BACK OFF; DMKATS 00341000 "
            "SPELLS THE SAME PLACE PAGTSWP+8 BECAUSE ITS BASE IS PAGSTMP. "
            "THE CARD CARRIES NO COMMENT BECAUSE THE EXPRESSION ITSELF "
            "REACHES COLUMN 54 AND THE LIMIT IS 61.") + [
            "         LA    R5,PAGTSWP-(PAGPFRA-PAGSTMP)+8(R14,R15)",
        ]),
        ('01034200', Deck.comment(
            "STCM B'1000' PUT R4'S BYTE 0 INTO THE STE'S BYTE 0, WHICH HELD THE "
            "LENGTH, SO IT COPIED THE OTHER PAGE TABLE'S LENGTH -- WHATEVER IT "
            "WAS. PTL IS THE LOW NIBBLE OF BYTE 3 NOW. THE FIRST VERSION OF THIS "
            "CARD OR'D IN SEGPTLF, A FULL TABLE, WHICH IS TRUE OF EVERY TABLE "
            "DMKBLDRT BUILDS AND IS STILL AN ASSUMPTION THE ORIGINAL DID NOT "
            "MAKE. R4'S OWN PTL IS TAKEN INSTEAD, VIA TEMPR7 -- UNUSED IN THIS "
            "MODULE -- BECAUSE R4 IS NEEDED WHOLE BY THE NEXT CARD.") + [
            "         ST    R4,TEMPR7      THE OTHER PAGE TABLE'S ENTRY",
            "         L     R15,SEGPTO     THE CURRENT ENTRY",
            "         N     R15,=A(X'FFFFFFFF'-SEGPTLF) WITHOUT PTL",
            "         NC    TEMPR7,=A(SEGPTLF) ITS PTL",
            "         O     R15,TEMPR7     RESET PAGTABLE LENGTH",
            "         ST    R15,SEGPTO     ...",
        ]),
        ('01034400', ["         N     R4,=A(SEGPTOM) STRIP OFF LENGTH"]),
        ('01045200', [
            "         L     R15,SEGPTO     THE CURRENT ENTRY",
            "         N     R15,=A(SEGFLGM) KEEP I, C AND PTL",
            "         OR    R15,R4         WITH THE OTHER PAGTABLE",
            "         ST    R15,SEGPTO     STORE ADDR OTHER PAGTABLE",
        ]),
        ('01047000', [
            "         SL    R5,=A(PAGPFRA-PAGSTMP)",
        ]),
        ('01049000', Deck.comment(
            "X'00FF0000' KEPT THE 64 KB SEGMENT NUMBER, BITS 8-15 -- WHICH "
            "IS EVERY SEGMENT A 24-BIT ADDRESS CAN NAME, SO THE ORIGINAL WAS "
            "GENERAL FOR ITS ARCHITECTURE. A 1 MB SEGMENT NUMBER IS BITS "
            "1-11, 2048 OF THEM, AND X'7FF00000' IS DMKVAT'S OWN CODEB0 "
            "MASK FOR THIS GEOMETRY. THIS CARD READ X'00F00000' FOR ONE "
            "BUILD CYCLE; THAT REACHES SIXTEEN SEGMENTS, WHICH IS A 16 MB "
            "MACHINE AND NOT AN ARCHITECTURE, AND IT COST THE CYCLE. "
            "I-188.") + [
            "         N     R1,=X'7FF00000' RESET R1 TO SEGMENT START",
        ]),
        ('01053000', ["         LA    R3,SEGPTO+4    POINT TO NEXT STE"]),
        # I-183, wall 20.  The card above advances the STE pointer by FOUR --
        # one fullword ESA/390 entry, covering one 1 MB segment -- and the two
        # cards below advance the VIRTUAL ADDRESS that must stay in step with
        # it.  They were left at 64 KB granularity, so R3 moved a megabyte per
        # iteration while R1 moved sixty-four kilobytes, and they drifted by a
        # factor of sixteen from the first pass.
        #
        # Measured at a breakpoint on the LRA inside the TRANS at 00962000:
        # R3 = X'FFD400', entry 256 of a table that CR1 = X'00FFD001' says
        # holds 32 entries, while R1 = 0 -- so DMKPGS tested segment 256's
        # invalid bit and asked DMKPTRAN to translate segment 0.  DMKPTRAN
        # cleared segment 0, the test never cleared, and PGOUT2 looped for
        # ever: no return to the dispatcher, so the console read was never
        # re-armed and the attention Hercules raised was never serviced.
        # The LRA's cc=3 is the length violation that entry 256 earns.
        #
        # The mask is the one THIS DECK already uses at 01049300, five cards
        # up, with the reasoning written out there.  Converting one of a pair
        # and not the other is I-162 exactly -- and then getting the shared
        # constant wrong in both is I-188, which is why the reasoning lives in
        # one place and both cards point at it.
        ('01054000', Deck.comment(
            "WAS N R1,=X'00FF0000' -- THE 64 KB SEGMENT-NUMBER MASK. SAME "
            "CHANGE AS 01049300, WHICH THIS DECK ALREADY MADE.") + [
            "         N     R1,=X'7FF00000' SAVE SEGMENT NUMBER",
        ]),
        ('01055000', Deck.comment(
            "WAS A R1,=X'00010000' -- A 64 KB BUMP. ONE SEGMENT IS NOW A "
            "MEGABYTE, AND R3 ABOVE ALREADY STEPS BY ONE FULLWORD STE, SO "
            "THIS IS THE CARD THAT KEEPS THE TWO IN STEP.") + [
            "         A     R1,=X'00100000' BUMP SEGMENT BY 1",
        ]),
        ('01116000', ["         L     R2,PAGPFRA     PTE"]),
        ('01117100', Deck.comment(
            "AN ESA/390 PTE IS THE FRAME'S REAL ADDRESS, SO THE SHIFT GOES.") + [
            "*                             (SLL R2,8 REMOVED)",
        ]),
        ('01117600', ["         N     R2,=A(PAGPFRM) CLEAR UNWANTED BITS"]),
        ('01164000', ["         MVC   PAGPFRA,=A(PAGINVW) INVALIDATE PTE"]),
        ('01179000', ["         N     R10,=A(SEGPTOM) LEAVE ONLY THE ADDRESS"]),
        ('01180000', [
            "         SL    R10,=A(PAGPFRA-PAGSHR) TO SHRTABLE PTR",
        ]),
        ('01201000', [
            "         NI    PAGPFRA+3,255-PAGREF RESET REF FLAG",
        ]),
        ('01217000', Deck.comment(
            "CLM R1,B'0010',SEGPAGE COMPARED BYTE 2 OF A VIRTUAL ADDRESS -- "
            "PAGE-WITHIN-SEGMENT TIMES 16 -- AGAINST BYTE 0 OF THE STE, WHICH "
            "WAS (PAGES-1) TIMES 16. THE SAME ENCODING BY ACCIDENT, SO ONE BYTE "
            "COMPARE TESTED FOR THE END OF THE PAGE TABLE. NOTHING LINES UP IN "
            "ESA/390: THE PAGE FIELD IS EIGHT BITS AT 12-19 AND PTL COUNTS "
            "SIXTEENS IN THE LOW NIBBLE OF BYTE 3. TEMPR6 AND TEMPR7 ARE UNUSED "
            "IN THIS MODULE, AND NEITHER L NOR LM SETS THE CONDITION CODE, SO "
            "THE RESTORE CAN FOLLOW THE COMPARE.") + [
            "*  CKSEG EQU * IS NOT REPEATED: IT IS RECORD 01216000,",
            "*  WHICH THIS DECK DOES NOT REPLACE, SO IT ALREADY",
            "*  LABELS THE CARD BELOW. EMITTING IT AGAIN GAVE IFO196",
            "*  HAS BEEN PREVIOUSLY DEFINED. I-143.",
            "         ST    R14,TEMPR7     SAVE THE WORK REGISTER",
            "         IC    R14,3(,R3)     THE STE FLAG BYTE",
            "         N     R14,=A(SEGPTLF) PTL",
            "         LA    R14,1(,R14)    UNITS OF 16 ENTRIES",
            "         SLL   R14,4+12       THE SEGMENT'S LENGTH IN BYTES",
            "*  THE CLM TESTED PAGE >= PAGES-1, I.E. 'THIS IS THE LAST",
            "*  PAGE'. LENGTH ALONE TESTED PAGE >= PAGES, NEVER TRUE,",
            "*  SO THE LOOP RAN OFF THE END OF EVERY PAGE AND SWAP TABLE",
            "*  INTO FREE STORAGE: SWPFLAG READ FROM DMKFRE'S PADDING,",
            "*  AND A ZERO SWPCYL REACHED DMKPGTPR -- PGT005 AT LOGOFF",
            "*  AND AT DEF STOR AFTER IPL (WALL 29, I-206).",
            "         S     R14,F4096      THE LAST PAGE'S OFFSET",
            "         ST    R14,TEMPR6     ...",
            "         LR    R14,R1         THE CURRENT VIRTUAL ADDRESS",
            "         N     R14,=A(X'000FF000') PAGE WITHIN SEGMENT",
            "         C     R14,TEMPR6     TEST FOR LAST PAGE",
            "         L     R14,TEMPR7     RESTORE",
        ], ),
        ('01220000', [
            "         LA    R9,L'PAGPFRA(,R9) POINT TO NEXT PTE",
        ]),
        ('01226000', [
            "         L     R14,SEGPTO-SEGPTO(,R3) GET PAGE TABLE",
        ]),
        ('01228000', [
            "         SL    R14,=A(PAGPFRA-PAGSHR) POINT TO PAGSHR",
        ]),
        ('01236000', ["         LA    R14,SEGINVAL   INVALID FLAG"]),
        ('01237000', ["         L     R1,SEGPTO-SEGPTO(,R3) GET STE"]),
        ('01238000', [
            "         ST    R14,SEGPTO-SEGPTO(,R3) INVALID STE",
        ]),
        ('01283000', ["CLCNTINV DC    A(SEGPTOM)     CLEAR COUNT AND INV"]),
        ('01285000', [
            "CLINVBIT DC    A(X'FFFFFFFF'-SEGINVAL) CLEAR INVALID BIT",
        ]),
    ],

    # Attaching and detaching shared segments: 23 flagged sites and 24 idiom
    # candidates, of which reading rejects four.  00805000-00808000 is the clean
    # example of candidate-versus-verdict -- `LR R7,R2 / N R7,XPAGNUM /
    # SRL R7,8 / AL R7,ACORETBL` starts from a REAL ADDRESS, not a PTE, so the
    # shift is already right and the card needs nothing.
    'DMKATS': [
        ('00126000', ["         USING PAGPFRA,R6"]),
        ('00187000', [
            "         L     R6,VMSEG       THE DESIGNATION",
            "         N     R6,=A(SEGSTOM) WITHOUT THE LENGTH",
            "         ALR   R8,R6          ADDRESS OF SEGTABLE ENTRY",
        ]),
        ('00188000', ["         L     R6,SEGPTO      LOAD ADDRESS OF PTO"]),
        ('00189000', [
            "         TM    SEGPTO+3,SEGINVAL SEGMENT VALID",
        ]),
        ('00194000', [
            "         SL    R0,=A(PAGPFRA-PAGSTMP) BACKUP TO PAGTABLE",
        ]),
        ('00196000', ["         L     R3,SEGPTO      LOAD R3 WITH STE"]),
        ('00197000', '00198000', Deck.comment(
            "SRL R3,28 TOOK SEGPLEN FROM BITS 0-3 AND THE NEXT CARD ADDED ONE. "
            "PTL IS BITS 28-31 IN UNITS OF 16 ENTRIES.") + [
            "         N     R3,=A(SEGPTLF) NUMBER OF PTES",
            "         LA    R3,1(,R3)      UNITS OF 16 ENTRIES",
            "         SLL   R3,4           PAGES IN THIS SEGMENT",
        ]),
        ('00289000', Deck.comment(
            "WAS SRL R2,16 -- THE 64 KB SEGMENT NUMBER. THE NEXT CARD'S "
            "SLL R2,2 IS RIGHT IN BOTH ARCHITECTURES, SINCE AN STE IS A "
            "FULLWORD IN BOTH; ONLY THE SHIFT THAT ISOLATES THE SEGMENT "
            "NUMBER MOVES, 16 TO 20. THE THREE CARDS AT 00291000 BELOW, "
            "WHICH THIS DECK ALREADY REPLACED, FORM THE ADDRESS THIS "
            "INDEX GOES INTO -- I-162: THE GROUP WAS CONVERTED AND ITS "
            "FIRST MEMBER WAS NOT.") + [
            "         SRL   R2,20          SEGMENT NO. ONLY",
        ]),
        ('00291000', [
            "         L     R6,VMSEG       THE DESIGNATION",
            "         N     R6,=A(SEGSTOM) WITHOUT THE LENGTH",
            "         ALR   R2,R6          ADDR OF SEGTABLE ENTRY",
        ]),
        ('00294000', [
            "         S     R2,=A(PAGPFRA-PAGSTMP) BACKUP TO HEADER",
        ]),
        ('00298000', Deck.comment(
            "WAS N R1,F15 -- A PAGE NUMBER WITHIN A SIXTEEN-PAGE SEGMENT. "
            "THE SRL 12 ABOVE IS RIGHT IN BOTH ARCHITECTURES AND THE SLL 3 "
            "BELOW IS AN EIGHT-BYTE SWPTABLE ENTRY, ALSO UNCHANGED; ONLY "
            "THE NUMBER OF PAGES A SEGMENT HOLDS MOVED. DMKPGS 01010000 IS "
            "THE SAME CARD AND ALREADY READS F255. BOTH F15 AND F255 ARE "
            "DEFINED IN PSA.MACRO, SO NOTHING ELSE HAS TO BE DECLARED.") + [
            "         N     R1,F255        PAGE NO. WITHIN SEGMENT",
        ]),
        ('00335000', Deck.comment(
            "WAS SRL R2,16. SAME CHANGE AS 00289000, IN REBRANGE RATHER "
            "THAN NXTRANGE -- THE TWO LOOPS ARE NEAR-DUPLICATES.") + [
            "         SRL   R2,20          SEGMENT NUMBER ONLY",
        ]),
        ('00337000', [
            "         L     R6,VMSEG       THE DESIGNATION",
            "         N     R6,=A(SEGSTOM) WITHOUT THE LENGTH",
            "         ALR   R2,R6          ADDR OF SEGMENT ENTRY",
        ]),
        ('00340000', [
            "         S     R2,=A(PAGPFRA-PAGSTMP) BACKUP TO HEADER",
        ]),
        ('00431000', ["         USING PAGPFRA,R6"]),
        ('00497000', [
            "         L     R5,VMSEG       THE DESIGNATION",
            "         N     R5,=A(SEGSTOM) WITHOUT THE LENGTH",
            "         ALR   R8,R5          ADDR SEGTABLE ENTRY",
        ]),
        ('00498000', ["         L     R6,SEGPTO      LOAD ADDR PTO"]),
        ('00500000', [
            "         S     R6,=A(PAGPFRA-PAGSTMP) BACKUP TO HEADER",
        ]),
        ('00510000', [
            "         A     R6,=A(PAGPFRA-PAGSTMP) RESET TO PTO",
        ]),
        ('00511000', ["         L     R3,SEGPTO      LOAD STE"]),
        ('00512000', '00513000', [
            "         N     R3,=A(SEGPTLF) NUMBER OF PTES",
            "         LA    R3,1(,R3)      UNITS OF 16 ENTRIES",
            "         SLL   R3,4           PAGES IN THIS SEGMENT",
        ]),
        ('00515000', ["         L     R1,PAGPFRA     USE CORTABLE FOR TEST"]),
        ('00515600', ["         CL    R1,INVLPTE     FRAME BEEN ASSIGNED"]),
        ('00517000', ["         L     R7,PAGPFRA     LOAD CORTABLE INDEX"]),
        ('00518000', [
            "         N     R7,RESMASK     CLEAR UNWANTED BITS",
            "         SRL   R7,8           A CORTABLE ENTRY IS 16 A PAGE",
        ]),
        ('00520000', [
            "         TM    PAGPFRA+2,PAGINV    CHANGED PAGE",
        ]),
        ('00566000', [
            "         LA    R6,PAGPFRA+L'PAGPFRA BUMP TO NEXT PTE",
        ]),
        ('00610000', ["         L     R0,SEGPTO      LOAD STE"]),
        ('00611000', '00612000', [
            "         N     R0,=A(SEGPTLF) NUMBER PTE'S",
            "         AL    R0,F1          UNITS OF 16 ENTRIES (I-237)",
            "         SLL   R0,4           PAGES IN THIS SEGMENT",
        ]),
        ('00613000', [
            "         A     R1,=A(PAGPFRA-PAGSTMP) LOAD ADDR PTO",
        ]),
        ('00614000', Deck.comment(
            "STCM KEPT BYTE 0, WHICH HELD SEGPLEN. THE FLAGS ARE BITS 26-31 NOW, "
            "SO THE ENTRY IS REBUILT FROM THE OLD FLAGS AND THE NEW ORIGIN.") + [
            "         L     R15,SEGPTO     THE CURRENT ENTRY",
            "         N     R15,=A(SEGFLGM) KEEP I, C AND PTL",
            "         OR    R15,R1         WITH THE NEW ORIGIN",
            "         ST    R15,SEGPTO     UPDATE SEGTABLE ENTRY",
        ]),
        ('00615000', [
            "         OI    SEGPTO+3,SEGINVAL MARK ENTRY AS INVALID",
        ]),
        ('00623000', ["         USING PAGPFRA,R1"]),
        ('00627000', [
            "         AL    R2,=A(PAGPFRA-PAGSTMP) BUMP TO PTO",
        ]),
        ('00629000', ["         MVC   PAGPFRA,INVLPTE INVALIDATE PTE"]),
        ('00630000', [
            "         TM    PAGPFRA+2-PAGPFRA(R2),PAGINV OLD PTE VALID",
        ]),
        ('00643000', [
            "NXTENT3  TM    PAGPFRA+2-PAGPFRA(R2),PAGINV PTE VALID",
        ]),
        ('00652000', [
            "         LA    R1,PAGPFRA+L'PAGPFRA BUMP TO NEXT NEW PTE",
        ]),
        ('00668000', ["         USING PAGPFRA,R6"]),
        ('00672000', [
            "         L     R3,PAGPFRA-PAGPFRA(,R2) GET CORTABLE INDEX",
        ]),
        ('00673000', [
            "         N     R3,RESMASK     CLEAR UNWANTED BITS",
            "         SRL   R3,8           A CORTABLE ENTRY IS 16 A PAGE",
        ]),
        ('00713000', [
            "         N     R6,=A(SEGPTOM) CLEAR PTE COUNTER",
        ]),
        ('00714000', '00715000', [
            "         N     R0,=A(SEGPTLF) NUMBER PTES",
            "         AL    R0,F1          UNITS OF 16 ENTRIES (I-237)",
            "         SLL   R0,4           PAGES IN THIS SEGMENT",
        ]),
        ('00719000', [
            "         S     R5,=A(PAGPFRA-PAGSTMP) BACKUP TO HEADER",
        ]),
        ('00735000', ["         L     R7,PAGPFRA     LOAD CORTABLE INDEX"]),
        ('00736000', [
            "         N     R7,RESMASK     CLEAR UNWANTED BITS",
            "         SRL   R7,8           A CORTABLE ENTRY IS 16 A PAGE",
        ]),
        ('00783000', [
            "         LA    R6,PAGPFRA+L'PAGPFRA BUMP TO NEXT PTE",
        ]),
        ('00815000', [
            "         SLL   R15,2          FOR 4 BYTE PG TABLE ENTRIES",
        ]),
        ('00817000', [
            "         SL    R6,=A(PAGPFRA-PAGSTMP) BACKUP TO HEADER",
        ]),
        # Five constants, every one of them a format assumption written out.
        ('00852000', ["RESMASK  DC    A(PAGPFRM)     MASK FOR PAGE RESIDENT"]),
        ('00854000', ["CLCNTINV DC    A(SEGPTOM)     CLEAR COUNT, INVALID &"]),
        ('00860000', Deck.comment(
            "PAGREF MOVED FROM BYTE 1 TO BYTE 3, SO THIS MASK IS DERIVED FROM "
            "PAGREF RATHER THAN WRITTEN OUT. IT WAS X'0000FFFE'.") + [
            "REFMASK  DC    A(X'FFFFFFFF'-PAGREF) FORCE REF BIT OFF",
        ]),
        ('00860500', [
            "INVLPTE  DC    A(PAGINVW)     INVALID PTE BIT MASK",
        ]),
        ('00861000', Deck.comment(
            "SWLENGTH WAS DC F'192' -- A HARD-CODED PAGBMP, IN THIS MODULE AND "
            "IN DMKVMA, WITH NOTHING JOINING IT TO CORE.COPY. I-116'S SHAPE.") + [
            "SWLENGTH DC    A(PAGBMP)      LENGTH OF SHARED PAGE &",
        ]),
        # The pair at 00330000/00331000 brackets a range to whole segments --
        # start down to page 0, end up to the last page -- and 00343000 reuses
        # the second mask to extract a page number.  All three are geometry.
        ('00863000', '00864000', Deck.comment(
            "FORCEPG0 WAS X'00FF0000', THE 64 KB SEGMENT NUMBER IN BITS 8-15, "
            "WHICH IS EVERY SEGMENT A 24-BIT ADDRESS CAN NAME. A 1 MB SEGMENT "
            "NUMBER IS BITS 1-11, SO THE MASK THAT LEAVES A SEGMENT START IS "
            "X'7FF00000' -- DMKVAT'S OWN CODEB0 VALUE, AND THE SAME ONE "
            "DMKPGS 01049300 AND 01054000 CARRY. I-188.") + Deck.comment(
            "FORCEPGF WAS X'0000F000', PAGE 15, THE LAST OF A 64 KB SEGMENT'S "
            "SIXTEEN. A 1 MB SEGMENT HAS 256 PAGES AND ITS LAST IS 255, SO "
            "THE MASK IS X'000FF000'. 00343000 ANDS WITH THIS SAME CONSTANT "
            "TO GET A PAGE NUMBER -- BITS 12-19 NOW, NOT 16-19 -- AND THE "
            "SRL 9 THAT FOLLOWS IT STAYS: IT RELATES A PAGE'S ADDRESS WEIGHT "
            "OF 4096 TO AN 8-BYTE SWPTABLE ENTRY, AND NEITHER MOVED.") + [
            "FORCEPG0 DC    X'7FF00000'    MASK FOR SEGMENT & PAGE 0",
            "FORCEPGF DC    X'000FF000'    MASK FOR LAST PAGE OF SEGMENT",
        ]),
    ],

    # The densest module in the conversion: the shared-segment and attached-
    # processor configuration.  Its AP path is DELIBERATELY NOT CONVERTED -- see
    # the ABEND at 01024000 and I-139.
    'DMKCFG': [
        # `L R4,VMSEG-VMBLOK(,R4)` loads the designation itself, so masking the
        # loaded value is right here; the sites that ADD it to an index must mask
        # VMSEG first instead, because an index of segnum*4 reaches STL's bits.
        ('00488000', [
            "         L     R4,VMSEG-VMBLOK(,R4) CP SEGTABLE",
            "         N     R4,=A(SEGSTOM) WITHOUT THE LENGTH",
        ]),
        ('00490000', [
            "         SRDL  R2,20          SEGMENT TO LOW ORDER OF GPR2,",
        ]),
        ('00497000', [
            "         N     R4,=A(SEGPTOM) CLEAR UNWANTED BITS",
        ]),
        ('00498000', Deck.comment(
            "R3 HOLDS THE ADDRESS BELOW THE SEGMENT. THE PAGE FIELD IS EIGHT "
            "BITS NOW, NOT FOUR, SO REACHING PAGE*8 TAKES 21 RATHER THAN 25.") + [
            "         SRL   R3,21          SET PAGE NUMBER *8",
        ]),
        ('00499000', [
            "         S     R4,=A(PAGPFRA-PAGSWP) TO SWPTABLE PTR",
        ]),
        ('00502000', Deck.comment(
            "PAGCORE-PAGSWP WAS BEING USED AS THE CONSTANT 4 TO REACH SWPCYL "
            "FROM SWPFLAG -- A DAT SYMBOL STANDING IN FOR AN UNRELATED OFFSET. "
            "IT IS 4 TODAY AND 12 AFTER PAGORIG, SO IT WOULD HAVE READ THE WRONG "
            "FIELD. SWPCYL-SWPFLAG IS WHAT IT MEANT.") + [
            "         L     R0,SWPCYL-SWPFLAG(R3,R4) DASD ADDRESS",
        ]),
        ('00770000', [
            "         SRL   R2,20          SEGMENT NO. ONLY",
        ]),
        ('00773000', [
            "         L     R1,VMSEG       THE DESIGNATION",
            "         N     R1,=A(SEGSTOM) WITHOUT THE LENGTH",
            "         ALR   R2,R1          STE POINTER",
        ]),
        ('00774000', [
            "         TM    3(R2),SEGINVAL SEGMENT OK?",
        ]),
        ('00780000', [
            "         N     R2,=A(SEGPTOM) CLEAR UNWANTED BITS",
        ]),
        ('00783000', [
            "         N     R1,F255        PAGE NO. WITHIN SEGMENT",
        ]),
        ('00786000', [
            "         LA    R2,256*L'PAGPFRA+(SWPFLAG-SWPVM)(R1,R2)",
        ]),
        # 00789000 `A R0,F2` and 00873000/00934000 `S Rn,F4` are counts and
        # indexes, not DAT offsets.  idiom.py marks them; reading rejects them.
        ('00881000', [
            "         LR    R7,R2          SAVE PTO",
            "         N     R7,=A(SEGPTOM) WITHOUT THE LENGTH",
        ]),
        ('00882000', [
            "         SL    R7,=A(PAGPFRA-PAGSTMP) BACK-UP TO HEADER",
        ]),
        ('00894000', [
            "         L     R1,VMSEG       LOAD ADDRESS OF SEGTABLE",
            "         N     R1,=A(SEGSTOM) WITHOUT THE LENGTH",
        ]),
        ('00896000', Deck.comment(
            "F1 WAS BEING USED AS SEGINV -- THE INVALID BIT AS A BARE 1, WITH NO "
            "SYMBOL. THE SIXTH SITE OF THAT SHAPE.") + [
            "         O     R2,=A(SEGINVAL) ASSURE SEGINV FLAG",
        ]),
        ('00907000', [
            "         LR    R1,R10         PTO",
            "         N     R1,=A(SEGPTOM) WITHOUT THE FLAGS",
        ]),
        ('00908000', [
            "         SL    R1,=A(PAGPFRA-PAGSTMP) BACKUP TO HEADER",
        ]),
        ('00972000', [
            "         L     R2,VMSEG       THE DESIGNATION",
            "         N     R2,=A(SEGSTOM) WITHOUT THE LENGTH",
            "         ALR   R7,R2          ADDRESS OF SEGTABLE",
        ]),
        ('00974000', [
            "         OI    3(R7),SEGINVAL MAKE SURE INVALID ON",
        ]),
        ('00975000', Deck.comment(
            "ONLY THE INVALID BIT IS CLEARED HERE, NOT THE WHOLE FLAG FIELD: "
            "THE PTL IS STILL NEEDED AT 00979000 TO COUNT THE ENTRIES.") + [
            "         N     R10,=A(X'FFFFFFFF'-SEGINVAL) VALIDATE",
        ]),
        ('00979000', '00981000', Deck.comment(
            "SRL R2,28 EXTRACTED SEGPLEN FROM BITS 0-3 AND THE NEXT CARD ADDED "
            "ONE. PTL IS BITS 28-31 AND COUNTS 16 ENTRIES AT A TIME, SO IT IS A "
            "MASK AND A SHIFT INSTEAD, AND THE PLUS ONE IS SUBSUMED.") + [
            "         N     R2,=A(SEGPTLF) NUMBER OF PAGTABLE ENTRIES",
            "         LA    R2,1(,R2)      UNITS OF 16 ENTRIES",
            "         SLL   R2,4           PAGES IN THIS SEGMENT",
        ]),
        ('00982000', [
            "         N     R10,=A(SEGPTOM) WITHOUT THE FLAGS",
            "         SL    R10,=A(PAGPFRA-PAGSTMP) BACKUP TO HDR",
        ]),
        # 4(4,R10) and 8(,R10) are PAGACT and PAGSHR and survive: PAGORIG went
        # in after PAGSWP, so the first twelve bytes of the header are unmoved.
        # 16+16*2 is PAGTSWP spelled as digits and does not survive.
        ('00985000', [
            "         MVC   PAGTSWP(4,R10),ASYSVM RE-ASIGN",
        ]),
        ('00986000', [
            "         LA    R10,PAGTSWP+(SWPFLAG-SWPVM)(,R10)",
        ]),
        ('01009000', [
            "         L     R0,VMSEG       THE DESIGNATION",
            "         N     R0,=A(SEGSTOM) WITHOUT THE LENGTH",
            "         ALR   R7,R0          GET ADDR SEGTABLE ENTRY",
        ]),
        ('01014000', [
            "         LA    R0,PAGPFRA     LOAD ADDRESS OF PTO",
        ]),
        ('01015000', Deck.comment(
            "STCM R0,B'0111',1(R7) STORED THREE BYTES AND KEPT BYTE 0, WHICH "
            "HELD SEGPLEN. THE FLAGS ARE BITS 26-31 NOW, SO THE ENTRY IS "
            "REBUILT FROM THE OLD FLAGS AND THE NEW ORIGIN.") + [
            "         L     R15,0(R7)      THE CURRENT ENTRY",
            "         N     R15,=A(SEGFLGM) KEEP I, C AND PTL",
            "         OR    R15,R0         WITH THE NEW ORIGIN",
            "         ST    R15,0(R7)      STORE NEW PTO IN STE",
        ]),
        ('01016000', [
            "         OI    3(R7),SEGINVAL FLAG STE AS INVALID",
        ]),
        ('01018000', Deck.comment(
            "STCM R10,8,SHRPAGE PUT THE PAGE COUNT IN BYTE 0. SHRPAGE IS AN STE "
            "IN ALL BUT NAME, SO ITS LENGTH MOVES TO THE LOW NIBBLE OF BYTE 3 "
            "WITH THE STE'S.") + [
            "         L     R15,SHRPAGE    THE ENTRY JUST STORED",
            "         O     R15,=A(SEGPTLF) FULL TABLE, 256 PAGES",
            "         ST    R15,SHRPAGE    NUMBER OF PAGES IN SEGMENT",
        ]),
        ('01020000', [
            "         N     R10,=A(SEGPTOM) CLEAR COUNT AND INV BITS",
        ]),
        ('01021000', [
            "         SL    R10,=A(PAGPFRA-PAGSTMP) BACKUP TO HEADER",
        ]),
        ('01024000', '01025000', Deck.comment(
            "THE ATTACHED-PROCESSOR SHARED-SEGMENT PATH IS DELIBERATELY NOT "
            "CONVERTED. PAGBMP IS 3136 BYTES AND MVC STOPS AT 256, SO THESE TWO "
            "COPIES NEED MVCL AND AN EVEN-ODD PAIR THIS ROUTINE HAS NOTHING "
            "SPARE FOR -- R0, R1, R5, R7, R10 AND R14 ARE ALL LIVE ACROSS THEM. "
            "THE PATH IS UNREACHABLE UNDER AP=NO, WHICH XA0014DK FORCES ON "
            "PURPOSE (I-50), SO IT ABENDS LOUDLY RATHER THAN BEING CONVERTED "
            "UNTESTABLY. I-139.") + [
            "         ABEND 9              AP SHARED SEGS NOT CONVERTED",
        ]),
        ('01035000', [
            "         LA    R0,PAGBMP+PAGPFRA         GET ADDR AP PTO",
        ]),
        ('01045000', [
            "         N     R15,=A(SEGPTLF) OBTAIN PTE COUNT",
            "         LA    R15,1(,R15)    UNITS OF 16 ENTRIES",
            "         SLL   R15,4          PAGES IN THIS SEGMENT",
        ]),
        ('01046000', [
            "*                             (BUMP FOR LOOP SUBSUMED ABOVE)",
        ]),
        ('01056000', [
            "         N     R14,=A(SEGPTLF) OBTAIN NUMBER PTE'S",
            "         LA    R14,1(,R14)    UNITS OF 16 ENTRIES",
            "         SLL   R14,4          PAGES IN THIS SEGMENT",
        ]),
        ('01056500', Deck.comment(
            "PAGBMP+PAGBMP IS 6272 AND AN LA DISPLACEMENT STOPS AT 4095.") + [
            "         L     R0,=A(PAGBMP+PAGBMP) AP table size",
        ]),
        ('01105000', [
            "         L     R1,VMSEG       THE DESIGNATION",
            "         N     R1,=A(SEGSTOM) WITHOUT THE LENGTH",
            "         ALR   R7,R1          LOAD ADDRESS OF STE",
        ]),
        ('01106000', ["         USING SEGPTO,R7"]),
        ('01107100', [
            "         L     R1,SEGPTO      MAIN (IPL) PROC PAGTABLE",
            "         N     R1,=A(SEGPTOM) WITHOUT THE FLAGS",
        ]),
        ('01109000', [
            "         L     R15,SEGPTO     THE CURRENT ENTRY",
            "         N     R15,=A(SEGFLGM) KEEP I, C AND PTL",
            "         OR    R15,R1         WITH THE AP PAGTABLE",
            "         ST    R15,SEGPTO     ADJUST TO ATTACHED PGT",
        ]),
        ('01141000', [
            "         L     R10,VMSEG      ADDRESS OF SEGMENT TABLE",
            "         N     R10,=A(SEGSTOM) WITHOUT THE LENGTH",
        ]),
        ('01151000', [
            "         SRL   R1,8           LEAVE ONLY SEGMENT NUMBER",
        ]),
        ('01154200', [
            "         N     R7,=A(SEGPTOM) CLEAR EXTENSION BITS",
        ]),
        ('01155000', [
            "         SL    R7,=A(PAGPFRA-PAGSTMP) BACKUP TO HEADER",
        ]),
        ('01161000', [
            "SEGSHR   LA    R1,L'SEGPTO(,R1) INDEX OF NEXT STE",
        ]),
        ('01414300', [
            "         SRL   R1,20          GET SEGMENT NUMBER ONLY",
        ]),
        ('01414500', [
            "         IC    R2,VMSEG+3     GET SEGMENT TABLE LENGTH",
            "         N     R2,=A(SEGSTLM) WITHOUT THE S BIT",
        ]),
        ('01415100', [
            "         L     R6,VMSEG       THE DESIGNATION",
            "         N     R6,=A(SEGSTOM) WITHOUT THE LENGTH",
            "         ALR   R1,R6          GET ADDRESS OF STE",
        ]),
        ('01415225', '01415325', Deck.comment(
            "THREE CARDS DID WHAT ONE MASKED LOAD DOES NOW: ICM BYTES 1-2, THEN "
            "IC BYTE 3, THEN A MASK CLEARING THE INVALID BIT -- BECAUSE THE "
            "S/370 PTO WAS BYTES 1-3 WITH THE LENGTH IN BYTE 0. THE ESA/390 PTO "
            "IS BITS 1-25 WITH THE FLAGS IN 26-31.") + [
            "         L     R6,SEGPTO-SEGTABLE(R1) THE WHOLE ENTRY",
            "         N     R6,=A(SEGPTOM) ANY PTE POINTER?",
            "         BZ    SETCC1         NO NAMED SEGMENT",
        ]),
        ('01415350', [
            "         SL    R6,=A(PAGPFRA-PAGSTMP) BACKUP TO HDR",
        ]),
    ],

    # The module with the clearest statement in the tree of what a PTE is, and a
    # hard-coded copy of PAGBMP.  `SLL R2,8  FORM REAL ADDRESS` says that a
    # masked S/370 PTE times 256 IS the frame's real address, so the shift is
    # REMOVED on that path while an SRL 8 is ADDED on the ACORETBL path -- from
    # one load, in opposite directions, four lines apart.
    'DMKVMA': [
        ('00133000', ["         USING PAGPFRA,R6"]),
        # Two sites I missed on the first pass, found later by idiom.py's
        # vmseg-add class.  `AL R8,VMSEG` adds the whole designation, STL and
        # all, to an index -- the same defect as `L Rn,VMSEG` with a different
        # opcode, and I had both blocks open and converted the cards after them.
        ('00195000', Deck.comment(
            "THE MASK GOES ON VMSEG, NOT ON THE SUM. AN INDEX OF SEGNUM*4 "
            "REACHES BIT 25 FOR 16 SEGMENTS, WHICH IS WHERE STL BEGINS, SO "
            "MASKING AFTER THE ADD WOULD CLEAR PART OF THE INDEX. R4 IS FREE "
            "HERE -- IT IS ZEROED THREE CARDS BELOW.") + [
            "         L     R4,VMSEG       THE SEGMENT TABLE DESIGNATION",
            "         N     R4,=A(SEGSTOM) WITHOUT THE LENGTH",
            "         ALR   R8,R4          OBTAIN PROPER STE ADDR",
        ]),
        ('00196000', [
            "         TM    SEGPTO+3,SEGINVAL SEGMENT INVALID",
        ]),
        ('00199000', Deck.comment(
            "PTL IS THE LOW NIBBLE OF BYTE 3 AND COUNTS 16 ENTRIES AT A TIME.") + [
            "         IC    R4,SEGPTO+3    NO. OF PAGES IN THIS SEG",
            "         N     R4,=A(SEGPTLF) KEEP ONLY PTL",
            "         LA    R4,1(,R4)      UNITS OF 16 ENTRIES",
            "         SLL   R4,4           PAGES IN THIS SEGMENT",
        ]),
        ('00202000', [
            "         L     R6,SEGPTO      GET PTO ADDRESS",
            "         N     R6,=A(SEGPTOM) WITHOUT THE FLAGS",
        ]),
        ('00204000', [
            "PAGEISK  TM    PAGPFRA+2,PAGINV IS PAGE IN STORAGE?",
        ]),
        ('00206000', [
            "         L     R2,PAGPFRA     PICK UP REAL PAGE ADDRESS",
        ]),
        ('00215000', [
            "INVAL    LA    R6,PAGPFRA+L'PAGPFRA NEXT PAGE TABLE ENTRY",
        ]),
        # A page-table address matched against every STE byte by byte, because
        # the S/370 PTO is bytes 1-3 and the flags are byte 0 and bit 31.  In
        # ESA/390 the origin is bits 1-25 and the flags 26-31, so the comparison
        # becomes one masked fullword compare.  TEMPR0 is a PSA fullword.
        ('00239040', [
            "         SLL   R15,2          ADJUSTED FOR 4 BYTE ENTRIES",
        ]),
        ('00239060', [
            "         SRL   R15,2          BACK TO VIRTUAL PAGE NUMBER",
        ]),
        ('00239100', '00239150', Deck.comment(
            "THE S/370 FORM COMPARED BYTES 1-2 WITH CLM, THEN BYTE 3 SEPARATELY "
            "WITH THE INVALID BIT REMOVED, BECAUSE THE PTO WAS BYTES 1-3 AND THE "
            "LENGTH WAS BYTE 0. AN ESA/390 PTO IS BITS 1-25 WITH THE FLAGS IN "
            "26-31, SO ONE MASKED FULLWORD COMPARE DOES IT.") + [
            "         MVC   TEMPR0,SEGTABLE THE WHOLE ENTRY",
            "         NC    TEMPR0,CLCNTINV ONLY THE PAGE TABLE ORIGIN",
            "         CL    R6,TEMPR0      FULL MATCH?",
            "         BE    FNDSEG         YES",
        ]),
        ('00239200', [
            "FNDSEG   SLL   R14,8          MAKE ROOM FOR PAGE NUMBER",
        ]),
        ('00239260', [
            "         SL    R6,=A(PAGPFRA-PAGSHR) BACK-UP TO THE SHRTABLE",
        ]),
        # The CORTABLE index and the real address, from one load, diverging.
        ('00272000', [
            "         L     R2,PAGPFRA     LOAD PAGTABLE ENTRY",
        ]),
        ('00273000', [
            "         N     R2,RESMASK     CLEAR UNWANTED BITS",
            "         SRL   R2,8           A CORTABLE ENTRY IS 16 A PAGE",
        ]),
        ('00278000', [
            "         OI    PAGPFRA+2,PAGINV FLAG PTE AS INVALID",
        ]),
        ('00337000', [
            "         L     R5,VMSEG            THE DESIGNATION",
            "         N     R5,=A(SEGSTOM)      WITHOUT THE LENGTH",
            "         ALR   R8,R5               GET ADDR OF SEGTABLE ENTRY",
        ]),
        ('00338000', [
            "         L     R5,SEGPTO           GET ADDR OF PAGE TABLE",
        ]),
        ('00340000', [
            "         TM    SEGPTO+3,SEGINVAL   IS SEG INVALID FOR VM",
        ]),
        ('00342000', [
            "         S     R5,=A(PAGPFRA-PAGSTMP) BACKUP TO HEADER",
        ]),
        ('00349000', [
            "         A     R5,=A(PAGPFRA-PAGSTMP) RESTORE PAGTABLE ORIGIN",
        ]),
        # STCM stored three bytes into 1-3, keeping byte 0's length.  The flags
        # are in the low six bits now, so the entry is rebuilt instead.
        ('00360000', Deck.comment(
            "STCM R5,7,SEGPAGE+1 KEPT BYTE 0, WHICH HELD SEGPLEN. THE FLAGS ARE "
            "BITS 26-31 NOW, SO THE ENTRY IS REBUILT: THE OLD FLAGS, OR'D WITH "
            "THE NEW ORIGIN. R5 IS LEFT CLEAN BECAUSE THE NEXT CARD SUBTRACTS "
            "THE HEADER OFFSET FROM IT.") + [
            "         L     R0,SEGPTO           THE CURRENT ENTRY",
            "         N     R0,=A(SEGFLGM)      KEEP I, C AND PTL",
            "         OR    R0,R5               WITH THE NEW ORIGIN",
            "         ST    R0,SEGPTO           STORE NEW PAGE TABLE",
        ]),
        ('00362000', [
            "         S     R5,=A(PAGPFRA-PAGSTMP) BACKUP TO PAGE HEADER",
        ]),
        ('00451000', [
            "         L     R7,PAGPFRA     LOAD PAGTABLE ENTRY",
        ]),
        ('00453000', [
            "         LR    R2,R7          PTE TO R2",
            "         SRL   R7,8           A CORTABLE ENTRY IS 16 A PAGE",
        ]),
        ('00455000', Deck.comment(
            "SLL R2,8  FORM REAL ADDRESS SAID IT OUTRIGHT: A MASKED S/370 PTE "
            "TIMES 256 IS THE FRAME'S REAL ADDRESS. AN ESA/390 PTE ALREADY IS "
            "THAT ADDRESS, SO THE SHIFT GOES -- WHILE THE CORTABLE PATH FROM THE "
            "SAME LOAD GAINS ONE, FOUR LINES ABOVE.") + [
            "*                             (SLL R2,8 REMOVED -- SEE ABOVE)",
        ]),
        ('00488000', [
            "         MVC   PAGPFRA,=A(PAGINVW) INVALIDATE THE PTE",
        ]),
        # Two constants that are masks in disguise, and one that is a hard-coded
        # PAGBMP.  SWLENGTH DC F'192' is I-116's shape for the sixth time: a
        # value computed in CORE.COPY and written out as a literal here, with
        # nothing joining them.  A(PAGBMP) cannot drift again.
        ('00513000', [
            "RESMASK  DC    A(PAGPFRM)     MASK FOR PAGE RESIDENT",
        ]),
        ('00514000', [
            "CLCNTINV DC    A(SEGPTOM)     CLEAR COUNT & UNWANTED BITS",
        ]),
        ('00518000', [
            "SWLENGTH DC    A(PAGBMP)      LENGTH OF SHARED PAGE &",
        ]),
    ],

    # Clearing a PTE's frame address while keeping its flags.  The halfword form
    # was MVI byte 0 / NI byte 1 keeping the low nibble / OI the invalid bit.
    # For a fullword the order has to change: PAGREF is saved FIRST, while byte 3
    # is still intact, because clearing bytes 0-2 is now a separate operation
    # from clearing the flags.
    'DMKMCH': [
        ('00746000', ["         USING PAGPFRA,R6     ADDRESSABILITY FOR PTE"]),
        ('00749000', '00751000', Deck.comment(
            "THE HALFWORD FORM CLEARED BYTE 0, THEN KEPT THE LOW NIBBLE OF BYTE "
            "1 -- WHERE PAGINVAL AND PAGREF LIVED -- THEN SET INVALID. A "
            "FULLWORD PTE KEEPS PAGREF IN BYTE 3 AND I IN BYTE 2, SO PAGREF IS "
            "SAVED FIRST, WHILE BYTE 3 IS STILL INTACT, AND THE FRAME ADDRESS "
            "IS CLEARED AS ITS OWN THREE BYTES.") + [
            "         NI    PAGPFRA+3,PAGREF KEEP ONLY REFERENCED",
            "         XC    PAGPFRA(3),PAGPFRA CLEAR THE FRAME ADDRESS",
            "         OI    PAGPFRA+2,PAGINV INVALIDATE THE PAGE TABLE",
        ]),
    ],
}


def dmkcpidat():
    """DMKCPI: the ESA/390 DAT tables CP builds for ITSELF, and the CORTABLE walk.

    `DMKBLDRT` allocates and shapes the tables; this routine fills them in for
    CP's own 16 MB and marks every page locked in the CORTABLE.  It is therefore
    the second of the two modules that must be right before `LRA` can succeed --
    the rest of the conversion is other people's virtual machines.

    Five sites are flagged and six are not.  The six are the usual shape:

      * `L R3,VMSEG` with no mask, and `LA R9,0(,R9)  CLEAR TABLE LENGTH`
        which strips nothing now that STL is in the low bits (`I-128`)
      * `S R8,F4  BACK UP TO SWPTABLE POINTER` -- the same assumption
        `DMKBLD` makes twice, that `PAGSWP` sits four bytes below the page
        table (`I-130`)
      * `LA R6,16  GET NUMBER OF PAGES IN A SEGMENT FOR BCT` and
        `AL R9,F2  POINT TO NEXT PAGTABLE ENTRY` -- 256 pages, 4-byte entries
      * `ALR R2,R4  BUMP REAL PAGE ADDRESS`, where `R4` is X'10' because it is
        *also* the `BXLE` increment for a 16-byte CORTABLE entry.  One register
        served two strides that happened to agree; they no longer do.

    And one flagged site is worth reading for what it says about literals:

        NI    SEGPAGE+3,255-1 CLEAR INVALID STE BIT

    `255-1`, not `255-SEGINV`.  The rename reached it only because the same card
    names `SEGPAGE`; had the author written `3(R3)` for the field as well, this
    would have been silent in a routine whose failure mode is a CP that builds
    plausible tables and dies in `LRA`.
    """
    d = Deck(XA35)
    src = SRC + '/DMKCPI.ASSEMBLE'

    def one(seq, lines, to=None):
        limit = next_seq(src, to or seq)
        base = int(seq)
        for inc in (100, 10, 1):
            if limit is None or base + inc * len(lines) < int(limit):
                d.replace(seq, to, first=str(base + inc).zfill(8), inc=inc,
                          limit=limit, lines=lines)
                return
        raise ValueError('no room after %s for %d cards' % (seq, len(lines)))

    one('01495000', [
        "         L     R3,VMSEG       GET ADDRESS OF SEGMENT TABLE",
        "         N     R3,=A(SEGSTOM) WITHOUT THE LENGTH",
    ])
    one('01496000', ["         USING SEGPTO,R3       ADDRESSABILITY"])
    one('01509000', Deck.comment(
        "255-1 WAS A LITERAL WHERE SEGINV WAS MEANT. THE RENAME REACHED THIS "
        "CARD ONLY BECAUSE IT ALSO NAMES SEGPAGE.") + [
        "         NI    SEGPTO+3,255-SEGINVAL CLEAR INVALID STE BIT",
    ])
    one('01510000', ["         L     R9,SEGPTO      GET PAGETABLE ADDR"])
    one('01511000', [
        "         N     R9,=A(SEGPTOM) CLEAR TABLE LENGTH",
    ])
    one('01512000', ["         USING PAGPFRA,R9     ADDRESSABILITY"])
    one('01513000', [
        "         LA    R6,256         NO. PAGES IN A SEGMENT FOR BCT",
    ])
    one('01515000', [
        "         S     R8,=A(PAGPFRA-PAGSWP) BACK UP TO SWPTABLE",
    ])
    one('01528000', [
        "         ST    R2,PAGPFRA     INITIALIZE PAGTABLE ENTRY",
    ])
    one('01546000', Deck.comment(
        "R4 IS X'10' BECAUSE IT IS ALSO THE BXLE INCREMENT FOR A 16-BYTE "
        "CORTABLE ENTRY, AND AN S/370 PTE HAPPENS TO STEP BY 16 TOO. AN ESA/390 "
        "PTE IS THE PAGE'S REAL ADDRESS, SO THE TWO STRIDES PART COMPANY.") + [
        "         AL    R2,F4096       BUMP REAL PAGE ADDRESS",
    ])
    one('01554000', [
        "         AL    R9,F4          POINT TO NEXT PAGTABLE ENTRY",
    ])
    return d


def equcopy():
    """The nine ESA/390 architecture constants, in the member every module sees.

    They lived in `CORE.COPY` first, beside the structures they describe, which
    read like the right call and was wrong: `CORE.COPY` is copied by 42 modules
    and `EQU.COPY` by 179 of 192.  `DMKCDB`, `DMKCDM` and `DMKDRD` name
    `SEGINVAL` and `SEGSTOM` and copy `EQU` but not `CORE`, so they failed with
    `IFO188 UNDEFINED SYMBOL` -- **seven of the twelve diagnostics in the
    1 October build, from one placement decision**.  `I-143`.

    The distinction that was missed is between a FIELD and a CONSTANT.  A field
    belongs to its structure: `SEGPTO` and `PAGPFRA` stay in `CORE.COPY`, and so
    do `PAGTSWP`, `PAGBMP` and `PAGSWPE`, because they are computed FROM those
    fields (`SWPCODE-SWPFLAG+1`) and cannot be stated without them.  A mask over
    an architected word is not part of any structure -- `X'7FFFF000'` is the
    ESA/390 STD, whoever is looking at it -- so it belongs where everyone can
    see it.  Nine EQUs, one definition each, still one place to be wrong.

    Of the 13 modules that do not copy `EQU`, only `DMKSYS` has a deck at all,
    and its deck names none of the nine; checked before the move rather than
    after.
    """
    d = Deck(XA37)
    # I-208: a DMKPTRAN PARM flag that says "R1 is a clean 31-bit virtual
    # address, do not strip it to 24 bits".  Set by TRANS OPT=(...,AMODE31)
    # and by CALL DMKPTRAN,PARM=...+AMODE31.  X'02' and X'01' were free.
    d.insert('00110060', first='00110065', inc=5, limit='00110100', lines=[
        "AMODE31  EQU   X'02'          R1 IS A CLEAN 31-BIT VIRTUAL",
        "*                             ADDRESS; STRIP BIT 0 ONLY",
        "*  M2 STEP 3: VMFSTAT BIT KEPT BY THE PSW GATEKEEPERS (DMKDSP",
        "*  PSWCKSUB, DMKPRV LPSW, DMKSVC): EC PSW, BIT 32 ON. IN BC",
        "*  MODE BIT 32 IS ILC, SO VMPSW+4 ALONE IS NOT THE TEST.",
        "VMAM31   EQU   X'01'          VMFSTAT: GUEST RUNS AMODE 31",
    ])
    d.insert('00168000', first='00168100', inc=10,
             limit=next_seq(SRC + '/EQU.COPY', '00168000'),
             lines=Deck.comment(
        "ESA/390 DAT CONSTANTS. S/370 PACKS LENGTHS AND FLAGS INTO THE HIGH "
        "BYTE OF A POINTER, WHICH 24-BIT ADDRESS FORMATION IGNORES, SO A PACKED "
        "WORD IS USABLE AS AN ADDRESS WITH NOTHING TO STRIP. ESA/390 MOVES THEM "
        "TO THE LOW BITS -- STL 25-31, STE FLAGS 26-31, PTE FLAGS 21-22 -- "
        "WHICH ADDRESS FORMATION NEVER IGNORES. SO EVERY PACKED POINTER NEEDS "
        "AN EXPLICIT MASK WHERE IT NEEDED NONE, AND AMODE 24 DOES NOT HELP. "
        "I-128. THESE ARE CONSTANTS OVER ARCHITECTED WORDS, NOT FIELDS OF ANY "
        "STRUCTURE, SO THEY LIVE HERE AND NOT IN CORE COPY -- I-143.") + [
        "SEGINVAL EQU   X'20'          STE SEGMENT INVALID -- BIT 26",
        "PAGINV   EQU   X'04'          PTE PAGE INVALID -- BIT 21",
        "PAGINVW  EQU   (PAGINV*256)   PTE INVALID, AS A FULLWORD",
        "SEGSTOM  EQU   X'7FFFF000'    STD SEG TABLE ORIGIN 1-19",
        "SEGSTLM  EQU   X'0000007F'    STD SEG TABLE LENGTH 25-31",
        "SEGPTOM  EQU   X'7FFFFFC0'    STE PAGE TABLE ORIGIN 1-25",
        "SEGPTLF  EQU   X'0F'          STE PTL, FULL, AT SEGPTO+3",
        "SEGFLGM  EQU   X'0000003F'    STE I, C AND PTL -- NOT PTO",
        "PAGPFRM  EQU   X'7FFFF000'    PTE PAGE FRAME ADDR 1-19",
    ])
    return d


def corecopy():
    """STE-DESIGN step 1: the DAT table DSECTs, with every changed name CHANGED.

    The renames are the design, not cosmetics.  `STE-DESIGN.md` originally said
    this step changed nothing's behaviour -- *"nothing executes differently yet;
    this makes the symbols mean the right thing"* -- and `tools/dattab.py` showed
    that to be wrong.  CP reaches the page-table entry with **13 `LH` and 5
    `STH`** instructions, and `LH` on a fullword field is legal assembler: change
    the DSECT alone and eighteen sites read the wrong two bytes and **assemble
    clean**.  That is `I-116`'s shape with 238 lines to hide in instead of one.

    So every symbol whose meaning moves is RENAMED WITH NO ALIAS, and the
    assembler becomes the checklist: an unconverted site fails with
    `IFO188 UNDEFINED SYMBOL` instead of quietly working on the wrong bytes.
    This is `19-M1-STEP2`'s reasoning reused -- `INTTIO` was renamed to `IOSCHNO`
    with no alias precisely because *"an alias would have let all 21 references
    keep assembling and silently compare the wrong thing."*

    Renaming the containers alone would not have been enough.  Seventeen sites
    reach the flags by explicit displacement and never name the field:

        TM    1(R1),PAGINVAL TRY TO CATCH CULPRIT              DMKPTR
        TM    3(R2),SEGINV   SEGMENT OK?                       DMKCFG
        N     R10,=AL4(X'FFFFFFFF'-SEGINV) CLEAR INVALID FLAG  DMKCFG

    The last two do arithmetic on the flag VALUE in a register, so only renaming
    the flag itself reaches them.

    What is renamed, and what deliberately is not:

      `SEGPAGE`  -> `SEGPTO`    the architected name, and its byte meanings move
      `SEGPLEN`  -> `SEGPTL`    bits 0-3 -> 28-31; the VALUE is unchanged, 15 for
                                a full table, because ESA/390's PTL counts in
                                units of 16 entries and S/370's counted pages
      `SEGINV`   -> `SEGINVAL`  X'01' (bit 31, inside PTL) -> X'20' (bit 26)
      `PAGCORE`  -> `PAGPFRA`   halfword -> FULLWORD, the architected name
      `PAGINVAL` -> `PAGINV`    X'08' at +1 -> X'04' at +2 (bit 21)

      `SEGENQ`   kept.  Its one live site names `SEGPTO`, so the rename reaches
                 it, and its bit position need not move: it is read only when the
                 pointer is zero -- that is, only with `I` set -- and with `I` set
                 the hardware does not interpret bit 25.
      `PAGREF`   kept, for the same reason: all four sites name `PAGPFRA` or
                 `PAGINV`.  Its value stays X'01' and it moves to `PAGPFRA+3`,
                 where it is SAFE: **bits 24-31 of an ESA/390 PTE are ignored by
                 the hardware**, so CP's private flag needs no new home.
      `PAGTSWP`, `PAGBMP`  kept.  They are derived EQUs, so changing 16 to 256
                 propagates correctly to every user -- and any `MVC` using them
                 as a length now exceeds 256 bytes and fails loudly by itself.

    `SEGMIG` is DELETED rather than converted.  It is `X'10'`, which is the
    ESA/390 **C (common segment)** bit, and `WHAT-31BIT-NEEDS.md` lists that
    collision as undesigned item 2.  Half of that item does not exist:
    **`SEGMIG` is defined here and referenced nowhere else in the tree** -- not in
    a module, not in a COPY, not in a MACRO.  Deleting it is the honest record of
    that, and if something ever needs it the absence will say so.
    """
    d = Deck(XA33)
    src = SRC + '/CORE.COPY'
    def one(seq, lines, inc=10):
        d.replace(seq, first=str(int(seq) + inc).zfill(8), inc=inc,
                  limit=next_seq(src, seq), lines=lines)

    one('00108000', Deck.comment(
        "ESA/390 SEGMENT TABLE ENTRY. BIT 0 MUST BE ZERO OR EVERY TRANSLATION "
        "TAKES A SPECIFICATION EXCEPTION -- WHICH IS WHAT PRG018 WAS. PTO IS "
        "BITS 1-25 WITH SIX ZEROS APPENDED, SO PAGE TABLES ARE 64-BYTE ALIGNED. "
        "I IS BIT 26, C IS BIT 27, PTL IS BITS 28-31. RENAMED FROM SEGPAGE WITH "
        "NO ALIAS SO EVERY SITE MUST BE VISITED. I-121.") + [
        "SEGPTO   DS    1F             PAGE TABLE ORIGIN, BITS 1-25",
    ])

    one('00111000', [
        "         ORG   SEGPTO+3       THE FLAG BYTE IS BYTE 3 NOW",
    ])

    one('00112000', Deck.comment(
        "BITS 24-27 ARE THE TWO LOW PTO BITS PLUS I AND C, SO PTL CANNOT LIVE "
        "AT BITS 0-3 ANY MORE. THE VALUE IS UNCHANGED -- 15 FOR A FULL TABLE -- "
        "BECAUSE ESA/390 COUNTS PTL IN UNITS OF 16 ENTRIES WHERE S/370 COUNTED "
        "PAGES, AND 256/16-1 IS ALSO 15.") + [
        "         DS    BL.4           BITS 24-27: PTO LOW, I, C",
        "SEGPTL   DS    BL.4       S*1 BITS 28-31: PAGE TABLE LEN",
    ])

    one('00114100', ["* BITS DEFINED IN SEGPTO+3"])

    one('00114200', Deck.comment(
        "THE ARCHITECTED SEGMENT-INVALID BIT IS 26, NOT 31. X'01' WAS INSIDE "
        "WHAT IS NOW PTL. RENAMED FROM SEGINV: 14 OF ITS 31 SITES REACH IT BY "
        "DISPLACEMENT OR BY ARITHMETIC ON THE VALUE AND NEVER NAME SEGPAGE, SO "
        "RENAMING THE CONTAINER ALONE WOULD HAVE MISSED THEM. THE DEFINITION "
        "ITSELF IS IN EQU COPY, NOT HERE: DMKCDB, DMKCDM AND DMKDRD NAME "
        "SEGINVAL AND DO NOT COPY CORE, WHICH COST SEVEN OF THE TWELVE "
        "DIAGNOSTICS IN THE 1 OCTOBER BUILD. I-143."))

    one('00114300', Deck.comment(
        "SEGMIG IS GONE. IT WAS X'10', WHICH IS THE ESA/390 COMMON-SEGMENT BIT, "
        "AND WHAT-31BIT-NEEDS LISTS THAT COLLISION AS UNDESIGNED ITEM 2. IT IS "
        "NOT A COLLISION: SEGMIG WAS DEFINED HERE AND REFERENCED NOWHERE ELSE "
        "IN THE TREE. DELETED RATHER THAN MOVED, SO THAT IF ANYTHING EVER WANTS "
        "IT THE ABSENCE SAYS SO.") + [
        "*                             (SEGMIG DELETED -- SEE ABOVE)",
    ])

    one('00114400', Deck.comment(
        "SEGENQ KEEPS BIT 25, WHICH IS THE LOWEST PTO BIT. THAT IS SAFE AND NOT "
        "AN OVERSIGHT: IT IS READ ONLY WHEN THE POINTER IS ZERO, SO ONLY WITH I "
        "SET, AND WITH I SET THE HARDWARE DOES NOT INTERPRET PTO AT ALL. PROVED "
        "BY EXECUTION: X'00000070' IS SEGMENT-INVALID, X'00000050' IS A VALID "
        "COMMON SEGMENT WITH PTO X'40'.") + [
        "SEGENQ   EQU   X'40'          ENQUEUED -- ONLY WITH I SET",
    ])

    one('00139000', Deck.comment(
        "ESA/390 PAGE TABLE ENTRY -- A FULLWORD, NOT A HALFWORD. PFRA IS BITS "
        "1-19, I IS BIT 21, P IS BIT 22, AND BITS 0, 20 AND 23 MUST BE ZERO. "
        "RENAMED FROM PAGCORE WITH NO ALIAS BECAUSE 13 LH AND 5 STH SITES WOULD "
        "OTHERWISE ASSEMBLE CLEAN AND READ THE WRONG TWO BYTES. I-121.") +
        Deck.comment(
        "PAGORIG HOLDS THE DMKFREE ADDRESS OF THIS BLOCK. IT IS NOT CALLED PAGFREE BECAUSE DMKPTR HAS HAD A LABEL OF THAT NAME SINCE 1979 -- PAGFREE EQU * ENTRY FROM WITHIN DMKPTRAN -- AND CORE.COPY IS COPIED BY 42 MODULES. TOOLS/SYMCHK.PY CHECKS THIS NOW. IT EXISTS BECAUSE THE "
        "PAGE TABLE MUST NOW BE 64-BYTE ALIGNED, SO DMKBLDRT ROUNDS THE BLOCK UP "
        "AND THE GAP BETWEEN WHAT DMKFREE RETURNED AND THE HEADER IS NO LONGER "
        "THE CONSTANT 16 THAT DMKBLDRL SUBTRACTS. STORING THE ADDRESS IS EXACT "
        "WHERE ARITHMETIC WOULD BE DERIVED, AND IT RETIRES "
        "N R1,=A(X'FFFFFE'), WHICH TRUNCATES A PAGE TABLE ADDRESS TO 24 BITS "
        "WHILE CLAIMING TO CLEAR A FLAG. I-122, I-130.") + Deck.comment(
        "IT CANNOT GO FIRST: STCK PAGSTMP STORES EIGHT BYTES AND NEEDS A "
        "DOUBLEWORD-ALIGNED OPERAND, SO PAGSTMP MUST STAY AT OFFSET 0. THE "
        "RESERVED FULLWORD KEEPS PAGPFRA ON A DOUBLEWORD AND PAGBMP AN EXACT "
        "MULTIPLE OF 8.") + [
        "PAGORIG  DS    1F             DMKFREE ADDRESS OF THE BLOCK",
        "         DS    1F             RESERVED -- KEEPS ALIGNMENT",
        "PAGPFRA  DS    1F             PAGE FRAME REAL ADDR, BITS 1-19",
    ])

    one('00141000', ["*        BITS DEFINED IN PAGPFRA+2"])

    one('00142000', Deck.comment(
        "PAGE INVALID IS BIT 21, SO X'04' IN BYTE 2. RENAMED FROM PAGINVAL: TWO "
        "OF ITS SITES REACH IT AS 1(R1) AND NEVER NAME THE FIELD. DEFINED IN "
        "EQU COPY WITH THE OTHER ARCHITECTURE CONSTANTS -- SEE I-143."))

    one('00143000', Deck.comment(
        "PAGREF KEEPS ITS NAME AND ITS VALUE AND MOVES TO PAGPFRA+3, WHICH IS "
        "SAFE: BITS 24-31 OF AN ESA/390 PTE ARE IGNORED BY THE HARDWARE, SO CP'S "
        "PRIVATE FLAG NEEDS NO NEW HOME. ALL FOUR SITES NAME PAGPFRA OR PAGINV, "
        "SO THEY ARE REACHED BY THOSE RENAMES.") + [
        "PAGREF   EQU   X'01'          REFERENCED -- AT PAGPFRA+3",
    ])

    d.replace('00143300', '00143400', first='00143310', inc=10,
              limit=next_seq(src, '00143400'),
              lines=Deck.comment(
        "A 1 MB SEGMENT HAS 256 PAGES, NOT 16, AND EACH ENTRY IS NOW A FULLWORD, "
        "SO A FULL PAGE TABLE IS 24+256*4 = 1048 BYTES INSTEAD OF 16+16*2 = 48. "
        "DERIVED, SO EVERY USER GETS THE NEW VALUE -- AND ANY MVC USING IT AS A "
        "LENGTH NOW EXCEEDS 256 BYTES AND FAILS LOUDLY BY ITSELF.") + [
        "PAGTSWP  EQU   (PAGPFRA-PAGSTMP+256*L'PAGPFRA) LENGTH OF A",
        "*                            FULL 256 ENTRY PAGE TABLE",
    ])

    d.replace('00143500', '00143700', first='00143510', inc=10,
              limit=next_seq(src, '00143700'),
              lines=Deck.comment(
        "THE SWAP TABLE IS ONE ENTRY PER PAGE TOO, SO IT GROWS 16 TO 256 WITH "
        "THE PAGE TABLE. SWPTABLE IS CP-PRIVATE, SO ONLY THE COUNT CHANGES. THE "
        "ENTRY SIZE BECOMES ITS OWN EQU BECAUSE THE ONE-LINE FORM IS 63 COLUMNS "
        "AND A CARD HOLDS 61 -- THE GENERATOR REFUSED IT RATHER THAN TRUNCATING "
        "IT INTO THE IDENTIFIER FIELD, WHICH IS WHAT R-04 IS FOR.") + Deck.comment(
        "THE SWAP TABLE HEADER IS 8 BYTES, NOT 12: SWPFLAG2 IS ORG'D OVER "
        "SWPPAG'S SLOT. READING THE FIELD LIST WITHOUT THE ORG GAVE 12 AND MADE "
        "PAGBMP 3108 INSTEAD OF 3112 -- NOT A MULTIPLE OF 8, WHICH THE "
        "TRUNCATING SRL R0,3 WOULD HAVE UNDER-ALLOCATED. I-127.") + Deck.comment("THE TRAILING 32 RATHER THAN 8 MAKES PAGBMP A MULTIPLE OF 64, NOT JUST OF 8. DMKVMA AND DMKATS PUT THE ATTACHED PROCESSOR'S PAGE TABLE AT PAGETABLE+PAGBMP, SO WITH 3112 THE SECOND TABLE WOULD NOT BE ON A 64-BYTE BOUNDARY AND AN ESA/390 PAGE TABLE ORIGIN MUST BE. 3136 IS 392 DOUBLEWORDS AND 49 TIMES 64. 24 BYTES A SEGMENT TO REMOVE THE PROBLEM RATHER THAN DOCUMENT IT.") + [
        "PAGSWPE  EQU   (SWPCODE-SWPFLAG+1) ONE SWAP ENTRY",
        "PAGBMP   EQU   (PAGTSWP+(SWPFLAG-SWPVM)+256*PAGSWPE+32)",
        "*                            LENGTH OF A CONTIGUOUS PAGE AND",
        "*                            SWAP TABLE",
    ] + Deck.comment(
        "THE MASKS BELOW EXIST BECAUSE OF THE ONE STRUCTURAL DIFFERENCE THAT "
        "GOVERNS THIS WHOLE CONVERSION. S/370 PACKS LENGTHS AND FLAGS INTO THE "
        "HIGH BYTE OF A POINTER, WHICH 24-BIT ADDRESS FORMATION IGNORES, SO A "
        "PACKED WORD IS USABLE AS AN ADDRESS WITH NOTHING TO STRIP. ESA/390 "
        "MOVES THEM TO THE LOW BITS -- STL 25-31, STE FLAGS 26-31, PTE FLAGS "
        "21-22 -- WHICH ADDRESS FORMATION NEVER IGNORES. SO EVERY PACKED "
        "POINTER NEEDS AN EXPLICIT MASK WHERE IT NEEDED NONE, AND AMODE 24 DOES "
        "NOT HELP. I-128. THE MASKS THEMSELVES ARE IN EQU COPY, WHICH 179 OF "
        "THE 192 MODULES COPY, BECAUSE THEY ARE ARCHITECTURE CONSTANTS AND NOT "
        "FIELDS OF THIS STRUCTURE -- PUTTING THEM HERE MADE THEM INVISIBLE TO "
        "EVERY MODULE THAT DOES NOT COPY CORE. I-143."))
    return d



# ---------------------------------------------------------------------------
# M2 step 2, part 1: the 24-bit strip sweep (I-126).  `LA Rx,0(,Ry)` clears
# bits 0-7 in AMODE 24 and only bit 0 in AMODE 31, so before CP's PSW can go
# AMODE 31 every site that uses it to drop a flag or length byte from a packed
# pointer has to say so with a mask that means the same thing in both modes:
#
#     LA Rx,0(,Rx)   ->  N  Rx,XRIGHT24          same size, sets the CC
#     LA Rx,0(,Ry)   ->  LR Rx,Ry / N Rx,XRIGHT24  +2 bytes
#
# XRIGHT24 is the PSA's X'00FFFFFF', addressable from base 0 in every module.
# This is a behaviour-preserving refactor while CP stays AMODE 24 -- which is
# how it is tested (i232) before the PSW flips (i233).  tools/strips.py is the
# inventory; it found 241 sites in 78 nucleus modules, one of them
# CC-sensitive and that one in DMKDDR, a utility.  Sites inside ranges that
# an earlier deck already replaced are skipped: those decks wrote explicit
# masks (SEGPTOM, PAGPFRM, ...) when they converted the field.  DMKLD00E is
# the loader, runs before CP in AMODE 24 and is left alone.
# Code that executes INSIDE the virtual machine is 24-bit guest code and keeps
# its LA strips: DMKLD00E (the loader) and DMKVMI, the IPL simulator CP copies
# into the guest's storage at X'20000' -- its N Rx,XRIGHT24 read the GUEST's
# page 0, not the PSA, got zero, and IPL 190 looped on an operation exception
# at virtual 6A (w104/w107, I-231).
STRIP_SKIP = {'DMKLD00E', 'DMKVMI'}

# I-233.  `ICM Rx,B'0111',FIELD+1` loads a 3-byte pointer and LEAVES BYTE 0 OF
# Rx AS IT WAS; AMODE 24 never looked at it.  In AMODE 31 a register that
# last held a packed word (count or flags in byte 0) then addresses storage
# above 16 MB: PRG005 in DMKPTR RSPGLOOP at AUTOLOG1's LOGOFF (i240, w109),
# `ICM R2,B'0111',PAGSHR+1` then `ICM R2,B'1111',SHRSEGCT-SHRTABLE(R2)`.
# Every ICM-3 in the nucleus whose register is not provably clean -- no
# SR/SLR/XR of it, no LA/LH/IC/SRL into it, within the previous eight
# instructions -- gets `SR Rx,Rx` in front: ICM sets the condition code the
# code then tests, so the SR changes nothing it reads.  The five it must not
# touch are listed: three where the register IS clean by a path the rule
# cannot see, and two (DMKCPS, DMKVDE) that build 'count || address' for
# DMKFRET on purpose with SLL 24 first.  tools/strips.py kind icm3 is the
# inventory (100 sites in nucleus modules; 59 get the SR).
ICM3_SKIP = {('DMKPER', '00628000'),   # R1 came from L R1,PERADDR, an address
             ('DMKRSE', '00508000'),   # R1 from SR + ICM two lines up
             ('DMKVER', '00571000'),   # R1 from SLR + ICM
             ('DMKCPS', '01358000'),   # SLL R3,24 then ICM: packed on purpose
             ('DMKVDE', '00813000')}   # same

def icm3cards():
    sys.path.insert(0, TOOLS)
    import strips, replchk
    nuc = set()
    for line in open('/home/claude/vmce/maintenance/files/194/CPLOAD.EXEC',
                     errors='replace'):
        for w in line.split():
            if w.startswith(('DMK', 'HDK')) and len(w) >= 6:
                nuc.add(w)
    clear = re.compile(r"^\S*\s+(SR|SLR|XR)\s+(R?\d+),(R?\d+)\b")
    skipops = re.compile(r"^\S*\s+(SPACE|EJECT|USING|DROP|AIF|ANOP)\b")
    def reg(x):
        return x if x.startswith('R') else 'R' + x
    out = {}
    for path in sorted(glob.glob(os.path.join(SRC, '*.ASSEMBLE'))):
        mod = os.path.basename(path).split('.')[0]
        if mod not in nuc or mod in STRIP_SKIP:
            continue
        sites = [r for r in strips.scan(path) if r['kind'] == 'icm3']
        if not sites:
            continue
        # ranges other decks of this module already replace or delete:
        # DMKPTR's VMSEG/SEGPAGE ICMs went with the DAT tables (XA0036DK),
        # and UPDATE stops on an anchor that is no longer there.
        taken = []
        for d in glob.glob(os.path.join(HERE, '%s.XA*DK' % mod)):
            if d.endswith(XA48):
                continue
            for op, frm, to, lines in replchk.deck_cards(d):
                if op in 'RD':
                    taken.append((int(frm), int(to)))
        sites = [r for r in sites
                 if not any(a <= int(r['seq']) <= b for a, b in taken)]
        L = [l.rstrip('\n') for l in open(path, errors='replace')]
        bynum = {l[72:80].strip(): i for i, l in enumerate(L)}
        for r in sites:
            if (mod, r['seq']) in ICM3_SKIP or r['seq'] not in bynum:
                continue
            i = bynum[r['seq']]
            t = L[i][:72]
            m = re.search(r"\bICM\s+(R?\d+),(7|B'0111'),(\S+)", t)
            if not m:
                continue
            rx = reg(m.group(1))
            safe = False
            for j in range(i - 1, max(i - 8, -1), -1):
                p = L[j][:72]
                if p.startswith('*') or not p.strip() or skipops.match(p):
                    continue
                mm = clear.match(p)
                if mm and reg(mm.group(2)) == rx and reg(mm.group(3)) == rx:
                    safe = True
                    break
                if re.match(r"^\S*\s+(L|LA|LH|LR|LM|IC|SLL|SRL|ICM)\s+%s\b" % rx, p) \
                        or re.match(r"^\S*\s+(L|LA|LH|LR)\s+%s," % rx, p) \
                        or re.match(r"^\S*\s+ICM\s+%s,(15|B'1111')," % rx, p):
                    safe = bool(re.match(r"^\S*\s+(LA|LH|IC|SRL)\s+%s" % rx, p))
                    break
                w = p.split()
                if len(w) > 1 and re.search(r"\b%s\b" % rx, w[1]):
                    break
            if safe:
                continue
            label = t.split()[0] if not t.startswith(' ') else ''
            body = t[len(label):].strip() if label else t.strip()
            parts = body.split(None, 2)
            icm = '         %-5s %s' % (parts[0], parts[1])
            if len(parts) > 2:
                icm = ('%-30s %s' % (icm, parts[2].strip()))[:61].rstrip()
            sr = ('%-30s CLEAN BYTE 0, I-233'
                  % ('%-8s SR    %s,%s' % (label, rx, rx)))
            out.setdefault(mod, []).append((r['seq'], [sr, icm]))
    return out

def stripdecks():
    sys.path.insert(0, TOOLS)
    import strips, replchk
    nuc = set()
    for line in open('/home/claude/vmce/maintenance/files/194/CPLOAD.EXEC',
                     errors='replace'):
        for w in line.split():
            if w.startswith(('DMK', 'HDK')) and len(w) >= 6:
                nuc.add(w)
    done = []
    for path in sorted(glob.glob(os.path.join(SRC, '*.ASSEMBLE'))):
        mod = os.path.basename(path).split('.')[0]
        if mod not in nuc or mod in STRIP_SKIP:
            continue
        sites = [r for r in strips.scan(path) if r['kind'].startswith('LA')]
        if not sites:
            continue
        # ranges other decks of this module already replace or delete
        taken = []
        for d in glob.glob(os.path.join(HERE, '%s.XA*DK' % mod)):
            if d.endswith(XA47):
                continue
            for op, frm, to, lines in replchk.deck_cards(d):
                if op in 'RD':
                    taken.append((int(frm), int(to)))
        cards = []
        for r in sites:
            s = int(r['seq'])
            if any(a <= s <= b for a, b in taken):
                continue
            if (mod, r['seq']) in SWEEP_EXCEPT:
                continue            # a guest address: G31MODS owns it
            # the record itself, for its label and comment
            rec = None
            for line in open(path, errors='replace'):
                if line[72:80].strip() == r['seq']:
                    rec = line[:72].rstrip()
                    break
            label = rec.split()[0] if rec and not rec.startswith(' ') else ''
            m = re.match(r'^\S*\s+LA\s+(R?\d+),0\((?:0?,)?(R?\d+)\)\s*(.*)$', rec)
            rx, ry, cmt = m.group(1), m.group(2), m.group(3).strip()
            rx = rx if rx.startswith('R') else 'R' + rx
            ry = ry if ry.startswith('R') else 'R' + ry
            cmt = re.sub(r'\s*(@V[A-Z0-9]+|HRC\d+DK|%V[A-Z0-9]+)\s*$', '', cmt)
            cmt = (cmt[:26] + ' I-126') if cmt else 'WAS LA: 24-BIT STRIP, I-126'
            if rx == ry:
                lines = ['%-8s N     %s,XRIGHT24 %s' % (label, rx, cmt)]
            else:
                lines = ['%-8s LR    %s,%s' % (label, rx, ry),
                         '         N     %s,XRIGHT24 %s' % (rx, cmt)]
            lines = [l.rstrip()[:61] for l in lines]
            cards.append((r['seq'], lines))
        out = os.path.join(HERE, '%s.%s' % (mod, XA47))
        if not cards:
            # every site excepted or taken: a deck left from an earlier
            # run would anchor on cards another deck now owns (ANCHOR-GONE)
            if os.path.exists(out):
                os.remove(out)
                aux(os.path.join(HERE, '%s.AUXLCL' % mod), [])
            continue
        cards.sort(key=lambda c: int(c[0]))
        dk = datdeck(mod, cards, ident=XA47)
        out = os.path.join(HERE, '%s.%s' % (mod, XA47))
        n = dk.write(out)
        aux(os.path.join(HERE, '%s.AUXLCL' % mod),
            [(XA47, 'AMODE 31 SWEEP: LA STRIPS BECOME N XRIGHT24 (I-126)')])
        print('%-8s %-9s %3d cards  %s' % (mod, XA47, n,
              'OK' if not verify(out) else 'BAD'))
        done.append((mod, len(cards)))
    print('strip sweep: %d sites in %d modules' % (sum(n for _, n in done), len(done)))
    return done


def main():
    d = psa()
    n = d.write(os.path.join(HERE, 'PSA.%s' % XA1))
    aux(os.path.join(HERE, 'PSA.AUXLCL'),
        [(XA1, 'ESA/390 LOWCORE: SUBSYSTEM ID AND INTERRUPTION PARAMETER')])

    r = rbloks()
    r.write(os.path.join(HERE, 'RBLOKS.%s' % XA2))
    aux(os.path.join(HERE, 'RBLOKS.AUXLCL'),
        [(XA2, 'RDEVSSID: ESA/390 SUBSYSTEM IDENTIFICATION WORD')])

    # VMFMAC's list EXEC: one line per member, format copied from 194/DMKMAC.EXEC
    i = ioblok()
    i.write(os.path.join(HERE, 'IOBLOKS.%s' % XA3))
    aux(os.path.join(HERE, 'IOBLOKS.AUXLCL'),
        [(XA3, 'IOBORB AND IOBIRB: PER-OPERATION ORB AND IRB')])

    o = dmkios()
    o.write(os.path.join(HERE, 'DMKIOS.%s' % XA4))
    aux(os.path.join(HERE, 'DMKIOS.AUXLCL'),
        [(XA4, 'SSCH PATH: ORB, SUBSYSTEM ID, AND THE CSW SHIM')])

    dsp, prv = guest_psa()
    dsp.write(os.path.join(HERE, 'DMKDSP.%s' % XA6))
    aux(os.path.join(HERE, 'DMKDSP.AUXLCL'),
        [(XA6, 'GUEST LOWCORE: G370TIO FOR THE S/370 INTERRUPT CODE')])
    prv.write(os.path.join(HERE, 'DMKPRV.%s' % XA7))
    aux(os.path.join(HERE, 'DMKPRV.AUXLCL'),
        [(XA7, 'GUEST LOWCORE: S370CHID FOR STIDC SIMULATION')])

    eig = dmkeig()
    eig.write(os.path.join(HERE, 'DMKEIG.%s' % XA8))
    aux(os.path.join(HERE, 'DMKEIG.AUXLCL'),
        [(XA8, 'CHANNEL LOGOUT: STUB THE ANALYSIS TO TERMINATION')])

    iog = dmkiog()
    iog.write(os.path.join(HERE, 'DMKIOG.%s' % XA9))
    aux(os.path.join(HERE, 'DMKIOG.AUXLCL'),
        [(XA9, 'NO STIDC SURVEY, AND THE S/370 LOGOUT FIELDS RENAMED')])

    vmi = dmkvmi()
    vmi.write(os.path.join(HERE, 'DMKVMI.%s' % XA11))
    aux(os.path.join(HERE, 'DMKVMI.AUXLCL'),
        [(XA11, 'GUEST IPL DEVICE STAYS AT X\'BA\' (I-241)')])

    iot = dmkiot()
    iot.write(os.path.join(HERE, 'DMKIOT.%s' % XA12))
    aux(os.path.join(HERE, 'DMKIOT.AUXLCL'),
        [(XA12, 'INTERRUPT ENTRY READS THE INTERRUPTION PARAMETER')])

    cpi = dmkcpi()
    cpi.write(os.path.join(HERE, 'DMKCPI.%s' % XA13))
    # A SECOND deck on DMKCPI rather than cards added to XA0013DK: UPDATE scans
    # forward once, so a card must follow every card with a lower anchor, and
    # XA0013DK's anchors already run to 03506100 while the DAT sites are at
    # 01495000.  Interleaving them into one generator would put the reasoning for
    # two unrelated changes in one place.  Verified not to overlap: XA0013DK
    # touches nothing between 01490000 and 01560000.
    cpd = dmkcpidat()
    n = cpd.write(os.path.join(HERE, 'DMKCPI.%s' % XA35))
    aux(os.path.join(HERE, 'DMKCPI.AUXLCL'),
        [(XA35, 'ESA/390 DAT TABLES FOR CP ITSELF, AND THE CORTABLE WALK'),
         (XA13, 'CR6 SUBCLASS MASK AND SUBCHANNEL DISCOVERY')])
    print('%-8s %-9s %3d cards  %s' % ('DMKCPI', XA35, n,
          'OK' if not verify(os.path.join(HERE, 'DMKCPI.%s' % XA35)) else 'BAD'))

    sys_ = dmksys()
    sys_.write(os.path.join(HERE, 'DMKSYS.%s' % XA14))
    aux(os.path.join(HERE, 'DMKSYS.AUXLCL'),
        [(XA14, 'RUN UNIPROCESSOR: AP=NO, SO NO CONCS AT IPL')])

    ckp = dmkckp()
    ckp.write(os.path.join(HERE, 'DMKCKP.%s' % XA15))
    aux(os.path.join(HERE, 'DMKCKP.AUXLCL'),
        [(XA15, 'CHANNEL SUBSYSTEM VIA XAIO, AND THE INTTIO SITES')])

    dmp = dmkdmp()
    dmp.write(os.path.join(HERE, 'DMKDMP.%s' % XA16))
    aux(os.path.join(HERE, 'DMKDMP.AUXLCL'),
        [(XA16, 'CHANNEL SUBSYSTEM VIA XAIO, AND THE INTTIO SITES')])

    # DMKSAV IS CONVERTED AGAIN, and the reasoning that reverted it was half
    # wrong.  I-83 said neither DMKLD00E nor DMKSAV is on the disk-IPL path.
    # The loader half is right and was tested; the DMKSAV half was inferred
    # and is false -- DMKCKP 00354000 is `GOTO DMKSAVRS  START SYSTEM RE-IPL`,
    # so the saved nucleus hands control to DMKSAV's restart entry.  DMKSAV
    # therefore runs on BOTH paths: the build executes it on a S/370 machine
    # (that is what writes SYSRES) and the disk IPL on an ESA/390 one.  I-96.
    #
    # Static opcodes cannot satisfy both, so XAIO now probes the architecture
    # once and takes the native path either way.  That makes one object deck
    # correct on both machines and is why this deck can come back.
    sav = dmksav()
    sav.write(os.path.join(HERE, 'DMKSAV.%s' % XA17))
    aux(os.path.join(HERE, 'DMKSAV.AUXLCL'),
        [(XA17, 'SUBCHANNEL I/O, ARCHITECTURE PROBED AT RUNTIME')])

    cch = dmkcch()
    cch.write(os.path.join(HERE, 'DMKCCH.%s' % XA10))
    aux(os.path.join(HERE, 'DMKCCH.AUXLCL'),
        [(XA10, 'CHANNEL CHECK: NO LCL ANALYSIS, TERMINATE INSTEAD')])

    psam = dmkpsa()
    psam.write(os.path.join(HERE, 'DMKPSA.%s' % XA22))
    aux(os.path.join(HERE, 'DMKPSA.AUXLCL'),
        [(XA22, 'HSCH AND TSCH IN LOWCORE, WITH A WRITE-ONLY IRB')])

    opr = dmkopr()
    opr.write(os.path.join(HERE, 'DMKOPR.%s' % XA23))
    aux(os.path.join(HERE, 'DMKOPR.AUXLCL'),
        [(XA23, 'OPERATOR CONSOLE I/O: THE MODULE THAT PRINTS THE MESSAGES')])

    cns = dmkcns()
    cns.write(os.path.join(HERE, 'DMKCNS.%s' % XA21))
    aux(os.path.join(HERE, 'DMKCNS.AUXLCL'),
        [(XA21, 'CONSOLE I/O VIA XAIOB, INCLUDING THE ONLY CLRIO')])

    e = dmkfre()
    e.write(os.path.join(HERE, 'DMKFRE.%s' % XA20))
    aux(os.path.join(HERE, 'DMKFRE.AUXLCL'),
        [(XA20, 'NO CHANNEL MASK: CR2 IS THE DUCT ORIGIN ON ESA/390')])

    f = dmkcfo()
    f.write(os.path.join(HERE, 'DMKCFO.%s' % XA19))
    aux(os.path.join(HERE, 'DMKCFO.AUXLCL'),
        [(XA19, 'CPCREG6 IS THE IO SUBCLASS MASK, NOT AN ASSIST WORD')])

    j = dmkvsj()
    j.write(os.path.join(HERE, 'DMKVSJ.%s' % XA18))
    aux(os.path.join(HERE, 'DMKVSJ.AUXLCL'),
        [(XA18, 'CLCH IS ALWAYS SIMULATED: NO REAL CLRCH ON ESA/390')])

    with open(os.path.join(HERE, 'DMKLCL.EXEC'), 'w') as f:
        # XAOPS must be here, not in a separate XALIB: DMKLCL.CNTRL's MACS
        # record is  DMKLCL DMKHRC DMKMAC DMSLCL CMSHRC CMSLIB OSMACRO  and
        # VMFASM globals exactly that list, so a macro library CP's control
        # file does not name is invisible however well it was built.  The
        # first DMKIOS assembly failed on precisely this: IFO078 UNDEFINED
        # OP CODE for SSCH and TSCH, with every other new symbol resolved.
        # RDEVICE joins the list for I-116: it is CP's own macro, and it has
        # to be in DMKLCL for DMKRIO to assemble against the updated copy
        # rather than the shipped one -- the same reason PSA is here.
        #
        # EQU joins it for I-149, and the failure is worth stating because the
        # file is easy to read as a MACLIB member list and is not one: it is
        # the list of members whose AUX DECKS VMFASM APPLIES.  `EQU.XA0037DK`
        # and `EQU.AUXLCL` were both staged onto the A-disk and verified read,
        # and the deck was still never applied -- the log shows
        # `APPLYING 'CORE XA0033DK A1'` and nothing for EQU -- because CORE is
        # named here and EQU was not.  The nine architecture constants had just
        # been MOVED out of CORE COPY into EQU COPY (I-143), so CORE's deck
        # removed them and EQU's deck never added them: all nine came back
        # `IFO188 UNDEFINED SYMBOL` in five modules, including DMKATS and
        # DMKBLD, which had assembled clean the previous build.  A move is two
        # halves and only one of them was wired up.
        for name, typ in (('PSA', 'MACRO'), ('RBLOKS', 'COPY'),
                          ('IOBLOKS', 'COPY'), ('XABLOKS', 'COPY'),
                          ('XAOPS', 'MACRO'), ('XAIO', 'MACRO'),
                          ('XAIOB', 'MACRO'), ('RDEVICE', 'MACRO'),
                          ('CORE', 'COPY'), ('EQU', 'COPY'),
                          ('TRANS', 'MACRO')):
            f.write((' &1 &2 %-8s %s' % (name, typ)).ljust(80) + '\n')

    ok = True
    for name in ('PSA.%s' % XA1, 'PSA.AUXLCL', 'RBLOKS.%s' % XA2,
                 'RBLOKS.AUXLCL', 'IOBLOKS.%s' % XA3, 'IOBLOKS.AUXLCL',
                 'DMKIOS.%s' % XA4, 'DMKIOS.AUXLCL',
                 'DMKDSP.%s' % XA6, 'DMKDSP.AUXLCL',
                 'DMKPRV.%s' % XA7, 'DMKPRV.AUXLCL',
                 'DMKEIG.%s' % XA8, 'DMKEIG.AUXLCL',
                 'DMKIOG.%s' % XA9, 'DMKIOG.AUXLCL',
                 'DMKCCH.%s' % XA10, 'DMKCCH.AUXLCL',
                 'DMKVMI.%s' % XA11, 'DMKVMI.AUXLCL',
                 'DMKIOT.%s' % XA12, 'DMKIOT.AUXLCL',
                 'DMKCPI.%s' % XA13, 'DMKCPI.AUXLCL',
                 'DMKSYS.%s' % XA14, 'DMKSYS.AUXLCL',
                 'DMKCKP.%s' % XA15, 'DMKCKP.AUXLCL',
                 'DMKDMP.%s' % XA16, 'DMKDMP.AUXLCL',
                 'DMKSAV.%s' % XA17, 'DMKSAV.AUXLCL',
                 'DMKVSJ.%s' % XA18, 'DMKVSJ.AUXLCL',
                 'DMKCFO.%s' % XA19, 'DMKCFO.AUXLCL',
                 'DMKFRE.%s' % XA20, 'DMKFRE.AUXLCL',
                 'DMKCNS.%s' % XA21, 'DMKCNS.AUXLCL',
                 'DMKPSA.%s' % XA22, 'DMKPSA.AUXLCL', 'DMKLCL.EXEC'):
        bad = verify(os.path.join(HERE, name))
        print('%-16s %3d cards  %s'
              % (name, sum(1 for _ in open(os.path.join(HERE, name))),
                 'OK' if not bad else 'BAD ' + repr(bad[:3])))
        ok = ok and not bad
    for m in sorted(DATMODS):
        dk = datdeck(m, DATMODS[m])
        path = os.path.join(HERE, '%s.%s' % (m, XA36))
        n = dk.write(path)
        aux(os.path.join(HERE, '%s.AUXLCL' % m),
            [(XA36, 'ESA/390 DAT TABLES: RENAMES, MASKS AND ADDRESS SPLITS')])
        print('%-8s %-9s %3d cards  %s' % (m, XA36, n,
              'OK' if not verify(path) else 'BAD'))

    for m in sorted(NAMEMODS):
        dk = datdeck(m, NAMEMODS[m], ident=XA39)
        path = os.path.join(HERE, '%s.%s' % (m, XA39))
        n = dk.write(path)
        aux(os.path.join(HERE, '%s.AUXLCL' % m),
            [(XA39, 'THE NAME IS VM/370+, NOT VM/380')])
        print('%-8s %-9s %3d cards  %s' % (m, XA39, n,
              'OK' if not verify(path) else 'BAD'))

    # Bisection control.  I-192's change set put 48 storage-key sites behind one
    # measurement and the result was a regression, so the way back in is one
    # group at a time.  KEYMODS_ONLY names the modules whose key deck is
    # emitted; everything else keeps its AUXLCL line removed, which is what
    # actually stops a deck being applied -- the file on disk is harmless if
    # nothing lists it.  Empty or unset means all of them, which is the normal
    # state once the culprit is found.
    only = os.environ.get('KEYMODS_ONLY', '').replace(',', ' ').split()
    for m in sorted(KEYMODS):
        if only and m not in only:
            auxdrop(os.path.join(HERE, '%s.AUXLCL' % m), XA38)
            print('%-8s %-9s  --  held out by KEYMODS_ONLY' % (m, XA38))
            continue
        dk = datdeck(m, KEYMODS[m], ident=XA38)
        path = os.path.join(HERE, '%s.%s' % (m, XA38))
        n = dk.write(path)
        aux(os.path.join(HERE, '%s.AUXLCL' % m),
            [(XA38, 'ESA/390 STORAGE KEYS AT 4 KB: THE 2 KB PAIRS COLLAPSE')])
        print('%-8s %-9s %3d cards  %s' % (m, XA38, n,
              'OK' if not verify(path) else 'BAD'))

    for m in sorted(CHANMODS):
        dk = datdeck(m, CHANMODS[m], ident=XA40)
        path = os.path.join(HERE, '%s.%s' % (m, XA40))
        n = dk.write(path)
        aux(os.path.join(HERE, '%s.AUXLCL' % m),
            [(XA40, 'NO TCH: A CHANNEL SUBSYSTEM HAS NO CHANNEL TO TEST')])
        print('%-8s %-9s %3d cards  %s' % (m, XA40, n,
              'OK' if not verify(path) else 'BAD'))

    for m in sorted(GUESTMODS):
        dk = datdeck(m, GUESTMODS[m], ident=XA41)
        path = os.path.join(HERE, '%s.%s' % (m, XA41))
        n = dk.write(path)
        aux(os.path.join(HERE, '%s.AUXLCL' % m),
            [(XA41, 'S/370 OPCODES ESA/390 DROPPED: SIMULATE AS PRIV OPS')])
        print('%-8s %-9s %3d cards  %s' % (m, XA41, n,
              'OK' if not verify(path) else 'BAD'))

    for m in sorted(STORMODS):
        dk = datdeck(m, STORMODS[m], ident=XA42)
        path = os.path.join(HERE, '%s.%s' % (m, XA42))
        n = dk.write(path)
        aux(os.path.join(HERE, '%s.AUXLCL' % m),
            [(XA42, 'VIRTUAL STORAGE ABOVE 16 MB: THE 256 MB CEILING')])
        print('%-8s %-9s %3d cards  %s' % (m, XA42, n,
              'OK' if not verify(path) else 'BAD'))

    for m in sorted(CONSMODS):
        dk = datdeck(m, CONSMODS[m], ident=XA44)
        path = os.path.join(HERE, '%s.%s' % (m, XA44))
        n = dk.write(path)
        aux(os.path.join(HERE, '%s.AUXLCL' % m),
            [(XA44, 'DISPLAY AND STORE: EIGHT-DIGIT HEXLOC, ABOVE 16 MB')])
        print('%-8s %-9s %3d cards  %s' % (m, XA44, n,
              'OK' if not verify(path) else 'BAD'))

    bld = dmkbld()
    n = bld.write(os.path.join(HERE, 'DMKBLD.%s' % XA34))
    aux(os.path.join(HERE, 'DMKBLD.AUXLCL'),
        [(XA34, 'BUILD ESA/390 SEGMENT AND PAGE TABLES, AND ALIGN THEM')])
    print('%-8s %-9s %3d cards  %s' % ('DMKBLD', XA34, n,
          'OK' if not verify(os.path.join(HERE, 'DMKBLD.%s' % XA34)) else 'BAD'))

    # SHRMODS last: XA0045DK must sit ABOVE XA0034DK in DMKBLD.AUXLCL
    # (applied after it), because it anchors on a card XA0034DK renumbered.
    for m in sorted(AMODEMODS):
        dk = datdeck(m, AMODEMODS[m], ident=XA46)
        path = os.path.join(HERE, '%s.%s' % (m, XA46))
        n = dk.write(path)
        aux(os.path.join(HERE, '%s.AUXLCL' % m),
            [(XA46, 'LRA IN AMODE 31: VIRTUAL STORAGE ABOVE 16 MB')])
        print('%-8s %-9s %3d cards  %s' % (m, XA46, n,
              'OK' if not verify(path) else 'BAD'))

    for m in sorted(G31MODS):
        dk = datdeck(m, G31MODS[m], ident=XA49)
        path = os.path.join(HERE, '%s.%s' % (m, XA49))
        n = dk.write(path)
        aux(os.path.join(HERE, '%s.AUXLCL' % m),
            [(XA49, '31-BIT GUESTS: PSW BIT 32 ADMITTED, ADDRESSES BY MODE')])
        print('%-8s %-9s %3d cards  %s' % (m, XA49, n,
              'OK' if not verify(path) else 'BAD'))

    for m in sorted(SHRMODS):
        dk = datdeck(m, SHRMODS[m], ident=XA45)
        path = os.path.join(HERE, '%s.%s' % (m, XA45))
        n = dk.write(path)
        aux(os.path.join(HERE, '%s.AUXLCL' % m),
            [(XA45, 'NAMED SYSTEMS SHARED BY FRAME: MODEL TABLES, COPIES')])
        print('%-8s %-9s %3d cards  %s' % (m, XA45, n,
              'OK' if not verify(path) else 'BAD'))

    for m in sorted(ECMODS):
        dk = datdeck(m, ECMODS[m], ident=XA51)
        path = os.path.join(HERE, '%s.%s' % (m, XA51))
        n = dk.write(path)
        aux(os.path.join(HERE, '%s.AUXLCL' % m),
            [(XA51, 'CMS IN EC MODE: PSWS, INTERRUPT CODES, MASKS (M5B)')])
        print('%-8s %-9s %3d cards  %s' % (m, XA51, n,
              'OK' if not verify(path) else 'BAD'))

    dk = m4bcpi()
    path = os.path.join(HERE, 'DMKCPI.%s' % XA53)
    n = dk.write(path)
    aux(os.path.join(HERE, 'DMKCPI.AUXLCL'),
        [(XA53, 'M4B: REAL STORAGE ABOVE 16 MB, CORTABLE BUILT AT IPL')])
    print('%-8s %-9s %3d cards  %s' % ('DMKCPI', XA53, n,
          'OK' if not verify(path) else 'BAD'))

    for m, dk in sorted(m4bslots().items()):
        path = os.path.join(HERE, '%s.%s' % (m, XA53))
        n = dk.write(path)
        aux(os.path.join(HERE, '%s.AUXLCL' % m),
            [(XA53, 'M4B: STORAGE ABOVE 16 MB AS THE PAGING STORE')])
        print('%-8s %-9s %3d cards  %s' % (m, XA53, n,
              'OK' if not verify(path) else 'BAD'))

    for m in sorted(TMRMODS):
        dk = datdeck(m, TMRMODS[m], ident=XA52)
        path = os.path.join(HERE, '%s.%s' % (m, XA52))
        n = dk.write(path)
        aux(os.path.join(HERE, '%s.AUXLCL' % m),
            [(XA52, 'INTERVAL TIMER EMULATED FROM THE TOD CLOCK (I-250)')])
        print('%-8s %-9s %3d cards  %s' % (m, XA52, n,
              'OK' if not verify(path) else 'BAD'))

    for m in sorted(CORSWMODS):
        dk = datdeck(m, CORSWMODS[m], ident=XA50)
        path = os.path.join(HERE, '%s.%s' % (m, XA50))
        n = dk.write(path)
        aux(os.path.join(HERE, '%s.AUXLCL' % m),
            [(XA50, 'CORSWPNT LOADED WHOLE: BYTE 0 IS CORFLAG (I-236)')])
        print('%-8s %-9s %3d cards  %s' % (m, XA50, n,
              'OK' if not verify(path) else 'BAD'))

    # I-233: ICM Rx,7 into a register whose byte 0 is not known clean.
    for m, cards in icm3cards().items():
        PSWMODS.setdefault(m, [])
        have = {c[0] for c in PSWMODS[m]}
        PSWMODS[m] = sorted(PSWMODS[m] + [c for c in cards if c[0] not in have],
                            key=lambda c: int(c[0]))
    for m in sorted(PSWMODS):
        dk = datdeck(m, PSWMODS[m], ident=XA48)
        path = os.path.join(HERE, '%s.%s' % (m, XA48))
        n = dk.write(path)
        aux(os.path.join(HERE, '%s.AUXLCL' % m),
            [(XA48, 'CP AT AMODE 31: THE NEW PSWS CARRY BIT 32 (I-224)')])
        print('%-8s %-9s %3d cards  %s' % (m, XA48, n,
              'OK' if not verify(path) else 'BAD'))

    # The strip sweep LAST of the module decks: it skips every record an
    # earlier deck replaces, so those decks must exist when it runs, and
    # aux() sorts XA0047DK highest so VMFASM applies it after them.
    stripdecks()


    eq = equcopy()
    n = eq.write(os.path.join(HERE, 'EQU.%s' % XA37))
    aux(os.path.join(HERE, 'EQU.AUXLCL'),
        [(XA37, 'ESA/390 DAT CONSTANTS: STD, STE AND PTE MASKS AND FLAGS')])
    print('%-8s %-9s %3d cards  %s' % ('EQU', XA37, n,
          'OK' if not verify(os.path.join(HERE, 'EQU.%s' % XA37)) else 'BAD'))

    cc = corecopy()
    n = cc.write(os.path.join(HERE, 'CORE.%s' % XA33))
    aux(os.path.join(HERE, 'CORE.AUXLCL'),
        [(XA33, 'ESA/390 DAT TABLES: STE AND PTE, RENAMED WITH NO ALIAS')])
    print('%-8s %-9s %3d cards  %s' % ('CORE', XA33, n,
          'OK' if not verify(os.path.join(HERE, 'CORE.%s' % XA33)) else 'BAD'))

    r = rdevice()
    n = r.write(os.path.join(HERE, 'RDEVICE.%s' % XA32))
    aux(os.path.join(HERE, 'RDEVICE.AUXLCL'),
        [(XA32, 'RDEVSSID: MATCH THE RDEVBLOK DSECT THAT XA0002DK GREW')])
    print('%-8s %-9s %3d cards  %s' % ('RDEVICE', XA32, n,
          'OK' if not verify(os.path.join(HERE, 'RDEVICE.%s' % XA32)) else 'BAD'))

    # I-114.  Written after the per-module sections above, so the two modules
    # that already have an AUXLCL get BOTH decks listed rather than having the
    # ECPS deck silently replace the one that is already there.  An AUXLCL lists
    # decks newest first.
    ECPSDESC = 'ECPS:VM ASSISTS NO-OPPED: ESA/390 HAS NONE'
    PRIOR = {'DMKDSP': [(XA6, 'GUEST LOWCORE: G370TIO FOR THE S/370 '
                              'INTERRUPT CODE')],
             'DMKFRE': [(XA20, 'NO CHANNEL MASK: CR2 IS THE DUCT ORIGIN ON '
                               'ESA/390')]}
    for m in sorted(ECPS):
        dk = ecps(m)
        path = os.path.join(HERE, '%s.%s' % (m, dk.ident))
        n = dk.write(path)
        aux(os.path.join(HERE, '%s.AUXLCL' % m),
            [(dk.ident, ECPSDESC)] + PRIOR.get(m, []))
        print('%-8s %-9s %3d cards  %s'
              % (m, dk.ident, n, 'OK' if not verify(path) else 'BAD'))

    # Every deck must be LISTED in its module's AUXLCL or VMFASM never applies
    # it.  Asserted here rather than trusted, because two generators writing the
    # same AUXLCL used to mean whichever ran last won.  I-138.
    miss = auxcheck(HERE)
    if miss:
        print()
        for base, why in miss:
            print('### %s: %s' % (base, why))
        ok = False
    else:
        print('\n%d decks, every one listed in its AUXLCL' % len(
            [f for f in os.listdir(HERE) if '.XA' in f and f.endswith('DK')]))

    print('%d cards in the PSA deck' % n)
    return 0 if ok else 1


if __name__ == '__main__':
    sys.exit(main())
