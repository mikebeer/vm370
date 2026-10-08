#ifndef M8_SYS_TERMIOS_H
#define M8_SYS_TERMIOS_H
typedef unsigned int tcflag_t; typedef unsigned char cc_t; typedef unsigned int speed_t;
#define NCCS 32
struct termios { tcflag_t c_iflag, c_oflag, c_cflag, c_lflag; cc_t c_cc[NCCS]; };
struct winsize { unsigned short ws_row, ws_col, ws_xpixel, ws_ypixel; };
#define TCSANOW 0
#define ECHO 8
#define ICANON 2
#define TIOCGWINSZ 0x5413
int tcgetattr(int fd, struct termios *t);
int tcsetattr(int fd, int act, const struct termios *t);
#endif
