/* M8.2 utf.h -- the native CMS build of current cREXX runs in EBCDIC: one
   byte is one character.  This replaces sheredom's utf8.h (utf8/utf.h) with
   the same functions over single bytes; code points are byte values, and
   case follows the C library (EBCDIC-aware toupper/tolower). */
#ifndef SHEREDOM_UTF8_H_INCLUDED
#define SHEREDOM_UTF8_H_INCLUDED
#include <stddef.h>
#include <stdlib.h>
#include <string.h>
#include <ctype.h>
#include <stdint.h>
typedef int32_t utf8_int32_t;
#define utf8_restrict
#define utf8_null 0
#define UB(p) ((const unsigned char *)(p))

static __inline__ int utf8casecmp(const void *a, const void *b)
{
    const unsigned char *s = UB(a), *t = UB(b);
    for (;; s++, t++) {
        int x = tolower(*s), y = tolower(*t);
        if (x != y) return x < y ? -1 : 1;
        if (!x) return 0;
    }
}
static __inline__ int utf8ncasecmp(const void *a, const void *b, size_t n)
{
    const unsigned char *s = UB(a), *t = UB(b);
    for (; n; n--, s++, t++) {
        int x = tolower(*s), y = tolower(*t);
        if (x != y) return x < y ? -1 : 1;
        if (!x) return 0;
    }
    return 0;
}
static __inline__ void *utf8cat(void *d, const void *s) { return strcat((char *)d, (const char *)s); }
static __inline__ void *utf8chr(const void *s, utf8_int32_t c) { return strchr((const char *)s, (int)c); }
static __inline__ int utf8cmp(const void *a, const void *b) { return strcmp((const char *)a, (const char *)b); }
static __inline__ void *utf8cpy(void *d, const void *s) { return strcpy((char *)d, (const char *)s); }
static __inline__ size_t utf8cspn(const void *s, const void *r) { return strcspn((const char *)s, (const char *)r); }
static __inline__ void *utf8dup_ex(const void *src, void *(*af)(void *, size_t), void *ud)
{
    size_t n = strlen((const char *)src) + 1;
    char *d = af ? (char *)af(ud, n) : (char *)malloc(n);
    if (d) memcpy(d, src, n);
    return d;
}
static __inline__ void *utf8dup(const void *s) { return utf8dup_ex(s, 0, 0); }
static __inline__ size_t utf8nlen(const void *s, size_t n)
{
    const char *p = (const char *)s;
    size_t i = 0;
    while (i < n && p[i]) i++;
    return i;
}
static __inline__ size_t utf8len(const void *s) { return strlen((const char *)s); }
static __inline__ void *utf8ncat(void *d, const void *s, size_t n) { return strncat((char *)d, (const char *)s, n); }
static __inline__ int utf8ncmp(const void *a, const void *b, size_t n) { return strncmp((const char *)a, (const char *)b, n); }
static __inline__ void *utf8ncpy(void *d, const void *s, size_t n) { return strncpy((char *)d, (const char *)s, n); }
static __inline__ void *utf8ndup_ex(const void *src, size_t n, void *(*af)(void *, size_t), void *ud)
{
    size_t l = utf8nlen(src, n);
    char *d = af ? (char *)af(ud, l + 1) : (char *)malloc(l + 1);
    if (d) { memcpy(d, src, l); d[l] = 0; }
    return d;
}
static __inline__ void *utf8ndup(const void *s, size_t n) { return utf8ndup_ex(s, n, 0, 0); }
static __inline__ void *utf8pbrk(const void *s, const void *a) { return strpbrk((const char *)s, (const char *)a); }
static __inline__ void *utf8rchr(const void *s, int c) { return strrchr((const char *)s, c); }
static __inline__ size_t utf8size(const void *s) { return strlen((const char *)s) + 1; }
static __inline__ size_t utf8size_lazy(const void *s) { return strlen((const char *)s); }
static __inline__ size_t utf8nsize_lazy(const void *s, size_t n) { return utf8nlen(s, n); }
static __inline__ size_t utf8spn(const void *s, const void *a) { return strspn((const char *)s, (const char *)a); }
static __inline__ void *utf8str(const void *h, const void *n) { return strstr((const char *)h, (const char *)n); }
static __inline__ void *utf8casestr(const void *h, const void *n)
{
    const char *p = (const char *)h;
    size_t l = strlen((const char *)n);
    for (; *p; p++)
        if (!utf8ncasecmp(p, n, l)) return (void *)p;
    return l ? 0 : (void *)h;
}
static __inline__ void *utf8valid(const void *s) { (void)s; return 0; }
static __inline__ void *utf8nvalid(const void *s, size_t n) { (void)s; (void)n; return 0; }
static __inline__ void *utf8nvalid_count(const void *s, size_t n, size_t *chars)
{
    (void)s;
    *chars = n;
    return 0;
}
static __inline__ int utf8makevalid(void *s, const utf8_int32_t r) { (void)s; (void)r; return 0; }
static __inline__ void *utf8codepoint(const void *s, utf8_int32_t *cp)
{
    *cp = *UB(s);
    return (void *)(UB(s) + 1);
}
static __inline__ size_t utf8codepointcalcsize(const void *s) { (void)s; return 1; }
static __inline__ size_t utf8rcodepointcalcsize(const void *s) { (void)s; return 1; }
static __inline__ size_t utf8codepointsize(utf8_int32_t c) { (void)c; return 1; }
static __inline__ void *utf8catcodepoint(void *s, utf8_int32_t c, size_t n)
{
    if (n < 1) return 0;
    *(unsigned char *)s = (unsigned char)c;
    return (char *)s + 1;
}
static __inline__ int utf8islower(utf8_int32_t c) { return c >= 0 && c < 256 && islower((int)c); }
static __inline__ int utf8isupper(utf8_int32_t c) { return c >= 0 && c < 256 && isupper((int)c); }
static __inline__ utf8_int32_t utf8lwrcodepoint(utf8_int32_t c) { return (c >= 0 && c < 256) ? tolower((int)c) : c; }
static __inline__ utf8_int32_t utf8uprcodepoint(utf8_int32_t c) { return (c >= 0 && c < 256) ? toupper((int)c) : c; }
static __inline__ void utf8lwr(void *s)
{
    unsigned char *p = (unsigned char *)s;
    for (; *p; p++) *p = (unsigned char)tolower(*p);
}
static __inline__ void utf8upr(void *s)
{
    unsigned char *p = (unsigned char *)s;
    for (; *p; p++) *p = (unsigned char)toupper(*p);
}
static __inline__ void *utf8rcodepoint(const void *s, utf8_int32_t *cp)
{
    *cp = *UB(s);
    return (void *)(UB(s) - 1);
}
#undef UB
#endif
