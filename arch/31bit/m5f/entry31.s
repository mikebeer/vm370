# VM/370+ M5f: CMS command entry for a -m31 C program (GCC s390, ELF).
# CMS calls in AMODE 24 with R13 -> save area, R1 -> tokenised PLIST.
# The image itself is loaded below 16 MB (CMS LOAD); the program runs in
# AMODE 31 and reaches storage above the line through HIGHSTOR.
# C ABI (s390 ELF): r15 stack pointer, 96-byte frame, args r2-r6,
# result r2, r6-r15 callee-saved.
 .section .text.entry,"ax",@progbits
 .balign 8
 .globl cms_entry
cms_entry:
 stm %r14,%r12,12(%r13)
 basr %r12,0
.Lb:
 l %r3,.Lsaved-.Lb(%r12)
 st %r13,0(%r3)            # CMS save area, for the way back
 l %r15,.Lstack-.Lb(%r12)  # C stack: top of a BSS block
 la %r2,0(%r1)             # the PLIST, for main (AMODE 24 LA: flag byte off)
 l %r3,.Lexsp-.Lb(%r12)
 st %r15,0(%r3)            # stack top, for cms_exit
 l %r1,.Lgo31-.Lb(%r12)
 o %r1,.Lhi-.Lb(%r12)      # AMODE bit (not an address constant)
 bsm 0,%r1                 # to AMODE 31
.Lin31:
 l %r1,.Lmain-.Lb(%r12)
 basr %r14,%r1             # rc = cms_main(plist)
.Lback:                    # cms_exit() arrives here, rc in r2
 basr %r12,0
.Lb2:
 ahi %r12,.Lb-.Lb2         # our base again
 l %r1,.Lgo24-.Lb(%r12)
 bsm 0,%r1                 # back to AMODE 24
.Lin24:
 l %r3,.Lsaved-.Lb(%r12)
 l %r13,0(%r3)
 lr %r15,%r2
 l %r14,12(%r13)
 lm %r0,%r12,20(%r13)
 br %r14
 .balign 4
.Lsaved: .long cms_saved
.Lstack: .long cms_stack+65536-96
.Lmain:  .long cms_main
.Lgo31:  .long .Lin31
.Lhi:    .long 0x80000000
.Lgo24:  .long .Lin24
.Lexsp:  .long cms_exit_sp

# void cms_exit(int rc): unwind to cms_entry from any depth (exit, abort).
 .text
 .balign 8
 .globl cms_exit
cms_exit:
 basr %r1,0
.Lx:
 l %r3,.Lxsp-.Lx(%r1)
 l %r15,0(%r3)
 l %r1,.Lxback-.Lx(%r1)
 br %r1
 .balign 4
.Lxsp: .long cms_exit_sp
.Lxback: .long .Lback

# int cms_onstack(void *top, int (*fn)(int, char **), int argc, char **argv):
# run fn(argc, argv) on the stack that ends at top (cms_run_main gives it
# one of several MB from the heap; the 64 KB BSS stack is only for start-up)
 .text
 .balign 8
 .globl cms_onstack
cms_onstack:
 stm %r6,%r15,24(%r15)
 lr %r10,%r15              # old stack, callee-saved across fn
 lr %r15,%r2
 ahi %r15,-96
 xc 0(4,%r15),0(%r15)      # no back chain
 lr %r1,%r3
 lr %r2,%r4
 lr %r3,%r5
 basr %r14,%r1
 lr %r15,%r10
 lm %r6,%r15,24(%r15)
 br %r14

# int cms202(void *plist): SVC 202 in AMODE 24.  The plist and anything
# it points to must be below 16 MB (static data is: the image is low).
 .text
 .balign 8
 .globl cms202
cms202:
 stm %r6,%r15,24(%r15)
 lr %r10,%r15
 basr %r12,0
.Lc:
 ahi %r15,-160
 l %r13,.Lcsa-.Lc(%r12)    # a CMS save area below 16 MB (the C stack
                           # may be above: cms_onstack)
 lr %r1,%r2
 l %r11,.Lc24-.Lc(%r12)
 bsm 0,%r11                # AMODE 24
.Lc_in24:
 .balign 4
 bcr 0,%r0
 svc 202
 .long .Lc_ret             # CMS error return: same place
.Lc_ret:
 l %r11,.Lc31-.Lc(%r12)
 o %r11,.Lchi-.Lc(%r12)
 bsm 0,%r11                # AMODE 31, R15 = CMS return code
.Lc_in31:
 lr %r2,%r15
 lm %r6,%r15,24(%r10)
 br %r14
 .balign 4
.Lcsa: .long cms_sa
.Lc24: .long .Lc_in24
.Lc31: .long .Lc_in31
.Lchi: .long 0x80000000

 .bss
 .balign 8
cms_saved: .skip 8
 .globl cms_exit_sp
cms_exit_sp: .skip 4
 .balign 8
cms_stack: .skip 65536
 .balign 8
cms_sa: .skip 96
 .section .note.GNU-stack,"",@progbits
