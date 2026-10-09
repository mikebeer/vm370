#!/bin/bash
# mkguide.sh OUT.docx : two passes -- the second carries a static table of contents
set -e
H=$(cd "$(dirname "$0")" && pwd); OUT=$(readlink -f "$1"); T=$(mktemp -d)
SOFF=${SOFF:-/root/.claude/skills/synced/004a80ff-5a8f-4597-8d6b-9c2731b8994a_5fb75d53-748b-40b7-b60d-47cbebea1b46/docx/scripts/office/soffice.py}
cd $H; node mkmanual.js $T/p1.docx >/dev/null
python3 $SOFF --headless --convert-to pdf --outdir $T $T/p1.docx >/dev/null 2>&1
python3 - $T/p1.pdf $T/toc.json <<'PY'
import sys, subprocess, json, re
pdf, out = sys.argv[1], sys.argv[2]
n = int(re.search(r'Pages:\s+(\d+)', subprocess.run(['pdfinfo', pdf], capture_output=True, text=True).stdout).group(1))
heads = json.load(open('headings.json'))
items, start = [], None
for pg in range(1, n + 1):
    txt = subprocess.run(['pdftotext', '-f', str(pg), '-l', str(pg), '-layout', pdf, '-'], capture_output=True, text=True).stdout
    if start is None and 'Preface' in txt and 'How this manual' in txt: start = pg
    if start is None: continue
    lines = [l.strip() for l in txt.splitlines()]
    for lvl, h in heads:
        if any(l == h for l in lines) and not any(i[1] == h for i in items):
            items.append([lvl, h, pg - start + 1])
order = {h: k for k, (l, h) in enumerate(heads)}
items.sort(key=lambda i: order[i[1]])
json.dump(items, open(out, 'w'))
print(len(items), 'contents entries')
PY
TOCJSON=$T/toc.json node mkmanual.js "$OUT"
rm -rf $T
