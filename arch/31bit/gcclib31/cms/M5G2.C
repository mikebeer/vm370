/* M5G2 -- GCCLIB31 test (VM/370plus M5g): AMODE 31, heap above 16 MB,  */
/* stack bins over 16 KB, file I/O and a command from heap buffers.  */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

static int deep(int n)
{
    char big[20000];
    memset(big, n, sizeof big);
    if (n == 10)
        printf("M5G2: 20000-byte frame at %08lX\n", (unsigned long)big);
    if (n == 0) return big[100];
    return deep(n - 1) + big[19999];
}

int main(int argc, char *argv[])
{
    char *p, *q, *s;
    char local[16];
    FILE *f;
    int i, n;
    unsigned long a;

    printf("M5G2: main %08lX, stack %08lX\n", (unsigned long)main,
           (unsigned long)local);
    for (i = 0; i < argc; i++) printf("M5G2: argv[%d] = %s\n", i, argv[i]);
    p = malloc(30000000);
    a = (unsigned long)p;
    printf("M5G2: malloc(30000000) = %08lX %s\n", a,
           a >= 0x1000000UL ? "ABOVE 16MB" : "below 16MB");
    if (!p) return 8;
    memset(p, 0x5A, 30000000);
    printf("M5G2: p[0] %02X p[29999999] %02X\n", (unsigned char)p[0],
           (unsigned char)p[29999999]);
    q = malloc(20000000);
    if (!q) return 9;
    memset(q, 0, 20000000);
    memcpy(q, p + 5000000, 20000000);
    printf("M5G2: memcpy 20000000 q=%08lX q[0] %02X q[16773120] %02X"
           " q[19999999] %02X\n", (unsigned long)q, (unsigned char)q[0],
           (unsigned char)q[16773120], (unsigned char)q[19999999]);
    q[19999999] = 1;
    printf("M5G2: memcmp 20000000 %d (-1 expected)\n",
           memcmp(q, p, 20000000));
    for (i = 0; i < 20000; i++) {
        s = malloc(100 + i % 400);
        if (!s) { printf("M5G2: small malloc %d failed\n", i); return 12; }
        memset(s, i, 100);
    }
    printf("M5G2: 20000 small blocks, last %08lX\n", (unsigned long)s);
    printf("M5G2: deep(10) = %d (55 expected)\n", deep(10));
    s = malloc(200);
    f = fopen("M5G2 DATA A", "w");
    if (!f) { printf("M5G2: fopen w failed\n"); return 16; }
    for (i = 0; i < 50; i++) {
        sprintf(s, "LINE %d OF M5G2 FROM %08lX", i, (unsigned long)s);
        fputs(s, f);
        fputc('\n', f);
    }
    fclose(f);
    f = fopen("M5G2 DATA A", "r");
    if (!f) { printf("M5G2: fopen r failed\n"); return 20; }
    n = 0;
    while (fgets(s, 200, f)) n++;
    fclose(f);
    printf("M5G2: read back %d lines, last: %s", n, s);
    strcpy(s, "LISTFILE M5G2 * A");
    i = system(s);
    printf("M5G2: system() from %08lX rc %d\n", (unsigned long)s, i);
    free(p);
    free(q);
    if (argc > 1 && !strcmp(argv[1], "EXIT")) {
        printf("M5G2: exit(3)\n");
        exit(3);
    }
    printf("M5G2 OK\n");
    return 0;
}
