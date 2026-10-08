/* UNHEX fn ft fm  out-fn out-ft out-fm : a hex text file (from the PC, via
   the card reader) back to its exact binary bytes -- RXBIN modules cannot
   travel as 80-byte cards (padding breaks the loader). M8. */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
static int hv(int c) { return c >= '0' && c <= '9' ? c - '0' : c >= 'A' && c <= 'F' ? c - 'A' + 10 : c >= 'a' && c <= 'f' ? c - 'a' + 10 : -1; }
int main(int argc, char **argv)
{
    char in[64], out[64];
    if (argc < 7) { printf("usage: unhex fn ft fm outfn outft outfm\n"); return 8; }
    sprintf(in, "%s %s %s", argv[1], argv[2], argv[3]);
    sprintf(out, "%s %s %s", argv[4], argv[5], argv[6]);
    FILE *f = fopen(in, "r"); if (!f) { printf("cannot open %s\n", in); return 28; }
    FILE *o = fopen(out, "wb"); if (!o) { printf("cannot open %s\n", out); return 28; }
    int c, h = -1; long n = 0;
    while ((c = fgetc(f)) != EOF) {
        int v = hv(c); if (v < 0) continue;
        if (h < 0) h = v; else { fputc(h * 16 + v, o); n++; h = -1; }
    }
    fclose(f); if (fclose(o)) { printf("write error\n"); return 12; }
    printf("%ld bytes to %s\n", n, out);
    return 0;
}
