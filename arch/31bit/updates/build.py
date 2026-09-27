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
        "IOBORB   DS    XL32           ORB -- MAP WITH ORBLOK",
        "IOBIRB   DS    XL64           IRB -- MAP WITH IRBLOK",
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

    with open(os.path.join(HERE, 'DMKLCL.EXEC'), 'w') as f:
        for name, typ in (('PSA', 'MACRO'), ('RBLOKS', 'COPY'),
                          ('IOBLOKS', 'COPY'), ('XABLOKS', 'COPY')):
            f.write((' &1 &2 %-8s %s' % (name, typ)).ljust(80) + '\n')

    ok = True
    for name in ('PSA.%s' % XA1, 'PSA.AUXLCL', 'RBLOKS.%s' % XA2,
                 'RBLOKS.AUXLCL', 'IOBLOKS.%s' % XA3, 'IOBLOKS.AUXLCL',
                 'DMKLCL.EXEC'):
        bad = verify(os.path.join(HERE, name))
        print('%-16s %3d cards  %s'
              % (name, sum(1 for _ in open(os.path.join(HERE, name))),
                 'OK' if not bad else 'BAD ' + repr(bad[:3])))
        ok = ok and not bad
    print('\n%d cards in the PSA deck' % n)
    return 0 if ok else 1


if __name__ == '__main__':
    sys.exit(main())
