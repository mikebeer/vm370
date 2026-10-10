#!/usr/bin/env python3
"""fold80.py IN OUT -- fold Smalltalk source lines to 80 columns for CMS
(F 80 card files).  Breaks only at a blank outside a string literal
('...') and a character literal ($c), where a line end is the same white
space to the Smalltalk scanner; comments ("...") may span lines."""
import sys

def breaks(line):
    ok, q, i = [], None, 0
    while i < len(line):
        c = line[i]
        if q:
            if q == '"' and c == ' ': ok.append(i)  # comments may span lines
            if c == q:
                if q == "'" and line[i + 1:i + 2] == "'": i += 1
                else: q = None
        elif c == '$': i += 1
        elif c in "'\"": q = c
        elif c == ' ': ok.append(i)
        i += 1
    return ok

def fold(line, w=80):
    out, ind = [], len(line) - len(line.lstrip(' '))
    while len(line) > w:
        cut = [b for b in breaks(line) if ind < b <= w]
        if not cut: break                       # cannot fold: left long
        b = cut[-1]
        out.append(line[:b].rstrip())
        line = ' ' * min(ind + 4, 20) + line[b + 1:].lstrip(' ')
    out.append(line)
    return out

src, dst = sys.argv[1:3]
lines = open(src, encoding='utf-8').read().split('\n')
res = [x for l in lines for x in fold(l.rstrip())]
long = [x for x in res if len(x) > 80]
open(dst, 'w', encoding='utf-8').write('\n'.join(res))
if long: print('fold80: %s: %d lines still over 80' % (src, len(long))); sys.exit(1)
