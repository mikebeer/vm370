#ifndef M8_ARPA_INET_H
#define M8_ARPA_INET_H
#include <netinet/in.h>
int inet_pton(int af, const char *src, void *dst);
const char *inet_ntop(int af, const void *src, char *dst, socklen_t size);
in_addr_t inet_addr(const char *cp);
#endif
