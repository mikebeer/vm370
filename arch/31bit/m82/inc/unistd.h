#ifndef CRX_UNISTD_H
#define CRX_UNISTD_H
#include <sys/types.h>
#define F_OK 0
#define X_OK 1
#define W_OK 2
#define R_OK 4
#define STDIN_FILENO 0
#define STDOUT_FILENO 1
#define STDERR_FILENO 2
int access(const char *path, int mode);
int unlink(const char *path);
int isatty(int fd);
char *getcwd(char *buf, size_t n);
int chdir(const char *path);
int rmdir(const char *path);
int close(int fd);
ssize_t read(int fd, void *b, size_t n);
ssize_t write(int fd, const void *b, size_t n);
unsigned sleep(unsigned s);
int usleep(unsigned long us);
pid_t getpid(void);
long sysconf(int n);
#define _SC_PAGESIZE 30
#define _SC_NPROCESSORS_ONLN 84
#endif
