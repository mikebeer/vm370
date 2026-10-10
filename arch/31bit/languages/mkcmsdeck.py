#!/usr/bin/env python3
"""mkcmsdeck.py RXBINDIR OUT.txt -- VM/370+: the reader deck that brings the
cREXX languages to CMS (READCARD *): each RXBIN as hex text (fn HEX, UNHEX
rebuilds the bytes: 80-byte card padding breaks the RXBIN loader), the
EXECs, and the test programs, plus LANGSUP EXEC that unhexes them."""
import os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
rx, out = sys.argv[1:3]
L = ['ID CMSUSER NAME LANGS']
def add(fn, ft, lines):
    L.append(':READ  %-8s %-8s A1' % (fn.upper(), ft.upper()))
    for l in lines:
        assert len(l) <= 80, (fn, ft, l)
        L.append(l)
mods = ['basic', 'logo', 'prolog', 'snobol', 'pascal', 'pasrt', 'lisp', 'smalltalk', 'plm', 'plmrt']
CMSN = {'smalltalk': 'smalltlk'}             # CMS file names: 8 characters
for m in mods:
    h = open(os.path.join(rx, m + '.rxbin'), 'rb').read().hex().upper()
    add(CMSN.get(m, m), 'hex', [h[i:i + 78] for i in range(0, len(h), 78)])
def text(path):
    return [l.rstrip('\r') for l in open(path, encoding='latin-1').read().rstrip('\n').split('\n')]
for d, f in (('basic/cms', 'BASIC.EXEC'), ('logo/cms', 'LOGO.EXEC'), ('prolog/cms', 'PROLOG.EXEC'),
             ('snobol/cms', 'SNOBOL.EXEC'), ('pascal/cms', 'PASCAL.EXEC'), ('lisp/cms', 'LISP.EXEC'),
             ('smalltalk/cms', 'SMALLTLK.EXEC'), ('plm/cms', 'PLM.EXEC'), ('turbo/cms', 'TURBO.EXEC'),
             ('turbo/cms', 'HELLO.TCEXAMPL'), ('turbo/cms', 'FIBFACT.TCEXAMPL'), ('turbo/cms', 'TCNEW.TCEXAMPL')):
    fn, ft = f.split('.')
    add(fn, ft, text(os.path.join(HERE, d, f)))
for d, f in (('basic/tests', 'hello.bas'), ('basic/tests', 'primes.bas'), ('basic/tests', 'mandel.bas'),
             ('snobol/tests', 'hello.sno'), ('snobol/tests', 'roman.sno'),
             ('pascal/tests', 'fib.pas'), ('pascal/tests', 'sieve.pas'),
             ('logo/examples', 'tree.logo'), ('prolog', 'recur.pl'), ('prolog', 'family.pl'),
             ('lisp/examples', 'hello.lisp'), ('lisp/examples', 'primes.lisp'),
             ('smalltalk/examples', 'hello.st'), ('smalltalk/examples', 'fib.st'),
             ('plm/examples', 'hello.plm'), ('plm/examples', 'sieve.plm')):
    fn, ft = f.split('.')
    add(fn, ft, text(os.path.join(HERE, d, f)))
# the Smalltalk class library, folded to 80 columns (smalltalk/tools/fold80.py);
# cmsrt cuts names longer than 8, so collections.st is COLLECTI ST
import subprocess, tempfile
tmp = tempfile.mkdtemp()
for f in sorted(os.listdir(os.path.join(HERE, 'smalltalk/lib'))):
    subprocess.run([sys.executable, os.path.join(HERE, 'smalltalk/tools/fold80.py'),
                    os.path.join(HERE, 'smalltalk/lib', f), os.path.join(tmp, f)], check=True)
    fn, ft = f.split('.')
    add(fn[:8], ft, text(os.path.join(tmp, f)))
add('langsup', 'exec', ["/* LANGSUP EXEC -- unhex the cREXX language modules */"] +
    [x for m in mods for x in ("'UNHEX %s HEX A %s RXBIN A'" % ((CMSN.get(m, m).upper(),) * 2),
                               "IF RC = 0 THEN 'ERASE %s HEX A'" % CMSN.get(m, m).upper())] + ["EXIT"])
open(out, 'w').write('\n'.join(L) + '\n')
print(len(L), 'cards')
