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
from mkdeck import Deck, aux, verify              # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
XA1 = 'XA0001DK'
XA2 = 'XA0002DK'
XA3 = 'XA0003DK'
XA4 = 'XA0004DK'


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
    d.insert('00044000', first='00044100', inc=10, limit='00045000',
             lines=Deck.comment(
        "ESA/390 OPERATION REQUEST BLOCK AND INTERRUPTION RESPONSE BLOCK, "
        "ONE PER OUTSTANDING OPERATION. DMKIOS IS REENTRANT AND NEVER "
        "DISABLES -- IT HAS NO STNSM, STOSM OR SSM ANYWHERE -- SO THESE "
        "CANNOT BE A SHARED WORK AREA. MAPPED WITH ORBLOK AND IRBLOK IN "
        "XABLOKS. THE IRB IS SIXTY-FOUR BYTES BECAUSE TSCH ALWAYS STORES "
        "ALL SIXTY-FOUR, EVEN THOUGH M1 READS ONLY THE SCSW.") + [
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
        "         DC    AL1(ORB5F)     FLAG5: FORMAT-1 CCWS",
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
    ])

    # 5. XABLOKS for ORB5F and ORBLPMOK.  Placed with the other COPYs so the
    #    DSECTs land after the CSECT, which is where block definitions
    #    already go in this module.
    d.insert('02801000', first='02801500', inc=100, limit='02802000', lines=[
        "         COPY  XABLOKS        ESA/390 CHANNEL SUBSYS BLOCKS",
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

    with open(os.path.join(HERE, 'DMKLCL.EXEC'), 'w') as f:
        # XAOPS must be here, not in a separate XALIB: DMKLCL.CNTRL's MACS
        # record is  DMKLCL DMKHRC DMKMAC DMSLCL CMSHRC CMSLIB OSMACRO  and
        # VMFASM globals exactly that list, so a macro library CP's control
        # file does not name is invisible however well it was built.  The
        # first DMKIOS assembly failed on precisely this: IFO078 UNDEFINED
        # OP CODE for SSCH and TSCH, with every other new symbol resolved.
        for name, typ in (('PSA', 'MACRO'), ('RBLOKS', 'COPY'),
                          ('IOBLOKS', 'COPY'), ('XABLOKS', 'COPY'),
                          ('XAOPS', 'MACRO')):
            f.write((' &1 &2 %-8s %s' % (name, typ)).ljust(80) + '\n')

    ok = True
    for name in ('PSA.%s' % XA1, 'PSA.AUXLCL', 'RBLOKS.%s' % XA2,
                 'RBLOKS.AUXLCL', 'IOBLOKS.%s' % XA3, 'IOBLOKS.AUXLCL',
                 'DMKIOS.%s' % XA4, 'DMKIOS.AUXLCL', 'DMKLCL.EXEC'):
        bad = verify(os.path.join(HERE, name))
        print('%-16s %3d cards  %s'
              % (name, sum(1 for _ in open(os.path.join(HERE, name))),
                 'OK' if not bad else 'BAD ' + repr(bad[:3])))
        ok = ok and not bad
    print('\n%d cards in the PSA deck' % n)
    return 0 if ok else 1


if __name__ == '__main__':
    sys.exit(main())
