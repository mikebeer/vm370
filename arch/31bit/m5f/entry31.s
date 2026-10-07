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
 lr %r2,%r1                # the PLIST, for main
 l %r1,.Lgo31-.Lb(%r12)
 o %r1,.Lhi-.Lb(%r12)      # AMODE bit (not an address constant)
 bsm 0,%r1                 # to AMODE 31
.Lin31:
 l %r1,.Lmain-.Lb(%r12)
 basr %r14,%r1             # rc = cms_main(plist)
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
 ahi %r15,-256
 la %r13,96(%r15)          # a CMS save area
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
.Lc24: .long .Lc_in24
.Lc31: .long .Lc_in31
.Lchi: .long 0x80000000

 .bss
 .balign 8
cms_saved: .skip 8
 .balign 8
cms_stack: .skip 65536
 .section .note.GNU-stack,"",@progbits
