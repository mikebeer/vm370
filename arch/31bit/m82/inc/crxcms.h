/* M8.2 crxcms.h -- included first into every current-cREXX source built
   natively on VM/370+ (GCC380 + GCCLIB31).  Declares what GCCLIB31 lacks;
   CRXRT C implements it. */
#ifndef CRXCMS_H
#define CRXCMS_H
#define __32BIT__ 1
/* the single-threaded CMS configuration of current cREXX */
#define CREXX_CMS_GCC 1
#define CREXX_VM_SINGLE_THREADED 1
#define NTHREADED 1
#define CREXX_VM_HANDLER_PANEL 1   /* handlers out of line: run() stays small */
#define MANUAL_PLUGIN_LINK 1
#define CREXX_VM_STATIC_ONLY 1
#define CREXX_VM_NO_SOCKETS 1
#define CREXX_VM_NO_CLOCK 1
#define CREXX_VM_PORTABLE_ALLOC 1
#define CREXX_VM_COMPACT 1
#define NUTF8 1
#define RXVM_MEMORY_SLAB_SIZE 4096
#define RXVM_MEMORY_MAX_STANDARD_SIZE 2048
#include <stddef.h>
#include <stdarg.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <errno.h>
#include <math.h>
#include <stdint.h>

#ifndef va_copy
#define va_copy(d, s) ((d) = (s))
#endif
#ifndef EILSEQ
#define EILSEQ 420
#endif
#ifndef SIZE_MAX
#define SIZE_MAX 4294967295UL
#endif

/* stdio: GCCLIB31's printf knows neither ll, z, j, t, hh nor snprintf.
   Every formatting call goes through crx_vsnprintf. */
int crx_vsnprintf(char *s, size_t n, const char *fmt, va_list ap);
int crx_snprintf(char *s, size_t n, const char *fmt, ...);
int crx_sprintf(char *s, const char *fmt, ...);
int crx_vsprintf(char *s, const char *fmt, va_list ap);
int crx_vfprintf(FILE *f, const char *fmt, va_list ap);
int crx_fprintf(FILE *f, const char *fmt, ...);
int crx_printf(const char *fmt, ...);
#ifndef CRXRT
#define vsnprintf crx_vsnprintf
#define snprintf crx_snprintf
#define sprintf crx_sprintf
#define vsprintf crx_vsprintf
#define vfprintf crx_vfprintf
#define fprintf crx_fprintf
#define printf crx_printf
#endif

/* stdlib / string */
long long strtoll(const char *s, char **e, int b);
unsigned long long strtoull(const char *s, char **e, int b);
long long llabs(long long v);
char *strdup(const char *s);
char *strndup(const char *s, size_t n);
size_t strnlen(const char *s, size_t n);
int strcasecmp(const char *a, const char *b);
int strncasecmp(const char *a, const char *b, size_t n);

/* math: hexadecimal floating point has no NaN and no infinity */
#define isnan(x) 0
#define isinf(x) 0
#define isfinite(x) 1
#define signbit(x) crx_signbit(x)
int crx_signbit(double x);
double trunc(double x);
double round(double x);
#ifndef INFINITY
#define INFINITY HUGE_VAL
#endif
#ifndef NAN
#define NAN 0.0
#endif

/* CMS file names: cREXX says "dir/fn.ft", GCCLIB31 wants "FN FT FM" */
FILE *crx_fopen(const char *path, const char *mode);
int crx_remove(const char *path);
int crx_rename(const char *from, const char *to);
#ifndef CRXRT
#define fopen crx_fopen
#define remove crx_remove
#define rename crx_rename
#endif
ptrdiff_t crexx_host_write_stderr(const char *bytes, size_t length);

/* funopen: a FILE with cookie functions (platform.c's codec, unused when
   the native charset is the file charset) */
FILE *funopen(const void *cookie, int (*rd)(void *, char *, int),
              int (*wr)(void *, const char *, int),
              long (*sk)(void *, long, int), int (*cl)(void *));
#endif
