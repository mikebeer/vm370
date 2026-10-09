/* M8.2 CRXRT C -- what current cREXX needs from C beyond GCCLIB31, for the
   native build on VM/370+ (GCC380, AMODE 31).  Compiled with CRXRT defined,
   so the names below are not redirected onto themselves.

   - printf family with C99 length modifiers (hh h l ll j z t L), the
     integer conversions done here, floating point handed to GCCLIB31;
   - snprintf/vsnprintf with real bounds;
   - strtoll/strtoull/strtoimax/strtoumax, llabs, strdup, strndup, strnlen,
     strcasecmp, strncasecmp, trunc, round, signbit;
   - CMS file names: "dir/fn.ft" -> "FN FT M" (dir = filemode letter, "."
     or none = search all disks), for fopen, remove, rename and stat;
   - opendir/readdir/closedir from LISTFILE * * m (EXEC.
   Everything here runs in the native character set (EBCDIC). */
#define CRXRT 1
int crxfline, crxflog[16];      /* prep.py M82TRACE debugging aid */
#include "crxcms.h"
#include <ctype.h>
#include <limits.h>
#include <sys/stat.h>
#include <dirent.h>

/* ------------------------------------------------------------------ */
/* formatted output                                                    */

typedef struct { char *buf; size_t cap; size_t len; } outb;

static void put(outb *o, char c)
{
    if (o->len + 1 < o->cap) o->buf[o->len] = c;
    o->len++;
}

static void puts_n(outb *o, const char *s, size_t n)
{
    size_t i;
    for (i = 0; i < n; i++) put(o, s[i]);
}

static void pad(outb *o, char c, int n)
{
    while (n-- > 0) put(o, c);
}

int crx_vsnprintf(char *s, size_t n, const char *fmt, va_list ap)
{
    outb o;
    const char *p;
    o.buf = s; o.cap = n; o.len = 0;
    for (p = fmt; *p; p++) {
        int left = 0, plus = 0, space = 0, alt = 0, zero = 0;
        int width = -1, prec = -1, len = 0;   /* len: 1 h, 2 hh, 3 l, 4 ll, 5 L */
        char conv;
        const char *start;
        if (*p != '%') { put(&o, *p); continue; }
        start = p;
        p++;
        for (;; p++) {
            if (*p == '-') left = 1;
            else if (*p == '+') plus = 1;
            else if (*p == ' ') space = 1;
            else if (*p == '#') alt = 1;
            else if (*p == '0') zero = 1;
            else break;
        }
        if (*p == '*') { width = va_arg(ap, int); if (width < 0) { left = 1; width = -width; } p++; }
        else if (isdigit((unsigned char)*p)) { width = 0; while (isdigit((unsigned char)*p)) width = width * 10 + (*p++ - '0'); }
        if (*p == '.') {
            p++;
            prec = 0;
            if (*p == '*') { prec = va_arg(ap, int); if (prec < 0) prec = -1; p++; }
            else while (isdigit((unsigned char)*p)) prec = prec * 10 + (*p++ - '0');
        }
        for (;; p++) {
            if (*p == 'h') len = (len == 1) ? 2 : 1;
            else if (*p == 'l') len = (len == 3) ? 4 : 3;
            else if (*p == 'q' || *p == 'j') len = 4;
            else if (*p == 'z' || *p == 't') len = 3;
            else if (*p == 'L') len = 5;
            else break;
        }
        conv = *p;
        if (!conv) break;
        if (conv == 'd' || conv == 'i' || conv == 'u' || conv == 'o' ||
            conv == 'x' || conv == 'X' || conv == 'p') {
            unsigned long long v;
            int neg = 0, base = 10, nd = 0, i, total;
            char dig[32], pre[3];
            int npre = 0;
            const char *ds = (conv == 'X') ? "0123456789ABCDEF" : "0123456789abcdef";
            if (conv == 'p') { v = (unsigned long)va_arg(ap, void *); base = 16; alt = 1; }
            else if (conv == 'd' || conv == 'i') {
                long long sv;
                if (len == 4) sv = va_arg(ap, long long);
                else if (len == 3) sv = va_arg(ap, long);
                else sv = va_arg(ap, int);
                if (len == 1) sv = (short)sv;
                if (len == 2) sv = (signed char)sv;
                if (sv < 0) { neg = 1; v = (unsigned long long)(-(sv + 1)) + 1; }
                else v = (unsigned long long)sv;
            } else {
                if (len == 4) v = va_arg(ap, unsigned long long);
                else if (len == 3) v = va_arg(ap, unsigned long);
                else v = va_arg(ap, unsigned int);
                if (len == 1) v = (unsigned short)v;
                if (len == 2) v = (unsigned char)v;
                if (conv == 'o') base = 8;
                if (conv == 'x' || conv == 'X') base = 16;
            }
            while (v) { dig[nd++] = ds[(int)(v % (unsigned)base)]; v /= (unsigned)base; }
            if (prec < 0) prec = 1; else zero = 0;
            if (neg) pre[npre++] = '-';
            else if (plus && (conv == 'd' || conv == 'i')) pre[npre++] = '+';
            else if (space && (conv == 'd' || conv == 'i')) pre[npre++] = ' ';
            if (alt && base == 16 && (nd || conv == 'p')) { pre[npre++] = '0'; pre[npre++] = (conv == 'X') ? 'X' : 'x'; }
            if (alt && base == 8 && prec <= nd) prec = nd + 1;
            total = npre + (prec > nd ? prec : nd);
            if (!left && !zero) pad(&o, ' ', width - total);
            puts_n(&o, pre, npre);
            if (!left && zero) pad(&o, '0', width - total);
            pad(&o, '0', prec - nd);
            for (i = nd - 1; i >= 0; i--) put(&o, dig[i]);
            if (left) pad(&o, ' ', width - total);
        } else if (conv == 'c') {
            char c = (char)va_arg(ap, int);
            if (!left) pad(&o, ' ', width - 1);
            put(&o, c);
            if (left) pad(&o, ' ', width - 1);
        } else if (conv == 's') {
            const char *str = va_arg(ap, const char *);
            size_t sl;
            if (!str) str = "(null)";
            if (prec >= 0) { sl = 0; while ((int)sl < prec && str[sl]) sl++; }
            else sl = strlen(str);
            if (!left) pad(&o, ' ', width - (int)sl);
            puts_n(&o, str, sl);
            if (left) pad(&o, ' ', width - (int)sl);
        } else if (conv == 'n') {
            if (len == 4) *va_arg(ap, long long *) = o.len;
            else *va_arg(ap, int *) = (int)o.len;
        } else if (conv == 'e' || conv == 'E' || conv == 'f' || conv == 'F' ||
                   conv == 'g' || conv == 'G' || conv == 'a' || conv == 'A') {
            /* one conversion, length modifier dropped, to GCCLIB31 */
            char f[32], tmp[512];
            int k = 0, m;
            double d = va_arg(ap, double);
            const char *q;
            for (q = start; q < p && k < 24; q++)
                if (*q != 'L' && *q != 'l' && *q != 'q' && *q != 'h' &&
                    *q != 'j' && *q != 'z' && *q != 't' && *q != '*') f[k++] = *q;
            if (width >= 0 && strchr(start, '*') && strchr(start, '*') < p) {
                /* re-insert '*' widths as numbers */
                k = 0;
                f[k++] = '%';
                if (left) f[k++] = '-';
                if (plus) f[k++] = '+';
                if (space) f[k++] = ' ';
                if (alt) f[k++] = '#';
                if (zero) f[k++] = '0';
                k += sprintf(f + k, "%d", width > 400 ? 400 : width);
                if (prec >= 0) k += sprintf(f + k, ".%d", prec > 100 ? 100 : prec);
            }
            f[k++] = (conv == 'F') ? 'f' : (conv == 'a' ? 'e' : (conv == 'A' ? 'E' : conv));
            f[k] = 0;
            m = sprintf(tmp, f, d);
            if (m > 0) puts_n(&o, tmp, (size_t)m);
        } else if (conv == '%') {
            put(&o, '%');
        } else {
            /* unknown: copy it */
            puts_n(&o, start, (size_t)(p - start + 1));
        }
    }
    if (o.cap) o.buf[o.len < o.cap ? o.len : o.cap - 1] = 0;
    return (int)o.len;
}

int crx_snprintf(char *s, size_t n, const char *fmt, ...)
{
    va_list ap; int r;
    va_start(ap, fmt);
    r = crx_vsnprintf(s, n, fmt, ap);
    va_end(ap);
    return r;
}

int crx_vsprintf(char *s, const char *fmt, va_list ap)
{
    return crx_vsnprintf(s, (size_t)INT_MAX, fmt, ap);
}

int crx_sprintf(char *s, const char *fmt, ...)
{
    va_list ap; int r;
    va_start(ap, fmt);
    r = crx_vsnprintf(s, (size_t)INT_MAX, fmt, ap);
    va_end(ap);
    return r;
}

int crx_vfprintf(FILE *f, const char *fmt, va_list ap)
{
    char local[512], *b = local;
    va_list cp;
    int n;
    va_copy(cp, ap);
    n = crx_vsnprintf(local, sizeof local, fmt, cp);
    if (n < 0) return n;
    if ((size_t)n >= sizeof local) {
        b = malloc((size_t)n + 1);
        if (!b) return -1;
        crx_vsnprintf(b, (size_t)n + 1, fmt, ap);
    }
    if (n && fwrite(b, 1, (size_t)n, f) != (size_t)n) n = -1;
    if (b != local) free(b);
    return n;
}

int crx_fprintf(FILE *f, const char *fmt, ...)
{
    va_list ap; int r;
    va_start(ap, fmt);
    r = crx_vfprintf(f, fmt, ap);
    va_end(ap);
    return r;
}

int crx_printf(const char *fmt, ...)
{
    va_list ap; int r;
    va_start(ap, fmt);
    r = crx_vfprintf(stdout, fmt, ap);
    va_end(ap);
    return r;
}

ptrdiff_t crexx_host_write_stderr(const char *bytes, size_t length)
{
    return (ptrdiff_t)fwrite(bytes, 1, length, stderr);
}

/* ------------------------------------------------------------------ */
/* numbers and strings                                                 */

static int digval(int c)
{
    static const char ds[] = "0123456789abcdefghijklmnopqrstuvwxyz";
    const char *q;
    if (!c) return 99;
    q = strchr(ds, tolower(c));
    return q ? (int)(q - ds) : 99;
}

unsigned long long strtoull(const char *s, char **e, int b)
{
    const char *p = s;
    unsigned long long v = 0;
    int neg = 0, any = 0, over = 0, d;
    while (isspace((unsigned char)*p)) p++;
    if (*p == '+' || *p == '-') { neg = (*p == '-'); p++; }
    if ((b == 0 || b == 16) && p[0] == '0' && (p[1] == 'x' || p[1] == 'X') && digval((unsigned char)p[2]) < 16) { p += 2; b = 16; }
    else if (b == 0) b = (p[0] == '0') ? 8 : 10;
    while ((d = digval((unsigned char)*p)) < b) {
        if (v > (~0ULL - (unsigned)d) / (unsigned)b) over = 1;
        v = v * (unsigned)b + (unsigned)d;
        p++; any = 1;
    }
    if (e) *e = (char *)(any ? p : s);
    if (over) { errno = ERANGE; return ~0ULL; }
    return neg ? (unsigned long long)(-(long long)v) : v;
}

long long strtoll(const char *s, char **e, int b)
{
    const char *p = s;
    unsigned long long v;
    int neg = 0;
    char *end;
    while (isspace((unsigned char)*p)) p++;
    if (*p == '-') neg = 1;
    if (*p == '+' || *p == '-') p++;
    if (*p == '+' || *p == '-') { if (e) *e = (char *)s; return 0; }
    errno = 0;
    v = strtoull(p, &end, b);
    if (e) *e = (end == p) ? (char *)s : end;
    if (errno == ERANGE || (!neg && v > 9223372036854775807ULL)) { errno = ERANGE; return neg ? (-9223372036854775807LL - 1) : 9223372036854775807LL; }
    if (neg && v > 9223372036854775808ULL) { errno = ERANGE; return -9223372036854775807LL - 1; }
    return neg ? (long long)(0 - v) : (long long)v;
}

intmax_t strtoimax(const char *s, char **e, int b) { return strtoll(s, e, b); }
uintmax_t strtoumax(const char *s, char **e, int b) { return strtoull(s, e, b); }
long long llabs(long long v) { return v < 0 ? -v : v; }

char *strdup(const char *s)
{
    size_t n = strlen(s) + 1;
    char *d = malloc(n);
    if (d) memcpy(d, s, n);
    return d;
}

size_t strnlen(const char *s, size_t n)
{
    size_t i = 0;
    while (i < n && s[i]) i++;
    return i;
}

char *strndup(const char *s, size_t n)
{
    size_t l = strnlen(s, n);
    char *d = malloc(l + 1);
    if (d) { memcpy(d, s, l); d[l] = 0; }
    return d;
}

int strncasecmp(const char *a, const char *b, size_t n)
{
    while (n--) {
        int x = tolower((unsigned char)*a++), y = tolower((unsigned char)*b++);
        if (x != y) return x - y;
        if (!x) break;
    }
    return 0;
}

int strcasecmp(const char *a, const char *b) { return strncasecmp(a, b, (size_t)-1); }

int crx_signbit(double x) { return (*(unsigned char *)&x & 0x80) != 0; }

double trunc(double x) { return x < 0 ? ceil(x) : floor(x); }
double round(double x) { return x < 0 ? ceil(x - 0.5) : floor(x + 0.5); }

/* ------------------------------------------------------------------ */
/* CMS file names                                                      */

/* "dir/fn.ft" -> "FN FT M"; a name with a blank is a CMS fileid already.
   Returns 0, or -1 (EINVAL) if it does not fit CMS. */
static int cmsname(const char *path, char *out, size_t cap)
{
    const char *slash, *base, *dot;
    char fn[9], ft[9], fm[3];
    size_t nf, nt, i;
    if (strchr(path, ' ')) {
        if (strlen(path) >= cap) return -1;
        strcpy(out, path);
        return 0;
    }
    while (path[0] == '.' && path[1] == '/') path += 2;
    slash = strrchr(path, '/');
    fm[0] = 0;
    if (slash) {
        size_t dl = (size_t)(slash - path);
        if (dl == 1 && path[0] != '.') { fm[0] = path[0]; fm[1] = 0; }
        else if (dl == 2 && isdigit((unsigned char)path[1])) { fm[0] = path[0]; fm[1] = path[1]; fm[2] = 0; }
        else if (!(dl == 1 && path[0] == '.') && dl != 0) return -1;
        base = slash + 1;
    } else base = path;
    dot = strchr(base, '.');
    nf = dot ? (size_t)(dot - base) : strlen(base);
    if (nf == 0 || nf > 8) return -1;
    for (i = 0; i < nf; i++) fn[i] = (char)toupper((unsigned char)base[i]);
    fn[nf] = 0;
    if (dot) {
        const char *t = dot + 1, *d2 = strchr(t, '.');
        nt = d2 ? (size_t)(d2 - t) : strlen(t);
        if (nt == 0 || nt > 8) return -1;
        for (i = 0; i < nt; i++) ft[i] = (char)toupper((unsigned char)t[i]);
        ft[nt] = 0;
        if (d2 && !fm[0] && d2[1] && strlen(d2 + 1) <= 2) {
            fm[0] = d2[1]; fm[1] = d2[2]; fm[2] = 0;
        }
    } else strcpy(ft, "FILE");
    for (i = 0; fm[i]; i++) fm[i] = (char)toupper((unsigned char)fm[i]);
    if (strlen(fn) + strlen(ft) + strlen(fm) + 3 > cap) return -1;
    sprintf(out, fm[0] ? "%s %s %s" : "%s %s", fn, ft, fm);
    return 0;
}

#undef fopen
FILE *crx_fopen(const char *path, const char *mode)
{
    char id[32];
    if (!path || cmsname(path, id, sizeof id)) { errno = EINVAL; return NULL; }
    return fopen(id, mode);
}

int crx_remove(const char *path)
{
    char id[32];
    if (!path || cmsname(path, id, sizeof id)) { errno = EINVAL; return -1; }
    return remove(id);
}

int crx_rename(const char *from, const char *to)
{
    char a[32], b[32];
    if (cmsname(from, a, sizeof a) || cmsname(to, b, sizeof b)) { errno = EINVAL; return -1; }
    return rename(a, b);
}

int stat(const char *path, struct stat *st)
{
    FILE *f = crx_fopen(path, "rb");
    if (!f) { errno = ENOENT; return -1; }
    fclose(f);
    memset(st, 0, sizeof *st);
    st->st_mode = S_IFREG | 0444;
    return 0;
}

int fstat(int fd, struct stat *st)
{
    (void)fd;
    memset(st, 0, sizeof *st);
    st->st_mode = S_IFREG;
    return 0;
}

/* ------------------------------------------------------------------ */
/* directories: a directory is a filemode letter ("a", "a/", "." = A)  */

struct m8_dir { char *names; int count, pos; struct dirent ent; };

DIR *opendir(const char *name)
{
    char mode = 'A', cmd[40], line[256];
    FILE *f;
    struct m8_dir *d = calloc(1, sizeof *d);
    size_t cap = 4096, used = 0;
    if (!d) { errno = ENOMEM; return 0; }
    if (name && name[0] && name[0] != '.') mode = (char)toupper((unsigned char)name[0]);
    d->names = malloc(cap);
    if (!d->names) { free(d); errno = ENOMEM; return 0; }
    sprintf(cmd, "LISTFILE * * %c ( EXEC", mode);
    if (system(cmd)) return d;                       /* no files: empty */
    f = fopen("CMS EXEC A1", "r");
    if (!f) return d;
    while (fgets(line, sizeof line, f)) {
        char *tk[6], *q = line;
        int nt = 0, b = 0, n, i;
        while (nt < 6) {
            while (*q == ' ' || *q == '\n') q++;
            if (!*q) break;
            tk[nt++] = q;
            while (*q && *q != ' ' && *q != '\n') q++;
            if (*q) *q++ = 0;
        }
        while (b < nt && tk[b][0] == '&') b++;
        if (nt - b < 2) continue;
        if (used + strlen(tk[b]) + strlen(tk[b + 1]) + 3 > cap) {
            char *nb = realloc(d->names, cap * 2);
            if (!nb) break;
            d->names = nb; cap *= 2;
        }
        n = sprintf(d->names + used, "%s.%s", tk[b], tk[b + 1]);
        for (i = 0; i < n; i++) d->names[used + i] = (char)tolower((unsigned char)d->names[used + i]);
        used += (size_t)n + 1;
        d->count++;
    }
    fclose(f);
    return d;
}

struct dirent *readdir(DIR *d)
{
    char *p;
    int i;
    if (!d || d->pos >= d->count) return 0;
    p = d->names;
    for (i = 0; i < d->pos; i++) p += strlen(p) + 1;
    d->pos++;
    strncpy(d->ent.d_name, p, sizeof d->ent.d_name - 1);
    d->ent.d_name[sizeof d->ent.d_name - 1] = 0;
    d->ent.d_type = DT_REG;
    return &d->ent;
}

int closedir(DIR *d)
{
    if (d) { free(d->names); free(d); }
    return 0;
}

/* GCC380 copies some structures with bcopy() */
void bcopy(const void *s, void *d, size_t n)
{
    memmove(d, s, n);
}
