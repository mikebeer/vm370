#!/usr/bin/env python3
"""Which registers do the converted cards write that the originals did not?

Every check this project has is a check the ASSEMBLER could in principle make:
an undefined symbol, a duplicate label, a length, a displacement, an orphaned
continuation.  `I-143` closed the last of those.  What remains is the class the
assembler cannot see at all, and it is the class that fails at IPL rather than at
build time: **a converted card that needs a work register and takes a live one.**

The conversion creates this risk by its nature.  S/370 packed a length into a
pointer's high byte and 24-bit address formation ignored it, so a packed word was
usable as an address with nothing to strip.  ESA/390 needs an explicit mask, and
a mask needs somewhere to put the result -- so one card becomes two or three, and
the extra cards need a register the original did not use.  `DMKPGS` 01034200
needed `TEMPR7` for exactly this reason.

So: for every replacement, compare the registers the NEW cards write against
those the OLD records wrote.  A newly-written register is a candidate clobber.
Then look forward from the end of the replacement, within the basic block, for a
READ of that register before anything writes it.  If one exists, the conversion
has taken a live register.

**Known gap, unfixed as this is committed.**  The forward walk reads the BASE
records, not the records as UPDATE will leave them, so a read it reports may sit
on a card another replacement in the same deck has already converted.  That is
how `DMKCFG` 01415225 came to be reported: the walk found
`ICM R6,B'0110',(SEGPAGE+1)-SEGTABLE(R1)` reading R6, and `SEGPAGE` no longer
exists -- the module assembled clean, so that record is certainly replaced.
Until the walk applies the deck to itself, a hit must be checked against the deck
before it is believed.  Of the four hits on the current decks, three were checked
by hand and are intentional (`DMKPTR` 01977000, `DMKVMA` 00453000 and
`DMKVAT` 00232300 each deliberately compute into the register the next card
consumes), and `DMKPTR`'s was worth the walk on its own: it led to `SLL R1,8` at
01986000, which had to go because R1's SCALE changed -- frame times 16 under
S/370, a real address under ESA/390 -- and which was already removed and
documented.  So the tool earned its place before it was finished, and it is not
finished.

This is a candidate list, not a verdict, for two further reasons worth stating.  The
model below covers the opcodes these decks actually use and treats an unknown
opcode as reading and writing nothing, which can only cause a MISS -- so a clean
report is weaker than a dirty one.  And `TEMPR6`/`TEMPR7`-style storage
locations are not registers; clobbering those is a different question this does
not ask.

    python3 regchk.py [module ...]
"""
import collections
import glob
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = '/home/claude/vmce/source/cp'
UPDATES = os.path.join(HERE, '..', 'updates')
CTL = re.compile(r'^\./ ([RDI])\s+(\d{8})(?:\s+(\d{8}))?')
LABEL = re.compile(r'^[A-Z@#$][A-Z@#$0-9]{0,7}\s')
UNCOND = re.compile(r'^\s+(B|BR|BAL|BALR|BCR\s+15|GOTO|EXIT|RETURN)\s|^\s+B\s')

# r = reads operand 1, w = writes operand 1.  The second operand of an RX/RS
# instruction is a storage address, so its base and index registers are READ.
#   'w'  writes R1, reads nothing else of R1
#   'rw' reads and writes R1 (arithmetic, logical)
#   'r'  reads R1 only (stores, compares)
OP = {
    'L': 'w', 'LA': 'w', 'LR': 'w', 'LH': 'w', 'IC': 'rw', 'LTR': 'rw',
    'ICM': 'rw', 'LM': 'w*', 'LCR': 'w', 'LNR': 'w', 'LPR': 'w', 'LRA': 'w',
    'ST': 'r', 'STC': 'r', 'STH': 'r', 'STM': 'r*', 'STCM': 'r',
    'N': 'rw', 'O': 'rw', 'X': 'rw', 'NR': 'rw', 'OR': 'rw', 'XR': 'rw',
    'A': 'rw', 'AL': 'rw', 'AR': 'rw', 'ALR': 'rw', 'AH': 'rw',
    'S': 'rw', 'SL': 'rw', 'SR': 'rw', 'SLR': 'rw', 'SH': 'rw',
    'M': 'rw*', 'MR': 'rw*', 'MH': 'rw', 'D': 'rw*', 'DR': 'rw*',
    'SRL': 'rw', 'SLL': 'rw', 'SRA': 'rw', 'SLA': 'rw',
    'SRDL': 'rw*', 'SLDL': 'rw*', 'SRDA': 'rw*', 'SLDA': 'rw*',
    'C': 'r', 'CL': 'r', 'CR': 'r', 'CLR': 'r', 'CH': 'r', 'CLM': 'r',
    'BCT': 'rw', 'BCTR': 'rw', 'BXH': 'rw', 'BXLE': 'rw',
    'BAL': 'w', 'BALR': 'w', 'BAS': 'w', 'BASR': 'w',
    'ISK': 'w', 'ISKE': 'w', 'SSK': 'r', 'SSKE': 'r', 'RRBE': 'r',
    'TM': '', 'CLI': '', 'MVI': '', 'OI': '', 'NI': '', 'XI': '',
    'MVC': '', 'MVCL': 'rw*', 'XC': '', 'NC': '', 'OC': '', 'CLC': '',
    'TR': '', 'TRT': '', 'ED': '', 'PACK': '', 'UNPK': '',
}
REG = re.compile(r'^R?(\d{1,2})$')


def regs_of(text):
    """(reads, writes) for one source statement."""
    t = text[9:] if len(text) > 9 else ''
    parts = t.split(None, 1)
    if not parts:
        return set(), set()
    op = parts[0].upper()
    if op not in OP:
        return set(), set()
    mode = OP[op]
    operand = parts[1].split()[0] if len(parts) > 1 else ''
    reads, writes = set(), set()

    def rnum(tok):
        m = REG.match(tok.strip())
        return int(m.group(1)) if m and int(m.group(1)) < 16 else None

    fields = operand.split(',')
    r1 = rnum(fields[0]) if fields else None
    if r1 is not None:
        if 'w' in mode:
            writes.add(r1)
            if mode.endswith('*'):
                writes.add((r1 + 1) % 16)      # even-odd pair
        if 'r' in mode:
            reads.add(r1)
            if mode.endswith('*'):
                reads.add((r1 + 1) % 16)
    # every base and index register in the whole operand field is READ
    for b in re.findall(r'\(([^)]*)\)', operand):
        for tok in b.split(','):
            n = rnum(tok)
            if n is not None:
                reads.add(n)
    # `SLR R4,R4`, `XR R1,R1`, `SR R15,R15` ZERO a register -- they do not
    # consume its value.  Treating them as reads reported three false clobbers
    # out of seven, every one of them a register being cleared on the next card,
    # which is the opposite of a live use.
    if (len(fields) > 1 and op in ('SLR', 'SR', 'XR', 'NR', 'SLBR')
            and rnum(fields[1]) == r1):
        reads.discard(r1)
        return reads, writes
    # RR-form second operand is read
    if len(fields) > 1 and '(' not in fields[1]:
        n = rnum(fields[1])
        if n is not None:
            reads.add(n)
    return reads, writes


def records(path):
    return [(l[72:80].strip(), l[:72].rstrip('\n'))
            for l in open(path, errors='replace')]


def iscomment(t):
    return t.startswith('*') or t.lstrip().startswith('.*')


def deck_ops(path):
    ops, cur = [], None
    for line in open(path, errors='replace'):
        m = CTL.match(line)
        if m:
            if cur:
                ops.append(cur)
            cur = [m.group(1), int(m.group(2)), int(m.group(3) or m.group(2)), []]
        elif cur is not None:
            cur[3].append(line[:72].rstrip('\n'))
    if cur:
        ops.append(cur)
    return ops


def check(mod):
    base = os.path.join(SRC, '%s.ASSEMBLE' % mod)
    if not os.path.exists(base):
        return []
    recs = records(base)
    byseq = {int(s): i for i, (s, _) in enumerate(recs) if s.isdigit()}
    out = []
    for deck in sorted(glob.glob(os.path.join(UPDATES, '%s.XA*DK' % mod))):
        for op, a, b, lines in deck_ops(deck):
            if op != 'R':
                continue
            idx = [i for n, i in byseq.items() if a <= n <= b]
            if not idx:
                continue
            oldw = set()
            for i in idx:
                if not iscomment(recs[i][1]):
                    oldw |= regs_of(recs[i][1])[1]
            neww = set()
            for l in lines:
                if not iscomment(l):
                    neww |= regs_of(l)[1]
            extra = neww - oldw
            if not extra:
                continue
            # Walk forward from the last replaced record to the end of the
            # basic block, looking for a READ before a WRITE.
            last = max(idx)
            live = set()
            j = last + 1
            while j < len(recs):
                t = recs[j][1]
                if iscomment(t) or not t.strip():
                    j += 1
                    continue
                if LABEL.match(t):
                    break                    # another path reaches here
                r, w = regs_of(t)
                live |= (extra & r) - live
                extra = extra - w
                if UNCOND.match(t) or not extra:
                    break
                j += 1
            for n in sorted(live):
                out.append((recs[last][0], n, recs[j][0] if j < len(recs) else '?',
                            recs[j][1][9:50].rstrip() if j < len(recs) else ''))
    return out


def main():
    mods = sys.argv[1:] or sorted(
        {os.path.basename(p).split('.')[0]
         for p in glob.glob(os.path.join(UPDATES, '*.XA*DK'))})
    total = 0
    for mod in mods:
        hits = check(mod)
        if not hits:
            continue
        print('=== %s' % mod)
        for seq, n, useseq, usetext in hits:
            total += 1
            print('  R%-2d written by the replacement at %s and READ at %s: %s'
                  % (n, seq, useseq, usetext))
    print()
    if total:
        print('%d candidate clobber(s).  Each is a register the conversion'
              % total)
        print('writes that the original did not, read afterwards in the same')
        print('basic block before anything else writes it.  Read each one: this')
        print('is the class the assembler cannot see and the IPL can.')
    else:
        print('no candidate clobbers -- but the model treats an unknown opcode')
        print('as reading and writing nothing, so a clean report here is weaker')
        print('than a dirty one.')
    return 0


if __name__ == '__main__':
    sys.exit(main())
