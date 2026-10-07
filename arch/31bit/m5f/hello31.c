/* VM/370+ M5f: GCC -m31 (mainline s390 backend) in AMODE 31 on CMS. */
typedef unsigned int u32;
int cms202(void *plist);

struct hs { char cmd[8]; char fn[8]; u32 bytes; u32 addr; };
static struct hs hsp;
static unsigned char typl[16];
static char line[130];
static const unsigned char e2a_dummy = 0;

/* ASCII source text -> EBCDIC for the few characters we print */
static unsigned char ebc(char c)
{
    static const char a[] = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ abcdefghijklmnopqrstuvwxyz:,.=-()/+'";
    static const unsigned char e[] = {
      0xF0,0xF1,0xF2,0xF3,0xF4,0xF5,0xF6,0xF7,0xF8,0xF9,
      0xC1,0xC2,0xC3,0xC4,0xC5,0xC6,0xC7,0xC8,0xC9,
      0xD1,0xD2,0xD3,0xD4,0xD5,0xD6,0xD7,0xD8,0xD9,
      0xE2,0xE3,0xE4,0xE5,0xE6,0xE7,0xE8,0xE9,0x40,
      0x81,0x82,0x83,0x84,0x85,0x86,0x87,0x88,0x89,
      0x91,0x92,0x93,0x94,0x95,0x96,0x97,0x98,0x99,
      0xA2,0xA3,0xA4,0xA5,0xA6,0xA7,0xA8,0xA9,
      0x7A,0x6B,0x4B,0x7E,0x60,0x4D,0x5D,0x61,0x4E,0x7D };
    for (int i = 0; a[i]; i++) if (a[i] == c) return e[i];
    return 0x6F; /* ? */
}

static void setname(char *d, const char *s)
{ int i = 0; for (; s[i] && i < 8; i++) d[i] = ebc(s[i]); for (; i < 8; i++) d[i] = 0x40; }

static int n;
static void put(const char *s) { while (*s) line[n++] = ebc(*s++); }
static void puthex(u32 v)
{ for (int i = 28; i >= 0; i -= 4) line[n++] = ebc("0123456789ABCDEF"[(v >> i) & 15]); }
static void putdec(u32 v)
{ char t[12]; int k = 0; do { t[k++] = '0' + v % 10; v /= 10; } while (v);
  while (k) line[n++] = ebc(t[--k]); }
static void say(void)
{
    u32 a = (u32)line;
    setname((char *)typl, "TYPLIN");
    typl[8] = 1; typl[9] = a >> 16; typl[10] = a >> 8; typl[11] = a;
    typl[12] = 0xC2; typl[13] = 0; typl[14] = n >> 8; typl[15] = n;
    cms202(typl);
    n = 0;
}

static int hs(const char *fn, u32 bytes, u32 addr)
{
    setname(hsp.cmd, "HIGHSTOR"); setname(hsp.fn, fn);
    hsp.bytes = bytes; hsp.addr = addr;
    return cms202(&hsp);
}

int cms_main(void *plist)
{
    u32 size = 40u << 20, p, bad = 0;
    unsigned long long sum = 0;
    (void)plist;
    {   /* where are we? BASSM/BSM put AMODE in bit 0 of the link register */
        u32 r14; __asm__ volatile ("basr %0,0" : "=r"(r14));
        put("HELLO31X: GCC -m31 CODE AT "); puthex(r14 & 0x7FFFFFFF);
        put(r14 & 0x80000000u ? ", AMODE 31" : ", AMODE 24"); say();
    }
    if (hs("OBTAIN", size, 0)) { put("HELLO31X: HIGHSTOR OBTAIN FAILED"); say(); return 8; }
    p = hsp.addr;
    for (u32 a = 0; a < size; a += 4096) *(volatile u32 *)(p + a) = p + a;
    for (u32 a = 0; a < size; a += 4096) {
        u32 v = *(volatile u32 *)(p + a);
        if (v != p + a) bad++;
        sum += v;
    }
    put("HELLO31X: 40 MB AT "); puthex(p); put(" WRITTEN/READ, PAGES="); putdec(size / 4096);
    put(" BAD="); putdec(bad); put(" SUM="); puthex((u32)(sum >> 32)); puthex((u32)sum); say();
    hs("RELEASE", size, p);
    return bad ? 8 : 0;
}
