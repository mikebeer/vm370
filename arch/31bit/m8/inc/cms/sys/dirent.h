/* M8: dirent for CMS (cmsrt.c): opendir("A") lists the files of the disk
   accessed as A, as "fn.ft" in lower case. */
#ifndef M8_SYS_DIRENT_H
#define M8_SYS_DIRENT_H
#include <sys/types.h>
struct dirent { unsigned int d_ino; unsigned char d_type; char d_name[20]; };
typedef struct m8_dir DIR;
#define DT_UNKNOWN 0
#define DT_REG 8
#define DT_DIR 4
DIR *opendir(const char *name);
struct dirent *readdir(DIR *d);
int closedir(DIR *d);
#endif
