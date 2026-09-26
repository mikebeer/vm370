#!/usr/bin/env python3
"""
What happens to VM/370 CE's shared segments when segments become 1 MB.

CP runs 64 KB segments; ESA/390 has only 1 MB segments, and a segment is
shared or not as a whole. DMKSNT's NAMESYS macros name each saved system's
shared segments in SYSHRSG (64 KB units) and its saved pages in SYSPGNM
(4 KB units). Sixteen 64 KB segments fit in one ESA/390 segment.

So the question is not "how much does granularity change" -- it is which
pages are PRIVATE today and would become COMMON under 1 MB segments. That
is what this computes.

    python3 snt-collisions.py /path/to/source/cp/DMKSNT.ASSEMBLE

Nothing about the SYSHRSG-to-page mapping is assumed: each shared segment's
sixteen pages are checked against that entry's own SYSPGNM, and a shared
segment whose pages are not all saved is reported rather than converted.

See docs/04-SHARED-SEGMENTS.md for what the output means.
"""
import re
import sys

PAGE = 4096
PAGES_PER_S370_SEG = 16          # 64 KB segment
PAGES_PER_ESA_SEG = 256          # 1 MB segment


def statements(path):
    """Join continued assembler statements. Column 72 is the continuation
    column; columns beyond 71 are not part of the statement."""
    out, cur = [], ''
    with open(path, encoding='utf-8', errors='replace') as fh:
        for line in fh:
            body = line.rstrip('\n')[:71].rstrip()
            cont = len(line.rstrip('\n')) > 71 and line.rstrip('\n')[71] not in ' '
            if body[:1] in ('*', '.'):
                continue
            cur += body if not cur else body.strip()
            if cont:
                continue
            if cur.strip():
                out.append(cur)
            cur = ''
    if cur.strip():
        out.append(cur)
    return out


def ranges(text):
    """Expand '0-15,32,3968-4015' into a set of ints."""
    vals = set()
    for part in text.split(','):
        part = part.strip()
        if '-' in part:
            lo, hi = part.split('-', 1)
            if lo.strip().isdigit() and hi.strip().isdigit():
                vals |= set(range(int(lo), int(hi) + 1))
        elif part.isdigit():
            vals.add(int(part))
    return vals


def entries(path):
    found = []
    for stmt in statements(path):
        if 'NAMESYS' not in stmt or stmt[:1].isspace():
            continue
        hrsg = re.search(r'SYSHRSG=\(([^)]*)\)', stmt)
        pgnm = re.search(r'SYSPGNM=\(([^)]*)\)', stmt)
        shared_segs = sorted(ranges(hrsg.group(1))) if hrsg else []
        saved = ranges(pgnm.group(1)) if pgnm else set()
        shared_pages = set()
        for s in shared_segs:
            shared_pages |= set(range(s * PAGES_PER_S370_SEG,
                                      (s + 1) * PAGES_PER_S370_SEG))
        found.append({
            'name': stmt.split()[0],
            'shared_segs': shared_segs,
            'saved': saved,
            'shared_pages': shared_pages,
            'private': saved - shared_pages,
            'unsaved_shared': shared_pages - saved,
        })
    return found


def mb(page):
    return page * PAGE / (1024 * 1024)


def main():
    path = sys.argv[1] if len(sys.argv) > 1 else 'DMKSNT.ASSEMBLE'
    ents = entries(path)
    if not ents:
        sys.exit(f'no NAMESYS entries found in {path}')

    # Every ESA/390 segment that any saved system forces to be common.
    common = {}
    for e in ents:
        for p in e['shared_pages']:
            common.setdefault(p // PAGES_PER_ESA_SEG, set()).add(e['name'])

    print('Saved systems and their shared segments')
    print('-' * 72)
    print(f'{"name":10} {"64 KB segs":12} {"shared at":>16}  '
          f'{"1 MB seg":9} consistency')
    for e in ents:
        if not e['shared_segs']:
            print(f'{e["name"]:10} {"(not shared)":12} {"":>16}  {"-":9}')
            continue
        esa = sorted({p // PAGES_PER_ESA_SEG for p in e['shared_pages']})
        span = (f'{e["shared_segs"][0]}-{e["shared_segs"][-1]}'
                if len(e['shared_segs']) > 1 else str(e['shared_segs'][0]))
        at = f'{mb(min(e["shared_pages"])):.3f}-{mb(max(e["shared_pages"]) + 1):.3f} MB'
        note = 'ok' if not e['unsaved_shared'] else \
            f'{len(e["unsaved_shared"])} shared pages not in SYSPGNM'
        print(f'{e["name"]:10} {span:12} {at:>16}  {str(esa):9} {note}')

    print('\nESA/390 segments forced common, and by whom')
    print('-' * 72)
    for seg, names in sorted(common.items()):
        flag = '  <-- several' if len(names) > 1 else ''
        print(f'  segment {seg:3} ({seg}-{seg + 1} MB)  '
              f'{", ".join(sorted(names))}{flag}')

    print('\nWhat actually breaks: private pages that become common')
    print('-' * 72)
    any_exposed = False
    for e in ents:
        exposed = sorted(p for p in e['private']
                         if p // PAGES_PER_ESA_SEG in common)
        if not exposed:
            continue
        any_exposed = True
        segs = sorted({p // PAGES_PER_ESA_SEG for p in exposed})
        made_by = sorted(set().union(*(common[s] for s in segs)))
        print(f'  {e["name"]}: {len(exposed)} private pages '
              f'({mb(min(exposed)):.3f}-{mb(max(exposed) + 1):.3f} MB) '
              f'fall in segment(s) {segs}')
        print(f'      made common by: {", ".join(made_by)}')
    if not any_exposed:
        print('  none')

    distinct = {s for e in ents for s in e['shared_segs']}
    print(f'\n{len(distinct)} distinct 64 KB shared segments '
          f'-> {len(common)} distinct 1 MB segments')


if __name__ == '__main__':
    main()
