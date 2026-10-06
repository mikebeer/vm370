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


/* Shocking hack ... todo - need to replace with fixed buffer logig for cms */
#define snprintf(s,sz,...) sprintf(s,__VA_ARGS__)
#define vsnprintf(s,sz,...) vsprintf(s,__VA_ARGS__)

#endif //CREXX_CMS_H
