#ifndef M8_SYS_DIRENT_H
#define M8_SYS_DIRENT_H
#include <sys/types.h>
struct dirent { ino_t d_ino; unsigned char d_type; char d_name[256]; };
typedef struct m8_dir DIR;
#define DT_UNKNOWN 0
#define DT_REG 8
#define DT_DIR 4
DIR *opendir(const char *name);
struct dirent *readdir(DIR *d);
int closedir(DIR *d);
#endif
