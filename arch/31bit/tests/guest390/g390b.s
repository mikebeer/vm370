# M7.2: an ESA/390 guest drives its console through the virtual channel
# subsystem.  Format-0 CCWs.  Results at X'1000' (16 bytes per entry: tag,
# info, data 8).  Run with SET ESA ON, IPL from tape.
        .text
        .org  0
start:  basr  %r12,0
base:   mvc   0x68(8,%r0),pgmnew-base(%r12)
        mvc   0x78(8,%r0),ionew-base(%r12)
        l     %r9,a1000-base(%r12)
        la    %r14,done-base(%r12)        # a program check ends the test
        st    %r14,resume-base(%r12)
# LOWC: X'B8' and X'BC' after IPL
        mvc   0(4,%r9),tlowc-base(%r12)
        mvc   8(8,%r9),0xb8(%r0)
        la    %r9,16(%r9)
# STAP
        mvc   0(4,%r9),tstap-base(%r12)
        stap  8(%r9)
        ipm   %r1
        st    %r1,4(%r9)
        oi    4(%r9),0xcc
        la    %r9,16(%r9)
# STSCH every subchannel until cc 3: count, devnums, find X'0009'
        mvc   0(4,%r9),tscan-base(%r12)
        l     %r1,ssid0-base(%r12)
        sr    %r3,%r3                       # count
        la    %r4,8(%r9)                    # devnum list (4)
        la    %r5,4
1:      la    %r2,schib-base(%r12)
        stsch 0(%r2)
        brc   1,9f                          # cc 3: end
        clc   6(2,%r2),h0009-base(%r12)
        bne   2f
        st    %r1,conssid-base(%r12)
2:      ltr   %r5,%r5
        bz    3f
        mvc   0(2,%r4),6(%r2)
        la    %r4,2(%r4)
        bctr  %r5,0
3:      la    %r3,1(%r3)
        la    %r1,1(%r1)
        b     1b-base(%r12)
9:      st    %r3,4(%r9)
        la    %r9,16(%r9)
# MSCH: enable the console, ISC 3, parameter 'CONS'
        mvc   0(4,%r9),tmsch-base(%r12)
        l     %r1,conssid-base(%r12)
        la    %r2,schib-base(%r12)
        stsch 0(%r2)
        mvc   0(4,%r2),pcons-base(%r12)
        mvi   4(%r2),0x18
        oi    5(%r2),0x80
        msch  0(%r2)
        ipm   %r6
        st    %r6,4(%r9)
        oi    4(%r9),0xcc
        stsch 0(%r2)
        mvc   8(8,%r9),0(%r2)               # intparm, flags, devnum
        la    %r9,16(%r9)
# SSCH a write, then wait enabled for the I/O interruption
        mvc   0(4,%r9),tssch-base(%r12)
        lctl  6,6,cr6-base(%r12)
        l     %r1,conssid-base(%r12)
        la    %r2,orb1-base(%r12)
        ssch  0(%r2)
        ipm   %r6
        st    %r6,4(%r9)
        oi    4(%r9),0xcc
        la    %r9,16(%r9)
        la    %r14,4f-base(%r12)
        st    %r14,resume-base(%r12)
        lpsw  waitio-base(%r12)
4:
# second write, I/O disabled: poll TPI, then TSCH
        mvc   0(4,%r9),tssc2-base(%r12)
        l     %r1,conssid-base(%r12)
        la    %r2,orb2-base(%r12)
        ssch  0(%r2)
        ipm   %r6
        st    %r6,4(%r9)
        oi    4(%r9),0xcc
        la    %r9,16(%r9)
        mvc   0(4,%r9),ttpi-base(%r12)
        l     %r7,loops-base(%r12)
5:      tpi   8(%r9)
        brc   4,6f                          # cc 1: got one
        bct   %r7,5b-base(%r12)
6:      ipm   %r6
        st    %r6,4(%r9)
        oi    4(%r9),0xcc
        la    %r9,16(%r9)
        bal   %r14,dotsch-base(%r12)
# TSCH with nothing pending: cc 1
        bal   %r14,dotsch-base(%r12)
done:   mvc   0(4,%r9),tend-base(%r12)
        lpsw  wait-base(%r12)
# TSCH the console, record cc, SCSW word 0 and word 2
dotsch: mvc   0(4,%r9),ttsch-base(%r12)
        l     %r1,conssid-base(%r12)
        la    %r2,irb-base(%r12)
        tsch  0(%r2)
        ipm   %r6
        st    %r6,4(%r9)
        oi    4(%r9),0xcc
        mvc   8(4,%r9),0(%r2)
        mvc   12(4,%r9),8(%r2)
        la    %r9,16(%r9)
        br    %r14
# I/O interruption: record X'B8'-X'BF', TSCH, resume
ioh:    mvc   0(4,%r9),tioi-base(%r12)
        mvc   8(8,%r9),0xb8(%r0)
        mvc   4(4,%r9),0x3c(%r0)            # old PSW address word
        la    %r9,16(%r9)
        bal   %r14,dotsch-base(%r12)
        l     %r14,resume-base(%r12)
        br    %r14
pgmh:   mvc   0(4,%r9),tpgm-base(%r12)
        mvc   4(4,%r9),0x8c(%r0)
        mvc   8(8,%r9),0x28(%r0)
        la    %r9,16(%r9)
        l     %r14,resume-base(%r12)
        br    %r14
        .align 8
pgmnew: .long 0x00080000, 0x80000000+0x400+(pgmh-start)
ionew:  .long 0x00080000, 0x80000000+0x400+(ioh-start)
waitio: .long 0x020a0000, 0x80000000
wait:   .long 0x000a0000, 0x00000039
ccw1:   .long 0x09000000+0x400+(msg1-start), 0x20000000+msg1l
ccw2:   .long 0x09000000+0x400+(msg2-start), 0x20000000+msg2l
orb1:   .long 0xd7d9e3f1, 0, 0x400+(ccw1-start), 0
orb2:   .long 0xd7d9e3f2, 0, 0x400+(ccw2-start), 0
a1000:  .long 0x1000
ssid0:  .long 0x00010000
cr6:    .long 0xff000000
loops:  .long 2000000
resume: .long 0
conssid: .long 0xffffffff
pcons:  .ascii "CONS"
h0009:  .short 0x0009
tlowc:  .ascii "LOWC"
tstap:  .ascii "STAP"
tscan:  .ascii "SCAN"
tmsch:  .ascii "MSCH"
tssch:  .ascii "SSCH"
tssc2:  .ascii "SSC2"
ttpi:   .ascii "TPI "
ttsch:  .ascii "TSCH"
tioi:   .ascii "IOI "
tpgm:   .ascii "PGM "
tend:   .ascii "DONE"
msg1:   .byte 0xc8,0xc5,0xd3,0xd3,0xd6,0x40,0xc6,0xd9,0xd6,0xd4,0x40,0xc5,0xe2,0xc1,0x61,0xf3,0xf9,0xf0
        .equ  msg1l, .-msg1
msg2:   .byte 0xe3,0xd7,0xc9,0x40,0xe6,0xd9,0xc9,0xe3,0xc5
        .equ  msg2l, .-msg2
        .align 4
schib:  .fill 64,1,0
irb:    .fill 96,1,0
