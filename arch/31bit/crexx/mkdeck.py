#!/usr/bin/env python3
"""M5e: build an 80-column reader deck of cREXX sources for CMSUSER.

    mkdeck.py OUT.txt FILE[=FN.FT] ...

ID card, then ':READ  FN FT A1' per file, so 'READCARD *' unpacks it
(READCARD ignores the filemode and writes to A; CRXMAKE copies to D).
 - tabs are expanded to 8;
 - C/H lines over 80 columns are split at column 79 with a backslash-
   newline: translation phase 2 splices them back before tokenisation,
   string literals included;
 - other file types must already fit in 80 columns.
FN/FT default to the upper-cased name and extension, FN cut to 8.
"""
import os
import sys


def cards(path, ftype):
    out = []
    for line in open(path, encoding='latin-1').read().split('\n'):
        line = line.rstrip('\r').expandtabs(8).rstrip()
        if ftype in ('C', 'H'):
            while len(line) > 80:
                out.append(line[:79] + '\\')
                line = line[79:]
        elif len(line) > 80:
            raise SystemExit('%s: line over 80 columns: %r' % (path, line))
        out.append(line)
    while out and out[-1] == '':
        out.pop()
    return out


def main():
    if len(sys.argv) < 3:
        raise SystemExit(__doc__)
    deck = ['ID CMSUSER NAME CREXX SRC']
    for arg in sys.argv[2:]:
        path, _, name = arg.partition('=')
        if not name:
            base = os.path.basename(path)
            fn, _, ft = base.partition('.')
            name = fn[:8].upper() + '.' + ft.upper()
        fn, ft = name.split('.')
        deck.append(':READ  %-8s %-8s A1' % (fn, ft))
        deck.extend(cards(path, ft))
    with open(sys.argv[1], 'w', encoding='latin-1') as f:
        for c in deck:
            f.write(c.ljust(80) + '\n')
    print('%s: %d cards' % (sys.argv[1], len(deck)))


if __name__ == '__main__':
    main()
