import re
from objpatch import cards, stream
def patch(fin, fout, rules):
    cs=cards(fin); data,where=stream(cs); b=bytes(data); n=0
    for pat, off, new in rules:
        for m in re.finditer(pat, b):
            i=m.start()+off
            for k,v in enumerate(new):
                ci,cj=where[i+k]; cs[ci][cj]=v
            n+=1
    # drop CP separator cards (non-object, non-library?) -- keep all cards as read except
    # those that are separator cards (first card(s) before data)
    open(fout,'wb').write(b''.join(bytes(c) for c in cs))
    return n
r_gcc=[(rb'\xb2\x0a\x00\x00\x80\x00\xc0[\x00-\xff]',4,bytes.fromhex('ac00d010')),
       (rb'\xb2\x0a\x20\x00\x80\x00\xcc\x82',4,bytes.fromhex('8000d010'))]
r_brx=[(rb'\xb2\x0a\x00\x00\x80\x00\xc0\x2b',4,bytes.fromhex('ac00c3b4'))]
print('gcclib text',patch('gcclib-text.pch','gcclib-text.new',r_gcc))
print('gcclib txtlib',patch('gcclib-txtlib.pch','gcclib-txtlib.new',r_gcc))
print('brexx text',patch('brexx-text.pch','brexx-text.new',r_brx))
