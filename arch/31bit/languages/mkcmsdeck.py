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
mods = ['basic', 'logo', 'prolog', 'snobol', 'pascal', 'pasrt']
for m in mods:
    h = open(os.path.join(rx, m + '.rxbin'), 'rb').read().hex().upper()
    add(m, 'hex', [h[i:i + 78] for i in range(0, len(h), 78)])
def text(path):
    return [l.rstrip('\r') for l in open(path, encoding='latin-1').read().rstrip('\n').split('\n')]
for d, f in (('basic/cms', 'BASIC.EXEC'), ('logo/cms', 'LOGO.EXEC'), ('prolog/cms', 'PROLOG.EXEC'),
             ('snobol/cms', 'SNOBOL.EXEC'), ('pascal/cms', 'PASCAL.EXEC')):
    fn, ft = f.split('.')
    add(fn, ft, text(os.path.join(HERE, d, f)))
for d, f in (('basic/tests', 'hello.bas'), ('basic/tests', 'primes.bas'), ('basic/tests', 'mandel.bas'),
             ('snobol/tests', 'hello.sno'), ('snobol/tests', 'roman.sno'),
             ('pascal/tests', 'fib.pas'), ('pascal/tests', 'sieve.pas'),
             ('logo/examples', 'tree.logo'), ('prolog', 'recur.pl'), ('prolog', 'family.pl')):
    fn, ft = f.split('.')
    add(fn, ft, text(os.path.join(HERE, d, f)))
add('langsup', 'exec', ["/* LANGSUP EXEC -- unhex the cREXX language modules */"] +
    ["'UNHEX %s HEX A %s RXBIN A'" % (m.upper(), m.upper()) for m in mods] +
    ["IF RC = 0 THEN 'ERASE %s HEX A'" % m.upper() for m in mods] + ["EXIT"])
open(out, 'w').write('\n'.join(L) + '\n')
print(len(L), 'cards')
