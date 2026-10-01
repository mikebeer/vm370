#!/usr/bin/env python3
"""Count the S/370-only privileged instructions still unconverted, by class.

`IPL-WALLS.md` said group 1 had "10 cards left: DMKCPI's SIO, DMKPSA x4 ISK,
DMKSAV x5".  The real figure is 95, and DMKPSA has five ISKs, not four.  The
note was three modules someone had looked at, recorded as a total; the error is
not that the count was stale but that it was never a count.  So this exists to
make the figure a measurement, cheap enough that quoting one is never easier
than taking one.  I-141.

**Reconciled against `s370only.py`**, which was already in this tree and which
counts the same instructions by a different method: it reads Hercules's own
opcode table and keeps every mnemonic marked `GENx370x___x___`, rather than a
hand-written list.  With the deck subtraction disabled the two agree on
**199 against 200**, and the single difference was `STIDC` -- absent from the
list here until this check, now added.  Every other opcode matches exactly:
TIO 71, SIO 48, ISK 38, SSK 16, RRB 13, HIO 5, HDV 4, TCH 3, CLRIO 1, and the
same four standalone utilities outside the nucleus.  Two tools written
independently, agreeing site for site on nine opcodes, is the strongest evidence
either of them is right.  The relationship is therefore: `s370only.py` counts
what CP ISSUES, this counts what is LEFT.

The method:

  * sweep every module for the opcodes 370-XA removed -- SIO SIOF TIO CLRIO
    HIO HDV TCH (channel) and ISK SSK RRB (2 KB storage keys);
  * drop comment lines, which `*        SIO IS ISSUED BUT ...` would otherwise
    contribute to the total;
  * subtract every sequence range the generated decks already `./ R` or
    `./ D`, so a converted site is not counted twice;
  * keep only modules named in CP's own `CPLOAD EXEC`.  Whether a module is in
    the nucleus decides whether it is on the IPL path at all, and the load list
    is the build's answer rather than mine: it puts DMKFMT, DMKDDR, DMKDIR and
    DMKSSP outside, because they are standalone utilities IPL'd on their own.

The split it reports is the point.  Storage keys and channel I/O are both
"group 1" and they are not the same job:

  keys  S/370 keys cover 2 KB, ESA/390 keys a whole 4 KB page, so code that
        does a thing twice -- `RRB 0(R6)` then `RRB 2048(R6)`, an ISK per half
        -- has only one key to ask about.  The first version of this tool said
        such a pair "gets DELETED"; that is wrong, and reading DMKPTR 01012000
        is what showed it.  CP keeps a key PER 2 KB HALF of its own accord:
        SWPTABLE has `SWPKEY1` and `SWPKEY2`, and the scan packs both hardware
        keys into one register --

            ISK   R15,R6         GET STORAGE KEY
            SLL   R15,8          MAKE ROOM FOR 2ND HALF OF PAGE
            LA    R14,2048(,R6)  ADDR FOR 2ND 2K
            ISK   R15,R14        GET OTHER STORAGE KEY
            LA    R14,SWPREF2*256+SWPREF2 GET CHANGE BIT MASK

        -- because ISK only loads bits 24-31.  So the pair feeds a two-byte
        mask, X'0202', and two stores.  Deleting the second ISK leaves R15 with
        one key in the wrong half and a mask that no longer matches anything.
        The conversion is to take the one 4 KB key ONCE and REPLICATE it into
        both halves, which leaves every downstream mask, flag and store
        untouched and makes the deviation explicit: the two halves of a page now
        always report identical reference and change bits, which is exactly what
        a 4 KB-key machine does.  That is R-12 seen from CP's side rather than
        the guest's.  ISKE/SSKE/RRBE are already in XAOPS MACRO, proven by
        execution.  A pair is therefore counted as a site that CHANGES SHAPE,
        not one that disappears.
  io    SIO/TIO polling loops in code that runs before there is an I/O
        supervisor to call: the standalone loader, DMKSAV, DMKVMI, DMKCPI's
        sense to the IPL device.  These are the IPL path, so they cannot ride
        with the deferred multi-channel work.

    python3 privchk.py [--sites]
"""
import collections
import glob
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = '/home/claude/vmce/source/cp'
UPDATES = os.path.join(HERE, '..', 'updates')
LOADLIST = '/home/claude/vmce/maintenance/files/194/CPLOAD.EXEC'

CHANNEL = ('SIO', 'SIOF', 'TIO', 'CLRIO', 'HIO', 'HDV', 'TCH', 'STIDC')
KEYS = ('ISK', 'SSK', 'RRB')
PRIV = re.compile(r'^.{9}(%s)\s' % '|'.join(CHANNEL + KEYS))
CTL = re.compile(r'^\./ ([RDI])\s+(\d{8})(?:\s+(\d{8}))?')


def converted():
    """{module: [(from, to)]} for every range the decks replace or delete."""
    cov = {}
    for d in sorted(glob.glob(os.path.join(UPDATES, '*.XA*DK'))):
        mod = os.path.basename(d).split('.')[0]
        for line in open(d):
            m = CTL.match(line)
            if m and m.group(1) in 'RD':
                cov.setdefault(mod, []).append(
                    (int(m.group(2)), int(m.group(3) or m.group(2))))
    return cov


def nucleus():
    text = open(LOADLIST, errors='replace').read().upper()
    return set(re.findall(r'\bDMK[A-Z0-9]{2,5}\b', text))


def scan():
    cov, nuc = converted(), nucleus()
    out = []
    for path in sorted(glob.glob(os.path.join(SRC, 'DMK*.ASSEMBLE'))):
        mod = os.path.basename(path).split('.')[0]
        inn = mod in nuc
        prev = None
        for line in open(path, errors='replace'):
            text = line[:72]
            if text.startswith('*') or text.lstrip().startswith('.*'):
                continue
            m = PRIV.match(text)
            if not m:
                continue
            seq = line[72:80].strip()
            if not seq.isdigit():
                continue
            n = int(seq)
            if any(a <= n <= b for a, b in cov.get(mod, [])):
                continue
            op = m.group(1)
            cls = 'keys' if op in KEYS else 'io'
            # A 2 KB pair: the same opcode again within five records.  The
            # second one does the other half of the page and goes away.
            pair = (cls == 'keys' and prev and prev[0] == op and n - prev[1] <= 5000)
            prev = (op, n) if cls == 'keys' else None
            out.append((mod, inn, seq, op, cls, bool(pair), text.rstrip()))
    return out


def main():
    sites = scan()
    nuc = [s for s in sites if s[1]]
    key = collections.Counter(s[0] for s in nuc if s[4] == 'keys')
    io = collections.Counter(s[0] for s in nuc if s[4] == 'io')
    pair = collections.Counter(s[0] for s in nuc if s[5])

    print('%-9s %5s %5s %7s' % ('module', 'keys', 'io', '2K pair'))
    for mod in sorted(set(key) | set(io)):
        print('%-9s %5d %5d %7d' % (mod, key[mod], io[mod], pair[mod]))
    print('%-9s %5d %5d %7d' % ('TOTAL', sum(key.values()), sum(io.values()),
                                sum(pair.values())))
    print()
    print('%d site(s) in nucleus modules, %d in standalone utilities (not M1).'
          % (len(nuc), len(sites) - len(nuc)))
    print('Of the key sites, %d are second halves of a 2 KB pair.  They are NOT'
          % sum(pair.values()))
    print('deletions: CP keeps a key per 2 KB half in SWPKEY1/SWPKEY2 and packs')
    print('both into one register, so the one 4 KB key is read once and')
    print('REPLICATED into both halves -- every downstream mask then still')
    print('matches, and the coarsening is stated rather than hidden.')

    if '--sites' in sys.argv:
        print()
        for mod, inn, seq, op, cls, p, text in sites:
            if not inn:
                continue
            print('  %-9s %s %-5s %-4s%s %s' % (mod, seq, op, cls,
                                                ' pair' if p else '     ',
                                                text[9:55].rstrip()))
    return 0


if __name__ == '__main__':
    sys.exit(main())
