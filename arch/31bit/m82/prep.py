#!/usr/bin/env python3
"""M8.2: stage current cREXX for a native build on CMS (GCC380, GCCLIB31).

    prep.py STAGE            -> STAGE/*.c, *.h with CMS names, map.txt

- every source (srcs.txt) and every header it reaches gets a CMS file name
  of at most 8 characters; #include lines are rewritten to "name.h";
- the shims in inc/ (stdint.h, sys/stat.h, ...) are staged the same way;
- every .c begins with #include "crxcms.h" (the shim layer) and
  "crxnames.h" (8-character external names, written by names.py);
- PATCHES apply exact, asserted replacements (the native-CMS deltas).
"""
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
C = '/home/claude/adesutherland/crexx'
H = '/home/claude/crexx-host'
SHIM = os.path.join(HERE, 'inc')
GCCLIB = os.path.join(HERE, '..', 'gcclib31', 'src')
INC = [SHIM, H + '/generated', C + '/interpreter', C + '/interpreter/rxvmplugin',
       C + '/assembler', C + '/binutils/include', C + '/rxpa', C + '/platform',
       C + '/avl_tree', C + '/utf8', C + '/inc',
       C + '/interpreter/rxvmplugin/rxvmplugins/mc_decimal/decnumber',
       C + '/compiler', H + '/compiler', H + '/assembler']
# GCCLIB31's own headers stay on its disk under their own names
LIBHDR = {f for f in os.listdir(GCCLIB) if f.endswith('.h')}

# The native-CMS deltas: (file basename, old, new), each must match once.
NATIVE_FS = ('(defined(CREXX_CMS_ELF) && defined(CREXX_CMS_DIRENT))',
             '((defined(CREXX_CMS_ELF) && defined(CREXX_CMS_DIRENT)) || defined(CREXX_CMS_GCC))')
PATCHES = [
    ('platform.c', NATIVE_FS[0], NATIVE_FS[1], 4),
    ('platform.c', '#if defined(CREXX_CMS_ELF) && defined(CREXX_CMS_DIRENT)\n',
     '#if (defined(CREXX_CMS_ELF) && defined(CREXX_CMS_DIRENT)) || defined(CREXX_CMS_GCC)\n', 1),
    ('platform.c', '#elif defined(CREXX_CMS_ELF)\n        FILE *probe',
     '#elif defined(CREXX_CMS_ELF) || defined(CREXX_CMS_GCC)\n        FILE *probe', 1),
    ('platform.c', '#elif defined(CREXX_CMS_ELF)\n            FILE *probe',
     '#elif defined(CREXX_CMS_ELF) || defined(CREXX_CMS_GCC)\n            FILE *probe', 1),
    # say why a module did not load (the loader's own error text)
    ('rxvmmain.c', 'fprintf(stderr, "ERROR reading module file %s\\n", file_name);',
     '{ const char *e = rxbin_last_error(); fprintf(stderr, "ERROR reading module file %s%s%s\\n", file_name, e ? ": " : "", e ? e : ""); }', 1),
]

UNRESOLVED = set()
LEX = re.compile(r'(/\*.*?\*/|//[^\n]*|"(?:\\.|[^"\\\n])*"|\'(?:\\.|[^\'\\\n])*\'|[A-Za-z_][A-Za-z_0-9]*)', re.S)


def rename(text, names):
    """Replace identifiers per names, outside comments and literals."""
    def sub(m):
        t = m.group(0)
        return names.get(t, t)
    return LEX.sub(sub, text)


INCRE = re.compile(r'^(\s*#\s*include\s*)([<"])([^>"]+)[>"](.*)$')


def find(name, quote, base):
    """Resolve an include as the PC compiler would; None if it is GCCLIB's."""
    if quote == '"':
        p = os.path.normpath(os.path.join(base, name))
        if os.path.isfile(p):
            return p
    for d in INC:
        p = os.path.normpath(os.path.join(d, name))
        if os.path.isfile(p):
            return p
    if os.path.basename(name) in LIBHDR or name in LIBHDR:
        return None
    UNRESOLVED.add(name)   # a dead #if branch (windows.h, pthread.h ...)
    return None


class Namer:
    def __init__(self):
        self.by_path = {}
        self.units = set()
        self.used = {'C': set(), 'H': set()}
        # never shadow GCCLIB31's headers or the shims' fixed names
        self.used['H'] |= {f[:-2].upper() for f in LIBHDR}

    def name(self, path):
        if path in self.by_path:
            return self.by_path[path]
        ft = 'C' if path.endswith('.c') else 'H'
        if ft == 'C' and path not in self.units:
            ft = 'H'   # a .c #included by another: staged as an H file
        rel = os.path.relpath(path, SHIM)
        stem = os.path.splitext(rel if not rel.startswith('..') else os.path.basename(path))[0]
        stem = re.sub('[^A-Z0-9]', '', stem.upper().replace('/', ''))
        if stem[:1].isdigit():
            stem = 'X' + stem
        cand = stem[:8]
        n = 0
        while cand in self.used[ft]:
            n += 1
            sfx = '%d' % n
            cand = stem[:8 - len(sfx)] + sfx
        self.used[ft].add(cand)
        self.by_path[path] = (cand, ft)
        return self.by_path[path]


def main():
    stage = sys.argv[1]
    names = {}
    if len(sys.argv) > 2:   # names.txt from names.py: rename externals
        for l in open(sys.argv[2]):
            a, b = l.split()
            names[a] = b
    os.makedirs(stage, exist_ok=True)
    srcs = [l.strip() for l in open(os.path.join(HERE, 'srcs.txt')) if l.strip()]
    namer = Namer()
    rt = os.path.join(SHIM, 'crxrt.c')
    lg = os.path.join(SHIM, 'crxlgcc.c')
    namer.units = set(srcs) | {rt, lg}
    for fixed in ('crxcms.h',):
        namer.by_path[os.path.join(SHIM, fixed)] = (fixed[:-2].upper(), 'H')
        namer.used['H'].add(fixed[:-2].upper())
    todo = list(srcs) + [os.path.join(SHIM, 'crxcms.h'), rt, lg]
    applied = {}
    units = []
    done = set()
    while todo:
        path = todo.pop()
        if path in done:
            continue
        done.add(path)
        fn, ft = namer.name(path)
        text = open(path, encoding='latin-1').read()
        b = os.path.basename(path)
        for pf, old, new, count in PATCHES:
            if pf == b:
                assert text.count(old) == count, (b, old[:40], text.count(old))
                text = text.replace(old, new)
                applied[(pf, old)] = True
        if names:
            text = rename(text, names)
        out = []
        if ft == 'C':
            units.append(fn.lower())
        if ft == 'C' and path not in (rt, lg):
            out += ['#include "crxcms.h"']
        for line in text.split('\n'):
            if re.match(r'\s*#\s*line\b', line):
                continue   # generators' #line: long PC paths, no use on CMS
            m = INCRE.match(line)
            if m:
                tgt = find(m.group(3), m.group(2), os.path.dirname(path))
                if tgt is not None:
                    todo.append(tgt)
                    tf, _ = namer.name(tgt)
                    line = '%s"%s.h"%s' % (m.group(1), tf.lower(), m.group(4))
            out.append(line)
        open(os.path.join(stage, '%s.%s' % (fn.lower(), ft.lower())), 'w',
             encoding='latin-1').write('\n'.join(out))
    for pf, old, new, count in PATCHES:
        assert (pf, old) in applied, ('patch not applied', pf, old[:40])
    open(os.path.join(stage, 'units.txt'), 'w').write('\n'.join(sorted(units)) + '\n')
    with open(os.path.join(stage, 'map.txt'), 'w') as f:
        for p, (fn, ft) in sorted(namer.by_path.items(), key=lambda x: x[1]):
            f.write('%-8s %s %s\n' % (fn, ft, p))
    print('%d files staged; left alone: %s' % (len(done), ' '.join(sorted(UNRESOLVED))))


if __name__ == '__main__':
    main()
