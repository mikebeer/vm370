/* cmsrt.c -- VM/370+ M5f: the CMS side of newlib for GCC -m31 programs.
 *
 * The program runs in AMODE 31 with its code, data, stack and plists in the
 * image CMS LOADed below 16 MB, and its heap above 16 MB from HIGHSTOR.
 * Every CMS service goes through cms202() (entry31.s): AMODE 24, SVC 202,
 * back to 31.  So nothing handed to CMS may live in the heap: plists,
 * record buffers and the terminal line are static.
 *
 * The C side is ASCII (Latin-1); CMS is EBCDIC (code page 037).  Text is
 * translated at the boundary (IBM-1047, as CE's Hercules CODEPAGE 819/1047): terminal lines, file records, command tokens.
 *
 * Files are whole-file: open for reading reads every record into the heap
 * (text: EBCDIC -> ASCII, F-format trailing blanks dropped, one '\n' per
 * record; binary: records concatenated), so read/lseek are memory
 * operations.  Open for writing collects the bytes and writes them at close
 * (text: one V record per line, an empty line is one blank; binary: V
 * records of up to RECMAX bytes).  Binary = filetype RXBIN or MODULE, or a
 * name ending in "(B)" -- newlib does not pass fopen's 'b' down.
 * Names: "fn.ft[.fm]" or "fn ft [fm]", case-insensitive, fm default A1.
 */
#include <errno.h>
#include <stdio.h>
#include <fcntl.h>
#include <string.h>
#include <stdlib.h>
#include <sys/stat.h>
#include <sys/times.h>
#include <sys/time.h>
#include <time.h>
#include "cp1047.h"

/* M8: cREXX's mainframe entry points call mainframe_set_text_conversion(0)
 * and do IBM-1047 themselves: raw record bytes, ASCII LF as the delimiter. */
static int rt_conv = 1;
void mainframe_set_text_conversion(int enabled) { rt_conv = enabled != 0; }
#define A2E(c) (rt_conv ? rt_a2e[(unsigned char)(c)] : (unsigned char)(c))
#define E2A(c) (rt_conv ? rt_e2a[(unsigned char)(c)] : (char)(c))

#undef errno
extern int errno;

int cms202(void *plist);
void cms_exit(int rc) __attribute__((noreturn));
int cms_onstack(void *top, int (*fn)(int, char **), int argc, char **argv);
int main(int, char **);
/* main runs on a stack of cms_stack_mb MB from the heap (above 16 MB):
   the 64 KB start-up stack is far too small for cREXX's recursion. */
unsigned int cms_stack_mb = 8;
static int cms_run_main(int argc, char **argv)
{
    char *s = malloc(cms_stack_mb << 20);
    if (!s) return main(argc, argv);
    return cms_onstack(s + (cms_stack_mb << 20), main, argc, argv);
}
int main(int argc, char **argv);

typedef unsigned int u32;

/* ---------------------------------------------------------------- terminal */
static unsigned char tline[130];
static int tlen;
static unsigned char typl[16];

static void put8(unsigned char *d, const char *s)
{
    int i = 0;
    for (; s[i] && i < 8; i++) d[i] = rt_a2e[(unsigned char)s[i]];
    for (; i < 8; i++) d[i] = 0x40;
}

static void tflush(void)
{
    u32 a = (u32)tline;
    if (tlen == 0) { tline[0] = 0x40; tlen = 1; }
    put8(typl, "TYPLIN");
    typl[8] = 1; typl[9] = a >> 16; typl[10] = a >> 8; typl[11] = a;
    typl[12] = 0xC2; typl[13] = 0; typl[14] = tlen >> 8; typl[15] = tlen;
    cms202(typl);
    tlen = 0;
}

static void tput(const char *p, int n)
{
    for (int i = 0; i < n; i++) {
        unsigned char c = p[i];
        if (c == '\n') { tflush(); continue; }
        if (c == '\r') continue;
        if (tlen == (int)sizeof tline) tflush();
        tline[tlen++] = c == '\t' && rt_conv ? 0x40 : A2E(c);
    }
}

/* RDTERM: one terminal line, translated, plus '\n' */
static unsigned char rdpl[16];
static unsigned char rdbuf[132];
static char tin[136];
static int tin_len, tin_pos;

static int tread(char *p, int n)
{
    if (tin_pos >= tin_len) {
        u32 a = (u32)rdbuf;
        int len;
        if (tlen) tflush();
        memset(rdbuf, 0x40, sizeof rdbuf);
        put8(rdpl, "WAITRD");
        rdpl[8] = 1; rdpl[9] = a >> 16; rdpl[10] = a >> 8; rdpl[11] = a;
        rdpl[12] = 0xE3; /* 'T': EDIT=NO, as typed */
        rdpl[13] = 0xF0; rdpl[14] = 0; rdpl[15] = 0;
        if (cms202(rdpl)) return 0;
        len = rdpl[14] << 8 | rdpl[15];             /* length read */
        if (len > 130) len = 130;
        for (int i = 0; i < len; i++) tin[i] = E2A(rdbuf[i]);
        tin[len] = '\n';
        tin_len = len + 1; tin_pos = 0;
    }
    int k = tin_len - tin_pos;
    if (k > n) k = n;
    memcpy(p, tin + tin_pos, k);
    tin_pos += k;
    return k;
}

/* ---------------------------------------------------------------- heap */
static struct { char cmd[8], fn[8]; u32 bytes, addr; } hsp;
static char *heap_base, *heap_end, *heap_brk;
static char low_heap[64 << 10] __attribute__((aligned(8)));

static int highstor(const char *fn, u32 bytes, u32 addr)
{
    put8((unsigned char *)hsp.cmd, "HIGHSTOR");
    put8((unsigned char *)hsp.fn, fn);
    hsp.bytes = bytes; hsp.addr = addr;
    return cms202(&hsp);
}

u32 cms_heap_mb = 0;        /* 0: the largest that HIGHSTOR gives, up to 232 MB */

static void heap_init(void)
{
    static const u32 tries[] = { 232, 224, 192, 160, 128, 96, 64, 48, 32, 16, 0 };
    if (cms_heap_mb) {
        if (!highstor("OBTAIN", cms_heap_mb << 20, 0)) {
            heap_base = (char *)hsp.addr; heap_end = heap_base + (cms_heap_mb << 20);
        }
    } else {
        for (int i = 0; tries[i]; i++)
            if (!highstor("OBTAIN", tries[i] << 20, 0)) {
                heap_base = (char *)hsp.addr; heap_end = heap_base + (tries[i] << 20);
                break;
            }
    }
    if (!heap_base) { heap_base = low_heap; heap_end = low_heap + sizeof low_heap; }
    heap_brk = heap_base;
}

static void heap_fini(void)
{
    if (heap_base && heap_base != low_heap)
        highstor("RELEASE", heap_end - heap_base, (u32)heap_base);
    heap_base = 0;
}

void *_sbrk(int incr)
{
    char *old = heap_brk;
    if (!heap_base) heap_init();
    old = heap_brk;
    if (incr < 0 || heap_brk + incr > heap_end) {
        static int told;
        if (!told++) {          /* say so once: a program may not check */
            static const char m[] = "CMSRT: out of storage (heap above 16 MB is full)\n";
            tput(m, sizeof m - 1);
            tflush();
        }
        errno = ENOMEM; return (void *)-1;
    }
    heap_brk += incr;
    return old;
}

/* ---------------------------------------------------------------- files */
#define NFILES 16
#define RECMAX 32760
static struct fscb {
    unsigned char cmd[8], fn[8], ft[8], fm[2];
    unsigned short recno;
    u32 buf, bsize;
    unsigned char recfm[2];
    unsigned short norec;
    u32 nread;
} fscb;
static unsigned char rec[RECMAX + 8];

struct cfile {
    int used, writing, binary, fm_given;
    unsigned char fn[8], ft[8], fm[2];
    char *data;
    u32 len, cap, pos;
};
static struct cfile files[NFILES];

static int parse_name(const char *name, struct cfile *f)
{
    char part[3][9];
    int np = 0, k = 0;
    const char *p = name;
    char dirmode[3] = {0, 0, 0};
    memset(part, 0, sizeof part);
    f->binary = 0;
    while (*p == ' ') p++;
    /* "dir/fn.ft": cREXX's openfile() builds these.  "." is no mode (search
       the accessed disks); otherwise the directory is the filemode letter. */
    const char *slash = strrchr(p, '/');
    if (slash) {
        if (!(slash - p == 1 && p[0] == '.') && slash > p) {
            dirmode[0] = p[0];
            if (slash - p > 1 && p[1] >= '0' && p[1] <= '9') dirmode[1] = p[1];
        }
        p = slash + 1;
    }
    for (; *p; p++) {
        if (*p == '(') { if ((p[1] == 'b' || p[1] == 'B')) f->binary = 1; break; }
        if (*p == '.' || *p == ' ') {
            if (k) { np++; k = 0; }
            if (np == 3) break;
            continue;
        }
        if (np >= 3) return -1;
        if (k >= 8) continue;   /* longer names are cut to 8, as CMS does */
        char c = *p;
        if (c >= 'a' && c <= 'z') c -= 32;
        part[np][k++] = c;
    }
    if (k) np++;
    if (np < 2) return -1;
    put8(f->fn, part[0]); put8(f->ft, part[1]);
    if (np >= 3) {
        f->fm[0] = rt_a2e[(unsigned char)part[2][0]];
        f->fm[1] = part[2][1] ? rt_a2e[(unsigned char)part[2][1]] : 0xF1;
        f->fm_given = 1;
    } else if (dirmode[0]) {
        char c = dirmode[0];
        if (c >= 'a' && c <= 'z') c -= 32;
        f->fm[0] = rt_a2e[(unsigned char)c];
        f->fm[1] = dirmode[1] ? rt_a2e[(unsigned char)dirmode[1]] : 0xF1;
        f->fm_given = 1;
    } else { f->fm[0] = 0xC1; f->fm[1] = 0xF1; f->fm_given = 0; }
    if (!memcmp(part[1], "RXBIN", 6) || !memcmp(part[1], "MODULE", 7)) f->binary = 1;
    return 0;
}

static void set_fscb(const char *cmd, struct cfile *f)
{
    memset(&fscb, 0, sizeof fscb);
    put8(fscb.cmd, cmd);
    memcpy(fscb.fn, f->fn, 8); memcpy(fscb.ft, f->ft, 8); memcpy(fscb.fm, f->fm, 2);
}

static int grow(struct cfile *f, u32 more)
{
    if (f->len + more <= f->cap) return 0;
    u32 n = f->cap ? f->cap * 2 : 4096;
    while (n < f->len + more) n *= 2;
    char *d = realloc(f->data, n);
    if (!d) return -1;
    f->data = d; f->cap = n;
    return 0;
}

static int read_whole(struct cfile *f)
{
    for (;;) {
        int rc;
        set_fscb("RDBUF", f);
        fscb.buf = (u32)rec; fscb.bsize = RECMAX;
        fscb.recfm[0] = 0xE5; fscb.recfm[1] = 0x40;   /* 'V ' -- CMS sets it */
        fscb.norec = 1;
        rc = cms202(&fscb);
        if (rc == 12) break;                           /* end of file */
        if (rc) { return rc == 1 || rc == 2 || rc == 28 ? -ENOENT : -EIO; }
        u32 n = fscb.nread;
        if (grow(f, n + 1)) return -ENOMEM;
        if (f->binary) {
            memcpy(f->data + f->len, rec, n); f->len += n;
        } else {
            while (n > 0 && rec[n - 1] == 0x40) n--;  /* F records are padded */
            for (u32 i = 0; i < n; i++) f->data[f->len++] = E2A(rec[i]);
            f->data[f->len++] = '\n';
        }
    }
    /* close it: CMS keeps a read position per open file */
    set_fscb("FINIS", f);
    cms202(&fscb);
    return 0;
}

static int write_rec(struct cfile *f, const unsigned char *p, u32 n)
{
    set_fscb("WRBUF", f);
    fscb.buf = (u32)p; fscb.bsize = n;
    fscb.recfm[0] = 0xE5; fscb.recfm[1] = 0x40;       /* 'V ' */
    fscb.norec = 1;
    return cms202(&fscb);
}

static int write_whole(struct cfile *f)
{
    int rc = 0;
    u32 i = 0;
    set_fscb("ERASE", f);
    cms202(&fscb);
    if (f->binary) {
        while (i < f->len && !rc) {
            u32 n = f->len - i > RECMAX ? RECMAX : f->len - i;
            memcpy(rec, f->data + i, n);
            rc = write_rec(f, rec, n);
            i += n;
        }
    } else {
        while (i < f->len && !rc) {
            u32 n = 0;
            while (i < f->len && f->data[i] != '\n') {
                if (n < RECMAX) rec[n++] = A2E(f->data[i]);
                i++;
            }
            if (i < f->len) i++;                      /* the '\n' */
            if (n == 0) rec[n++] = 0x40;
            rc = write_rec(f, rec, n);
        }
    }
    set_fscb("FINIS", f);
    cms202(&fscb);
    return rc ? -EIO : 0;
}

int _open(const char *name, int flags, int mode)
{
    int fd;
    (void)mode;
    for (fd = 3; fd < NFILES && files[fd].used; fd++) ;
    if (fd == NFILES) { errno = EMFILE; return -1; }
    struct cfile *f = &files[fd];
    memset(f, 0, sizeof *f);
    if (parse_name(name, f)) { errno = EINVAL; return -1; }
    f->used = 1;
    if ((flags & O_ACCMODE) == O_RDONLY) {
        if (!f->fm_given) f->fm[0] = 0x5C;            /* '*': any accessed disk */
        int rc = read_whole(f);
        if (rc) { free(f->data); f->used = 0; errno = -rc; return -1; }
    } else {
        f->writing = 1;
        if (flags & O_APPEND) {
            struct cfile g = *f;
            if (read_whole(&g) == 0) { *f = g; f->writing = 1; f->pos = f->len; }
        }
    }
    return fd;
}

int _close(int fd)
{
    if (fd < 3) return 0;
    if (fd >= NFILES || !files[fd].used) { errno = EBADF; return -1; }
    struct cfile *f = &files[fd];
    int rc = f->writing ? write_whole(f) : 0;
    free(f->data);
    f->used = 0;
    if (rc) { errno = -rc; return -1; }
    return 0;
}

int _write(int fd, const char *p, int n)
{
    if (fd == 1 || fd == 2) { tput(p, n); return n; }
    if (fd < 3 || fd >= NFILES || !files[fd].used || !files[fd].writing) { errno = EBADF; return -1; }
    struct cfile *f = &files[fd];
    if (f->pos + n > f->len && grow(f, f->pos + n - f->len)) { errno = ENOSPC; return -1; }
    memcpy(f->data + f->pos, p, n);
    f->pos += n;
    if (f->pos > f->len) f->len = f->pos;
    return n;
}

int _read(int fd, char *p, int n)
{
    if (fd == 0) return tread(p, n);
    if (fd < 3 || fd >= NFILES || !files[fd].used) { errno = EBADF; return -1; }
    struct cfile *f = &files[fd];
    u32 k = f->len - f->pos;
    if ((u32)n < k) k = n;
    memcpy(p, f->data + f->pos, k);
    f->pos += k;
    return k;
}

int _lseek(int fd, int off, int whence)
{
    if (fd < 3) return 0;
    if (fd >= NFILES || !files[fd].used) { errno = EBADF; return -1; }
    struct cfile *f = &files[fd];
    long np = whence == SEEK_SET ? off : whence == SEEK_CUR ? (long)f->pos + off : (long)f->len + off;
    if (np < 0) { errno = EINVAL; return -1; }
    if ((u32)np > f->len && f->writing) { if (grow(f, np - f->len)) { errno = ENOSPC; return -1; }
        memset(f->data + f->len, 0, np - f->len); f->len = np; }
    if ((u32)np > f->len) np = f->len;
    f->pos = np;
    return np;
}

int _fstat(int fd, struct stat *st)
{
    memset(st, 0, sizeof *st);
    if (fd < 3) { st->st_mode = S_IFCHR; return 0; }
    if (fd >= NFILES || !files[fd].used) { errno = EBADF; return -1; }
    st->st_mode = S_IFREG; st->st_size = files[fd].len; st->st_blksize = 4096;
    return 0;
}

int _stat(const char *name, struct stat *st)
{
    int fd = _open(name, O_RDONLY, 0);
    if (fd < 0) return -1;
    _fstat(fd, st);
    _close(fd);
    return 0;
}

int stat(const char *name, struct stat *st) { return _stat(name, st); }
int fstat(int fd, struct stat *st) { return _fstat(fd, st); }
int _isatty(int fd) { return fd < 3; }

int _unlink(const char *name)
{
    struct cfile f;
    memset(&f, 0, sizeof f);
    if (parse_name(name, &f)) { errno = EINVAL; return -1; }
    set_fscb("ERASE", &f);
    if (cms202(&fscb)) { errno = ENOENT; return -1; }
    return 0;
}

/* No processes on CMS: system() would LOAD a MODULE over the running one. */
int system(const char *cmd) { return cmd ? -1 : 0; }
int _execve(const char *n, char *const a[], char *const e[]) { (void)n; (void)a; (void)e; errno = ENOSYS; return -1; }
int _fork(void) { errno = ENOSYS; return -1; }
int _wait(int *st) { (void)st; errno = ECHILD; return -1; }
int write(int fd, const void *p, size_t n) { return _write(fd, p, n); }

int _link(const char *a, const char *b) { (void)a; (void)b; errno = EMLINK; return -1; }
int _kill(int pid, int sig) { (void)pid; (void)sig; errno = EINVAL; return -1; }
int _getpid(void) { return 1; }
clock_t _times(struct tms *t) { memset(t, 0, sizeof *t); return 0; }

/* TOD clock: bit 51 = 1 microsecond, epoch 1900 */
int gettimeofday(struct timeval *tv, void *tz)
{
    unsigned long long tod;
    (void)tz;
    __asm__ volatile ("stck %0" : "=Q"(tod) : : "cc");
    unsigned long long us = tod >> 12;
    us -= 2208988800ULL * 1000000ULL;
    tv->tv_sec = (long)(us / 1000000ULL);
    tv->tv_usec = (long)(us % 1000000ULL);
    return 0;
}

void _exit(int rc)
{
    for (int fd = 3; fd < NFILES; fd++) if (files[fd].used) _close(fd);
    if (tlen) tflush();
    heap_fini();
    cms_exit(rc);
}

/* ---------------------------------------------------------------- startup */
#define MAXARGS 32
static char argbuf[MAXARGS][9];
static char *argv_[MAXARGS + 1];

int cms_main(unsigned char *plist)
{
    int argc = 0;
    while (argc < MAXARGS && plist[0] != 0xFF) {
        int k = 0;
        for (int i = 0; i < 8 && plist[i] != 0x40; i++) {
            char c = rt_e2a[plist[i]];
            if (c >= 'A' && c <= 'Z' && argc == 0) c += 32;   /* program name */
            argbuf[argc][k++] = c;
        }
        argbuf[argc][k] = 0;
        argv_[argc] = argbuf[argc];
        argc++;
        plist += 8;
    }
    argv_[argc] = 0;
    /* CMS cuts every token to 8 characters: an EXEC passes longer
       arguments by stacking them (QUEUE) and giving the token =STACK,
       which is replaced by the words of that stacked line (case kept;
       "..." or '...' groups a word with blanks) */
    for (int j = 1; j < argc; j++) {
        static char sline[256];
        static char *sargv[MAXARGS + 1];
        char *q;
        int n = 0, len;
        if (strcmp(argv_[j], "=STACK") && strcmp(argv_[j], "=stack")) continue;
        len = tread(sline, sizeof sline - 1);
        sline[len] = 0;
        if (len && sline[len - 1] == '\n') sline[len - 1] = 0;
        for (int i = 0; i < j; i++) sargv[n++] = argv_[i];
        q = sline;
        while (*q && n < MAXARGS) {
            while (*q == ' ') q++;
            if (!*q) break;
            if (*q == '"' || *q == '\'') {
                char d = *q++;
                sargv[n++] = q;
                while (*q && *q != d) q++;
            } else {
                sargv[n++] = q;
                while (*q && *q != ' ') q++;
            }
            if (*q) *q++ = 0;
        }
        for (int i = j + 1; i < argc && n < MAXARGS; i++) sargv[n++] = argv_[i];
        sargv[n] = 0;
        tin_len = tin_pos = 0;
        exit(cms_run_main(n, sargv));
    }
    exit(cms_run_main(argc, argv_));
}
int _gettimeofday(struct timeval *tv, void *tz) { return gettimeofday(tv, tz); }

/* M8: cREXX's CREXX_CMS_TEXT_IO hooks.  The file is opened as usual; with
 * mainframe_set_text_conversion(0) its records arrive as raw IBM-1047 bytes
 * with ASCII LF between them, and cREXX's own codec decodes them. */
FILE *crexx_cms_text_open(const char *path, const char *mode) { return fopen(path, mode); }
int crexx_cms_text_encoding(const char *encoding) { (void)encoding; return 0; }

/* M8: opendir/readdir/closedir for cREXX's import discovery (CREXX_CMS_DIRENT).
 * A directory is a filemode letter ("A", "a", "a/" or "." for A).  The listing
 * comes from  LISTFILE * * m (EXEC , which writes CMS EXEC A1 with one
 * "&1 &2 FN FT FM" line per file.  Names are returned as "fn.ft". */
struct dirent { unsigned int d_ino; unsigned char d_type; char d_name[20]; };
struct m8_dir { char *names; int count, pos; struct dirent ent; };
struct m8_dir *opendir(const char *name)
{
    static unsigned char pl[8 * 7];  /* below 16 MB: the stack is not */
    char mode = 'A';
    if (name && name[0] && name[0] != '.') mode = name[0];
    if (mode >= 'a' && mode <= 'z') mode -= 32;
    const char *tok[6] = { "LISTFILE", "*", "*", 0, "(", "EXEC" };
    char m[2] = { mode, 0 };
    tok[3] = m;
    memset(pl, 0x40, sizeof pl);
    for (int t = 0; t < 6; t++)
        for (int i = 0; tok[t][i] && i < 8; i++) pl[t * 8 + i] = rt_a2e[(unsigned char)tok[t][i]];
    memset(pl + 48, 0xFF, 8);
    int rc = cms202(pl);
    struct m8_dir *d = calloc(1, sizeof *d);
    if (!d) { errno = ENOMEM; return 0; }
    if (rc) return d;                                /* no files: empty */
    struct cfile f;
    memset(&f, 0, sizeof f);
    if (parse_name("CMS EXEC A1", &f)) return d;
    int save = rt_conv; rt_conv = 1;
    int r = read_whole(&f);
    rt_conv = save;
    if (r) { free(f.data); return d; }
    d->names = malloc(f.len / 2 + 64);
    char *out = d->names, *p = f.data, *end = f.data + f.len;
    while (p < end) {
        char *nl = memchr(p, '\n', end - p); if (!nl) nl = end;
        char tk[5][16]; int nt = 0;
        for (char *q = p; q < nl && nt < 5; ) {
            while (q < nl && *q == ' ') q++;
            int k = 0;
            while (q < nl && *q != ' ' && k < 15) tk[nt][k++] = *q++;
            while (q < nl && *q != ' ') q++;
            if (k) { tk[nt][k] = 0; nt++; }
        }
        int b = 0; while (b < nt && tk[b][0] == '&') b++;
        if (nt - b >= 2) {
            int n = sprintf(out, "%s.%s", tk[b], tk[b + 1]);
            for (int i = 0; i < n; i++) if (out[i] >= 'A' && out[i] <= 'Z') out[i] += 32;
            out += n + 1; d->count++;
        }
        p = nl + 1;
    }
    free(f.data);
    return d;
}
struct dirent *readdir(struct m8_dir *d)
{
    if (!d || d->pos >= d->count) return 0;
    char *p = d->names;
    for (int i = 0; i < d->pos; i++) p += strlen(p) + 1;
    d->pos++;
    strncpy(d->ent.d_name, p, sizeof d->ent.d_name - 1);
    d->ent.d_type = 8;
    return &d->ent;
}
int closedir(struct m8_dir *d) { if (d) { free(d->names); free(d); } return 0; }
