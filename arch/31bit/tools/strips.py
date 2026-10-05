#!/usr/bin/env python3
"""Inventory of CP's 24-bit strip idioms, for M2 step 2 (CP at AMODE 31).

`LA Rx,0(,Ry)` clears bits 0-7 in AMODE 24 and only bit 0 in AMODE 31, so
every site that uses it to drop a flag or length byte from a packed pointer
(I-126, I-128) stops stripping the instant CP's PSW goes AMODE 31.  This lists
them all, with what the sweep needs to know about each one:

  kind   LA-self   LA Rx,0(,Rx)            -> N Rx,XRIGHT24           (+0 bytes)
         LA-copy   LA Rx,0(,Ry)            -> LR Rx,Ry / N Rx,XRIGHT24 (+2)
         mask24    N/=X'00FFFFFF'/XRIGHT24  already explicit, mode-independent
         xpagnum   N ..,XPAGNUM            X'00FFF000': page mask, 24-bit
         icm3/stcm3  3-byte address fields  structural (M4), listed for the count
  cc     Y when a condition-code test follows before anything else sets the
         CC -- N sets the CC, LA did not, so such a site needs the shift pair
         SLL 8 / SRL 8 (+4) or a different home for the mask.

Two more kinds, found by running rather than by this scan (I-228, I-229) and
listed since so the scan is complete:

         balr0     BALR Rx,0 / BALR Rx,R0    byte 0 of Rx held ILC, CC and
                   mask in AMODE 24; nothing in AMODE 31.  Those followed by
                   SPM Rx (or STCM Rx,8) are CC saves -> IPM Rx (XAOPS); the
                   rest only establish a base and are harmless.
         spm       every SPM Rx, with the instruction that last set Rx
                   -- a BALR (I-228), a BAL link register (I-229: the trace
                   subroutines), or an IPM once converted.

Usage: strips.py [--csv out.csv] [--module DMKxxx]
"""
import csv, glob, os, re, sys

SRC = '/home/claude/vmce/source/cp'
LA_SELF = re.compile(r'^\S*\s+LA\s+(R\d+|\d+),0\((?:0?,)?(R\d+|\d+)\)')
MASK24 = re.compile(r"\bN\s+(R?\d+),(XRIGHT24|=X'00FFFFFF'|=A\(X'FFFFFF'\)|=XL4'00FFFFFF')")
XPAG = re.compile(r"\bN\s+(R?\d+),XPAGNUM")
ICM3 = re.compile(r"\b(ICM|STCM)\s+(R?\d+),(7|B'0111'),")
SETS_CC = re.compile(r'^\S*\s+(A|AL|AR|ALR|S|SL|SR|SLR|N|NR|O|OR|X|XR|C|CL|CR|CLR|CLI|CLC|CLM|TM|LTR|LCR|LPR|LNR|ICM|LRA|SLA|SRA|SLDA|SRDA|AH|SH|MVCL|CLCL|TRT|CS|CDS|BAL|BALR|BAS|BASR|SVC|CALL|TRANS|GOTO|EXIT|ENTER|LCTL|STCK|TS|ED|EDMK|AP|SP|CP|ZAP|MP|DP|SRP|LPSW)\b')
BRANCH_CC = re.compile(r'^\S*\s+(BC|BCR|BE|BNE|BZ|BNZ|BH|BL|BNH|BNL|BO|BNO|BM|BP|BNM|BNP|BER|BNER|BZR|BNZR|BHR|BLR|BNHR|BNLR|BOR|BNOR|BMR|BPR|BNMR|BNPR)\b')

def reg(s):
    return s if s.startswith('R') else 'R' + s

BALR0 = re.compile(r'^\S*\s+BALR\s+(R\d+|\d+),(0|R0)\b')
SPM = re.compile(r'^\S*\s+SPM\s+(R\d+|\d+)\b')

def cc_saved(lines, i, r):
    """Is the BALR's register later handed to SPM or STCM ..,8 (a CC save),
    before it is reloaded?  Looks ahead one screen; a long gap is reported as
    not saved and must be read by hand."""
    for j in range(i + 1, min(i + 60, len(lines))):
        t = lines[j]
        if t.startswith('*') or not t.strip():
            continue
        if re.match(r'^\S*\s+SPM\s+%s\b' % r, t) or \
           re.match(r'^\S*\s+STCM\s+%s,(8|B\'1000\'),' % r, t) or \
           re.match(r'^\S*\s+ST\s+%s,' % r, t):
            return True
        if re.match(r'^\S*\s+(L|LR|LA|LH|IC|ICM|LM|SR|SLR|BAL|BALR)\s+%s\b' % r, t) \
           or re.match(r'^\S*\s+(L|LR|LA|LH|LM)\s+%s,' % r, t):
            return False
    return False

def cc_source(lines, i, r):
    """What last set the register SPM restores from: 'balr', 'bal-link'
    (the register is a BAL link into this subroutine -- the I-229 class),
    'ipm', 'load' (restored from storage), or '?'."""
    for j in range(i - 1, max(i - 80, -1), -1):
        t = lines[j]
        if t.startswith('*') or not t.strip():
            continue
        if re.match(r'^\S*\s+BALR\s+%s,(0|R0)\b' % r, t):
            return 'balr'
        if re.match(r'^\S*\s+IPM\s+%s\b' % r, t):
            return 'ipm'
        if re.match(r'^\S*\s+L\s+%s,' % r, t):
            return 'load'
        if re.match(r'^\S*\s+(BAL|BALR)\s+%s,' % r, t):
            return 'bal-link'
        if re.match(r'^\S+\s+(EQU|DS)\s', t) and re.match(r'^[A-Z]', t):
            # a labelled entry with no setter above it in this block: the
            # register came in from the caller -- a BAL link if the block
            # ends with B 2(,Rx), else the caller's own BALR (DMKVSJ's R0).
            tail = ' '.join(lines[i:i + 3])
            return 'bal-link' if re.search(r'\bB\s+2\(,?%s\)' % r, tail) \
                or re.search(r'\bB\s+2\(0,%s\)' % r, tail) else 'caller'
    return '?'

def cc_sensitive(lines, i):
    """Does a CC-test follow before any instruction that sets the CC?"""
    for j in range(i + 1, min(i + 12, len(lines))):
        t = lines[j]
        if t.startswith('*') or not t.strip():
            continue
        if BRANCH_CC.match(t):
            return True
        if SETS_CC.match(t):
            return False
        if re.match(r'^\S*\s+(B|BR|EX)\b', t):
            return False
    return False

def scan(path):
    out = []
    raw = [l.rstrip('\n') for l in open(path, errors='replace')]
    lines = [l[:72] for l in raw]
    mod = os.path.basename(path).split('.')[0]
    for i, t in enumerate(lines):
        if t.startswith('*') or t.startswith('.*'):
            continue
        seq = raw[i][72:80].strip()
        m = LA_SELF.match(t)
        kind = None
        if m:
            a, b = reg(m.group(1)), reg(m.group(2))
            kind = 'LA-self' if a == b else 'LA-copy'
        elif MASK24.search(t):
            kind = 'mask24'
        elif XPAG.search(t):
            kind = 'xpagnum'
        elif ICM3.search(t):
            kind = 'icm3' if 'ICM' in t.split()[1:2] or ' ICM ' in t else 'stcm3'
        elif BALR0.match(t):
            kind = 'balr0'
        elif SPM.match(t):
            kind = 'spm'
        if not kind:
            continue
        parts = t.split(None, 3) if not t.startswith(' ') else t.split(None, 2)
        comment = (parts[-1] if len(parts) >= 3 else '').strip()
        if not t.startswith(' '):
            comment = (t.split(None, 3)[3] if len(t.split(None, 3)) > 3 else '').strip()
        else:
            comment = (t.split(None, 2)[2] if len(t.split(None, 2)) > 2 else '').strip()
        cc = ''
        if kind.startswith('LA'):
            cc = 'Y' if cc_sensitive(lines, i) else ''
        elif kind == 'balr0':
            cc = 'Y' if cc_saved(lines, i, reg(BALR0.match(t).group(1))) else ''
        elif kind == 'spm':
            cc = cc_source(lines, i, reg(SPM.match(t).group(1)))
        out.append(dict(module=mod, seq=seq, kind=kind, cc=cc,
                        text=t.strip()[:60], comment=comment[:50]))
    return out

def main():
    want = None
    if '--module' in sys.argv:
        want = sys.argv[sys.argv.index('--module') + 1].upper()
    rows = []
    for p in sorted(glob.glob(os.path.join(SRC, '*.ASSEMBLE'))):
        if want and not os.path.basename(p).startswith(want):
            continue
        rows += scan(p)
    if '--csv' in sys.argv:
        out = sys.argv[sys.argv.index('--csv') + 1]
        with open(out, 'w', newline='') as f:
            w = csv.DictWriter(f, fieldnames=['module', 'seq', 'kind', 'cc', 'text', 'comment'])
            w.writeheader(); w.writerows(rows)
    kinds = {}
    mods = {}
    for r in rows:
        kinds[r['kind']] = kinds.get(r['kind'], 0) + 1
        if r['kind'].startswith('LA'):
            mods[r['module']] = mods.get(r['module'], 0) + 1
    for k in sorted(kinds):
        print('%-8s %4d' % (k, kinds[k]))
    la = [r for r in rows if r['kind'].startswith('LA')]
    print('%d LA strip sites in %d modules, %d CC-sensitive' % (
        len(la), len(mods), sum(1 for r in la if r['cc'])))
    if want:
        for r in rows:
            print('%s %-8s %s %-60s' % (r['seq'], r['kind'], r['cc'] or ' ', r['text']))

if __name__ == '__main__':
    main()
