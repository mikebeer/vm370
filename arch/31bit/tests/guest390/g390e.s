# M7.3: SPX and ESA/390 guest DAT.  Tape-IPLed at X'400', PSW 00080000
# 80000400, results at X'1000' (tag, info, 8 bytes data; info = ILC+code
# from X'8C' after a program check, or CCxx00cc).
#
# T1 SPEX: a prefix page at X'5000' with a marker and the program-new PSW,
#    SPX X'5000', then real X'200' -> the marker (VM/370plus copies the page)
# T2 STPX
# T3 DATP: segment table X'6000' (STL 0, 16 entries), page table X'7000'
#    (PTL 15): identity, except virtual X'8000' -> real X'9000'.  CR0 byte
#    1 = X'B0', CR1 = X'6000'.  DAT on in primary mode: load virtual X'8000'
#    -> "REAL9000", not "REAL8000" (identity mapping proves nothing)
# T4 DATH: same in home mode (CR13 = the same STD, PSW ASC 11)
# T5 IPTE: invalidate virtual X'8000', load it -> page-translation (X'11')
# T6 SEGX: virtual X'200000' (segment 2: invalid STE) -> X'10'
        .text
        .org  0
start:  basr  %r12,0
base:   mvc   0x68(8,%r0),pgmnew-base(%r12)  # program new PSW -> pgmh
        l     %r9,a1000-base(%r12)
# T1: SPX
        mvc   0(4,%r9),t1-base(%r12)
        l     %r2,a5000-base(%r12)           # the new prefix page is a
        la    %r3,4095(%r0)                  # copy of page 0 (this code
        la    %r3,1(%r3)                     # runs in it)
        sr    %r4,%r4
        lr    %r5,%r3
        mvcl  %r2,%r4
        l     %r2,a5000-base(%r12)
        mvc   0x200(8,%r2),mark-base(%r12)
        la    %r14,1f-base(%r12)
        spx   a5000-base(%r12)
        mvc   8(8,%r9),0x200(%r0)            # real 0 now: the marker?
1:      la    %r9,16(%r9)
# T2: STPX
        mvc   0(4,%r9),t2-base(%r12)
        la    %r14,1f-base(%r12)
        stpx  8(%r9)
1:      la    %r9,16(%r9)
# tables: segment table X'6000' all invalid, entry 0 -> page table X'7000'
        l     %r2,a6000-base(%r12)
        la    %r3,16
        l     %r4,stinv-base(%r12)
2:      st    %r4,0(%r2)
        la    %r2,4(%r2)
        brct  %r3,2b
        l     %r2,a6000-base(%r12)
        l     %r4,a7000-base(%r12)
        o     %r4,f15-base(%r12)             # PTL 15: 256 entries
        st    %r4,0(%r2)
        l     %r2,a7000-base(%r12)           # page table: identity
        sr    %r4,%r4
        la    %r3,256
2:      st    %r4,0(%r2)
        la    %r2,4(%r2)
        ahi   %r4,4096
        brct  %r3,2b
        l     %r2,a7000-base(%r12)
        l     %r4,a9000-base(%r12)
        st    %r4,8*4(%r2)                   # page 8 -> frame 9
        l     %r1,a8000-base(%r12)
        mvc   0(8,%r1),r8000-base(%r12)
        l     %r1,a9000-base(%r12)
        mvc   0(8,%r1),r9000-base(%r12)
        stctl %c0,%c0,cr0-base(%r12)
        mvi   cr0+1-base(%r12),0xb0
        lctl  %c0,%c0,cr0-base(%r12)
        lctl  %c1,%c1,a6000-base(%r12)
        lctl  %c7,%c7,a6000-base(%r12)
        lctl  %c13,%c13,a6000-base(%r12)
# T3: DAT on, primary
        mvc   0(4,%r9),t3-base(%r12)
        la    %r14,1f-base(%r12)
        stosm sm-base(%r12),0x04             # DAT on
        l     %r1,a8000-base(%r12)
        mvc   8(8,%r9),0(%r1)
        stnsm sm-base(%r12),0xfb             # DAT off
1:      la    %r9,16(%r9)
# T4: DAT on, home space (ASC 11)
        mvc   0(4,%r9),t4-base(%r12)
        la    %r14,endh-base(%r12)
        lpsw  pswhome-base(%r12)
home:   l     %r1,a8000-base(%r12)
        mvc   8(8,%r9),0(%r1)
        lpsw  pswreal-base(%r12)
endh:   la    %r9,16(%r9)
# T5: IPTE virtual X'8000', then load it under DAT: X'11'
        mvc   0(4,%r9),t5-base(%r12)
        l     %r1,a7000-base(%r12)
        l     %r2,a8000-base(%r12)
        ipte  %r1,%r2
        la    %r14,1f-base(%r12)
        stosm sm-base(%r12),0x04
        l     %r1,a8000-base(%r12)
        mvc   8(8,%r9),0(%r1)
1:      stnsm sm-base(%r12),0xfb
        la    %r9,16(%r9)
# T6: segment 2 invalid: X'10'
        mvc   0(4,%r9),t6-base(%r12)
        la    %r14,1f-base(%r12)
        stosm sm-base(%r12),0x04
        l     %r1,a200000-base(%r12)
        mvc   8(8,%r9),0(%r1)
1:      stnsm sm-base(%r12),0xfb
        la    %r9,16(%r9)
        mvc   0(4,%r9),tend-base(%r12)
        lpsw  wait-base(%r12)
# program check: record ILC+code and the old PSW, DAT off, resume at R14
pgmh:   mvc   4(4,%r9),0x8c(%r0)
        mvc   8(4,%r9),0x2c(%r0)
        mvc   12(4,%r9),0x90(%r0)            # translation exception id
        stnsm sm-base(%r12),0xfb
        br    %r14
        .align 8
pgmnew: .long 0x00080000, 0x80000000+0x400+(pgmh-start)
wait:   .long 0x000a0000, 0x00000039
pswhome:.long 0x040cc000, 0x80000000+0x400+(home-start)
pswreal:.long 0x00080000, 0x80000000+0x400+(endh-start)
cr0:    .long 0
sm:     .long 0
a1000:  .long 0x1000
a5000:  .long 0x5000
a6000:  .long 0x6000
a7000:  .long 0x7000
a8000:  .long 0x8000
a9000:  .long 0x9000
a200000:.long 0x200000
stinv:  .long 0x00000020
f15:    .long 15
mark:   .ascii "PREFIXED"
r8000:  .ascii "REAL8000"
r9000:  .ascii "REAL9000"
t1:     .ascii "SPEX"
t2:     .ascii "STPX"
t3:     .ascii "DATP"
t4:     .ascii "DATH"
t5:     .ascii "IPTE"
t6:     .ascii "SEGX"
tend:   .ascii "DONE"
