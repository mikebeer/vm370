#!/usr/bin/env python3
"""M8.2: the reader deck and the build EXEC for the native cREXX build.

    mkcms.py STAGE XFDIR OUTDIR
                           -> OUTDIR/crx82src.txt (READCARD deck: every staged
                              file and the EXEC), OUTDIR/crx82mk.txt (CRX82MK EXEC + CRX82 PARM)

CRX82MK EXEC compiles every unit with GCC380 (GCC31 EXEC, GCCLIB31's headers
on G), then links RXBVM82, RXAS82 and RXC82 with GCCLIB31 TXTLIB.
'CRX82MK fn' recompiles one unit; 'CRX82MK LINK' only links."""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
C = '/home/claude/adesutherland/crexx'
sys.path.insert(0, os.path.join(HERE, '..', 'crexx'))
from mkdeck import cards  # noqa: E402

PARM = '-w -O1 -S -DNDEBUG -D__CMS__ -o dd:out -'


def units_of(stage):
    """original path -> staged unit name"""
    m = {}
    for l in open(os.path.join(stage, 'map.txt')):
        fn, ft, path = l.split(None, 2)
        if ft == 'C':
            m[path.strip()] = fn
    return m


XF = None   # the xform output: a unit split in parts lists them in UNIT.parts


def expand(us):
    out = []
    for u in us:
        pf = os.path.join(XF, u.lower() + '.parts') if XF else ''
        out += open(pf).read().split() if pf and os.path.exists(pf) else [u]
    return out


def programs(stage):
    m = units_of(stage)
    srcs = [l.strip() for l in open(os.path.join(HERE, 'srcs.txt')) if l.strip()]
    sh = open(os.path.join(HERE, '..', 'm8', 'build.sh')).read()
    vm_rel = sh.split('VM="', 1)[1].split('"', 1)[0].split()
    vm = [m[C + '/' + r] for r in vm_rel]
    as_paths = sh.split('AS="', 1)[1].split('"', 1)[0].split()
    asm = []
    for p in as_paths:
        p = p.replace('$C', C).replace('$H', '/home/claude/crexx-host')
        p = p.replace('/home/claude/crexx-host/assembler/rxasscan.c', HERE + '/gen/rxasscan.c')
        asm.append(m[p])
    rt = m[os.path.join(HERE, 'inc', 'crxrt.c')] + ' ' + m[os.path.join(HERE, 'inc', 'crxlgcc.c')]
    main = {k: m[C + v] for k, v in (('vm', '/interpreter/rxvmmain.c'),
                                     ('as', '/assembler/rxasmain.c'),
                                     ('c', '/compiler/rxc_main.c'))}
    rt = rt.split()
    used = set(vm) | set(asm) | set(main.values()) | set(rt) | {m[C + '/interpreter/rxvml.c']}
    comp = [m[p] for p in srcs if m[p] not in used]
    return [('RXBVM82', expand([main['vm']] + vm + rt)),
            ('RXAS82', expand([main['as']] + asm + vm + rt)),
            ('RXC82', expand([main['c']] + comp + [m[C + '/interpreter/rxvml.c']] + vm + asm + rt))]


def exec_text(stage):
    progs = programs(stage)
    allu = []
    for _, us in progs:
        for u in us:
            if u not in allu:
                allu.append(u)
    L = ['/* CRX82MK EXEC -- M8.2: current cREXX built natively on VM/370+ */',
         '/* GCC380 (GCC31 EXEC), GCCLIB31 on G, sources and output on A.  */',
         '/* CRX82MK          compile every unit and link                    */',
         '/* CRX82MK fn ...   compile only these units;  CRX82MK LINK: link  */',
         'ARG ONLY',
         "SRC = 'A'",
         'BAD = 0',
         "UNITS = ''"]
    line = ''
    for u in allu:
        if len(line) + len(u) > 50:
            L.append("UNITS = UNITS '%s'" % line.strip())
            line = ''
        line += ' ' + u.upper()
    if line:
        L.append("UNITS = UNITS '%s'" % line.strip())
    L += ["/* CRX82 MACLIB: GCC31's, PDPTOP fixing GCC380's 64-bit code */",
          "'MACLIB GEN CRX82 CMSCRAB GCCCRAB PDPEPIL PDPPRLG PDPTOP VTENTRY'",
          "'MACLIB ADD CRX82 VTABLE'",
          "IF ONLY = 'LINK' THEN SIGNAL LINKALL",
          "IF ONLY <> '' THEN UNITS = ONLY",
          'DO I = 1 TO WORDS(UNITS)',
          '  U = WORD(UNITS, I)',
          "  SAY 'CRX82MK: COMPILING' U '(' I 'OF' WORDS(UNITS) ')'",
          "  CALL COMPILE U",
          "  IF RESULT <> 0 THEN DO",
          "    SAY 'CRX82MK: ***' U 'RC' RESULT; BAD = BAD + 1",
          "  END",
          'END',
          "IF ONLY <> '' THEN EXIT BAD",
          'LINKALL:',
          "'GLOBAL TXTLIB GCCLIB31'"]
    for name, us in progs:
        L.append("SAY 'CRX82MK: LINKING %s'" % name)
        L.append("'LOAD %s (NOAUTO NOLIBE CLEAR'" % us[0].upper())
        rest = [u.upper() for u in us[1:]]
        for i in range(0, len(rest), 5):
            last = i + 5 >= len(rest)
            L.append("'INCLUDE %s (NOAUTO%s'" % (' '.join(rest[i:i + 5]), '' if last else ' NOLIBE'))
        L.append("IF RC <> 0 THEN BAD = BAD + 1")
        L.append("'GENMOD %s'" % name)
        L.append("IF RC <> 0 THEN BAD = BAD + 1")
    L += ["IF BAD > 0 THEN SAY 'CRX82MK: *****' BAD 'ERRORS *****'",
          "ELSE SAY 'CRX82MK: BUILD OK'",
          'EXIT BAD',
          '',
          '/* GCC380 -O1 (-O0 if it fails inside, RC 12); CRXLGCC defines */',
          '/* the helpers PDPTOP declares, so it is built with GCC31 MACLIB */',
          'COMPILE: PROCEDURE EXPOSE SRC',
          '  ARG U',
          "  L = 'CRX82'",
          "  IF U = 'CRXLGCC' THEN L = 'GCC31'",
          "  'EXEC GCC31' U 'C' SRC '( LIB' L 'PARM CRX82 KEEP'",
          '  IF RC = 12 THEN DO',
          "    SAY 'CRX82MK:' U 'AGAIN WITH -O0'",
          "    'EXEC GCC31' U 'C' SRC '( LIB' L 'PARM CRX82O0 KEEP'",
          '  END',
          '  R = RC',
          '  IF R > 4 THEN CALL ASMERR U',
          "  'ERASE' U 'ASSEMBLE A'",
          "  'ERASE' U 'LISTING A'",
          '  IF R = 4 THEN R = 0',
          '  RETURN R',
          '',
          '/* the assembler\'s error lines from the LISTING */',
          'ASMERR: PROCEDURE',
          '  ARG U',
          "  'STATE' U 'LISTING A'",
          '  IF RC <> 0 THEN RETURN',
          '  N = 0',
          '  DO FOREVER',
          "    'EXECIO 500 DISKR' U 'LISTING A (STEM LL.'",
          '    E = RC',
          '    DO I = 1 TO LL.0 WHILE N < 40',
          "      IF POS('IFO', LL.I) > 0 | POS('*** ERROR', LL.I) > 0 THEN DO",
          "        SAY 'ASMERR:' STRIP(LL.I); N = N + 1",
          '      END',
          '    END',
          '    IF E <> 0 | N >= 40 THEN LEAVE',
          '  END',
          "  'FINIS' U 'LISTING A'",
          "  'QUERY DISK A'",
          '  RETURN']
    for l in L:
        assert len(l) <= 72, l
    return L


def main():
    global XF
    stage, xfdir, out = sys.argv[1:4]
    XF = xfdir
    deck = ['ID CMSUSER NAME CRX82 SRC']
    files = sorted(f for f in os.listdir(xfdir) if f.endswith('.c'))
    for f in files:
        fn = f[:-2]
        cs = cards(os.path.join(xfdir, f), 'C')
        if len(cs) <= 60000:
            deck.append(':READ  %-8s C        A1' % fn.upper())
            deck.extend(cs)
            continue
        # a CMS file holds 65,533 records: the unit #includes its pieces,
        # cut between source lines (a card ending in a backslash goes on)
        parts, cur = [], []
        for c in cs:
            cur.append(c)
            if len(cur) >= 50000 and not c.endswith('\\'):
                parts.append(cur)
                cur = []
        if cur:
            parts.append(cur)
        main = []
        for k, part in enumerate(parts):
            pn = '%s%02d' % (fn[:6], k + 1)
            deck.append(':READ  %-8s H        A1' % pn.upper())
            deck.extend(part)
            main.append('#include "%s.h"' % pn.lower())
        deck.append(':READ  %-8s C        A1' % fn.upper())
        deck.extend(main)
    mk = [':READ  CRX82MK  EXEC     A1'] + exec_text(stage)
    mk += [':READ  CRX82    PARM     A1', PARM]
    mk += [':READ  CRX82O0  PARM     A1', PARM.replace('-O1', '-O0')]
    top = open(os.path.join(HERE, '..', 'gcclib31', 'src', 'pdptop.copy')).read().rstrip('\n').split('\n')
    top = ['SLDA     OPSYN SLDL           M8.2: GCC380 shifts 64 bits with SLDA'] + top + [
        '* M8.2: GCC380 calls its 64-bit helpers (CRXLGCC) through =A()',
        '         EXTRN @@DIVDI3,@@UDIVDI,@@MODDI3,@@UMODDI',
        '         EXTRN @@MULDI3,@@NEGDI2,@@CMPDI2,@@UCMPDI']
    mk += [':READ  PDPTOP   COPY     A1'] + top
    with open(os.path.join(out, 'crx82src.txt'), 'w', encoding='latin-1') as fo:
        for c in deck + mk:
            fo.write(c.ljust(80) + '\n')
    mk = ['ID CMSUSER NAME CRX82 MK'] + mk
    with open(os.path.join(out, 'crx82mk.txt'), 'w', encoding='latin-1') as fo:
        for c in mk:
            fo.write(c.ljust(80) + '\n')
    print('%d files, %d cards; %s' % (len(files), len(deck),
          ' '.join('%s=%d' % (n, len(u)) for n, u in programs(stage))))


if __name__ == '__main__':
    main()
