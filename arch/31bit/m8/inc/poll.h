#ifndef M8_POLL_H
#define M8_POLL_H
struct pollfd { int fd; short events; short revents; };
typedef unsigned int nfds_t;
#define POLLIN 1
#define POLLPRI 2
#define POLLOUT 4
#define POLLERR 8
#define POLLHUP 16
#define POLLNVAL 32
int poll(struct pollfd *fds, nfds_t nfds, int timeout);
#endif
