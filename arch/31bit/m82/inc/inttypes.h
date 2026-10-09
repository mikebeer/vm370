/* M8.2: inttypes.h -- the formats crxlibc's printf understands */
#ifndef CRX_INTTYPES_H
#define CRX_INTTYPES_H
#include <stdint.h>
#define PRId8 "d"
#define PRId16 "d"
#define PRId32 "d"
#define PRId64 "lld"
#define PRIi32 "i"
#define PRIi64 "lli"
#define PRIu8 "u"
#define PRIu16 "u"
#define PRIu32 "u"
#define PRIu64 "llu"
#define PRIx32 "x"
#define PRIx64 "llx"
#define PRIX32 "X"
#define PRIX64 "llX"
#define PRIo64 "llo"
#define PRIdMAX "lld"
#define PRIuMAX "llu"
#define PRIdPTR "ld"
#define PRIuPTR "lu"
#define PRIxPTR "lx"
#define SCNd64 "lld"
#define SCNu64 "llu"
#define SCNx64 "llx"
intmax_t strtoimax(const char *s, char **e, int b);
uintmax_t strtoumax(const char *s, char **e, int b);
#endif
