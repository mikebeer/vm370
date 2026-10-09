import sys, subprocess, pycparser
from pycparser import c_parser
ST = sys.argv[1]
units = open(ST + '/units.txt').read().split()
CPP = ['s390x-linux-gnu-gcc', '-E', '-m31', '-undef', '-nostdinc', '-D__CMS__', '-D__GNUC__=3', '-D__GNUC_MINOR__=2',
       '-D__i370__', '-D__CHAR_UNSIGNED__', '-D__attribute__(x)=', '-D__inline__=inline', '-D__inline=inline', '-D__restrict__=', '-D__restrict=', '-D__extension__=',
       '-I' + ST, '-Ixf/inc', '-I../gcclib31/src']
bad = 0
for u in units:
    src = subprocess.run(CPP + [ST + '/' + u + '.c'], capture_output=True, text=True, encoding='latin-1').stdout
    try:
        c_parser.CParser().parse(src, u)
    except Exception as e:
        bad += 1
        print(u, str(e)[:150])
print('bad', bad, 'of', len(units))
