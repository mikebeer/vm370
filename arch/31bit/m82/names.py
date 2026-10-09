#!/usr/bin/env python3
"""M8.2: names.txt -- GCC380 writes external names as 8 upper-case
characters, so every external the cREXX objects define that is longer than
8 characters, or not unique in that form, gets a short alias CXnnnnn.

    names.py OBJDIR STAGE NAMES.TXT  (OBJDIR: pre.sh's objects; prep.py
    STAGE NAMES.TXT then renames them in the staged sources)"""
import subprocess, sys, os, glob
objdir, stage = sys.argv[1:3]
units = open(os.path.join(stage, 'units.txt')).read().split()
defs = set()
for u in units:
    out = subprocess.run(['s390x-linux-gnu-nm', os.path.join(objdir, u + '.o')],
                         capture_output=True, text=True).stdout
    for l in out.splitlines():
        p = l.split()
        if len(p) == 3 and p[1] in 'TDBRCG' and not p[2].startswith('__'):
            defs.add(p[2])
short = {}
for d in defs:
    short.setdefault(d.upper()[:8], []).append(d)
names = sorted(d for d in defs if len(d) > 8 or len(short[d.upper()[:8]]) > 1)
# keep the numbers already given (so a unit rebuilt alone still matches the
# others); a new name gets the next free number
old = {}
if os.path.exists(sys.argv[3]):
    for l in open(sys.argv[3]):
        p = l.split()
        if len(p) == 2:
            old[p[0]] = int(p[1][2:])
nxt = max(old.values(), default=-1) + 1
num = {}
for n in names:
    if n in old:
        num[n] = old[n]
    else:
        num[n] = nxt
        nxt += 1
with open(sys.argv[3], 'w') as f:
    for n in sorted(names, key=lambda n: num[n]):
        f.write('%s CX%05d\n' % (n, num[n]))
print('%d externals, %d renamed' % (len(defs), len(names)))
