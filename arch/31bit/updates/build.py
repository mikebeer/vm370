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

    prv = Deck(XA7)
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
        ('00410100', '00410110', 10, '00410200',
         "         CLC   IOINTPRM+2(2),IOBRADD"),
        ('00513000', '00513100', 100, '00514000',
         "         LH    R1,IOINTPRM+2  ADDR. OF INTERRUPTING UNIT"),
        ('00846000', '00846100', 100, '00847000',
         "         LH    R4,IOINTPRM+2  SAVE INTERRUPT DEVICE ADDR."),
        ('00864000', '00864100', 100, '00865000',
         "         CLC   IOINTPRM+2(2),2(R14) IS IT PRIMARY CONSOLE?"),
        ('00873000', '00873100', 100, '00874000',
         "         CLC   IOINTPRM+2(2),2(R14) ALTERNATE CONSOLE?"),
    ):
        d.replace(seq, first=first, inc=inc, limit=limit, lines=[text])
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
    one('00684000', ["CKPST5   XASIO R1             SLAM IT TO THE MSC"])
    one('00685000', ["         BC    2,CKPST5       BUSY, KEEP TRYING..."])
    one('00690000', ["CKPWT5   XATIO R1             CHECK OUT STATUS"])
    one('00691000', ["         BC    2,CKPWT5       BUSY, KEEP TRYING."])

    # --- L6: the two halts.  HSCH covers HIO and HDV alike.
    one('00713000', ["         XAHIO R1             HALT IO"])
    one('00726000', ["         XAHIO R1             HALT IO"])

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

    cch = dmkcch()
    cch.write(os.path.join(HERE, 'DMKCCH.%s' % XA10))
    aux(os.path.join(HERE, 'DMKCCH.AUXLCL'),
        [(XA10, 'CHANNEL CHECK: NO LCL ANALYSIS, TERMINATE INSTEAD')])

    with open(os.path.join(HERE, 'DMKLCL.EXEC'), 'w') as f:
        # XAOPS must be here, not in a separate XALIB: DMKLCL.CNTRL's MACS
        # record is  DMKLCL DMKHRC DMKMAC DMSLCL CMSHRC CMSLIB OSMACRO  and
        # VMFASM globals exactly that list, so a macro library CP's control
        # file does not name is invisible however well it was built.  The
        # first DMKIOS assembly failed on precisely this: IFO078 UNDEFINED
        # OP CODE for SSCH and TSCH, with every other new symbol resolved.
        for name, typ in (('PSA', 'MACRO'), ('RBLOKS', 'COPY'),
                          ('IOBLOKS', 'COPY'), ('XABLOKS', 'COPY'),
                          ('XAOPS', 'MACRO'), ('XAIO', 'MACRO')):
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
                 'DMKDMP.%s' % XA16, 'DMKDMP.AUXLCL', 'DMKLCL.EXEC'):
        bad = verify(os.path.join(HERE, name))
        print('%-16s %3d cards  %s'
              % (name, sum(1 for _ in open(os.path.join(HERE, name))),
                 'OK' if not bad else 'BAD ' + repr(bad[:3])))
        ok = ok and not bad
    print('\n%d cards in the PSA deck' % n)
    return 0 if ok else 1


if __name__ == '__main__':
    sys.exit(main())
