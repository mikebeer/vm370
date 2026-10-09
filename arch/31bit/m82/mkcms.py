#!/usr/bin/env python3
"""M8.2: the reader deck and the build EXEC for the native cREXX build.

    mkcms.py STAGE OUTDIR  -> OUTDIR/crx82src.txt (READCARD deck, every staged
                              file), OUTDIR/crx82mk.txt (CRX82MK EXEC + CRX82 PARM)

CRX82MK EXEC compiles every unit with GCC380 (GCC31 EXEC, GCCLIB31's headers
on G), then links RXBVM82, RXAS82 and RXC82 with GCCLIB31 TXTLIB.
'CRX82MK fn' recompiles one unit; 'CRX82MK LINK' only links."""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
C = '/home/claude/adesutherland/crexx'
sys.path.insert(0, os.path.join(HERE, '..', 'crexx'))
from mkdeck import cards  # noqa: E402

PARM = '-O1 -S -DNDEBUG -D__CMS__ -o dd:out -'


def units_of(stage):
    """original path -> staged unit name"""
    m = {}
    for l in open(os.path.join(stage, 'map.txt')):
        fn, ft, path = l.split(None, 2)
        if ft == 'C':
            m[path.strip()] = fn
    return m


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
    rt = m[os.path.join(HERE, 'inc', 'crxrt.c')]
    main = {k: m[C + v] for k, v in (('vm', '/interpreter/rxvmmain.c'),
                                     ('as', '/assembler/rxasmain.c'),
                                     ('c', '/compiler/rxc_main.c'))}
    used = set(vm) | set(asm) | set(main.values()) | {rt, m[C + '/interpreter/rxvml.c']}
    comp = [m[p] for p in srcs if m[p] not in used]
    return [('RXBVM82', [main['vm']] + vm + [rt]),
            ('RXAS82', [main['as']] + asm + vm + [rt]),
            ('RXC82', [main['c']] + comp + [m[C + '/interpreter/rxvml.c']] + vm + asm + [rt])]


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
    L += ["IF ONLY = 'LINK' THEN SIGNAL LINKALL",
          "IF ONLY <> '' THEN UNITS = ONLY",
          'DO I = 1 TO WORDS(UNITS)',
          '  U = WORD(UNITS, I)',
          "  SAY 'CRX82MK: COMPILING' U '(' I 'OF' WORDS(UNITS) ')'",
          "  'EXEC GCC31' U 'C' SRC '( LIB GCC31 PARM CRX82'",
          "  IF RC <> 0 THEN DO; SAY 'CRX82MK: ***' U 'RC' RC; BAD = BAD + 1; END",
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
          'EXIT BAD']
    for l in L:
        assert len(l) <= 72, l
    return L


def main():
    stage, out = sys.argv[1:3]
    deck = ['ID CMSUSER NAME CRX82 SRC']
    files = sorted(f for f in os.listdir(stage) if f.endswith(('.c', '.h')))
    for f in files:
        fn, ft = f.split('.')
        deck.append(':READ  %-8s %-8s A1' % (fn.upper(), ft.upper()))
        deck.extend(cards(os.path.join(stage, f), ft.upper()))
    with open(os.path.join(out, 'crx82src.txt'), 'w', encoding='latin-1') as fo:
        for c in deck:
            fo.write(c.ljust(80) + '\n')
    mk = ['ID CMSUSER NAME CRX82 MK', ':READ  CRX82MK  EXEC     A1'] + exec_text(stage)
    mk += [':READ  CRX82    PARM     A1', PARM]
    with open(os.path.join(out, 'crx82mk.txt'), 'w', encoding='latin-1') as fo:
        for c in mk:
            fo.write(c.ljust(80) + '\n')
    print('%d files, %d cards; %s' % (len(files), len(deck),
          ' '.join('%s=%d' % (n, len(u)) for n, u in programs(stage))))


if __name__ == '__main__':
    main()
