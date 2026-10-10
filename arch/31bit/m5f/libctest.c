/* VM/370plus M5f: newlib on CMS in AMODE 31 -- printf, malloc above 16 MB,
   floating point (soft-fp), files. */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>
#include <time.h>

int main(int argc, char **argv)
{
    printf("LIBCTEST: %s, %d argument(s):", argv[0], argc - 1);
    for (int i = 1; i < argc; i++) printf(" [%s]", argv[i]);
    printf("\n");

    size_t big = 30u << 20;
    char *p = malloc(big);
    printf("malloc(30 MB) = %p (%s)\n", (void *)p,
           (unsigned long)p >= 0x01000000UL ? "above the line" : "below the line");
    if (!p) return 8;
    memset(p, 0x5A, big);
    unsigned long sum = 0;
    for (size_t i = 0; i < big; i += 4096) sum += (unsigned char)p[i];
    printf("touched %u pages, sum %lu\n", (unsigned)(big / 4096), sum);
    free(p);

    double x = 2.0;
    printf("sqrt(2) = %.12f, pi = %.10f, 1e300*1e5 = %g, 22/7 = %f\n",
           sqrt(x), 4 * atan(1.0), 1e300 * 1e5, 22.0 / 7);

    FILE *f = fopen("libctest.output.a", "w");
    if (!f) { printf("fopen for write failed\n"); return 8; }
    for (int i = 1; i <= 5; i++) fprintf(f, "line %d of %d: %s\n", i, 5, i == 3 ? "" : "text");
    fprintf(f, "\n");
    fclose(f);
    f = fopen("libctest.output", "r");
    if (!f) { printf("fopen for read failed\n"); return 8; }
    char buf[100]; int n = 0;
    while (fgets(buf, sizeof buf, f)) { n++; printf("  read %d: %s", n, buf); }
    fclose(f);
    printf("read %d lines back\n", n);

    f = fopen("profile exec", "r");
    if (f) { fgets(buf, sizeof buf, f); printf("PROFILE EXEC line 1: %s", buf); fclose(f); }
    time_t t = time(0);
    printf("time(): %s", ctime(&t));
    printf("LIBCTEST OK\n");
    return 0;
}
