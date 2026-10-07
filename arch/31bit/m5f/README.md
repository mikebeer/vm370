# M5f: mainline GCC `-m31` on VM/370+ (first proof, 7 October 2026)

    s390x-linux-gnu-gcc -m31 -mesa -march=z900 -O2 -ffreestanding -fno-pic \
        -fno-asynchronous-unwind-tables -fno-builtin -c hello31.c
    s390x-linux-gnu-as -m31 -mesa entry31.s -o entry31.o
    s390x-linux-gnu-ld -m elf_s390 -static --emit-relocs -T image.ld \
        -o hello31.elf entry31.o hello31.o
    elf_to_cms hello31.elf hello31x.text      # TEXT deck with RLDs

Compiler: Ubuntu `gcc-s390x-linux-gnu` 13.2 (`apt`), binutils 2.42.
Exporter: Adrian Sutherland's `tools/elf_to_cms.c` (mainframe-lab), with
`elf_to_cms-pcrel.patch`: PC-relative fields (LARL/BRASL; R_390_PC16DBL,
PC32DBL, PLT32DBL, PC32) are resolved by the static link and move with the
image, so only R_390_32 needs an RLD.

`entry31.s`: CMS calls in AMODE 24; the stub saves CMS's R13, sets up a
64 KB BSS stack, BSMs to AMODE 31, calls `cms_main(plist)`, BSMs back.
`cms202()` is the service bridge: plist below 16 MB (the image is), BSM to
AMODE 24, `SVC 202` with the error-return word, BSM back to 31.

**Needs Hercules 4.x**: GCC 13's lowest `-march` is z900, and it emits
LARL, BRASL, ALCR, MLR -- the N3 instructions Hercules 4 allows in ESA/390
mode and 3.13 does not (`feat390.h`).

Result (w255, Hercules 4.9.1, CMSUSER 128M, EC-mode CMS from 290):

    load hello31x (start
    Execution begins...
    HELLO31X: GCC -m31 CODE AT 000203E8, AMODE 31
    HELLO31X: 40 MB AT 01000000 WRITTEN/READ, PAGES=10240 BAD=0 SUM=00000059FEC00000

(sum of the page addresses: 10240*X'01000000' + 4096*52423680 = X'59FEC00000')
