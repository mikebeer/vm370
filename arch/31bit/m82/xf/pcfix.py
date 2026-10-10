#!/usr/bin/env python3
"""pcfix.py IN.c OUT.c -- M8.2 test aid: make an xform output unit build for
s390x Linux (64-bit, big-endian) so the transformed cREXX can run under
qemu-s390x on the PC.  If that copy works and the GCC380 one does not, the
fault is GCC380's code generation, not xform.
- GCCLIB's char* va_list becomes the compiler's (real varargs)
- CRXLGCC's 32-bit words: unsigned long -> unsigned int, (long) -> (int)"""
import re, sys
s = open(sys.argv[1]).read()
s = s.replace('typedef char *va_list;', 'typedef __builtin_va_list va_list;')
vas = set(re.findall(r'\bva_list (\w+)', s)) | {'ap'}
for v in vas:
    s = re.sub(r'\*\(\((\w[\w\s\*]*?)\s*\*\)\s*\(\(%s \+= sizeof\(\1\), %s - \(sizeof\(\1\)\)\)\)\)' % (v, v),
               r'__builtin_va_arg(%s, \1)' % v, s)
    s = re.sub(r'\b%s = \(\(char \*\) \(&(\w+)\)\) \+ 4;' % v, r'__builtin_va_start(%s, \1);' % v, s)
    s = re.sub(r'\b%s = 0;' % v, '__builtin_va_end(%s);' % v, s)
# GCCLIB's CRAB (stdio and errno through R13) -> the C library's
s = s.replace('__crx_crab()->gstdout', 'stdout').replace('__crx_crab()->gstderr', 'stderr')
s = s.replace('__crx_crab()->gstdin', 'stdin').replace('__crx_crab()->gerrno', '(*__errno_location())')
s = 'extern struct FILE *stdout, *stderr, *stdin; extern int *__errno_location(void);\n' + s
# copying a va_list
s = re.sub(r'\b(\w+) = ap;', r'__builtin_va_copy(\1, ap);', s)
# 31-bit layout assertions do not hold on 64-bit
s = re.sub(r'^typedef char \w*must_be\w*\[.*\];$', '', s, flags=re.M)
if 'crxadd64' in s and 'typedef unsigned long u32;' in s:
    s = s.replace('typedef unsigned long u32;', 'typedef unsigned int u32;')
    s = s.replace('(long)', '(int)').replace('(long) ', '(int) ')
    s = s.replace('long crxsw64(long long a)', 'long crxsw64(long long a)')
open(sys.argv[2], 'w').write(s)
