#ifndef M8_SYS_RANDOM_H
#define M8_SYS_RANDOM_H
#include <sys/types.h>
ssize_t getrandom(void *buf, size_t len, unsigned int flags);
#endif
