/* setjmp.h -- VM/370plus M5f: newlib has no s390 setjmp, so cmsrt's
   entry31.s supplies setjmp/longjmp: R6-R15 saved (soft float, so no
   floating-point registers) in a jmp_buf of 16 words. */
#ifndef M5F_SETJMP_H
#define M5F_SETJMP_H
typedef int jmp_buf[16];
int setjmp(jmp_buf env);
void longjmp(jmp_buf env, int val);
#endif
