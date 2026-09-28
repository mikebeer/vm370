#!/usr/bin/env python3
"""Find every S/370-only instruction CP issues.

`STIDC` in DMKIOG was found by reading one module.  That is not a method: an
S/370-only instruction assembles perfectly under Assembler XF -- the assembler
has no idea which architecture the object will run on -- and then takes an
operation exception at execution.  The 183-module nucleus cannot be read line
by line, so the sweep is mechanical.

Hercules's own opcode table is the oracle.  A row marked

    /*B203*/ AD_GENx370x___x___ ( "STIDC" , S , ASMFMT_S , store_channel_id )

is installed in S/370 mode and in no other, so on ESA/390 it is an operation
exception.  Thirty-four mnemonics are marked that way.

    python3 s370only.py /path/to/opcode.c /path/to/vmce [--all]

Reported counts are sites in the resolved tree, which is CE's own source as of
its 20 September 2026 import (`UPSTREAM.md`); where a number matters, confirm
it against what `VMFASM` produces.  R-23.
"""
import os
import re
import sys

# Mnemonics that are also ordinary CP labels, macro names or operands.  Every
# one of these needs the opcode-column test, not a substring match: DMKFRE's
# entry points are literally FREE and FRET.
# S/370 I/O sub-functions: 9C/9D/9E/9F dispatch on the low-order bits of the
# operand address, so these are real Assembler XF mnemonics with no row of
# their own in Hercules' opcode table.  A purely table-driven sweep misses all
# of them -- HDV alone accounts for four nucleus sites, two of them the ones
# DMKIOS still owes.  Supplied by hand, with the opcode's second byte shown.
SUPPLEMENT = {'HDV': '9E01', 'SIOF': '9C01', 'CLRIO': '9D01',
              'CLRCH': '9F01', 'TIOB': '9D02'}

# DC-encoded sites the conversion has closed.  Neither was closed by converting
# the instruction, which is why they are worth naming rather than deleting from
# the report: the sweep reads base source and cannot see an UPDATE level.
DC_CLOSED = {
    'DMKCPI': 'CONCS is dead under AP=NO -- XA0014DK, I-50',
    'DMKVSJ': 'CLRCH removed, CLCH always simulated -- XA0018DK, I-62',
}

# What each one becomes.  ISKE, SSKE, RRBE and IVSK are GENx370x390x900 -- valid
# in every mode -- so the storage-key family is a mechanical substitution.  The
# channel family is not: cc1 from TIO means "CSW stored", cc1 from TSCH means
# "no status pending", so the sense inverts at every site.
REPLACEMENT = {'SIO': 'SSCH', 'SIOF': 'SSCH', 'TIO': 'TSCH, cc inverted',
               'TIOB': 'TSCH', 'HIO': 'HSCH', 'HDV': 'HSCH',
               'CLRIO': 'CSCH', 'CLRCH': 'CSCH',
               'TCH': 'none -- force the channel-available path',
               'STIDC': 'none -- report every channel unidentified',
               'ISK': 'ISKE', 'SSK': 'SSKE', 'RRB': 'RRBE'}

FAMILY = dict.fromkeys(('SIO', 'SIOF', 'TIO', 'TIOB', 'HIO', 'HDV', 'CLRIO',
                        'CLRCH', 'TCH', 'STIDC'), 'channel')
FAMILY.update(dict.fromkeys(('ISK', 'SSK', 'RRB'), 'key'))

AMBIGUOUS = {'FREE', 'FRET', 'FREEX', 'FRETX', 'DISP0', 'DISP2', 'ASSIST',
             'STEVL', 'PRFMA', 'CCWGN', 'DFCCW', 'DNCCW', 'FCCWS', 'UXCCW',
             'SCNRU', 'SCNVU', 'TRLCK', 'LCSPG', 'VLKPG', 'VULKP', 'VIPT',
             'VIST', 'CONCS', 'DISCS', 'ECPS_DISP1', 'ECPS_TRBRG'}


def s370_only(opcode_c):
    pat = re.compile(r'/\*([0-9A-Fa-f]{2,4})\*/\s*\w*GENx370x_+x_+\s*\(\s*"([^"]+)"')
    found = {m.group(2).strip().upper(): m.group(1)
             for m in pat.finditer(open(opcode_c, errors='replace').read())}
    found.update(SUPPLEMENT)
    return found


# Instructions CP writes as constants because Assembler XF has no mnemonic for
# them, or because the author wanted the bytes explicit.  A scan of the opcode
# column cannot see any of these, and CONCS is live in CE: OPTIONS.COPY sets
# `&AP SETB 1` via HRC035DK, so the Attached Processor blocks are assembled.
# CONCS and DISCS are channel-SET instructions with no ESA/390 counterpart at
# all -- the channel subsystem replaced channel sets -- so they must be removed
# rather than translated.  I-49.
DC_ENCODED = {'B200': 'CONCS', 'B201': 'DISCS', '9C01': 'SIOF', '9D01': 'CLRIO',
              '9E01': 'HDV', '9F01': 'CLRCH', '9F00': 'TCH', '9D02': 'TIOB',
              'B203': 'STIDC', 'B213': 'RRB'}

# Verified by reading each site: a DC can be an executed instruction or merely a
# comparison operand, and nothing mechanical distinguishes them.  These are the
# ones confirmed by hand; anything not listed is reported for review.
DC_VERDICT = {
    ('DMKCPI', 'B200'): 'instruction',   # CONCS 0(R1), channel-set connect
    ('DMKCPP', 'B200'): 'instruction',
    ('DMKCPP', 'B201'): 'instruction',
    ('DMKMCT', 'B200'): 'instruction',   # "ACTUAL CONNECT INSTRUCTION"
    ('DMKMCT', 'B201'): 'instruction',   # "ACTUAL DISCONNECT INSTRUCTION"
    ('DMKVSJ', '9F01'): 'instruction',   # CLRCH 0(R1), followed by DC S(0(1))
    ('DMKVSI', '9F00'): 'operand',       # CLC VMINST(2),TCHOPER -- not executed
}


# Lowcore referenced by absolute address instead of by PSA symbol.  A scan for
# renamed symbols cannot see these at all, and they are the same hazard: the
# field at that address means something else under ESA/390.  Verified by hand --
# a bare decimal in an operand is far more often a length or a message number.
ABS_LOWCORE = {
    ('DMKCKP', '184'): "MVC SAVEDEV(4),184 -- X'B8', now the subsystem ID word",
    ('DMKLD00E', '72'): "ST 2,72 x3 -- X'48', the CAW, which ESA/390 has not",
}


def abs_sites(src):
    """Absolute-numeric references to lowcore, reported for review.

    Found in DMKCKP by reading the module, not by any tool: `MVC SAVEDEV(4),184`
    stores from absolute 184 = X'B8'.  DMKLD00E then turned out to have three
    `ST 2,72` -- the CAW -- written the same way, and it uses bare register
    numbers throughout, so nothing about it matches the usual patterns.  I-53.
    """
    # MVI and CLI are excluded: their second operand is an immediate byte, never
    # an address.  Including them gave nine false positives -- pages per
    # cylinder, RECMAX, byte counts -- against two real sites.
    pat = re.compile(r"^\s+(?:MVC|L|ST|LH|STH|CLC|IC|STC|XC|NC|OC)\s+"
                     r"[A-Z0-9()+,']+,(\d{2,3})(?:\s|$)")
    out = []
    for name in sorted(os.listdir(src)):
        if not name.endswith('.ASSEMBLE'):
            continue
        mod = name[:-9]
        for line in open(os.path.join(src, name), errors='replace'):
            m = pat.match(line[:71])
            if not m or '(' in m.group(0).split(',')[-1]:
                continue
            addr = m.group(1)
            if 64 <= int(addr) <= 200:
                out.append((mod, addr, ABS_LOWCORE.get((mod, addr), 'REVIEW')))
    return out


def dc_sites(src, nucleus):
    """Find S/370-only instructions hand-coded as DC constants."""
    pat = re.compile(r"^\s+DC\s+X'([0-9A-F]{4})", re.I)
    out = []
    for name in sorted(os.listdir(src)):
        if not name.endswith('.ASSEMBLE'):
            continue
        mod = name[:-9]
        for line in open(os.path.join(src, name), errors='replace'):
            m = pat.match(line[:71])
            if m and m.group(1).upper() in DC_ENCODED:
                op = m.group(1).upper()
                out.append((mod, op, DC_ENCODED[op],
                            DC_VERDICT.get((mod, op), 'REVIEW'),
                            mod in nucleus))
    return out


def opcode_of(line):
    """The operation field of an assembler statement, or None.

    Columns 1-8 are the label, 9 is blank, the operation starts at 10 -- but
    CP is not always tidy, so take the first token beginning at column 9 or
    later on a line that is neither a comment nor a continuation.
    """
    if not line or line[0] in '*.':
        return None
    body = line[:71].rstrip()
    if len(body) < 10 or not body[:9].endswith(' ') and body[0] != ' ':
        pass
    m = re.match(r'(?:\S{0,8})\s+(\S+)', body)
    if not m or body[0] not in ' ' and len(body.split()[0]) > 8:
        return None
    return m.group(1).upper()


def main():
    opcode_c, root = sys.argv[1], sys.argv[2]
    table = s370_only(opcode_c)
    src = os.path.join(root, 'source', 'cp')
    nucleus = {m.group(1) for m in re.finditer(
        r'(?m)^&1 &2 &3 (\S+)',    # anchored: DMKSST is commented out, I-66
        open(os.path.join(root, 'maintenance', 'files', '094',
                          'CPLOAD.EXEC')).read())} - {'LOADER', 'LDT',
                                                      'SLC', 'SPB'}

    hits = {}
    for name in sorted(os.listdir(src)):
        if not name.endswith('.ASSEMBLE'):
            continue
        mod = name[:-9]
        for n, line in enumerate(open(os.path.join(src, name),
                                     errors='replace'), 1):
            op = opcode_of(line.rstrip('\n'))
            if op in table:
                seq = line[72:80].strip() if len(line) > 72 else ''
                hits.setdefault(op, []).append((mod, seq or str(n)))

    print('S/370-ONLY INSTRUCTIONS ISSUED BY CP')
    print('(opcode table: %d mnemonics marked GENx370x___x___)\n' % len(table))
    print('%-7s %-6s %5s %5s  %-8s %s'
          % ('MNEM', 'OPC', 'NUCL', 'OTHER', 'FAMILY', 'BECOMES'))
    print('-' * 76)
    byfam = {}
    for op in sorted(hits, key=lambda o: -sum(1 for m, _ in hits[o]
                                              if m in nucleus)):
        n = sum(1 for m, _ in hits[op] if m in nucleus)
        byfam[FAMILY[op]] = byfam.get(FAMILY[op], 0) + n
        flag = '  <-- also a CP label; verify' if op in AMBIGUOUS else ''
        print('%-7s %-6s %5d %5d  %-8s %s%s'
              % (op, table[op], n, len(hits[op]) - n, FAMILY[op],
                 REPLACEMENT.get(op, '?'), flag))
    print('-' * 76)
    for fam, n in sorted(byfam.items()):
        print('%-30s %d' % ('nucleus sites, %s family' % fam, n))
    print('%-30s %d' % ('nucleus sites, total', sum(byfam.values())))
    print('%-30s %d' % ('nucleus modules affected',
                        len({m for v in hits.values() for m, _ in v
                             if m in nucleus})))
    print('%-30s %s' % ('non-nucleus (utilities)',
                        ' '.join(sorted({m for v in hits.values()
                                         for m, _ in v
                                         if m not in nucleus}))))

    dc = dc_sites(src, nucleus)
    if dc:
        print()
        print('HAND-CODED AS DC CONSTANTS (invisible to the column scan)')
        print('%-8s %-6s %-7s %-12s %s' % ('MODULE', 'BYTES', 'MNEM',
                                           'VERDICT', 'IN'))
        print('-' * 60)
        for mod, byt, mnem, verdict, nucl in dc:
            print('%-8s %-6s %-7s %-12s %s'
                  % (mod, byt, mnem, verdict, 'yes' if nucl else 'lib'))
        live = [d for d in dc if d[3] == 'instruction' and d[4]]
        print('%-46s %d' % ('  live nucleus instruction sites', len(live)))
        print('%-46s %s' % ('  modules', ' '.join(sorted({d[0] for d in live}))))
        # The sweep reads base source, and the conversion is an UPDATE level,
        # so a site stays visible here after its deck has closed it -- the same
        # caveat HANDLED carries in status.py.  Both of these are now dealt
        # with, and neither is dealt with by converting the instruction.
        for mod, why in sorted(DC_CLOSED.items()):
            if mod in {d[0] for d in live}:
                print('  %-8s closed: %s' % (mod, why))

    ab = abs_sites(src)
    if ab:
        print()
        print('LOWCORE BY ABSOLUTE ADDRESS (invisible to the symbol scan)')
        print('-' * 66)
        for mod, addr, note in ab:
            print('%-9s %-5s %s' % (mod, addr, note))

    if '--all' in sys.argv:
        for op in sorted(hits):
            print('\n%s (%s)' % (op, table[op]))
            for mod, seq in hits[op]:
                print('    %-9s %s' % (mod, seq))
    return 0


if __name__ == '__main__':
    sys.exit(main())
