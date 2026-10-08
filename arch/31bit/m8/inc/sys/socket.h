#ifndef M8_SYS_SOCKET_H
#define M8_SYS_SOCKET_H
#include <sys/types.h>
typedef unsigned int socklen_t; typedef unsigned short sa_family_t;
struct sockaddr { sa_family_t sa_family; char sa_data[14]; };
struct sockaddr_storage { sa_family_t ss_family; char ss_pad[126]; };
#define AF_INET 2
#define AF_UNIX 1
#define AF_INET6 10
#define AF_UNSPEC 0
#define SOCK_STREAM 1
#define SOCK_DGRAM 2
#define SOL_SOCKET 1
#define SO_REUSEADDR 2
#define SHUT_RDWR 2
#define SHUT_WR 1
#define SHUT_RD 0
#define MSG_NOSIGNAL 0x4000
int socket(int, int, int); int bind(int, const struct sockaddr *, socklen_t);
int listen(int, int); int accept(int, struct sockaddr *, socklen_t *);
int connect(int, const struct sockaddr *, socklen_t);
ssize_t send(int, const void *, size_t, int); ssize_t recv(int, void *, size_t, int);
int setsockopt(int, int, int, const void *, socklen_t); int shutdown(int, int);
int socketpair(int, int, int, int[2]);
int getsockname(int, struct sockaddr *, socklen_t *);
#endif
