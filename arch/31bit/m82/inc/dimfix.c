/* DIMFIX fn -- M8.2: repair GCC380's 64-bit loads in fn ASSEMBLE A.

   GCC380 loads a 64-bit value through a pointer as

            L     2,0(2)          high word -- overwrites the pointer
            L     3,4+0(2)        low word through the clobbered register

   when the register pair it picks starts with the pointer's own register.
   Swapping the two is no answer when the address also uses the second
   register (8(2,3)), so DIMFIX loads the pair with LM, which forms the
   address once:  LM 2,3,0(2)  -- or, with an index register,
   LA 3,8(2,3) then LM 2,3,0(3).  It writes fn ASSEMBF A, then replaces
   fn ASSEMBLE A with it.

   It reads and writes with FSREAD/FSWRITE in sequence (record number 0)
   rather than GCCLIB stdio, which stops at 32,768 records. */
#include <stdio.h>
#include <string.h>
#include <cmssys.h>

static char ibuf[81], obuf[81], prev[81];
static CMSFILE in, out;

/* the register number of a 1- or 2-digit decimal operand, or -1 */
static int regno(const char *s, int *len)
{
    int r = 0, n = 0;
    while (s[n] >= '0' && s[n] <= '9' && n < 2)
        r = r * 10 + (s[n++] - '0');
    *len = n;
    return n ? r : -1;
}

/* "         L     R,ADDR" -> R, and the address text; else -1 */
static int is_load(const char *l, char *addr)
{
    int r, n, k = 0;
    const char *p;
    if (strncmp(l, "         L     ", 15) != 0) return -1;
    r = regno(l + 15, &n);
    if (r < 0 || l[15 + n] != ',') return -1;
    p = l + 16 + n;
    while (*p && *p != ' ' && k < 40) addr[k++] = *p++;
    addr[k] = 0;
    return r;
}

/* does the address use register r: "(r)", "(x,r)" or "(r,x)" */
static int uses(const char *addr, int r)
{
    char a[8], b[8], c[8];
    sprintf(a, "(%d)", r);
    sprintf(b, ",%d)", r);
    sprintf(c, "(%d,", r);
    return strstr(addr, a) || strstr(addr, b) || strstr(addr, c);
}

/* blank-fill a sprintf'd card to 80 columns */
static void pad80(char *l)
{
    int k = strlen(l);
    while (k < 80) l[k++] = ' ';
    l[80] = 0;
}

static int nout;

static int put(const char *l)
{
    memcpy(obuf, l, 80);
    /* record 1 first, then 0: the next one */
    return CMSfileWrite(&out, nout++ ? 0 : 1, 80);
}

int main(int argc, char **argv)
{
    char fin[19], fout[19], name[9], a1[48], a2[48], want[52];
    int got, rc, have = 0, fixed = 0, n = 0, r1, r2, i;
    if (argc < 2) { printf("usage: DIMFIX fn\n"); return 24; }
    memset(name, ' ', 8); name[8] = 0;
    for (i = 0; argv[1][i] && i < 8; i++) {
        char c = argv[1][i];
        name[i] = (c >= 'a' && c <= 'z') ? (char)(c - 'a' + 'A') : c;
    }
    sprintf(fin, "%-8sASSEMBLEA1", name);
    sprintf(fout, "%-8sASSEMBF A1", name);
    CMSfileErase(fout);
    if (CMSfileOpen(fin, ibuf, 80, 'F', 1, 1, &in)) {
        printf("DIMFIX: no %s ASSEMBLE A\n", name);
        return 28;
    }
    /* rc 28, not found, is expected: a new file */
    CMSfileOpen(fout, obuf, 80, 'F', 1, 1, &out);
    for (;;) {
        rc = CMSfileRead(&in, 0, &got);
        if (rc == 12) break;
        if (rc) { printf("DIMFIX: read error %d\n", rc); return 12; }
        ibuf[80] = 0;
        n++;
        if (have) {
            r1 = is_load(prev, a1);
            r2 = is_load(ibuf, a2);
            sprintf(want, "4+%s", a1);
            if (r1 >= 0 && r2 == r1 + 1 && uses(a1, r1) &&
                strcmp(a2, want) == 0) {
                char l1[81], l2[81];
                memset(l1, ' ', 80); memset(l2, ' ', 80);
                l1[80] = l2[80] = 0;
                if (strchr(a1, ',')) {          /* index and base */
                    sprintf(l1, "         LA    %d,%s", r1 + 1, a1);
                    sprintf(l2, "         LM    %d,%d,0(%d)", r1, r1 + 1,
                            r1 + 1);
                } else {
                    sprintf(l1, "         LM    %d,%d,%s", r1, r1 + 1, a1);
                    l2[0] = 0;
                }
                pad80(l1);
                if (put(l1)) { printf("DIMFIX: write error\n"); return 12; }
                if (l2[0]) {
                    pad80(l2);
                    if (put(l2)) { printf("DIMFIX: write error\n"); return 12; }
                }
                fixed++;
                have = 0;
                continue;
            }
            if (put(prev)) {
                printf("DIMFIX: write error\n");
                return 12;
            }
        }
        memcpy(prev, ibuf, 81);
        have = 1;
    }
    if (have && put(prev)) { printf("DIMFIX: write error\n"); return 12; }
    CMSfileClose(&in);
    CMSfileClose(&out);
    if (CMSfileErase(fin)) {
        printf("DIMFIX: cannot erase %s ASSEMBLE\n", name);
        return 12;
    }
    if (CMSfileRename(fout, fin)) {
        printf("DIMFIX: cannot rename\n");
        return 12;
    }
    if (fixed)
        printf("DIMFIX: %s %d records, %d 64-bit loads made LM\n",
               name, n, fixed);
    return 0;
}
