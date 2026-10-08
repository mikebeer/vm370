#ifndef M8_NETINET_IN_H
#define M8_NETINET_IN_H
#include <sys/socket.h>
#include <stdint.h>
typedef uint32_t in_addr_t; typedef uint16_t in_port_t;
struct in_addr { in_addr_t s_addr; };
struct sockaddr_in { sa_family_t sin_family; in_port_t sin_port; struct in_addr sin_addr; char sin_zero[8]; };
#define INADDR_ANY 0
#define INADDR_LOOPBACK 0x7f000001
#define IPPROTO_TCP 6
/* big-endian machine */
#define htons(x) ((uint16_t)(x))
#define ntohs(x) ((uint16_t)(x))
#define htonl(x) ((uint32_t)(x))
#define ntohl(x) ((uint32_t)(x))
#endif
