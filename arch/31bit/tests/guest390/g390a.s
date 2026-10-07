# M7.0 baseline: what does VM/370+ do today with an ESA/390 guest?
# Tape-IPLed at X'400' with PSW 00080000 80000400.  Results at X'1000',
# 16 bytes per test: tag(4) info(4) data(8).  info = X'CCxx00cc' (ran,
# condition code) or the program interruption ILC+code from X'8C'.
        .text
        .org  0
start:  basr  %r12,0
base:   mvc   0x68(8,%r0),pgmnew-base(%r12)  # program new PSW -> pgmh
        l     %r9,a1000-base(%r12)
# T1: lowcore X'00' and X'B8' as IPL left them
        mvc   0(4,%r9),t1-base(%r12)
        mvc   8(4,%r9),0x00(%r0)
        mvc   12(4,%r9),0xb8(%r0)
        la    %r9,16(%r9)
# T2: STIDP
        mvc   0(4,%r9),t2-base(%r12)
        la    %r14,1f-base(%r12)
        stidp 8(%r9)
        ipm   %r1
        st    %r1,4(%r9)
        oi    4(%r9),0xcc
1:      la    %r9,16(%r9)
# T3: STSCH subchannel 0
        mvc   0(4,%r9),t3-base(%r12)
        l     %r1,ssid-base(%r12)
        l     %r2,a1200-base(%r12)
        la    %r14,1f-base(%r12)
        stsch 0(%r2)
        ipm   %r1
        st    %r1,4(%r9)
        oi    4(%r9),0xcc
1:      la    %r9,16(%r9)
# T4: TPI
        mvc   0(4,%r9),t4-base(%r12)
        la    %r14,1f-base(%r12)
        tpi   8(%r9)
        ipm   %r1
        st    %r1,4(%r9)
        oi    4(%r9),0xcc
1:      la    %r9,16(%r9)
# T5: STAP
        mvc   0(4,%r9),t5-base(%r12)
        la    %r14,1f-base(%r12)
        stap  8(%r9)
        ipm   %r1
        st    %r1,4(%r9)
        oi    4(%r9),0xcc
1:      la    %r9,16(%r9)
# T6: SSCH subchannel 0 with an empty ORB
        mvc   0(4,%r9),t6-base(%r12)
        l     %r1,ssid-base(%r12)
        l     %r2,a1300-base(%r12)
        la    %r14,1f-base(%r12)
        ssch  0(%r2)
        ipm   %r1
        st    %r1,4(%r9)
        oi    4(%r9),0xcc
1:      la    %r9,16(%r9)
        mvc   0(4,%r9),tend-base(%r12)
        lpsw  wait-base(%r12)
# program check: record ILC+code, resume after the instruction's BRAS target
pgmh:   mvc   4(4,%r9),0x8c(%r0)
        mvc   8(8,%r9),0x28(%r0)               # program old PSW
        br    %r14
        .align 8
pgmnew: .long 0x00080000, 0x80000000+0x400+(pgmh-start)
wait:   .long 0x000a0000, 0x00000039
ssid:   .long 0x00010000
a1000:  .long 0x1000
a1200:  .long 0x1200
a1300:  .long 0x1300
t1:     .ascii "LOWC"
t2:     .ascii "STID"
t3:     .ascii "STSC"
t4:     .ascii "TPI "
t5:     .ascii "STAP"
t6:     .ascii "SSCH"
tend:   .ascii "DONE"
