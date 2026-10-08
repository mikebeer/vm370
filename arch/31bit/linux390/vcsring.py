import re,sys
# vcsring.py LOG: decode the DMKVCS diagnostic ring from a "dcp <DMKVCS>.1900" in the operator log
lines=open(sys.argv[1],errors='replace').read().split('\n')
st=[i for i,l in enumerate(lines) if re.search(r'dcp 36738\.1900',l)][0]
mem={};last=None
for l in lines[st+1:]:
    if '/(0009)' in l: break
    m=re.search(r'([0-9A-F]{8})((?:  [0-9A-F]{8}){1,4})',l)
    if m:
        a=int(m.group(1),16)
        for k,w in enumerate(m.group(2).split()): mem[a+4*k]=bytes.fromhex(w)
        last=a
    m2=re.search(r'TO ([0-9A-F]{8}) SUPPRESSED',l)
    if m2 and last is not None:
        e=int(m2.group(1),16); a=last+16
        while a<e:
            for k in range(4): mem[a+4*k]=mem[last+4*k]
            a+=16
base=min(mem); data=b''.join(mem.get(a,b'\0\0\0\0') for a in range(base,max(mem)+4,4))
i=data.find(bytes.fromhex('E5C3D9C9D5C74040'))
nxt=int.from_bytes(data[i+8:i+12],'big'); ring=int.from_bytes(data[i+16:i+20],'big')
r=ring-base
for k in [(nxt//16+k)%32 for k in range(32)]:
    e=data[r+16*k:r+16*k+16]
    if e==bytes(16): continue
    print('%s gr1=%s psw=%s exit=%02x%s rep=%s' % (e[0:4].hex(), e[4:8].hex(), e[8:12].hex(), e[12], chr(e[13]) if e[13] else ' ', e[14:16].hex()))
