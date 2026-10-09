/* M8.2 CRXLGCC C -- the 64-bit helpers GCC380 calls but nothing supplies
   (libgcc's __divdi3 & co.).  GCC380 calls them as =A(@@DIVDI3) (names cut to
   8: __udivdi3 is @@UDIVDI); ASMFIX turns those into =V().  (__floatundidf would also be @@FLOATD: GCC380 converts
   unsigned with __floatdidf.)  Their calling convention
   is GCC380's own for a function of long long (R1 -> the values, R0 -> the
   result), so they are written as ordinary C -- but only with 32-bit
   arithmetic, or they would call themselves. */

typedef unsigned long u32;
typedef struct { u32 hi, lo; } dw;              /* big-endian halves */
typedef union { long long s; unsigned long long u; dw w; double d; } du;

static dw mk(u32 hi, u32 lo) { dw r; r.hi = hi; r.lo = lo; return r; }

static dw add(dw a, dw b)
{
    dw r;
    r.lo = a.lo + b.lo;
    r.hi = a.hi + b.hi + (r.lo < a.lo);
    return r;
}

static dw neg(dw a)
{
    return add(mk(~a.hi, ~a.lo), mk(0, 1));
}

static int ucmp(dw a, dw b)            /* -1, 0, 1 */
{
    if (a.hi != b.hi) return a.hi < b.hi ? -1 : 1;
    if (a.lo != b.lo) return a.lo < b.lo ? -1 : 1;
    return 0;
}

static dw sub(dw a, dw b) { return add(a, neg(b)); }

static dw shl1(dw a) { return mk((a.hi << 1) | (a.lo >> 31), a.lo << 1); }

/* unsigned divide: shift-subtract, 64 steps */
static dw udivmod(dw n, dw d, dw *rem)
{
    dw q = mk(0, 0), r = mk(0, 0);
    int i;
    if (!d.hi && !d.lo) { if (rem) *rem = n; return mk(0, 0); }
    if (!n.hi && !d.hi) {                         /* the common case */
        q = mk(0, n.lo / d.lo);
        if (rem) *rem = mk(0, n.lo % d.lo);
        return q;
    }
    for (i = 63; i >= 0; i--) {
        r = shl1(r);
        if (i >= 32) r.lo |= (n.hi >> (i - 32)) & 1;
        else r.lo |= (n.lo >> i) & 1;
        q = shl1(q);
        if (ucmp(r, d) >= 0) { r = sub(r, d); q.lo |= 1; }
    }
    if (rem) *rem = r;
    return q;
}

static int isneg(dw a) { return (a.hi & 0x80000000UL) != 0; }

unsigned long long __udivdi3(unsigned long long a, unsigned long long b)
{
    du x, y, r;
    x.u = a; y.u = b;
    r.w = udivmod(x.w, y.w, 0);
    return r.u;
}

unsigned long long __umoddi3(unsigned long long a, unsigned long long b)
{
    du x, y, r;
    dw m;
    x.u = a; y.u = b;
    udivmod(x.w, y.w, &m);
    r.w = m;
    return r.u;
}

long long __divdi3(long long a, long long b)
{
    du x, y, r;
    int s = 0;
    x.s = a; y.s = b;
    if (isneg(x.w)) { x.w = neg(x.w); s ^= 1; }
    if (isneg(y.w)) { y.w = neg(y.w); s ^= 1; }
    r.w = udivmod(x.w, y.w, 0);
    if (s) r.w = neg(r.w);
    return r.s;
}

long long __moddi3(long long a, long long b)
{
    du x, y, r;
    dw m;
    int s = 0;
    x.s = a; y.s = b;
    if (isneg(x.w)) { x.w = neg(x.w); s = 1; }
    if (isneg(y.w)) y.w = neg(y.w);
    udivmod(x.w, y.w, &m);
    r.w = s ? neg(m) : m;
    return r.s;
}

/* 32 x 32 -> 64 from 16-bit pieces */
static dw umul32(u32 a, u32 b)
{
    u32 al = a & 0xFFFF, ah = a >> 16, bl = b & 0xFFFF, bh = b >> 16;
    u32 ll = al * bl, lh = al * bh, hl = ah * bl, hh = ah * bh;
    dw r = mk(hh, ll);
    r = add(r, mk(lh >> 16, lh << 16));
    r = add(r, mk(hl >> 16, hl << 16));
    return r;
}

long long __muldi3(long long a, long long b)
{
    du x, y, r;
    x.s = a; y.s = b;
    r.w = umul32(x.w.lo, y.w.lo);
    r.w.hi += x.w.hi * y.w.lo + x.w.lo * y.w.hi;
    return r.s;
}

long long __negdi2(long long a)
{
    du x;
    x.s = a;
    x.w = neg(x.w);
    return x.s;
}

int __cmpdi2(long long a, long long b)          /* 0 <, 1 =, 2 > */
{
    du x, y;
    x.s = a; y.s = b;
    if ((long)x.w.hi != (long)y.w.hi) return (long)x.w.hi < (long)y.w.hi ? 0 : 2;
    if (x.w.lo != y.w.lo) return x.w.lo < y.w.lo ? 0 : 2;
    return 1;
}

int __ucmpdi2(unsigned long long a, unsigned long long b)
{
    du x, y;
    x.u = a; y.u = b;
    return ucmp(x.w, y.w) + 1;
}

static double u32d(u32 v)
{
    return (double)(long)(v >> 1) * 2.0 + (double)(long)(v & 1);
}

double __floatdidf(long long a)
{
    du x;
    int s = 0;
    double d;
    x.s = a;
    if (isneg(x.w)) { x.w = neg(x.w); s = 1; }
    d = u32d(x.w.hi) * 4294967296.0 + u32d(x.w.lo);
    return s ? -d : d;
}

static dw d2u(double d)                         /* 0 <= d < 2**64 */
{
    double h = d / 4294967296.0;
    u32 hi, lo;
    if (h >= 2147483648.0) hi = (u32)(long)(h - 2147483648.0) + 0x80000000UL;
    else hi = (u32)(long)h;
    d -= u32d(hi) * 4294967296.0;
    if (d < 0) d = 0;
    if (d >= 2147483648.0) lo = (u32)(long)(d - 2147483648.0) + 0x80000000UL;
    else lo = (u32)(long)d;
    return mk(hi, lo);
}

long long __fixdfdi(double d)
{
    du r;
    if (d < 0) r.w = neg(d2u(-d));
    else r.w = d2u(d);
    return r.s;
}

unsigned long long __fixunsdfdi(double d)
{
    du r;
    if (d < 0) r.w = mk(0, 0);
    else r.w = d2u(d);
    return r.u;
}

long long __ashldi3(long long a, int n)
{
    du x;
    x.s = a;
    n &= 63;
    if (n >= 32) x.w = mk(x.w.lo << (n - 32), 0);
    else if (n) x.w = mk((x.w.hi << n) | (x.w.lo >> (32 - n)), x.w.lo << n);
    return x.s;
}

long long __lshrdi3(long long a, int n)
{
    du x;
    x.s = a;
    n &= 63;
    if (n >= 32) x.w = mk(0, x.w.hi >> (n - 32));
    else if (n) x.w = mk(x.w.hi >> n, (x.w.lo >> n) | (x.w.hi << (32 - n)));
    return x.s;
}

long long __ashrdi3(long long a, int n)
{
    du x;
    u32 fill;
    x.s = a;
    n &= 63;
    fill = isneg(x.w) ? 0xFFFFFFFFUL : 0;
    if (n >= 32) x.w = mk(fill, (u32)((long)x.w.hi >> (n - 32)));
    else if (n) x.w = mk((u32)((long)x.w.hi >> n), (x.w.lo >> n) | (x.w.hi << (32 - n)));
    return x.s;
}

/* GCC380 has no 64-bit add at all (internal compiler error), and folds a
   subtract of a constant into an add: xform.py turns every 64-bit +, -,
   +=, -=, ++ and -- into these. */
long long crxadd64(long long a, long long b)
{
    du x, y;
    x.s = a; y.s = b;
    x.w = add(x.w, y.w);
    return x.s;
}

long long crxsub64(long long a, long long b)
{
    du x, y;
    x.s = a; y.s = b;
    x.w = sub(x.w, y.w);
    return x.s;
}

long long crxadt64(long long *p, long long b)       /* *p += b */
{
    du x, y;
    x.s = *p; y.s = b;
    x.w = add(x.w, y.w);
    *p = x.s;
    return x.s;
}

long long crxinc64(long long *p, long long d, int post)   /* ++ -- */
{
    du x, y, old;
    x.s = *p; y.s = d;
    old = x;
    x.w = add(x.w, y.w);
    *p = x.s;
    return post ? old.s : x.s;
}

/* 64-bit comparisons under && and ||, and 64-bit switch: GCC380 folds them
   into range tests that subtract a constant (= an add, which it cannot) */
int crxcmp64(long long a, long long b)
{
    du x, y;
    x.s = a; y.s = b;
    if ((long)x.w.hi != (long)y.w.hi) return (long)x.w.hi < (long)y.w.hi ? -1 : 1;
    if (x.w.lo != y.w.lo) return x.w.lo < y.w.lo ? -1 : 1;
    return 0;
}

int crxucm64(unsigned long long a, unsigned long long b)
{
    du x, y;
    x.u = a; y.u = b;
    return ucmp(x.w, y.w);
}

long crxsw64(long long a)        /* out of range: a value no case uses */
{
    du x;
    x.s = a;
    if ((x.w.hi == 0 && !(x.w.lo & 0x80000000UL)) ||
        (x.w.hi == 0xFFFFFFFFUL && (x.w.lo & 0x80000000UL)))
        return (long)x.w.lo;
    return (long)0x80000000UL;
}

/* 64-bit multiply by call: GCC380 builds a multiply by a constant from
   shifts and 64-bit adds, which it cannot compile */
long long crxmul64(long long a, long long b)
{
    du x, y, r;
    x.s = a; y.s = b;
    r.w = umul32(x.w.lo, y.w.lo);
    r.w.hi += x.w.hi * y.w.lo + x.w.lo * y.w.hi;
    return r.s;
}

long long crxmut64(long long *p, long long b)       /* *p *= b */
{
    *p = crxmul64(*p, b);
    return *p;
}

/* __builtin_{add,sub,mul}_overflow for 64-bit signed (rxinteger.h):
   1 if the true result does not fit */
int crxaov64(long long a, long long b, long long *r)
{
    du x, y, z;
    x.s = a; y.s = b;
    z.w = add(x.w, y.w);
    *r = z.s;
    return isneg(x.w) == isneg(y.w) && isneg(z.w) != isneg(x.w);
}

int crxsov64(long long a, long long b, long long *r)
{
    du x, y, z;
    x.s = a; y.s = b;
    z.w = sub(x.w, y.w);
    *r = z.s;
    return isneg(x.w) != isneg(y.w) && isneg(z.w) != isneg(x.w);
}

int crxmov64(long long a, long long b, long long *r)
{
    du x, y, z, q;
    int s = 0;
    x.s = a; y.s = b;
    z.s = crxmul64(a, b);
    *r = z.s;
    if ((!x.w.hi && !x.w.lo) || (!y.w.hi && !y.w.lo))
        return 0;
    /* overflow iff z / b != a, or the INT64_MIN * -1 case */
    if (isneg(x.w)) { x.w = neg(x.w); s ^= 1; }
    if (isneg(y.w)) { y.w = neg(y.w); s ^= 1; }
    if (isneg(z.w)) q.w = udivmod(neg(z.w), y.w, 0);
    else q.w = udivmod(z.w, y.w, 0);
    if (ucmp(q.w, x.w) != 0) return 1;
    return (isneg(z.w) != (s != 0)) && (z.w.hi || z.w.lo);
}

/* widening of a 32-bit constant expression (sizeof, enum, ...) at run
   time: GCC380 folds it into a 64-bit constant and moves it with MVC 8
   from a 4-byte literal, so the value lands in the high half */
long long crxs64(long v)
{
    du x;
    x.w = mk(v < 0 ? 0xFFFFFFFFUL : 0, (u32)v);
    return x.s;
}

unsigned long long crxz64(unsigned long v)
{
    du x;
    x.w = mk(0, v);
    return x.u;
}
