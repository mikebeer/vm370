/* mingw/compat.h -- force-included (-include) when building SDL Hercules
   with the MinGW-w64 GCC cross compiler using the _MSVC_ (Win32) code paths.
   Neutralises MSVC-only constructs.  Everything is guarded by __MINGW32__. */
#ifndef HERC_MINGW_COMPAT_H
#define HERC_MINGW_COMPAT_H
#if defined(__MINGW32__)

#define __pragma(x)                 /* MSVC __pragma(): ignore */
/* hatomic.h: use GCC __atomic builtins instead of MSVC _Interlocked*8 */
#define HAVE_ATOMIC_INTRINSICS  1

#define __assume(x)     ((x) ? (void)0 : __builtin_unreachable())

/* Pull in MinGW's own <time.h> (which declares clock_gettime/nanosleep
   via winpthreads' <pthread_time.h>) first, then rename Hercules' own
   Win32 implementations so they don't clash with MinGW's declarations. */
#include <sys/types.h>
#include <time.h>
#define clock_gettime   herc_clock_gettime
#define nanosleep       herc_nanosleep

#endif /* __MINGW32__ */
#endif /* HERC_MINGW_COMPAT_H */
