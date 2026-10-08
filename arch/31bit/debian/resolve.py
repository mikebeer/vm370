import gzip,re,sys
pk={}; cur={}
for line in gzip.open('Packages.gz','rt',errors='replace'):
    line=line.rstrip('\n')
    if not line:
        if cur: pk.setdefault(cur['Package'],cur); cur={}
        continue
    if line[0]==' ': continue
    k,_,v=line.partition(': '); cur[k]=v
if cur: pk.setdefault(cur['Package'],cur)
prov={}
for n,p in pk.items():
    for pv in p.get('Provides','').split(','):
        pv=pv.strip()
        if pv: prov.setdefault(pv,n)
want=[n for n,p in pk.items() if p.get('Priority') in ('required','important')]
want+=sys.argv[1:]
sel=set(); stack=list(want); miss=set()
def name(alt):
    alt=re.sub(r'\(.*?\)','',alt).strip().split(':')[0]
    return alt
while stack:
    n=stack.pop()
    if n in sel: continue
    if n not in pk:
        if n in prov: n=prov[n]
        else: miss.add(n); continue
        if n in sel: continue
    sel.add(n); p=pk[n]
    for f in ('Pre-Depends','Depends'):
        for dep in p.get(f,'').split(','):
            dep=dep.strip()
            if not dep: continue
            alts=[name(a) for a in dep.split('|')]
            if any(a in sel for a in alts): continue
            for a in alts:
                if a in pk or a in prov: stack.append(a); break
            else: miss.add(dep)
tot=sum(int(pk[n]['Size']) for n in sel)
print(len(sel),'packages, %.1f MB'%(tot/1e6), 'missing:',sorted(miss)[:20], file=sys.stderr)
for n in sorted(sel): print(pk[n]['Filename'], pk[n]['Size'], pk[n].get('SHA256',''))
