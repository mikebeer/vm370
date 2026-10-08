/* M8 cmscompat.h -- forced into every cREXX source for CMS (VM/370+).
   CMS has no processes, signals beyond the basics, sockets, dynamic
   loading or threads: these declarations let the sources compile; the
   functions (cmscompat.c) fail with ENOSYS, and the single-threaded
   pthread calls succeed trivially. */
#ifndef CMSCOMPAT_H
#define CMSCOMPAT_H
#ifndef SA_RESTART
#define SA_RESTART 0x10000000
#endif
#ifndef SA_SIGINFO
#define SA_SIGINFO 4
#endif
#endif
