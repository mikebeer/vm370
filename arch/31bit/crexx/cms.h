//
// CMS Build Fixes
//

#ifndef CREXX_CMS_H
#define CREXX_CMS_H

#undef RX_INLINE
#define RX_INLINE static inline /* VM/370+: not extern -- 8-char names collide */

/* VM/370 has a 32 bit (or 24/32) architecture */
#define __32BIT__

/*
 * GCC in VM/370 can't seem to handle all the computed gotos - so use a
 * classic bytecode architecture
 */
#define NTHREADED

/*
 * VM/370 does not support UTF
 */
#define NUTF8


/* Date / tiem stubs */
struct timeval {
    long	tv_sec;		/* seconds */
    long	tv_usec;	/* and microseconds */
};
#define timezone 0
static char* tzname[] = {"",""};
static void tzset(void) {};
#define daylight 0

#ifndef SIZE_MAX
#define SIZE_MAX ((size_t)-1)    /* VM/370+: GCCLIB lacks it */
#endif

/* VM/370+: GCCLIB has no gettimeofday -- seconds from time() */
#include <time.h>
static int gettimeofday(struct timeval *tv, void *tz) {
    tv->tv_sec = (long) time(0);
    tv->tv_usec = 0;
    return 0;
}


/*
 * VM/370+ (M5g): GCCLIB has no snprintf/vsnprintf.  The original hack
 * mapped them to sprintf/vsprintf and so ignored the size -- and the
 * compiler sizes its buffers by calling vsnprintf with a small one first
 * (rxcpemit.c, rxcpast.c), so every long line overran the heap: the
 * DLMALLOC PANIC of native RXC.  Format into a 64 KB scratch buffer (one
 * per translation unit, from malloc on first use), copy what fits, and
 * return the full length as C99 does.
 */
#include <stdarg.h>
#include <string.h>
#include <stdlib.h>
static char *rx_snbuf = 0;
static int rx_vsnprintf(char *s, size_t sz, const char *fmt, va_list ap) {
    int n;
    size_t c;
    if (!rx_snbuf) rx_snbuf = malloc(65536);
    n = vsprintf(rx_snbuf, fmt, ap);
    if (sz) {
        c = (size_t) n < sz ? (size_t) n : sz - 1;
        memcpy(s, rx_snbuf, c);
        s[c] = 0;
    }
    return n;
}
static int rx_snprintf(char *s, size_t sz, const char *fmt, ...) {
    va_list ap;
    int n;
    va_start(ap, fmt);
    n = rx_vsnprintf(s, sz, fmt, ap);
    va_end(ap);
    return n;
}
#define snprintf rx_snprintf
#define vsnprintf rx_vsnprintf

#endif //CREXX_CMS_H
