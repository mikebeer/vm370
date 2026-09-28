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
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'tools'))
from mkdeck import Deck, aux, verify, next_seq    # noqa: E402

# The resolved tree the anchors are measured against.  R-23.
SRC = '/home/claude/vmce/source/cp'

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
        "         ST    R2,IOBOCCW     CCW ADDRESS FOR THIS OPERATION",
    ])

    # 2. SIO -> SSCH.  The operand meaning inverts: SIO takes the device
    #    address in R1 and ignores its operand; SSCH takes the subsystem id
    #    in R1 and the ORB as its operand.  LH R1,IOBRADD upstream is left
    #    alone because IOSQTIO still needs the device address in R1.
    d.replace('01206000', first='01206100', inc=10, limit='01207000',
              lines=Deck.comment(
        "SIO TOOK THE DEVICE ADDRESS IN R1 AND IGNORED ITS OPERAND. SSCH "
        "TAKES THE SUBSYSTEM ID IN R1 AND THE ORB AS ITS OPERAND -- THE TWO "
        "SWAP ROLES. THE LH R1,IOBRADD UPSTREAM IS LEFT ALONE BECAUSE "
        "IOSQTIO STILL WANTS THE DEVICE ADDRESS THERE.") + [
        "         L     R1,RDEVSSID    X'0001' || SUBCHANNEL NUMBER",
        "         SSCH  IOBORB         START SUBCHANNEL",
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

    d.insert('02651100', first='02651110', inc=10, limit='02652000',
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
        "         HSCH  0              HALT SUBCHANNEL",
        "         BR    R14",
        "         SPACE 1",
        "IOSXSIO  DS    0H             SSCH FOR THE SENSE PATH",
        "         MVC   IOBORB,ORBTMPL BUILD THE ORB",
        "         MVC   IOBOCCW,CAW    CCW ADDRESS THE CALLER SET",
        "         L     R1,RDEVSSID    X'0001' || SUBCHANNEL NUMBER",
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
        "SYSIPLDV IS CP'S OWN FIELD FOR THIS AND ALWAYS WAS -- SEE DMKCPI "
        "00484000. WRITING IT HERE REPLACES A COPY INTO THE ARCHITECTED I/O "
        "INTERRUPTION CODE, WHICH ON ESA/390 IS THE SUBSYSTEM ID WORD AND MUST "
        "NOT HOLD A DEVICE ADDRESS. NO SEMANTIC CHANGE. I-47.") + [
        "         STH   R13,SYSIPLDV   SET IPL DEVICE ADDRESS",
    ])
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
        ('00288000', '00288100', 100, '00289000',
         "         LH    R1,IOINTPRM+2  INTERRUPTING UNIT'S ADDRESS"),
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

    # SCHIBLOK, PMCW* and the subchannel EQUs live in XABLOKS, which until now
    # was copied only into DMKIOS.  Added beside DMKCPI's own COPY list rather
    # than at the point of use, which is where CP keeps its DSECTs.
    d.insert('03506100', first='03506110', inc=10,
             limit=next_seq(SRC + '/DMKCPI.ASSEMBLE', '03506100'),
             lines=["         COPY  XABLOKS"])
    return d


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

    # --- 00208000: the IPL device address DMKVMI now leaves in SYSIPLDV.
    one('00208000', Deck.comment(
        "SYSIPLDV IS WHERE DMKVMI PUTS IT NOW -- XA0011DK -- AND WHERE DMKCPI "
        "PUTS IT AT 00484000. I-47.") + [
        "         LH    R0,SYSIPLDV         GET SYS IPL ADDRESS",
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

    # The work area goes AFTER CLR1SIZE, and that placement is the whole point.
    # Putting XAIOWORK inside CLR1 was the first attempt and CE rejected it with
    # IFO224 LENGTH ERROR: 250-odd bytes took CLR1SIZE past the 256-byte limit
    # of the XC that clears it.  The length error was the lucky part -- the real
    # hazard is that CLR1 is *zeroed at startup*, and XAIOWORK contains the
    # executable lookup subroutine, so it would have been erased at runtime with
    # no diagnostic at all.  Here it is outside CLR1 and ahead of ALLOCBUF, so
    # outside the ACBUFF clear as well.  I-55.
    d.insert('01674000', first='01674100', inc=100,
             limit=nxt('01674000'),
             lines=Deck.comment(
        "OUTSIDE EVERY CLEARED REGION ON PURPOSE: CLR1 ENDS ON THE LINE ABOVE "
        "AND ALLOCBUF BEGINS BELOW, AND BOTH ARE ZEROED AT RUNTIME. XAIOWORK "
        "HOLDS EXECUTABLE CODE. I-55.") + [
        "         XAIOWORK             XAIO WORK AREAS AND LOOKUP",
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

    # --- 00149100 and 00150000.  The label is literally SIO.
    d.replace('00149100', '00150000', first='00149200', inc=100,
              limit=nxt('00150000'), lines=Deck.comment(
        "THE LABEL HERE IS SIO, WHICH IS ALSO A MNEMONIC -- THAT HAS ALWAYS "
        "BEEN TRUE IN THIS MODULE AND STILL ASSEMBLES. R-26: *-4 NAMES IT.") + [
        "SIO      XASIO R10",
        "         BC    7,SIO",
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
        [(XA11, 'IPL DEVICE ADDRESS GOES IN SYSIPLDV, NOT LOWCORE')])

    iot = dmkiot()
    iot.write(os.path.join(HERE, 'DMKIOT.%s' % XA12))
    aux(os.path.join(HERE, 'DMKIOT.AUXLCL'),
        [(XA12, 'INTERRUPT ENTRY READS THE INTERRUPTION PARAMETER')])

    cpi = dmkcpi()
    cpi.write(os.path.join(HERE, 'DMKCPI.%s' % XA13))
    aux(os.path.join(HERE, 'DMKCPI.AUXLCL'),
        [(XA13, 'CR6 SUBCLASS MASK AND SUBCHANNEL DISCOVERY')])

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

    sav = dmksav()
    sav.write(os.path.join(HERE, 'DMKSAV.%s' % XA17))
    aux(os.path.join(HERE, 'DMKSAV.AUXLCL'),
        [(XA17, 'CHANNEL SUBSYSTEM VIA XAIO')])

    cch = dmkcch()
    cch.write(os.path.join(HERE, 'DMKCCH.%s' % XA10))
    aux(os.path.join(HERE, 'DMKCCH.AUXLCL'),
        [(XA10, 'CHANNEL CHECK: NO LCL ANALYSIS, TERMINATE INSTEAD')])

    psam = dmkpsa()
    psam.write(os.path.join(HERE, 'DMKPSA.%s' % XA22))
    aux(os.path.join(HERE, 'DMKPSA.AUXLCL'),
        [(XA22, 'HSCH AND TSCH IN LOWCORE, WITH A WRITE-ONLY IRB')])

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
        for name, typ in (('PSA', 'MACRO'), ('RBLOKS', 'COPY'),
                          ('IOBLOKS', 'COPY'), ('XABLOKS', 'COPY'),
                          ('XAOPS', 'MACRO'), ('XAIO', 'MACRO'),
                          ('XAIOB', 'MACRO')):
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
    print('\n%d cards in the PSA deck' % n)
    return 0 if ok else 1


if __name__ == '__main__':
    sys.exit(main())
