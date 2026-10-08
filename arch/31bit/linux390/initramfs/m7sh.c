/* m7sh -- a tiny interactive /init for Linux/390 31-bit on VM/370+.
 * No C library: raw system calls (SVC n, arguments in r2-r6).
 * Commands: help echo ls cat mem ps uname uptime mount mkdir cd pwd dmesg
 *           write halt.  Mounts /proc and /sys, and a tmpfs on /tmp.     */
typedef unsigned long size_t;
typedef long ssize_t;

static long sc(long n, long a, long b, long c, long d, long e)
{
    register long r1 asm("1") = n;
    register long r2 asm("2") = a;
    register long r3 asm("3") = b;
    register long r4 asm("4") = c;
    register long r5 asm("5") = d;
    register long r6 asm("6") = e;
    asm volatile("svc 0" : "+d"(r2) : "d"(r1), "d"(r3), "d"(r4), "d"(r5), "d"(r6) : "memory", "cc");
    return r2;
}
#define SYS_exit 1
#define SYS_read 3
#define SYS_write 4
#define SYS_open 5
#define SYS_close 6
#define SYS_chdir 12
#define SYS_mount 21
#define SYS_mkdir 39
#define SYS_reboot 88
#define SYS_syslog 103
#define SYS_uname 122
#define SYS_getdents 141
#define SYS_getcwd 183

static size_t slen(const char *s) { size_t n = 0; while (s[n]) n++; return n; }
static int seq(const char *a, const char *b) { while (*a && *a == *b) a++, b++; return *a == *b; }
static void out(const char *s) { sc(SYS_write, 1, (long)s, slen(s), 0, 0); }
static void outn(const char *s, size_t n) { sc(SYS_write, 1, (long)s, n, 0, 0); }
static void num(long v) { char b[16]; int i = 15; b[i] = 0; if (!v) b[--i] = '0'; while (v) { b[--i] = '0' + v % 10; v /= 10; } out(b + i); }
static void err(const char *what, long rc) { out(what); out(": error "); num(-rc); out("\n"); }

static char buf[8192];
static int cat(const char *path, int quiet)
{
    long fd = sc(SYS_open, (long)path, 0, 0, 0, 0), n;
    if (fd < 0) { if (!quiet) err(path, fd); return -1; }
    while ((n = sc(SYS_read, fd, (long)buf, sizeof buf, 0, 0)) > 0) outn(buf, n);
    sc(SYS_close, fd, 0, 0, 0, 0);
    return 0;
}
static long readfile(const char *path, char *b, long max)
{
    long fd = sc(SYS_open, (long)path, 0, 0, 0, 0), n, t = 0;
    if (fd < 0) return fd;
    while (t < max - 1 && (n = sc(SYS_read, fd, (long)b + t, max - 1 - t, 0, 0)) > 0) t += n;
    sc(SYS_close, fd, 0, 0, 0, 0);
    b[t] = 0;
    return t;
}

struct ldirent { unsigned long d_ino, d_off; unsigned short d_reclen; char d_name[1]; };
static char dbuf[4096];
static void ls(const char *path, int procs)
{
    long fd = sc(SYS_open, (long)path, 0x10000 /* O_DIRECTORY */, 0, 0, 0), n;
    if (fd < 0) { err(path, fd); return; }
    if (procs) out("  PID  COMMAND\n");
    while ((n = sc(SYS_getdents, fd, (long)dbuf, sizeof dbuf, 0, 0)) > 0) {
        for (long off = 0; off < n; ) {
            struct ldirent *d = (struct ldirent *)(dbuf + off);
            char type = dbuf[off + d->d_reclen - 1];
            if (procs) {
                if (d->d_name[0] >= '0' && d->d_name[0] <= '9') {
                    char p[64], s[256]; int i = 0;
                    const char *a = "/proc/"; while (*a) p[i++] = *a++;
                    for (a = d->d_name; *a; ) p[i++] = *a++;
                    a = "/comm"; while (*a) p[i++] = *a++; p[i] = 0;
                    out("  "); out(d->d_name); out("  ");
                    if (readfile(p, s, sizeof s) > 0) out(s); else out("?\n");
                }
            } else if (!seq(d->d_name, ".") && !seq(d->d_name, "..")) {
                out(d->d_name); out(type == 4 ? "/\n" : "\n");
            }
            off += d->d_reclen;
        }
    }
    sc(SYS_close, fd, 0, 0, 0, 0);
}

static void uname(void)
{
    char u[6][65];
    long rc = sc(SYS_uname, (long)u, 0, 0, 0, 0);
    if (rc < 0) { err("uname", rc); return; }
    for (int i = 0; i < 5; i++) { out(u[i]); out(i < 4 ? " " : "\n"); }
}

static void help(void)
{
    out("m7sh commands:\n"
        "  ls [dir]       list a directory          cat file    show a file\n"
        "  mem            /proc/meminfo             ps          processes\n"
        "  uname          system name/version       uptime      seconds up\n"
        "  mount          mounted file systems      dmesg       kernel log\n"
        "  cpu            /proc/cpuinfo             echo text   echo it\n"
        "  mkdir dir      make a directory          cd dir      change dir\n"
        "  pwd            current directory         write f txt write a file\n"
        "  halt           stop Linux (CP: disabled wait)\n");
}

static char line[256];
static char *argv[8];
static int split(char *s)
{
    int n = 0;
    while (*s && n < 8) {
        while (*s == ' ' || *s == '\t') *s++ = 0;
        if (!*s) break;
        argv[n++] = s;
        while (*s && *s != ' ' && *s != '\t') s++;
    }
    return n;
}

void m7main(void);
asm(".globl _start\n_start:\n\tahi %r15,-96\n\txc 0(4,%r15),0(%r15)\n\tbrasl %r14,m7main\n\tsvc 1\n");
void m7main(void)
{
    sc(SYS_mkdir, (long)"/proc", 0555, 0, 0, 0);
    sc(SYS_mkdir, (long)"/sys", 0555, 0, 0, 0);
    sc(SYS_mkdir, (long)"/tmp", 01777, 0, 0, 0);
    sc(SYS_mount, (long)"proc", (long)"/proc", (long)"proc", 0, 0);
    sc(SYS_mount, (long)"sysfs", (long)"/sys", (long)"sysfs", 0, 0);
    sc(SYS_mount, (long)"tmpfs", (long)"/tmp", (long)"tmpfs", 0, 0);
    out("\nHELLO FROM LINUX/390 ON VM/370+ (M7)\n");
    uname();
    out("m7sh: type 'help' for commands\n");
    for (;;) {
        char cwd[128];
        if (sc(SYS_getcwd, (long)cwd, sizeof cwd, 0, 0, 0) > 0) out(cwd);
        out(" # ");
        long n = sc(SYS_read, 0, (long)line, sizeof line - 1, 0, 0);
        if (n <= 0) continue;
        line[n] = 0;
        for (long i = 0; i < n; i++) if (line[i] == '\n' || line[i] == '\r') line[i] = 0;
        int argc = split(line);
        if (!argc) continue;
        char *c = argv[0];
        if (seq(c, "help") || seq(c, "?")) help();
        else if (seq(c, "echo")) { for (int i = 1; i < argc; i++) { out(argv[i]); out(i + 1 < argc ? " " : ""); } out("\n"); }
        else if (seq(c, "ls")) ls(argc > 1 ? argv[1] : ".", 0);
        else if (seq(c, "cat")) { if (argc > 1) cat(argv[1], 0); }
        else if (seq(c, "mem")) cat("/proc/meminfo", 0);
        else if (seq(c, "cpu")) cat("/proc/cpuinfo", 0);
        else if (seq(c, "ps")) ls("/proc", 1);
        else if (seq(c, "uname")) uname();
        else if (seq(c, "uptime")) { out("up (s, idle s): "); cat("/proc/uptime", 0); }
        else if (seq(c, "mount")) cat("/proc/mounts", 0);
        else if (seq(c, "dmesg")) { long k = sc(SYS_syslog, 3, (long)buf, sizeof buf, 0, 0); if (k > 0) outn(buf, k); out("\n"); }
        else if (seq(c, "mkdir")) { if (argc > 1) { long rc = sc(SYS_mkdir, (long)argv[1], 0755, 0, 0, 0); if (rc < 0) err(argv[1], rc); } }
        else if (seq(c, "cd")) { long rc = sc(SYS_chdir, (long)(argc > 1 ? argv[1] : "/"), 0, 0, 0, 0); if (rc < 0) err("cd", rc); }
        else if (seq(c, "pwd")) { if (sc(SYS_getcwd, (long)cwd, sizeof cwd, 0, 0, 0) > 0) { out(cwd); out("\n"); } }
        else if (seq(c, "write")) {
            if (argc > 2) {
                long fd = sc(SYS_open, (long)argv[1], 01 | 0100 | 01000, 0644, 0, 0);
                if (fd < 0) err(argv[1], fd);
                else { for (int i = 2; i < argc; i++) { sc(SYS_write, fd, (long)argv[i], slen(argv[i]), 0, 0); sc(SYS_write, fd, (long)(i + 1 < argc ? " " : "\n"), 1, 0, 0); } sc(SYS_close, fd, 0, 0, 0, 0); }
            }
        }
        else if (seq(c, "halt")) { out("halting\n"); sc(SYS_reboot, 0xfee1dead, 672274793, 0xCDEF0123, 0, 0); }
        else { out(c); out(": not found (help lists the commands)\n"); }
    }
}
