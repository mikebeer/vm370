/* Pre-include for building the SDL telnet package with MinGW-w64 */
#include <winsock2.h>
#include <windows.h>
#include <stdio.h>
#include <stdarg.h>
#include <stdlib.h>
#include <errno.h>
#include <string.h>
#include <stdbool.h>
#include <stdint.h>
#define close(s) closesocket(s)
