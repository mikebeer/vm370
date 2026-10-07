# M7.2: IPL from the virtual READER the way Linux/390 does (head.S): the
# IPL record's CCWs load 0x18-0xb7, whose CCWs load 0xf0-0x72f; iplstart
# then reads the rest of the deck with SSCH (format-1 ORB, 20 chained
# 80-byte reads) on the subchannel found at X'B8', until unit exception.
# Then it writes the message at the very end of the image to the console.
# Results at X'1000' as in g390b.  Run with SET ESA ON, IPL 00C.
        .text
        .org  0
        .long 0x00080000,0x80000000+iplstart
        .long 0x02000018,0x60000050
        .long 0x02000068,0x60000050
        .fill 80-24,1,0x40
        .long 0x020000f0,0x60000050
        .long 0x02000140,0x60000050
        .long 0x02000190,0x60000050
        .long 0x020001e0,0x60000050
        .long 0x02000230,0x60000050
        .long 0x02000280,0x60000050
        .long 0x020002d0,0x60000050
        .long 0x02000320,0x60000050
        .long 0x02000370,0x60000050
        .long 0x020003c0,0x60000050
        .long 0x02000410,0x60000050
        .long 0x02000460,0x60000050
        .long 0x020004b0,0x60000050
        .long 0x02000500,0x60000050
        .long 0x02000550,0x60000050
        .long 0x020005a0,0x60000050
        .long 0x020005f0,0x60000050
        .long 0x02000640,0x60000050
        .long 0x02000690,0x60000050
        .long 0x020006e0,0x20000050
        .org  0x200
iplstart:
        basr  %r12,0
base:   l     %r9,a1000-base(%r12)
        mvc   0(4,%r9),tlowc-base(%r12)
        mvc   8(8,%r9),0xb8(%r0)
        la    %r9,16(%r9)
        mvc   0x68(8,%r0),pgmnew-base(%r12)
        lh    %r1,0xb8(%r0)
        chi   %r1,1
        jne   crash
        l     %r1,0xb8(%r0)                 # the IPL subchannel
        st    %r1,rdrssid-base(%r12)
        la    %r2,0x730                     # load the rest here
        la    %r3,orb-base(%r12)
        la    %r5,irb-base(%r12)
        la    %r6,ccws-base(%r12)
        la    %r7,20
1:      st    %r2,4(%r6)
        la    %r2,0x50(%r2)
        la    %r6,8(%r6)
        brct  %r7,1b
        lctl  6,6,cr6-base(%r12)
        slr   %r2,%r2                       # bytes loaded
        sr    %r8,%r8                       # SSCH count
ldlp:   l     %r1,rdrssid-base(%r12)
        ssch  0(%r3)
        jnz   sscherr
        la    %r8,1(%r8)
2:      mvc   0x78(8,%r0),ionew-base(%r12)
        lpsw  waitio-base(%r12)
ioint:  l     %r1,rdrssid-base(%r12)
        c     %r1,0xb8(%r0)
        jne   2b
        tsch  0(%r5)
        slr   %r0,%r0
        ic    %r0,8(%r5)                    # device status
        chi   %r0,8
        je    cont
        chi   %r0,12
        je    cont
        l     %r0,4(%r5)                    # the end: bytes read by the
        s     %r0,8(%r3)                    # last SSCH
        mhi   %r0,10
        lh    %r4,10(%r5)
        sr    %r0,%r4
        ar    %r2,%r0
        j     loaded
cont:   ahi   %r2,0x640
        la    %r6,ccws-base(%r12)
        la    %r7,20
3:      l     %r0,4(%r6)
        ahi   %r0,0x640
        st    %r0,4(%r6)
        ahi   %r6,8
        brct  %r7,3b
        j     ldlp
loaded: mvc   0(4,%r9),tload-base(%r12)
        st    %r2,4(%r9)                    # total bytes after 0x730
        st    %r8,8(%r9)                    # SSCHs issued
        mvc   12(4,%r9),0(%r5)              # last SCSW word 0
        la    %r9,16(%r9)
        mvc   0(4,%r9),tirb-base(%r12)
        mvc   4(12,%r9),0(%r5)              # last IRB: SCSW
        la    %r9,16(%r9)
# the message is the last 40 bytes of the image: at 0x730+r2-40
        la    %r6,0x730
        ar    %r6,%r2
        ahi   %r6,-40
        st    %r6,msgccw+4-base(%r12)       # format-1 CCW data address
# find the console (device 0009) and write it
        l     %r1,ssid0-base(%r12)
4:      la    %r2,schib-base(%r12)
        stsch 0(%r2)
        jo    crash
        clc   6(2,%r2),h0009-base(%r12)
        je    5f
        ahi   %r1,1
        j     4b
5:      oi    5(%r2),0x80
        msch  0(%r2)
        la    %r3,corb-base(%r12)
        ssch  0(%r3)
        mvc   0x78(8,%r0),ionew2-base(%r12)
        lpsw  waitio-base(%r12)
ioint2: la    %r5,irb-base(%r12)
        tsch  0(%r5)
        mvc   0(4,%r9),tcons-base(%r12)
        mvc   4(12,%r9),0(%r5)
        la    %r9,16(%r9)
        j     done
sscherr: ipm  %r0
        mvc   0(4,%r9),terr-base(%r12)
        st    %r0,4(%r9)
        st    %r8,8(%r9)
        la    %r9,16(%r9)
        j     done
crash:  mvc   0(4,%r9),tcrash-base(%r12)
        la    %r9,16(%r9)
done:   mvc   0(4,%r9),tend-base(%r12)
        lpsw  wait-base(%r12)
pgmh:   mvc   0(4,%r9),tpgm-base(%r12)
        mvc   4(4,%r9),0x8c(%r0)
        mvc   8(8,%r9),0x28(%r0)
        la    %r9,16(%r9)
        j     done
        .align 8
pgmnew: .long 0x00080000, 0x80000000+pgmh
ionew:  .long 0x00080000, 0x80000000+ioint
ionew2: .long 0x00080000, 0x80000000+ioint2
waitio: .long 0x020a0000, 0x80000000
wait:   .long 0x000a0000, 0x00000039
orb:    .long 0, 0x0080ff00, ccws, 0
corb:   .long 0xc3d6d5e2, 0x0080ff00, msgccw, 0
msgccw: .long 0x09200028, 0
a1000:  .long 0x1000
ssid0:  .long 0x00010000
cr6:    .long 0xff000000
rdrssid: .long 0
h0009:  .short 0x0009
tlowc:  .ascii "LOWC"
tload:  .ascii "LOAD"
tirb:   .ascii "IRB "
tcons:  .ascii "CONS"
terr:   .ascii "SSER"
tcrash: .ascii "CRSH"
tend:   .ascii "DONE"
tpgm:   .ascii "PGM "
        .align 8
ccws:   .rept 19
        .long 0x02600050, 0
        .endr
        .long 0x02200050, 0
        .align 4
schib:  .fill 64,1,0
irb:    .fill 96,1,0
        .org  0x730
# the part iplstart loads: 3000 bytes of filler, then the message
        .fill 3000,1,0x5c
msgend: .byte 0xd3,0xd6,0xc1,0xc4,0xc5,0xc4,0x40,0xc2,0xe8,0x40,0xe2,0xe2,0xc3,0xc8,0x40,0xc6,0xd9,0xd6,0xd4,0x40,0xe3,0xc8,0xc5,0x40,0xd9,0xc5,0xc1,0xc4,0xc5,0xd9,0x40,0x4d,0xd4,0xf7,0x4b,0xf2,0x5d,0x40,0x40,0x40
