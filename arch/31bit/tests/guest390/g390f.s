# M7.4: the clock comparator of an ESA/390 guest.  Tape-IPLed at X'400',
# results at X'1000'.  The program arms the clock comparator 10 ms ahead,
# waits enabled for external interruptions, and on each one (code 1004)
# counts it and re-arms, five times, the way Linux's periodic tick does.
#   X'1000' "CKC ", count, last code; X'1010' "DONE"; codes from X'1020'
        .text
        .org  0
start:  basr  %r12,0
base:   mvc   0x58(8,%r0),extnew-base(%r12)   # external new PSW
        mvc   0x68(8,%r0),pgmnew-base(%r12)   # program new PSW
        l     %r9,a1000-base(%r12)
        mvc   0(4,%r9),tckc-base(%r12)
        xc    4(12,%r9),4(%r9)
        stctl %c0,%c0,cr0-base(%r12)
        oi    cr0+2-base(%r12),0x08           # CR0 bit 20: clock comparator
        ni    cr0+2-base(%r12),0xfb           # CR0 bit 21 (CPU timer) off
        spt   far-base(%r12)                  # CPU timer far away
        lctl  %c0,%c0,cr0-base(%r12)
        bras  %r14,arm
        lpsw  waite-base(%r12)                # enabled wait
# external interruption: count, re-arm, wait again (five times)
exth:   mvc   8(2,%r9),0x86(%r0)              # last interruption code
        l     %r1,4(%r9)
        lr    %r2,%r1
        sll   %r2,1
        la    %r2,32(%r2,%r9)                 # codes from X'1020'
        mvc   0(2,%r2),0x86(%r0)
        ahi   %r1,1
        st    %r1,4(%r9)
        chi   %r1,5
        jnl   done
        bras  %r14,arm
        lpsw  waite-base(%r12)
done:   mvc   16(4,%r9),tend-base(%r12)
        lpsw  wait-base(%r12)
pgmh:   mvc   16(4,%r9),tpgm-base(%r12)
        mvc   20(4,%r9),0x8c(%r0)
        mvc   24(8,%r9),0x28(%r0)
        lpsw  wait-base(%r12)
# arm: clock comparator = TOD + 10 ms (10000 us << 12)
arm:    stck  tod-base(%r12)
        lm    %r2,%r3,tod-base(%r12)
        al    %r3,ten-base(%r12)
        brc   12,1f                           # no carry
        ahi   %r2,1
1:      stm   %r2,%r3,tod-base(%r12)
        sckc  tod-base(%r12)
        br    %r14
        .align 8
extnew: .long 0x00080000, 0x80000000+0x400+(exth-start)
pgmnew: .long 0x00080000, 0x80000000+0x400+(pgmh-start)
waite:  .long 0x010a0000, 0x80000000            # EXT enabled, wait
wait:   .long 0x000a0000, 0x00000039
tod:    .long 0, 0
far:    .long 0x7fffffff, 0xffffffff
cr0:    .long 0
ten:    .long 10000*4096
a1000:  .long 0x1000
tckc:   .ascii "CKC "
tend:   .ascii "DONE"
tpgm:   .ascii "PGM "
