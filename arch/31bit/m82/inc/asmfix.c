/* M8.2 ASMFIX C -- correct GCC380's assembler output before ASMAHL.
 *
 *     ASMFIX fn        reads FN ASSEMBLE A, writes it back corrected
 *
 * 1. 64-bit left shifts come out as SLDA, an arithmetic shift that keeps
 *    the sign bit and so loses the top bit of every unsigned result whose
 *    bit 0 should be set.  C's << is logical: SLDA -> SLDL.
 * 2. Calls to the 64-bit helpers (@@DIVDI3 & co., CRXLGCC C) are made
 *    through =A(@@...) with no EXTRN, which does not assemble: =V(@@...).
 */
#include <stdio.h>
#include <string.h>
#include <stdlib.h>

static char *lines[200000];
static const char *helpers[] = { "@@DIVDI3)", "@@UDIVDI)", "@@MODDI3)", "@@UMODDI)",
    "@@MULDI3)", "@@NEGDI2)", "@@CMPDI2)", "@@UCMPDI)", "@@FIXDFDI)", "@@FIXUNS)",
    "@@FLOATD)", "@@FIXDFD)", "@@ASHLDI)", "@@ASHRDI)", "@@LSHRDI)", 0 };

static int helper(const char *p)
{
    int i;
    for (i = 0; helpers[i]; i++)
        if (!strncmp(p, helpers[i], strlen(helpers[i]))) return 1;
    return 0;
}

int main(int argc, char *argv[])
{
    char in[40], out[40], buf[256];
    FILE *f;
    int n = 0, i, fixed = 0;
    if (argc < 2) { printf("ASMFIX fn\n"); return 24; }
    sprintf(in, "%s ASSEMBLE A", argv[1]);
    f = fopen(in, "r");
    if (!f) { printf("ASMFIX: %s not found\n", in); return 28; }
    while (fgets(buf, sizeof buf, f)) {
        char *p, *q;
        size_t l = strlen(buf);
        if (l && buf[l - 1] == '\n') buf[--l] = 0;
        if (buf[0] != '*') {
            p = strstr(buf, " SLDA ");
            if (p) { p[4] = 'L'; fixed++; }
            for (q = buf; (q = strstr(q, "=A(@@")) != 0; q += 5)
                if (helper(q + 3)) { q[1] = 'V'; fixed++; }
        }
        if (n >= (int)(sizeof lines / sizeof lines[0])) { printf("ASMFIX: too long\n"); return 20; }
        lines[n] = malloc(l + 1);
        strcpy(lines[n++], buf);
    }
    fclose(f);
    if (!fixed) return 0;
    sprintf(out, "%s ASSEMBLE A F 80", argv[1]);
    f = fopen(out, "w");
    if (!f) { printf("ASMFIX: cannot write %s\n", out); return 28; }
    for (i = 0; i < n; i++) { fputs(lines[i], f); fputc('\n', f); }
    fclose(f);
    printf("ASMFIX: %s: %d fixes\n", argv[1], fixed);
    return 0;
}
