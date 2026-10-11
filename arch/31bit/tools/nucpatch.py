import re,sys
src,dst=sys.argv[1],sys.argv[2]; only=sys.argv[3].split(',') if len(sys.argv)>3 else None
d=bytearray(open(src,'rb').read())
cards=len(d)//80
cur=None; buf={}
for ci in range(cards):
    c=d[ci*80:(ci+1)*80]
    t=bytes(c[1:4])
    if t==b'\xc5\xe2\xc4' and int.from_bytes(c[14:16],'big')==1 and c[24]==0:
        cur=bytes(c[16:24]).decode('cp500').strip()
    elif t==b'\xe3\xe7\xe3' and cur:
        addr=int.from_bytes(c[5:8],'big'); n=int.from_bytes(c[10:12],'big')
        m=buf.setdefault(cur,{})
        for k in range(n): m[addr+k]=ci*80+16+k
tot=0
for mod,m in buf.items():
    if only and mod not in only: continue
    if not m: continue
    top=max(m)+1
    b=bytes(d[m[i]] if i in m else 0 for i in range(top))
    for x in re.finditer(rb'\xb1(?=...\x41\xf0..\x56\xf0..\x0b\x0f)',b,re.S):
        o=x.start()+4+4   # the O instruction, then BSM: NOPs, CC kept, AMODE 31 kept
        for k,v in enumerate(b'\x07\x00\x07\x00\x07\x00'): d[m[o+k]]=v
        tot+=1; print(mod, hex(o))
open(dst,'wb').write(d); print('patched',tot)
