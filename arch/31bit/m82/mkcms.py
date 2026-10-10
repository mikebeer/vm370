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
        af = os.path.join(XF, u.lower() + '.asm') if XF else ''
        if af and os.path.exists(af):
            out += open(af).read().split()          # its tables, in assembler
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
    # the VM and the assembler are libraries: each program takes only the
    # units it reaches (as the PC build's archives do).  CMS TXTLIB will not
    # take GCC380's large TEXT decks, so the selection is made here, from
    # the same units compiled on the PC (objects in XF/obj)
    lib = expand(asm) + expand(vm + rt)
    progs = [('RXBVM82', expand([main['vm']] + rt)),
             ('RXAS82', expand([main['as']] + rt)),
             ('RXC82', expand([main['c']] + comp + [m[C + '/interpreter/rxvml.c']] + rt))]
    return [(n, close(us, lib)) for n, us in progs], {}


def symbols(u):
    import subprocess
    o = os.path.join(XF, 'obj', u.lower() + '.o')
    want = u.lower() + ('.assemble' if u.upper().startswith('CT') else '.c')
    src = os.path.join(XF, next((f for f in os.listdir(XF) if f.lower() == want), want))
    if u.upper().startswith('CT'):
        return {u.upper()}, set()
    if not os.path.exists(o) or os.path.getmtime(o) < os.path.getmtime(src):
        os.makedirs(os.path.dirname(o), exist_ok=True)
        subprocess.run(['s390x-linux-gnu-gcc', '-m31', '-march=z900', '-O0', '-w', '-c', src, '-o', o], check=True)
    d, un = set(), set()
    for l in subprocess.run(['s390x-linux-gnu-nm', o], capture_output=True, text=True).stdout.splitlines():
        p = l.split()
        if len(p) == 3 and p[1] in 'TDBRCG':
            d.add(p[2])
        elif len(p) == 2 and p[0] == 'U':
            un.add(p[1])
    return d, un


def close(units, lib):
    """units plus the library units they reach, in link order"""
    out = list(units)
    defined, need = set(), set()
    for u in out:
        d, un = symbols(u)
        defined |= d
        need |= un
    provider = {}
    for u in lib:
        for x in symbols(u)[0]:
            provider.setdefault(x, u)
    changed = True
    while changed:
        changed = False
        for x in sorted(need - defined):
            u = provider.get(x)
            if u and u not in out:
                out.append(u)
                d, un = symbols(u)
                defined |= d
                need |= un
                changed = True
    return out


def csname(u, used):
    """the CSECT name of a unit: '$' + 7 (TXTLIB takes no private code,
    and the unit's name may be a function's)"""
    c = '$' + u.upper()[:7]
    k = 0
    while c in used:
        k += 1
        c = '$' + u.upper()[:7 - len(str(k))] + str(k)
    used.add(c)
    return c


def link_exec(progs, cs):
    """CRX82LK EXEC (CMS EXEC language): link the three modules"""
    L = ['&CONTROL ERROR', '* CRX82LK EXEC -- M8.2: link RXBVM82, RXAS82, RXC82',
         '* (CMS EXEC: LOAD may not run from REXX, which sits in the user area)',
         'GLOBAL TXTLIB GCCLIB31']
    for name, us in progs:
        rest = [u.upper() for u in us[1:]]
        L.append('&TYPE CRX82LK: LINKING %s' % name)
        L.append('LOAD %s ( NOAUTO NOLIBE CLEAR' % us[0].upper())
        for i in range(0, len(rest), 5):
            last = i + 5 >= len(rest)
            L.append('INCLUDE %s ( NOAUTO%s' % (' '.join(rest[i:i + 5]), '' if last else ' NOLIBE'))
        # GENMOD's default start is the loader table's third entry (here
        # the main unit's MAIN), which leaves out the entry @@MAIN and the
        # static data in front of it: start at the main unit's CSECT
        L.append('GENMOD %s ( FROM %s' % (name, cs[us[0].upper()]))
    L.append('&TYPE CRX82LK: DONE')
    for l in L:
        assert len(l) <= 72, l
    return L


def exec_text(stage):
    progs, libs = programs(stage)
    allu = []
    for us in [p[1] for p in progs]:
        for u in us:
            if u not in allu:
                allu.append(u)
    used = set()
    cs = [(u.upper(), csname(u, used)) for u in allu if not u.upper().startswith('CT')]
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
    for u, c in cs:
        L.append("CS.%s = '%s'" % (u, c))
    L.append("CS.TK = '$TK'                 /* the test unit */")
    L.append("CS.DIMFIX = '$DIMFIX'         /* the assembler repair filter */")
    L.append("CS.UNHEXT = '$UNHEXT'         /* long text files from the PC */")
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
          "/* LOAD and GENMOD may not run from a REXX EXEC: the interpreter */",
          "/* is in the user area the program loads into.  CRX82LK is a    */",
          "/* CMS EXEC (EXEC 1, in the nucleus), run from the command line */",
          "SAY 'CRX82MK: COMPILED -- NOW LINK WITH:  EXEC CRX82LK'"]
    L += ["IF BAD > 0 THEN SAY 'CRX82MK: *****' BAD 'ERRORS *****'",
          "ELSE SAY 'CRX82MK: BUILD OK'",
          'EXIT BAD',
          '',
          '/* GCC380 -O1 (-O0 if it fails inside, RC 12); CRXLGCC defines */',
          '/* the helpers PDPTOP declares, so it is built with GCC31 MACLIB */',
          'COMPILE: PROCEDURE EXPOSE SRC CS.',
          '  ARG U',
          "  IF LEFT(U, 2) = 'CT' THEN DO      /* a table: assembler source */",
          "    'GLOBAL MACLIB GCC31 DMSGPI CMSHRC CMSLIB OSMACRO TSOMAC'",
          "    'ASMAHL' U '(NOTERM'",
          '    R = RC',
          '    IF R > 4 THEN CALL ASMERR U',
          "    'ERASE' U 'LISTING A'",
          '    IF R = 4 THEN R = 0',
          '    RETURN R',
          '  END',
          "  L = 'CRX82'",
          "  IF U = 'CRXLGCC' | U = 'DIMFIX' | U = 'UNHEXT' THEN L = 'GCC31'",
          "  /* READCARD writes to A; a unit may also come from another disk */",
          "  'STATE' U 'C A'",
          "  IF RC = 0 THEN SRC = 'A'",
          "  ELSE SRC = 'H'",
          "  'EXEC GCC31' U 'C' SRC '( LIB' L 'PARM CRX82 NOASM KEEP'",
          '  IF RC = 12 THEN DO',
          "    SAY 'CRX82MK:' U 'AGAIN WITH -O0'",
          "    'EXEC GCC31' U 'C' SRC '( LIB' L 'PARM CRX82O0 NOASM KEEP'",
          '  END',
          '  IF RC > 4 THEN RETURN RC',
          '  /* name the CSECT: TXTLIB takes no private code */',
          "  'MAKEBUF'",
          "  QUEUE 'SERIAL OFF'",
          "  QUEUE 'LOCATE /         CSECT/'",
          "  QUEUE 'CHANGE /         CSECT/'LEFT(CS.U, 9)'CSECT/'",
          "  QUEUE 'FILE'",
          "  'EDIT' U 'ASSEMBLE A'",
          '  E = RC',
          "  'DROPBUF'",
          '  IF E <> 0 THEN RETURN 100 + E',
          "  /* GCC380's 64-bit loads that clobber their own base register */",
          "  IF U <> 'DIMFIX' & U <> 'UNHEXT' THEN DO",
          "    'STATE DIMFIX MODULE *'",
          "    IF RC = 0 THEN 'DIMFIX' U",
          "    ELSE SAY 'CRX82MK: *** NO DIMFIX MODULE (EXEC DIMFIXLK)'",
          "    IF RC <> 0 THEN RETURN 200 + RC",
          "  END",
          "  'GLOBAL MACLIB' L 'DMSGPI CMSHRC CMSLIB OSMACRO TSOMAC'",
          "  'ASMAHL' U '(NOTERM'",
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
    # only the table CSECTs a unit lists (xform renumbers them on each run)
    live = set()
    for a in os.listdir(xfdir):
        if a.endswith('.asm'):
            live |= {w.lower() for w in open(os.path.join(xfdir, a)).read().split()}
    for f in sorted(f for f in os.listdir(xfdir) if f.endswith('.assemble') and f[:-9] in live):
        deck.append(':READ  %-8s ASSEMBLE A1' % f[:-9].upper())
        deck.extend(cards(os.path.join(xfdir, f), 'ASSEMBLE'))
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
    progs = programs(stage)[0]
    used, cs = set(), {}
    allu = []
    for p in progs:
        for u in p[1]:
            if u not in allu:
                allu.append(u)
    for u in allu:
        if not u.upper().startswith('CT'):
            cs[u.upper()] = csname(u, used)
    mk += [':READ  CRX82LK  EXEC     A1'] + link_exec(progs, cs)
    # the build tools, plain GCCLIB31 programs: DIMFIX (run by CRX82MK on
    # every unit) and UNHEXT (long-line text files from the PC)
    for tool in ('dimfix', 'unhext'):
        dl = [l.rstrip() for l in open(os.path.join(HERE, 'inc', tool + '.c')).read().rstrip('\n').split('\n')]
        assert all(len(l) <= 80 for l in dl), tool + '.c: a line over 80 columns'
        mk += [':READ  %-8s C        A1' % tool.upper()] + dl
    mk += [':READ  DIMFIXLK EXEC     A1', '&CONTROL ERROR',
           '* DIMFIXLK EXEC -- M8.2: link DIMFIX and UNHEXT (LOAD may not',
           '* run from REXX)',
           'GLOBAL TXTLIB GCCLIB31', 'LOAD DIMFIX ( CLEAR', 'GENMOD DIMFIX',
           'LOAD UNHEXT ( CLEAR', 'GENMOD UNHEXT', '&TYPE DIMFIXLK: DONE']
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
    progs, libs = programs(stage)
    print('%d files, %d cards; %s; %s' % (len(files), len(deck),
          ' '.join('%s=%d' % (p[0], len(p[1])) for p in progs), ''))


if __name__ == '__main__':
    main()
