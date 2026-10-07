#!/usr/bin/env python3
"""M5g: GCCLIB31 -- GCCLIB for C programs that run AMODE 31 on VM/370+.

    mk31.py <cms-370-gcclib checkout> <outdir>

Copies the GCCLIB sources (adesutherland/cms-370-gcclib, 1.0.0 F0054,
8babe46) and applies the 31-bit changes below.  Every edit is an exact
match that must hit the stated number of times, so a different upstream
level fails here rather than producing a half-converted library.

The design (docs/36-M5-CMS31.md, XA-CMS-light):
 * C code runs AMODE 31.  CMSENTRY enters __cstub with BASSM (bit 0 set)
   and comes back in AMODE 24 for CMS; @@EXIT switches to 24 first.
 * Every C function returns with BSM 0,R14 (DYNSTK @DSTAKOT), so it
   returns in its caller's mode: a BALR from AMODE 31 sets bit 0 of R14,
   BASSM from AMODE 24 clears it.
 * Every CMSSYS stub that touches CMS switches to AMODE 24 on entry
   (BASR/LA/BSM, no base needed) and returns with BSM 0,R14.  So SVC 202,
   DMSFREE, FSxxxx run exactly as for a 24-bit program -- which means
   everything they are handed must be below 16 MB.
 * Two heaps.  malloc() is dlmalloc with its segments from the HIGHSTOR
   nucleus extension (above 16 MB; DMSFREE when HIGHSTOR is absent or
   full).  Storage CMS sees -- FILE (holds the FSCB), record buffers,
   command strings, EPLIST argument lists and the dynamic stack bins
   (C locals are handed to CMS all the time) -- comes from _lmalloc(),
   which is DMSFREE (__dmsfre/__dmsfrt).
 * CMScommand / system() and CMSfunction* copy high strings below the line.
 * memcpy/memset: MVCL lengths are 24 bits, so moves over 16 MB loop;
   string.h sends memcpy/memset/memcmp to the library, not to GCC's
   inline MVCL/CLCL builtins (24-bit lengths too).
 * DYNSTK: 'LA R11,0(,R11)' clears only bit 0 in AMODE 31 -- the stack
   flag byte (X'01', X'06') stayed in the address; SLL/SRL 8 instead.
 * Upstream bug, fixed for both builds: dynamic stack bins for frames over
   16 KB were sized '(size + 4) && 0xFFF000' (logical AND -> 1), so a
   large frame ran off its bin into the heap.
 * CMSSETNU/CMSSETFL: the M5b SSM fix (STNSM/SSM of the caller's mask).
 * printf %g: trailing zeros dropped (upstream printed 0.1 as
   0.10000000000000).
Restrictions: pointers handed directly to the other CMSxxx() calls
(CMSconsoleWrite, CMSfileOpen buffers, rexxsaa SHVBLOCKs, ...) must be
below 16 MB -- stack, static or _lmalloc() storage, not malloc().
"""
import os
import re
import shutil
import sys

FILES = '''cmsentry.assemble cmsrunta.assemble dynstk.assemble cmsjump.assemble
cmssys.assemble cmscrab.macro gcccrab.macro pdpprlg.macro pdpepil.macro
pdptop.copy vtentry.macro vtable.macro
assert.c cmsio.c cmsrtstb.c cmsruntm.c cmsstdio.c cmsstdlb.c cmssysc.c
condrv.c ctype.c dskdrv.c locale.c malloc.c math.c prtdrv.c pundrv.c
rdrdrv.c rexxsaa.c signal.c string.c time.c
assert.h cmsruntm.h cmssys.h ctype.h errno.h float.h gcccrab.h limits.h
locale.h math.h rexxsaa.h setjmp.h signal.h stdarg.h stddef.h stdio.h
stdlib.h string.h time.h'''.split()


def edit(text, old, new, count=1, name=''):
    n = text.count(old)
    if n != count:
        raise SystemExit('%s: %r found %d times, expected %d' % (name, old[:60], n, count))
    return text.replace(old, new)


def card(s):
    """An assembler card: columns 1-71, no sequence field."""
    if len(s) > 71:
        raise SystemExit('card too long: %r' % s)
    return s


def asm_lines(*cards):
    return '\n'.join(card(c) for c in cards) + '\n'


AM24 = asm_lines(
    "         DC    X'0DF0'        BASR R15,0     GCCLIB31: CMS IN AMODE 24",
    "         LA    R15,6(,R15)    BIT 0 OFF: THE BSM'S SUCCESSOR",
    "         DC    X'0B0F'        BSM  0,R15")
RET = "         DC    X'0B0E'        BSM 0,R14: BACK IN THE CALLER'S AMODE"


def cmssys(t):
    n = 'cmssys'
    # M5b: SSM *+1 / SSM =X'FF' assume BC mode (arch/31bit/gcclib/CMSSYS-ssm.diff)
    t = edit(t, "         SSM   *+1\n",
             "         STNSM 16(R13),X'00'  SAVE MASK IN R15 SLOT, DISABLE (EC/BC)\n", 3, n)
    t = edit(t, "         SSM   =X'FF'\n",
             "         SSM   16(R13)        RESTORE CALLER'S MASK (EC/BC)\n", 2, n)
    # AMODE 24 after the base is set, in every routine but @@GETCLK (STCK
    # into the caller's clock, which may be anywhere)
    slr = "         SLR   R12,R15\n"
    parts = t.split(slr)
    if len(parts) != 27:
        raise SystemExit('cmssys: %d SLR sites' % (len(parts) - 1))
    out = parts[0]
    for p in parts[1:]:
        getclk = '@@GETCLK DS    0H' in out.rsplit('ENTRY', 1)[-1]
        out += slr + ('' if getclk else AM24) + p
    t = out
    t = edit(t, "         BR    R14            return to our caller\n",
             RET + "\n", 14, n)
    return t


def cmsentry(t):
    n = 'cmsentry'
    t = edit(t, "         L     R15,=V(@@CSTUB)\n         BALR  R14,R15\n",
             asm_lines("         L     R15,=V(@@CSTUB)",
                       "         O     R15,=X'80000000'  GCCLIB31: C RUNS AMODE 31",
                       "         DC    X'0CEF'        BASSM R14,R15: BACK IN AMODE 24"), 1, n)
    t = edit(t, "         USING @@EXIT,R12     establish addressiblity\n",
             "         USING @@EXIT,R12     establish addressiblity\n" + asm_lines(
                 "         LA    R2,EXIT24      GCCLIB31: EXIT() COMES FROM AMODE 31",
                 "         DC    X'0B02'        BSM 0,R2: AMODE 24 FOR CMS",
                 "EXIT24   DS    0H"), 1, n)
    return t


def dynstk(t):
    n = 'dynstk'
    t = edit(t, "         LA    R11,0(,R11)    Remove flag bits\n", asm_lines(
        "         SLL   R11,8          REMOVE FLAG BITS (LA KEEPS BITS 1-7",
        "         SRL   R11,8          IN AMODE 31) -- GCCLIB31"), 1, n)
    t = edit(t, "         BR    R14              return to the caller's caller\n",
             RET + "\n", 1, n)
    return t


LOWDECL = '''
#ifdef __GCC31__
/* GCCLIB31: storage CMS will see, below 16 MB (DMSFREE) */
void *_lmalloc(size_t bytes);
void _lfree(void *p);
#else
#define _lmalloc(n) malloc(n)
#define _lfree(p) free(p)
#endif
'''


def cmsruntm_h(t):
    return edit(t, 'typedef void *mspace;\n', 'typedef void *mspace;\n' + LOWDECL, 1, 'cmsruntm.h')


def cmsruntm_c(t):
    n = 'cmsruntm.c'
    t = edit(t, '((size + sizeof(size_t)) && 0xFFF000) + 0x1000',
             '((size + sizeof(size_t)) & 0xFFFFF000) + 0x1000', 1, n)
    t = edit(t, '((requested + sizeof(size_t)) && 0xFFF000) + 0x1000',
             '((requested + sizeof(size_t)) & 0xFFFFF000) + 0x1000', 1, n)
    t = edit(t, 'CMSCRAB *crab = malloc(size);', 'CMSCRAB *crab = _lmalloc(size);', 1, n)
    t = edit(t, '        free(bin);\n', '        _lfree(bin);\n', 1, n)
    t = edit(t, '    free(gcccrab->dynamicstack);\n', '    _lfree(gcccrab->dynamicstack);\n', 1, n)
    return t


def cmsstdlb(t):
    return edit(t, '    free(GETGCCCRAB()->dynamicstack);\n',
                '    _lfree(GETGCCCRAB()->dynamicstack);\n', 1, 'cmsstdlb.c')


def cmsio(t):
    n = 'cmsio.c'
    t = edit(t, 'theFile = (FILE *) malloc(sizeof(FILE));',
             'theFile = (FILE *) _lmalloc(sizeof(FILE));', 1, n)
    t = edit(t, '        free(theFile);\n', '        _lfree(theFile);\n', 1, n)
    t = edit(t, '    free(file);\n    return rc;\n', '    _lfree(file);\n    return rc;\n', 1, n)
    return t


def driver(t, name):
    n1 = len(re.findall(r'\bmalloc\(', t))
    n2 = len(re.findall(r'\bfree\(', t))
    if not (n1 == 1 and n2 >= 1):
        raise SystemExit('%s: %d malloc, %d free' % (name, n1, n2))
    t = re.sub(r'\bmalloc\(', '_lmalloc(', t)
    return re.sub(r'\bfree\(', '_lfree(', t)


CMSSYSC_LOW = r'''
#ifdef __GCC31__
/* GCCLIB31: storage handed to CMS must be below 16 MB */
void *_lmalloc(size_t bytes) {
    return __dmsfre(bytes, CMS_USER);
}

void _lfree(void *p) {
    if (p) __dmsfrt(p, 0);
}
#endif

static int cmd_with_plist0(char *command, int calltype);

/* GCCLIB31: a command string above the line is copied below it */
static int cmd_with_plist(char *command, int calltype) {
    char *low;
    int rc;
    if ((unsigned long) command < 0x1000000UL)
        return cmd_with_plist0(command, calltype);
    low = _lmalloc(strlen(command) + 1);
    if (!low) return -3;
    strcpy(low, command);
    rc = cmd_with_plist0(low, calltype);
    _lfree(low);
    return rc;
}
'''

CMSFND31 = r'''
#ifdef __GCC31__
static int __CMSFND0(char *physical, char *logical, int is_proc, char **ret_val,
                     int argc, char *argv[], int lenv[]);

/* GCCLIB31: the logical name and the argument data go in the EPLIST, so
   they are copied below the line (the physical name is copied into the
   PLIST anyway) */
int
__CMSFND(char *physical, char *logical, int is_proc, char **ret_val, int argc,
         char *argv[], int lenv[]) {
    char *low, *p;
    char **lowv;
    int a, total, rc;

    if (!(physical && strlen(physical))) return -1;
    if (!(logical && strlen(logical))) logical = physical;
    total = strlen(logical) + 1;
    for (a = 0; a < argc; a++) total += lenv[a];
    low = _lmalloc(total);
    lowv = malloc((argc + 1) * sizeof(char *));
    if (!low || !lowv) {
        _lfree(low);
        if (lowv) free(lowv);
        return -2;
    }
    strcpy(low, logical);
    p = low + strlen(logical) + 1;
    for (a = 0; a < argc; a++) {
        memcpy(p, argv[a], lenv[a]);
        lowv[a] = p;
        p += lenv[a];
    }
    rc = __CMSFND0(physical, low, is_proc, ret_val, argc, lowv, lenv);
    _lfree(low);
    free(lowv);
    return rc;
}
#define __CMSFNDI __CMSFND0
static int
#else
#define __CMSFNDI __CMSFND
int
#endif
__CMSFNDI(char *physical, char *logical, int is_proc, char **ret_val, int argc,
         char *argv[], int lenv[]) {'''


def cmssysc(t):
    n = 'cmssysc.c'
    t = edit(t, 'void *_DMSFREE(int doublewords);\n',
             'void *_DMSFREE(int doublewords);\n' + CMSSYSC_LOW, 1, n)
    t = edit(t, 'static int cmd_with_plist(char *command, int calltype) {\n    int i, j',
             'static int cmd_with_plist0(char *command, int calltype) {\n    int i, j', 1, n)
    t = edit(t, 'newcommand = (char *) malloc(', 'newcommand = (char *) _lmalloc(', 2, n)
    t = edit(t, '            free(newcommand);\n', '            _lfree(newcommand);\n', 1, n)
    t = edit(t, '        free(newcommand);\n', '        _lfree(newcommand);\n', 1, n)
    t = edit(t, 'eplist.ArgList = (ADLEN *) malloc(', 'eplist.ArgList = (ADLEN *) _lmalloc(', 1, n)
    t = edit(t, 'free(eplist.ArgList);', '_lfree(eplist.ArgList);', 2, n)
    t = edit(t, '''int
__CMSFND(char *physical, char *logical, int is_proc, char **ret_val, int argc,
         char *argv[], int lenv[]) {''', CMSFND31, 1, n)
    return t


MALLOC_HIGH = r'''
#ifdef __GCC31__
/* GCCLIB31 (VM/370+ M5g): dlmalloc's segments come from above 16 MB, from
   the HIGHSTOR nucleus extension (SYSPROF loads it).  DMSFREE below the
   line only when HIGHSTOR is absent or full.  The plist is static, so it
   is in the module, below the line. */
int __SVC202(void *plist, void *eplist, int calltype);
static struct {
    char cmd[8];
    char fn[8];
    size_t bytes;
    void *addr;
    char fence[8];
} __hsplist;

static void *highstor(char *fn, size_t bytes, void *addr) {
    memcpy(__hsplist.cmd, "HIGHSTOR", 8);
    memcpy(__hsplist.fn, fn, 8);
    __hsplist.bytes = bytes;
    __hsplist.addr = addr;
    memset(__hsplist.fence, 0xFF, 8);
    if (__SVC202(&__hsplist, 0, 0)) return 0;
    return __hsplist.addr;
}
#endif

static void *cmsmmap(size_t bytes) {
    void *newpage, *additional;
    int pages;
    int rc;

#ifdef __GCC31__
    newpage = highstor("OBTAIN  ", (bytes + 0xFFF) & ~0xFFF, 0);
    if (newpage) return newpage;
#endif
'''


def malloc_c(t):
    n = 'malloc.c'
    t = edit(t, '''
static void *cmsmmap(size_t bytes) {
    void *newpage, *additional;
    int pages;
    int rc;
''', MALLOC_HIGH, 1, n)
    t = edit(t, '''static int cmsmunmap(void *address, size_t bytes) {
''', '''static int cmsmunmap(void *address, size_t bytes) {
#ifdef __GCC31__
    if ((size_t) address >= 0x1000000)
        return highstor("RELEASE ", (bytes + 0xFFF) & ~0xFFF, address) ? 0 : -1;
#endif
''', 1, n)
    t = edit(t, '#define DEFAULT_GRANULARITY 16384\n', '''#ifdef __GCC31__
#define DEFAULT_GRANULARITY 262144  /* HIGHSTOR pages: fewer, larger segments */
#else
#define DEFAULT_GRANULARITY 16384
#endif
''', 1, n)
    return t


STRING_MVCL = r'''/* GCCLIB31: one MVCL moves at most 16 MB - 1 (24-bit lengths) */
static void __mvcl(void *s1, const void *s2, size_t sz) {
    register size_t src_addr __asm__("2") = s2;  /* Source Addr */
    register size_t src_len __asm__("3") = sz; /* Source Length */
    register size_t dest_addr __asm__("4") = s1; /* Dest Addr */
    register size_t dest_len __asm__("5") = sz; /* Dest Length */

    __asm__ __volatile__("MVCL 4,2"
    : "+d" (src_addr), "+d" (src_len), "+d" (dest_addr), "+d" (dest_len)
    :
    : "cc", "memory"
    );
}

static void __mvclset(void *s, int c, size_t sz) {
    register size_t src_addr __asm__("2") = s;  /* Source Addr */
    register size_t src_len_pad __asm__("3") =
            (size_t) (c & 0xff) << 24; /* Fill Char in high byte + 0 length */
    register size_t dest_addr __asm__("4") = s; /* Dest Addr */
    register size_t dest_len __asm__("5") = sz; /* Dest Length */

    __asm__ __volatile__("MVCL 4,2"
    : "+d" (src_addr), "+d" (src_len_pad), "+d" (dest_addr), "+d" (dest_len)
    :
    : "cc", "memory"
    );
}

#define MVCLMAX 0x00FFF000

static void *__copy31(void *s1, const void *s2, size_t sz) {
    char *d = s1;
    const char *s = s2;
    if (!s1) return 0;
    if (!s2) return s1;
    if (!sz) return s1;
    if (s1 == s2) return s1;
    while (sz > MVCLMAX) {
        __mvcl(d, s, MVCLMAX);
        d += MVCLMAX;
        s += MVCLMAX;
        sz -= MVCLMAX;
    }
    __mvcl(d, s, sz);
    return s1;
}

void *memcpy(void *s1, const void *s2, size_t sz) {
    return __copy31(s1, s2, sz);
}

/* string.h maps memcpy/memset/memcmp here: GCC's inline expansions of
   the builtins use MVCL/CLCL with the length in 24 bits */
void *__mcpy31(void *s1, const void *s2, size_t sz) {
    return __copy31(s1, s2, sz);
}

int __mcmp31(const void *s1, const void *s2, size_t n) {
    const unsigned char *a = s1;
    const unsigned char *b = s2;
    for (; n; n--, a++, b++)
        if (*a != *b) return *a < *b ? -1 : 1;
    return 0;
}
'''

STRING_SET = r'''static void *__set31(void *s, int c, size_t sz) {
    char *d = s;
    if (!s) return 0;
    if (!sz) return s;
    while (sz > MVCLMAX) {
        __mvclset(d, c, MVCLMAX);
        d += MVCLMAX;
        sz -= MVCLMAX;
    }
    __mvclset(d, c, sz);
    return s;
}

void *memset(void *s, int c, size_t sz) {
    return __set31(s, c, sz);
}

void *__mset31(void *s, int c, size_t sz) {
    return __set31(s, c, sz);
}
'''


def string_c(t):
    n = 'string.c'
    a = t.index('void *memcpy(void *s1, const void *s2, size_t sz) {')
    b = t.index('#ifdef memmove')
    t = t[:a] + '#ifdef __GCC31__\n' + STRING_MVCL + '#define MEMCPY31 __copy31\n#else\n' + \
        t[a:b] + '#define MEMCPY31 memcpy\n#endif\n\n' + t[b:]
    t = edit(t, 'return memcpy(s1, s2, sz);', 'return MEMCPY31(s1, s2, sz);', 2, n)
    a = t.index('void *memset(void *s, int c, size_t sz) {')
    b = t.index('#ifdef strcat')
    t = t[:a] + '#ifdef __GCC31__\n' + STRING_SET + '#else\n' + t[a:b] + '#endif\n\n' + t[b:]
    return t


def string_h(t):
    return edit(t, """#if defined (__GNUC__) && __GNUC__ >= 3
#define memcpy(a, b, c) (__builtin_memcpy((a),(b),(c)))
#define memcmp(s1, s2, n) (__builtin_memcmp((s1),(s2),(n)))
#endif
""", """#if defined (__GNUC__) && __GNUC__ >= 3
/* GCCLIB31: not the builtins -- GCC expands them inline as MVCL/CLCL
   with a 24-bit length, so a 20 MB memcpy moved 3 MB (w264) */
void *__mcpy31(void *s1, const void *s2, size_t n);
void *__mset31(void *s, int c, size_t n);
int __mcmp31(const void *s1, const void *s2, size_t n);
#define memcpy(a, b, c) (__mcpy31((a),(b),(c)))
#define memset(s, c, n) (__mset31((s),(c),(n)))
#define memcmp(s1, s2, n) (__mcmp31((s1),(s2),(n)))
#endif
""", 1, 'string.h')


def cmsstdio(t):
    old = """    if (format ==
        0) {                                                      /* exp format - put exp on end */"""
    new = """    if (cnvtype == 'g' || cnvtype == 'G') {
        /* %g drops trailing zeros and a bare point (C89 7.9.6.1); GCCLIB
           printed 0.1 as 0.10000000000000 (cREXX 'say 0.1', w265) */
        char *dot = result, *e;
        while (*dot && *dot != '.') dot++;
        if (*dot) {
            e = dot + strlen(dot);
            while (e > dot + 1 && e[-1] == '0') e--;
            if (e == dot + 1) e--;
            *e = 0;
        }
    }
""" + old
    return edit(t, old, new, 1, 'cmsstdio.c')


EDITS = {
    'cmssys.assemble': cmssys, 'cmsentry.assemble': cmsentry,
    'dynstk.assemble': dynstk, 'cmsruntm.h': cmsruntm_h,
    'cmsruntm.c': cmsruntm_c, 'cmsstdlb.c': cmsstdlb, 'cmsio.c': cmsio,
    'cmssysc.c': cmssysc, 'malloc.c': malloc_c, 'string.c': string_c, 'string.h': string_h, 'cmsstdio.c': cmsstdio,
}
for d in ('condrv.c', 'dskdrv.c', 'prtdrv.c', 'pundrv.c', 'rdrdrv.c'):
    EDITS[d] = (lambda name: lambda t: driver(t, name))(d)


def main():
    if len(sys.argv) != 3:
        raise SystemExit(__doc__)
    src, out = sys.argv[1:]
    if os.path.exists(out):
        shutil.rmtree(out)
    os.makedirs(out)
    for f in FILES:
        t = open(os.path.join(src, f), encoding='latin-1').read()
        t = '\n'.join(l.rstrip() for l in t.split('\n'))
        if f in EDITS:
            t = EDITS[f](t)
        open(os.path.join(out, f), 'w', encoding='latin-1').write(t)
    print('%s: %d files, %d edited' % (out, len(FILES), len(EDITS)))


if __name__ == '__main__':
    main()
