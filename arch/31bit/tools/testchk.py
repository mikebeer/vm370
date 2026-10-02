#!/usr/bin/env python3
"""Did a converted test keep the SHAPE of the test it replaced?

`I-159`: `DMKPGS` 00956000 was `CLI SEGPAGE+3,SEGINV` -- an EQUALITY test -- and
I converted it to `TM SEGPTO+3,SEGINVAL`, a BIT test.  Those are not the same
question.  Byte 3 equals `SEGINV` exactly only when the page-table origin's low
byte is zero and the invalid flag is set: the "never built" case.  The two cards
after it separate a second case, built-but-invalid, which is the one the
`TRANS OPT=(DEFER)` at 00962000 exists to wait for.  Collapsing the two meant
any invalid entry took `NEXTSEG`, so reaching 00958000 implied the bit was clear,
`BZ` was always taken, and **the `TRANS` became dead code**.

The assembler cannot see this: both forms assemble, and the branch after them
reads perfectly well either way.  `block.py` warned about the inversion risk in
its docstring and that warning did not survive contact, because the error was not
an inversion -- the branch sense was right (`BO` for CC3) -- it was a change of
QUESTION.

So sweep for it.  For every record a deck replaces, compare the opcode CLASS of
the original against the replacement:

    equality -> bit     CLI/CLC/CL/C becomes TM.  Report always: a bit test
                        cannot ask "equals exactly".  Correct only when the mask
                        covers every bit that could be set in the compared value,
                        which has to be read -- `DMKBLD` 00321000 is correct for
                        that reason (`X'0F'` over PTL, CC3 iff PTL is 15, i.e.
                        exactly the "16 pages" the `CLI X'F0'` asked about).
    bit -> equality     the reverse, same reasoning.
    and the BRANCH       `TM` sets CC0/CC1/CC3, so `BE`/`BNE` after a converted
                        test are suspect where `BO`/`BZ`/`BM` are the natural
                        partners; `CLI` sets CC0/CC1/CC2 and `BO` is meaningless.

Verdicts are CANDIDATE, never CORRECT: the tool finds the shape change, a human
reads the mask.  All three hits on the current decks were real findings -- one
defect, one equivalent, one improvement.

    python3 testchk.py
"""
import glob
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = '/home/claude/vmce/source/cp'
UPDATES = os.path.join(HERE, '..', 'updates')
CTL = re.compile(r'^\./ ([RDI])\s+(\d{8})(?:\s+(\d{8}))?')

EQUALITY = {'CLI', 'CLC', 'CL', 'C', 'CH', 'CLM', 'CR', 'CLR'}
BITTEST = {'TM'}
# Branches that make sense after each kind of test.
TM_OK = {'BO', 'BZ', 'BM', 'BNO', 'BNZ', 'BNM', 'BC'}
CMP_OK = {'BE', 'BNE', 'BL', 'BH', 'BNL', 'BNH', 'BC', 'BZ', 'BNZ'}


def records(path):
    return [(l[72:80].strip(), l[:72].rstrip())
            for l in open(path, errors='replace')]


def opcode(text):
    f = text[9:].split()
    return f[0].upper() if f else ''


def deck_ops(path):
    out, cur = {}, None
    for line in open(path, errors='replace'):
        m = CTL.match(line)
        if m:
            cur = m.group(2) if m.group(1) == 'R' else None
            if cur:
                out[cur] = []
        elif cur is not None:
            t = line[:72].rstrip()
            if t and not t.startswith('*'):
                out[cur].append(t)
    return out


# Constants this project introduced, with their bit counts.  A TM whose mask has
# more than one bit gives CC3 only when ALL of them are set, and CC1 when some
# are -- so `BO` means "all", `BNZ`/`BM` mean "any", and the two are different
# questions.  I-159 was the same confusion from the other direction.
MASKS = {'SEGINVAL': 0x20, 'PAGINV': 0x04, 'SEGPTLF': 0x0F, 'SEGFLGM': 0x3F,
         'SEGENQ': 0x10, 'PAGREF': 0x02, 'PAGSHR': 0x01, 'SEGMIG': 0x10,
         'PAGTSWP': None, 'SWPSHR': 0x01, 'CORSHARE': 0x01}
BITS = re.compile(r"X'([0-9A-F]+)'")


def maskbits(operand):
    """How many bits does this TM mask select?  None if unresolvable."""
    arg = operand.split(',')[-1].strip()
    tot = 0
    for part in re.split(r'\+', arg):
        part = part.strip()
        m = BITS.match(part)
        if m:
            tot |= int(m.group(1), 16)
        elif part in MASKS and MASKS[part] is not None:
            tot |= MASKS[part]
        elif part.isdigit():
            tot |= int(part)
        else:
            return None
    return bin(tot).count('1')


def multibit(deck, recs, byseq, D):
    """TM cards a deck INTRODUCES whose mask selects more than one bit."""
    out = []
    for seq, lines in D.items():
        for ln in lines:
            if opcode(ln) != 'TM':
                continue
            f = ln[9:].split(None, 1)
            if len(f) < 2:
                continue
            n = maskbits(f[1].split()[0])
            if n is None or n < 2:
                continue
            # the branch that follows, converted or kept
            br = ''
            i = byseq.get(seq)
            if i is not None:
                for j in range(i + 1, min(i + 4, len(recs))):
                    s2, t2 = recs[j]
                    if opcode(t2).startswith('B'):
                        br = (opcode(D[s2][0]) if s2 in D and D[s2]
                              else opcode(t2) + ' (kept)')
                        break
            out.append((seq, n, f[1].split()[0], br))
    return out


def main():
    hits = []
    multi = []
    for deck in sorted(glob.glob(os.path.join(UPDATES, '*.XA*DK'))):
        mod = os.path.basename(deck).split('.')[0]
        src = os.path.join(SRC, '%s.ASSEMBLE' % mod)
        if not os.path.exists(src):
            continue
        recs = records(src)
        byseq = {s: i for i, (s, _) in enumerate(recs) if s}
        D = deck_ops(deck)
        for seq, lines in D.items():
            if not lines or seq not in byseq:
                continue
            oo, no = opcode(recs[byseq[seq]][1]), opcode(lines[0])
            shape = None
            if oo in EQUALITY and no in BITTEST:
                shape = 'equality -> bit'
            elif oo in BITTEST and no in EQUALITY:
                shape = 'bit -> equality'
            if not shape:
                continue
            # what does the branch after it look like, converted or not?
            i = byseq[seq] + 1
            br_o = br_n = ''
            while i < len(recs) and i < byseq[seq] + 4:
                s2, t2 = recs[i]
                if opcode(t2).startswith('B'):
                    br_o = opcode(t2)
                    br_n = opcode(D[s2][0]) if s2 in D and D[s2] else '(kept)'
                    break
                i += 1
            ok = (br_n in TM_OK) if no == 'TM' else (br_n in CMP_OK)
            hits.append((mod, seq, shape, oo, no, br_o,
                         br_n, 'branch ok' if ok or br_n == '(kept)'
                         else 'BRANCH SUSPECT'))
        for seq, n, mask, br in multibit(deck, recs, byseq, D):
            multi.append((mod, seq, n, mask, br))
    print('%d test-shape change(s).  Each is a CANDIDATE: the tool finds the'
          % len(hits))
    print('shape change, a human reads the mask.')
    print()
    for mod, seq, shape, oo, no, bo, bn, verdict in hits:
        print('  %-8s %s  %-16s %-4s -> %-3s   branch %-4s -> %-7s %s'
              % (mod, seq, shape, oo, no, bo, bn, verdict))
    if not hits:
        print('  none')
    print()
    print('%d introduced TM(s) with a MULTI-BIT mask.  `BO` asks "all these'
          % len(multi))
    print('bits", `BNZ`/`BM` ask "any of them" -- different questions.')
    print()
    for mod, seq, n, mask, br in sorted(multi):
        verdict = ('reads as ALL' if br.startswith('BO')
                   else 'reads as ANY' if br.startswith(('BNZ', 'BM'))
                   else 'read it')
        print('  %-8s %s  %d bits  %-24s branch %-12s %s'
              % (mod, seq, n, mask, br or '(none found)', verdict))
    if not multi:
        print('  none')
    return 0


if __name__ == '__main__':
    sys.exit(main())
