#!/bin/bash
# Validate XAOPS.MACRO by differential assembly.
#
# The obvious way to check a macro library is to assemble it and read the
# listing against a table of expected opcodes by eye. This does better: it
# assembles each instruction TWICE in one program -- once as the assembler's
# own built-in instruction, once through the XAOPS macro -- and diffs the
# generated object code. If they are identical, the macro is right, including
# its base-register and displacement resolution.
#
# That matters because the encodings were never the doubtful part. Whether an
# S-type address constant resolves through the active USING exactly as an
# S-format instruction's operand does was the doubtful part, and only a
# byte-for-byte comparison settles it.
#
# Requires z390 (https://github.com/z390development/z390) and a JDK.
#
#     ./validate.sh /path/to/z390
#
# z390 is used because it is an independent assembler that already knows the
# channel-subsystem instructions -- which is also why it could confirm the
# opcodes. CE's own ASSEMBLE predates them and cannot play this role: there,
# the macros are the only way to get the instructions at all.
set -e
Z390=${1:?usage: validate.sh /path/to/z390}
HERE=$(cd "$(dirname "$0")" && pwd)
WORK=$(mktemp -d)
trap 'rm -rf "$WORK"' EXIT

# z390 wants one macro per file, named for the macro. A CMS MACLIB holds many
# per member, so XAOPS.MACRO has to be split. And each macro is renamed with
# an X prefix so the assembler's built-in cannot shadow it -- which is the
# whole point: we need BOTH forms in one assembly.
mkdir -p "$WORK/mac"
python3 - "$HERE/../XAOPS.MACRO" "$WORK/mac" <<'PY'
import re, sys, os
src, out = sys.argv[1], sys.argv[2]
cur, inmac, name = [], False, None
for l in open(src, encoding='utf-8', errors='replace'):
    body = l[:71].rstrip()
    if re.match(r'^\s+MACRO\s*$', body):
        inmac, cur, name = True, [body], None
        continue
    if not inmac:
        continue
    if name is None and body.strip() and body.lstrip()[:1] not in ('.', '*'):
        f = body.split()
        name = f[1] if not body[:1].isspace() else f[0]
        body = re.sub(r'(\s)' + name + r'(\s|$)', r'\1X' + name + r'\2',
                      body, count=1)
    cur.append(body)
    if re.match(r'^\s+MEND', body):
        open(os.path.join(out, 'X%s.MAC' % name), 'w').write('\n'.join(cur) + '\n')
        inmac = False
PY

CLASSES="$Z390/classes"
if [ ! -d "$CLASSES" ]; then
    mkdir -p "$CLASSES"
    javac -nowarn -d "$CLASSES" -sourcepath "$Z390/src" \
          "$Z390/src/mz390.java" "$Z390/src/az390.java" 2>/dev/null
fi

cp "$HERE/XCMP.MLC" "$WORK/"
cd "$WORK"
java -cp "$CLASSES" mz390 XCMP.MLC \
     "sysmac(+$WORK/mac+$Z390/mac)" "syscpy(+$WORK/mac+$Z390/mac)" >/dev/null 2>&1

python3 - XCMP.PRN <<'PY'
import re, sys
lines = open(sys.argv[1], encoding='utf-8', errors='replace').read().split('\n')
def stmt(l):
    m = re.match(r'^([0-9A-F]{6})\s+([0-9A-F]*)\s', l)
    mm = re.search(r'\(\d+/\d+\)\d+(\+?)\s*(.*)$', l)
    return (m.group(2), mm.group(1) == '+', mm.group(2).rstrip()) if m and mm else None
rows = [r for r in (stmt(l) for l in lines) if r]
builtin, macro = {}, {}
for i, (obj, gen, txt) in enumerate(rows):
    f = txt.split()
    if not f or gen:
        continue
    op = f[0]
    if op.startswith('X') and len(op) > 1:
        got = ''
        for j in range(i + 1, len(rows)):
            if not rows[j][1]:
                break
            got += rows[j][0]
        macro[op[1:]] = got
    elif obj:
        builtin.setdefault(op, obj)
print("%-10s %-16s %-16s %s" % ("instruction", "built-in", "XAOPS macro", "verdict"))
print("-" * 58)
bad = 0
for k in ("SSCH","MSCH","TSCH","STSCH","CSCH","HSCH","RSCH","SAL","TPI",
          "STCRW","BSM","BASSM"):
    a, b = builtin.get(k, ''), macro.get(k, '')
    same = bool(a) and a == b
    bad += not same
    print("%-10s %-16s %-16s %s" % (k, a, b, "MATCH" if same else "DIFFERS"))
print("-" * 58)
print("%d of 12 differ" % bad)
sys.exit(1 if bad else 0)
PY
