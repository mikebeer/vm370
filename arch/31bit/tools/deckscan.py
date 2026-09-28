#!/usr/bin/env python3
"""Read a punched CP load deck and say what is actually in it.

`VMFLOAD CPLOAD DMKLCL` says `SYSTEM LOAD DECK COMPLETE` whether or not it
found a single `TXTLCL` file, because falling back to `TEXT` is not an error --
it is the mechanism working as designed.  So "it ran" proves nothing about
whether the conversion reached the deck, and the record count does not either.
The deck has to be read.

An object deck is 80-byte card images.  A loader record is

    col 1       X'02'
    cols 2-4    ESD | TXT | RLD | END   (EBCDIC)

and the rest is per type:

    ESD   cols 11-12 data length, 15-16 first ESDID, 17-72 items of 16 bytes:
          8 bytes name, 1 type, 3 address, 1 flag, 3 length-or-LDID
          type 00 = SD, 01 = LD, 02 = ER, 04 = PC, 05 = CM, 0A = WX
    TXT   cols 6-8 load address, 11-12 byte count, 15-16 ESDID,
          17-72 up to 56 bytes of text
    END   optionally cols 6-8 entry address

Cards that are not X'02' records are the loader's own bootstrap and the LDT,
and are reported as `other` rather than guessed at.

    python3 deckscan.py <deck> [--find <hex>] [--module <NAME>] [--modules]
                               [--audit]

`--audit` counts both instruction families per module, which is the first
measure of conversion progress taken against the **artifact** rather than
against source: `s370only.py` reads base source and cannot see an UPDATE
level, so it reports a site as live long after its deck has closed it.

A byte pattern is evidence, not proof.  `B230` turns up in `DMKVSP`, which has
no `CSCH` and no XA mnemonic anywhere in its source -- it is two adjacent bytes
of some constant.  So read a *positive* in an unconverted module as noise until
the source says otherwise, and lean on the two results that are hard to fake: a
pattern **absent** from the whole deck, and an ESA/390 opcode **present** in a
module known to be converted, since no base `TEXT` could contain one.

`ISK` and `SSK` are RR-format with one-byte opcodes and cannot be searched for
this way; `RRB` (`B213`) can.

`--find` searches the TEXT of every module for a byte pattern and names the
modules it appears in, which is the direct test: `--find 9F01` finds DMKVSJ's
CLRCH if and only if the deck was built from the unconverted `TEXT`.

The deck is EBCDIC.  Punch it with `devinit 000d <file>` and NO `ascii`
operand -- CE's config has `000D 3525 io/punch.txt ascii`, and the translation
mangles every TXT record while leaving the ESD names readable, so a corrupted
deck still scans as if it were fine.
"""
import sys


def cards(path):
    """Yield 80-byte card images, tolerating a trailing newline per card."""
    data = open(path, 'rb').read()
    if not data:
        return
    # Hercules writes fixed 80-byte images; some paths add a newline each.
    stride = 80
    if len(data) % 81 == 0 and data[80:81] == b'\n':
        stride = 81
    for i in range(0, len(data) - stride + 1, stride):
        yield data[i:i + 80]


def kind(card):
    if len(card) < 4 or card[0] != 0x02:
        return 'other'
    try:
        k = card[1:4].decode('cp037')
    except Exception:
        return 'other'
    return k if k in ('ESD', 'TXT', 'RLD', 'END') else 'other'


def esd_names(card):
    """The SD (section definition) names an ESD card declares."""
    out = []
    n = int.from_bytes(card[10:12], 'big')
    for off in range(16, 16 + n, 16):
        item = card[off:off + 16]
        if len(item) < 16:
            break
        name = item[0:8].decode('cp037').strip()
        typ = item[8]
        if typ in (0x00, 0x04, 0x05) and name:     # SD, PC, CM
            out.append(name)
    return out


def segment(path):
    """Split the deck into [(module, [cards])], in deck order.

    A module starts at its first ESD card carrying an SD and runs to its END.
    Cards before the first ESD are the loader's own, under the name `(loader)`.
    """
    segs = []
    cur, name = [], '(loader)'
    for c in cards(path):
        k = kind(c)
        if k == 'ESD':
            names = esd_names(c)
            if names and cur and name != names[0]:
                segs.append((name, cur))
                cur = []
            if names:
                name = names[0]
        cur.append(c)
        if k == 'END':
            segs.append((name, cur))
            cur, name = [], '(between)'
    if cur:
        segs.append((name, cur))
    return segs


def text_of(seg):
    """Concatenate the TXT data of one module's cards."""
    out = bytearray()
    for c in seg:
        if kind(c) == 'TXT':
            n = int.from_bytes(c[10:12], 'big')
            out += c[16:16 + n]
    return bytes(out)


# Two-byte opcodes, which is what makes a byte search specific enough to be
# worth doing.  The S/370 I/O instructions dispatch on the second byte -- 9C00
# is SIO and 9C01 is SIOF -- so each is a distinct pattern rather than a single
# opcode byte that would match anything.
S370 = [('SIO', '9C00'), ('SIOF', '9C01'), ('TIO', '9D00'),
        ('CLRIO', '9D01'), ('TIOB', '9D02'), ('HIO', '9E00'),
        ('HDV', '9E01'), ('TCH', '9F00'), ('CLRCH', '9F01'),
        ('STIDC', 'B203'), ('RRB', 'B213')]
XA = [('CSCH', 'B230'), ('HSCH', 'B231'), ('MSCH', 'B232'),
      ('SSCH', 'B233'), ('STSCH', 'B234'), ('TSCH', 'B235'),
      ('RCHP', 'B23B'), ('ISKE', 'B229'), ('RRBE', 'B22A'),
      ('SSKE', 'B22B')]


def audit(segs):
    """Per-module counts of both instruction families, in deck order."""
    print()
    print('%-8s  %-28s  %s' % ('MODULE', 'S/370', 'ESA/390'))
    print('-' * 72)
    tot = {}
    seen = set()
    for name, seg in segs:
        if name.startswith('(') or name in seen:
            continue          # the deck may hold more than one copy
        seen.add(name)
        t = text_of(seg)
        old = [(m, t.count(bytes.fromhex(h))) for m, h in S370]
        new = [(m, t.count(bytes.fromhex(h))) for m, h in XA]
        old = [(m, n) for m, n in old if n]
        new = [(m, n) for m, n in new if n]
        for m, n in old + new:
            tot[m] = tot.get(m, 0) + n
        if old or new:
            print('%-8s  %-28s  %s'
                  % (name,
                     ' '.join('%s x%d' % (m, n) for m, n in old),
                     ' '.join('%s x%d' % (m, n) for m, n in new)))
    print('-' * 72)
    o = sum(n for m, n in tot.items() if m in dict(S370))
    x = sum(n for m, n in tot.items() if m in dict(XA))
    print('%-8s  %-28s  %s' % ('total',
                               ' '.join('%s x%d' % (m, tot[m])
                                        for m, _ in S370 if m in tot),
                               ' '.join('%s x%d' % (m, tot[m])
                                        for m, _ in XA if m in tot)))
    print('%d S/370 sites left in the deck, %d ESA/390 sites in it' % (o, x))


def loadmap(path):
    """Assign each CSECT a load address the way the loader would, and report it.

    The loader is what decides where a module lands, and when it goes wrong it
    says so only on a printer that may not be listening.  This does the same
    arithmetic on the host: walk the deck in order, and for each SD in an ESD
    card give the section the next address, rounded up to a doubleword.  TXT
    cards carry CSECT-RELATIVE addresses, so a module's absolute extent is its
    base plus the highest TXT address and length it holds.

    That is the loader's ESD pass, not its RLD pass, so the addresses are
    right and the relocated contents are not -- which is enough to answer
    "where did DMKSAVNC go" and "does anything overlap low storage".
    """
    addr, rows, cur = 0, [], None
    for c in cards(path):
        if kind(c) == 'ESD':
            n = int.from_bytes(c[10:12], 'big')
            for off in range(16, 16 + n, 16):
                item = c[off:off + 16]
                if len(item) < 16:
                    break
                name = item[0:8].decode('cp037').strip()
                typ, ln = item[8], int.from_bytes(item[13:16], 'big')
                if typ in (0x00, 0x04) and name:          # SD, PC
                    addr = (addr + 7) & ~7
                    cur = [name, addr, ln, 0]
                    rows.append(cur)
                    addr += ln
        elif kind(c) == 'TXT' and cur is not None:
            a2 = int.from_bytes(c[5:8], 'big')
            n2 = int.from_bytes(c[10:12], 'big')
            cur[3] = max(cur[3], a2 + n2)
    print()
    print('LOAD MAP, as the loader would assign it')
    print('%-9s %-9s %-9s %-8s %s' % ('CSECT', 'FROM', 'TO', 'LENGTH', 'NOTE'))
    print('-' * 62)
    for name, base, ln, hi in rows:
        note = ''
        if hi > ln:
            note = 'TXT OVERRUNS ITS ESD LENGTH by %d' % (hi - ln)
        if base < 0x300 and ln:
            note = (note + '  ' if note else '') + 'covers low storage'
        print('%-9s %08X  %08X  %6d  %s' % (name, base, base + ln, ln, note))
    print('-' * 62)
    print('%d sections, %d bytes, top at %08X' % (len(rows), addr, addr))
    for want in ('DMKSAVNC', 'DMKCPINT', 'DMKPSA'):
        for name, base, ln, hi in rows:
            if name == want:
                print('  %-9s at %08X' % (name, base))


def main():
    path = sys.argv[1]
    segs = segment(path)
    counts = {}
    for c in cards(path):
        counts[kind(c)] = counts.get(kind(c), 0) + 1

    print('%s' % path)
    print('  cards          %d' % sum(counts.values()))
    for k in ('ESD', 'TXT', 'RLD', 'END', 'other'):
        if counts.get(k):
            print('  %-14s %d' % (k, counts[k]))
    mods = [n for n, _ in segs if not n.startswith('(')]
    print('  modules        %d' % len(mods))

    if '--modules' in sys.argv:
        print()
        for i in range(0, len(mods), 8):
            print('  ' + ' '.join('%-8s' % m for m in mods[i:i + 8]))

    if '--module' in sys.argv:
        want = sys.argv[sys.argv.index('--module') + 1].upper()
        for name, seg in segs:
            if name == want:
                t = text_of(seg)
                print()
                print('  %s: %d cards, %d bytes of text'
                      % (name, len(seg), len(t)))

    if '--map' in sys.argv:
        loadmap(path)

    if '--audit' in sys.argv:
        audit(segs)

    if '--find' in sys.argv:
        pat = bytes.fromhex(sys.argv[sys.argv.index('--find') + 1])
        print()
        print('  searching module text for %s' % pat.hex().upper())
        hits = []
        for name, seg in segs:
            t = text_of(seg)
            n = t.count(pat)
            if n:
                hits.append((name, n))
        if not hits:
            print('    not present in any module')
        for name, n in hits:
            print('    %-8s x%d' % (name, n))
    return 0


if __name__ == '__main__':
    sys.exit(main())
