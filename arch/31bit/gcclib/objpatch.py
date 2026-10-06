import sys, re
def cards(path):
    d=open(path,'rb').read(); return [bytearray(d[i:i+80]) for i in range(0,len(d),80)]
TXT=bytes([0x02])+'TXT'.encode('cp037')
def stream(cs):
    data=bytearray(); where=[]
    for ci,c in enumerate(cs):
        if c[0:4]==TXT:
            n=int.from_bytes(c[10:12],'big')
            for k in range(n): data.append(c[16+k]); where.append((ci,16+k))
    return data, where
def scan(path):
    cs=cards(path); data,where=stream(cs)
    for m in re.finditer(rb'\x80\x00[\x00-\xff]{2}',bytes(data)):
        i=m.start()
        ctx=bytes(data[max(0,i-8):i+8]).hex()
        print(path.split('/')[-1], i, ctx)
    return cs,data,where
if __name__=='__main__':
    for p in sys.argv[1:]: scan(p)
