*=====================================================================
* DATTEST -- does DAT come on without faulting?
*
* No operating system underneath: no CP, no CMS, nothing to IPL.  The
* program is loaded into real storage and started with the Hercules
* restart command.
*
* It loads a segment-table designation into CR1, turns DAT on, stores
* a byte and reads it back.  The tables identity map the first 64 KB,
* which holds lowcore, this code and the tables themselves, so the
* instruction stream stays valid the moment translation goes live.
*
* That is the whole question.  Nothing above the 16 MB line, no
* addressing-mode switch, no translation to a different frame - each
* of those fails for its own reasons and belongs in its own test.
*
* The field layouts are Hercules's own, from esa390.h, because the
* emulator is what decides whether a table is acceptable:
*
*   STD_STO         7FFFF000   segment table origin, 4 KB aligned
*   STD_STL         0000007F   length in 64-byte units, less one
*   SEGTAB_PTO      7FFFFFC0   page table origin, 64-byte aligned
*   SEGTAB_INVALID  00000020
*   SEGTAB_PTL      0000000F   length in 16-entry units, less one
*   PAGETAB_PFRA    7FFFF000   page frame real address
*   PAGETAB_INVALID 00000400
*
* MEMORY MAP, all real:
*   000000-001FFF  lowcore, untouched but for the program-check PSW
*   002000         this program
*   003000         SEGTAB, 16 entries, 4 KB aligned as STD_STO wants
*   003040         PAGETAB, 16 entries, 64-byte aligned, identity
*
* RESULT, read as the instruction address in the PSW on the panel:
*   00600D   the store survived translation
*   000BAD   it did not
*   000DED   a program check: the tables were rejected outright
*=====================================================================
         PRINT NOGEN
DATTEST  START X'2000'
*
* Establish a base.  After a restart the registers hold whatever they
* held - nothing has been called, so R15 is not the entry address.
*
         BALR  15,0
         USING *,15
*
* Arm the failure answer before anything can go wrong.  Lowcore is
* still directly addressable: DAT is off.
*
         MVC   X'68'(8,0),PCPSW    program check new PSW
*
* Load the segment table designation, then set PSW bit 5.
*
         LCTL  1,1,CR1VAL
         STOSM MASKSAVE,X'04'      DAT on
*
* The test.  This store and load go through translation.
*
         MVI   MARKER,X'C3'
         CLI   MARKER,X'C3'
         BNE   FAIL
*
         STNSM MASKSAVE,X'FB'      DAT off again, tidily
         LPSW  PASSPSW
*
FAIL     STNSM MASKSAVE,X'FB'
         LPSW  FAILPSW
*
*--------------------------------------------------------------------
* Wait PSWs.  Byte 1 is X'0A': bit 12 on, as ESA/390 requires, and
* bit 14 on for the wait state.  The instruction address is the
* answer.
*--------------------------------------------------------------------
         DS    0D
PASSPSW  DC    X'000A0000',X'0000600D'
FAILPSW  DC    X'000A0000',X'00000BAD'
PCPSW    DC    X'000A0000',X'00000DED'
*
CR1VAL   DC    A(SEGTAB)           STO, with STL zero: 16 entries
MASKSAVE DS    X
MARKER   DS    X
         LTORG
*
*--------------------------------------------------------------------
* The tables, assembled rather than built at run time - every value
* is known now, and a loop is one more thing to get wrong.
*
* Segment table entry 0 points at the page table, length zero
* meaning sixteen entries, invalid bit off.  The rest are invalid,
* so a stray reference outside the first megabyte gets a clean
* exception instead of reading rubbish.
*--------------------------------------------------------------------
         ORG   DATTEST+X'1000'
SEGTAB   DC    A(PAGETAB)
         DC    15A(X'00000020')
*
* Sixteen pages, each mapped to itself: virtual n to real n.
*
PAGETAB  DC    A(X'0000'),A(X'1000'),A(X'2000'),A(X'3000')
         DC    A(X'4000'),A(X'5000'),A(X'6000'),A(X'7000')
         DC    A(X'8000'),A(X'9000'),A(X'A000'),A(X'B000')
         DC    A(X'C000'),A(X'D000'),A(X'E000'),A(X'F000')
         ORG
         END   DATTEST
