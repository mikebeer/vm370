/* M8.2 TMAIN: GCC380's 64-bit arithmetic against the PC's answers */
#include <stdio.h>
typedef long long ll;
typedef unsigned long long ull;
static void p(const char *t, ull v)
{
    printf("%s %08lX%08lX\n", t, (unsigned long)(v >> 32), (unsigned long)v);
}
static ll V[] = { 0LL, 1LL, -1LL, 7LL, -7LL, 1000000007LL, -123456789012LL,
                  9223372036854775807LL, 4294967296LL, 81985529216486895LL };
int main(void)
{
    int i, j, n;
    for (i = 0; i < 10; i++) {
        ll a = V[i];
        p("NEG", (ull)-a);
        if (a < 4503599627370496LL && a > -4503599627370496LL) p("FD", (ull)(ll)((double)a));
        p("FDU", (ull)(double)(ull)(a & 0x7FFFFFFFFFFFFLL));
        for (n = 0; n < 64; n += 9) {
            p("SHL", (ull)a << n);
            p("SHR", (ull)a >> n);
            p("SAR", (ull)(a >> n));
            p("SL32", (ull)((unsigned long)a << (n & 31)));
            p("SR32", (ull)((unsigned long)a >> (n & 31)));
            p("SA32", (ull)(unsigned long)((long)a >> (n & 31)));
        }
        for (j = 0; j < 10; j++) {
            ll b = V[j];
            p("MUL", (ull)(a * b));
            p("CMP", (ull)((a < b) * 4 + (a == b) * 2 + ((ull)a > (ull)b)));
            if (b) {
                if (!(a == (-9223372036854775807LL - 1) && b == -1)) {
                    p("DIV", (ull)(a / b));
                    p("MOD", (ull)(a % b));
                }
                p("UDIV", (ull)a / (ull)b);
                p("UMOD", (ull)a % (ull)b);
            }
        }
    }
    printf("TMAIN END\n");
    return 0;
}
