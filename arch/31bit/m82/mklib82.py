#!/usr/bin/env python3
"""mklib82.py OUT.txt -- M8.2: the reader deck that builds the cREXX library
(lib/rxfnsb) natively on CMS with RXC82 and RXAS82.

Upstream builds library.rxbin by compiling each function module in order
(rxc -x --no-exe-import --import-rxas -i <rxas dir>), assembling it, and
concatenating the RXBINs (the rexx archive, then the rxas one); rxlink
then only merges constant pools.  RXBVM82 and RXC82 read a file of
concatenated modules directly, so LIB82 EXEC concatenates with COPYFILE.

Sources travel as hex of their EBCDIC (IBM-1047, as Hercules' 819/1047
reader) text with X'15' line ends: UNHEXT turns each back into a text
file of variable-length records (lines up to 1,180 columns, which cards
would cut at 80).  The files keep their own names (the compiler finds a
sibling function by its file name), mapped as CRXRT maps them: a name
longer than 8 characters becomes its first 3, '$', and 4 hex digits of an
FNV-1a hash (cmsfn() here, cmsname() in inc/crxrt.c)."""
import os
import re
import sys

C = '/home/claude/adesutherland/crexx/lib/rxfnsb'
ID = 'ID CMSUSER NAME LIB82'

# IBM-1047 from cp037: the six code points the two differ in
E1047 = {'[': 0xAD, ']': 0xBD, '^': 0x5F, '\xac': 0xB0, '\xdd': 0xBA, '\xa8': 0xBB}


def ebcdic(text):
    out = bytearray()
    for ch in text:
        if ch == '\n':
            out.append(0x15)
        elif ch in E1047:
            out.append(E1047[ch])
        else:
            out += ch.encode('cp037', errors='replace')
    return bytes(out)


def cmsfn(name):
    """CRXRT's CMS file name for a base name (see cmsname() in crxrt.c);
    the hash is over the IBM-1047 bytes of the lower-case name"""
    if len(name) <= 8:
        return name.upper()
    h = 2166136261
    for b in ebcdic(name.lower()):
        h ^= b
        h = (h * 16777619) & 0xFFFFFFFF
    return name[:3].upper() + '$%04X' % ((h ^ (h >> 16)) & 0xFFFF)


def main():
    out = sys.argv[1]
    body = re.search(r'set\(BIFS(.*?)\)', open(C + '/rexx/CMakeLists.txt').read(), re.S).group(1)
    bifs = [w for l in body.split('\n') for w in l.split('#')[0].split()]
    rxas = ['_elapsed', '_rxvml_address_native']      # assembled / import interface
    deck = [ID]
    names = []

    def add(fn, ft, path):
        t = open(path, encoding='utf-8').read()
        if not t.endswith('\n'):
            t += '\n'
        h = ebcdic(t).hex().upper()
        deck.append(':READ  %-8s HEX      A1' % fn)
        deck.extend(h[i:i + 78] for i in range(0, len(h), 78))
        names.append((fn, ft))

    for r in rxas:
        add(cmsfn(r), 'RXAS', '%s/rxas/%s.rxas' % (C, r))
    for b in bifs:
        add(cmsfn(b), 'CREXX', '%s/rexx/%s.crexx' % (C, b))
    fns = [f for f, _ in names]
    assert len(set(fns)) == len(fns), 'CMS name collision'
    mods = [(cmsfn(b), b) for b in bifs]
    ex = ['/* LIB82 EXEC -- M8.2: the cREXX library built with RXC82/RXAS82 */',
          "PARSE ARG FROM .",
          "IF FROM = '' THEN FROM = 1",
          "BAD = ''",
          "IF FROM = 1 THEN DO",
          "  'EXEC LIB82U'",
          "  'RXAS82 _elapsed'",
          "  IF RC <> 0 THEN BAD = BAD '_elapsed'",
          "END"]
    ex += ["N = %d" % len(mods)]
    for i, (fn, b) in enumerate(mods):
        ex += ["M.%d = '%s'" % (i + 1, b), "F.%d = '%s'" % (i + 1, fn)]
    ex += ["DO I = FROM TO N",
           "  B = M.I",
           "  'RXC82 -x --no-exe-import --import-rxas -o' B '-i a' B",
           "  IF RC <> 0 THEN DO; BAD = BAD B; ITERATE; END",
           "  'RXAS82' B",
           "  IF RC <> 0 THEN BAD = BAD B",
           "  ELSE SAY 'LIB82:' I B 'OK'",
           "END",
           "IF BAD <> '' THEN DO",
           "  SAY 'LIB82: *** FAILED:' BAD",
           "  EXIT 8",
           "END",
           "'ERASE LIBRARY RXBIN A'",
           "DO I = 1 TO N",
           "  IF I = 1 THEN 'COPYFILE' F.I 'RXBIN A LIBRARY RXBIN A'",
           "  ELSE 'COPYFILE' F.I 'RXBIN A LIBRARY RXBIN A ( APPEND'",
           "END",
           "'COPYFILE _ELAPSED RXBIN A LIBRARY RXBIN A ( APPEND'",
           "'LISTFILE LIBRARY RXBIN A ( LABEL'",
           "SAY 'LIB82: LIBRARY RXBIN BUILT'",
           "EXIT 0"]
    un = ['/* LIB82U EXEC -- unhex the library sources */']
    for fn, ft in names:
        un += ["'UNHEXT %s HEX A %s %s A'" % (fn, fn, ft),
               "IF RC = 0 THEN 'ERASE %s HEX A'" % fn]
    deck.append(':READ  LIB82    EXEC     A1')
    deck.extend(ex)
    deck.append(':READ  LIB82U   EXEC     A1')
    deck.extend(un)
    for l in deck:
        assert len(l) <= 80, l
    with open(out, 'w', encoding='latin-1') as f:
        f.write('\n'.join(l.ljust(80) for l in deck) + '\n')
    print('%d cards, %d modules, %d rxas' % (len(deck), len(bifs), len(rxas)))


if __name__ == '__main__':
    main()
