/* cmstz.h -- VM/370plus: newlib's tz variables under their POSIX names,
   for cREXX's clock services (TIME, DATE) on CMS. CMS has no TZ: UTC. */
#ifndef CMSTZ_H
#define CMSTZ_H
#include <time.h>
extern long _timezone;
extern char *_tzname[2];
#ifndef timezone
#define timezone _timezone
#endif
#ifndef tzname
#define tzname _tzname
#endif
#endif
