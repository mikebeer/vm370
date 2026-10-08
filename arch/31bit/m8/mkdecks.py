#!/usr/bin/env python3
"""M8: reader decks for CMSUSER from the cross build.
   TEXT decks: ID card + the CMS TEXT cards (EBCDIC, 80 bytes each).
   m8files.txt: ID card, then ':READ  FN FT A1' + lines, for READCARD *
   (ASCII; devinit ... ascii eof trunc): REXX sources, and RXBIN modules
   as hex text (UNHEX rebuilds the exact bytes)."""
import sys, os
IO = sys.argv[1]
def textdeck(name, text):
    card = ('ID CMSUSER NAME %s TEXT' % name).ljust(80).encode('cp037')
    open(os.path.join(IO, name.lower() + '.rdr'), 'wb').write(card + open(text, 'rb').read())
for n, t in (('RXC8', 'rxc.text'), ('RXAS8', 'rxas.text'), ('RXBVM8', 'rxbvm.text'), ('UNHEX', 'unhex.text')):
    textdeck(n, t)
lines = ['ID CMSUSER NAME M8 FILES']
def add(fn, ft, body):
    lines.append(':READ  %-8s %-8s A1' % (fn, ft)); lines.extend(body)
for arg in sys.argv[2:]:
    path, name = arg.split('=')
    fn, ft = name.split('.')
    data = open(path, 'rb').read()
    if ft == 'HEX':
        h = data.hex().upper()
        add(fn, ft, [h[i:i + 78] for i in range(0, len(h), 78)])
    else:
        add(fn, ft, [l.rstrip()[:80] for l in data.decode('latin-1').split('\n')])
open(os.path.join(IO, 'm8files.txt'), 'w').write('\n'.join(lines) + '\n')
print(len(lines), 'lines in m8files.txt')
