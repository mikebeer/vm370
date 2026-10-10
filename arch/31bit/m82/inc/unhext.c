/* UNHEXT fn ft fm outfn outft outfm -- M8.2: a hex text file (from the
   PC, via the card reader) back to a CMS text file of variable-length
   records.  The PC sends EBCDIC bytes with X'15' (NL) at each line end;
   in text mode NL ends a record, so lines of any length (up to 4096)
   arrive whole -- READCARD would cut them at 80 columns. */
#include <stdio.h>
#include <string.h>

static int hv(int c)
{
    if (c >= '0' && c <= '9') return c - '0';
    if (c >= 'A' && c <= 'F') return c - 'A' + 10;
    if (c >= 'a' && c <= 'f') return c - 'a' + 10;
    return -1;
}

int main(int argc, char **argv)
{
    char in[64], out[64];
    FILE *f, *o;
    int c, h = -1, v;
    long n = 0, lines = 0;
    if (argc < 7) {
        printf("usage: UNHEXT fn ft fm outfn outft outfm\n");
        return 24;
    }
    sprintf(in, "%s %s %s", argv[1], argv[2], argv[3]);
    sprintf(out, "%s %s %s V 4096", argv[4], argv[5], argv[6]);
    f = fopen(in, "r");
    if (!f) { printf("UNHEXT: cannot open %s\n", in); return 28; }
    o = fopen(out, "w");
    if (!o) { printf("UNHEXT: cannot open %s\n", out); return 28; }
    while ((c = fgetc(f)) != EOF) {
        v = hv(c);
        if (v < 0) continue;
        if (h < 0) { h = v; continue; }
        c = h * 16 + v;
        h = -1;
        fputc(c, o);
        n++;
        if (c == '\n') lines++;
    }
    fclose(f);
    if (fclose(o)) { printf("UNHEXT: write error\n"); return 12; }
    printf("UNHEXT: %ld bytes, %ld lines to %s %s %s\n", n, lines,
           argv[4], argv[5], argv[6]);
    return 0;
}
