import sys,re
d=open(sys.argv[1],'rb').read(); i=0
while i<len(d):
    a=int.from_bytes(d[i:i+4],'big'); n=int.from_bytes(d[i+4:i+8],'big'); b=d[i+8:i+8+n]; i+=8+n
    if a==int(sys.argv[2],16) if len(sys.argv)>2 else a==0x29c570:
        t=''.join(chr(c) if 32<=c<127 else '\n' for c in b)
        print('\n'.join(l for l in re.sub(r'\n+','\n',t).split('\n') if len(l)>6))
