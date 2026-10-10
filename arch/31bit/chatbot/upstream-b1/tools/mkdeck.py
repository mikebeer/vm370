#!/usr/bin/env python3
"""Build the card decks for loading the CHATBOT guest on CMS.

usage: mkdeck.py <files dir> <out deck> [--binary]

Every regular file in <files dir> becomes a  :READ FN FT A  card followed by its
lines padded to 80 columns (ASCII; the PC-to-VM/370 transfer translates to EBCDIC).
Lines longer than 80 columns are refused.  File names are FN.FT (upper-case).
Load on CMS with   READCARD  (it reads the :READ cards and creates the files).
"""
import sys, os

def main():
    d, out = sys.argv[1], sys.argv[2]
    n = 0
    with open(out, 'w', newline='\n') as o:
        for name in sorted(os.listdir(d)):
            p = os.path.join(d, name)
            if not os.path.isfile(p) or '.' not in name:
                continue
            fn, ft = name.upper().rsplit('.', 1)
            lines = open(p, encoding='ascii').read().split('\n')
            if lines and lines[-1] == '':
                lines.pop()
            o.write((':READ %s %s A' % (fn, ft)).ljust(80) + '\n')
            for l in lines:
                if len(l) > 80:
                    sys.exit('%s: line longer than 80 columns: %r' % (name, l[:40]))
                o.write(l.ljust(80) + '\n')
            n += 1
    print('%s: %d files' % (out, n))

main()
