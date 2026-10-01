#!/usr/bin/env python3
"""Harvest the assembler's own diagnostics and reconcile them against the sweep.

`CORE.XA0033DK` renames CP's DAT-table fields **without aliases**, on purpose:
every one of the 154 sites `dattab.py` found becomes `IFO188 UNDEFINED SYMBOL`,
and the assembler -- not a regex of mine -- becomes the checklist.  This tool
reads the resulting build log and answers the only question worth asking of two
independent lists:

    CONFIRMED  flagged by the assembler and found by the sweep
    MISSED     flagged by the assembler, **not** found by the sweep
    SILENT     found by the sweep, **not** flagged -- the dangerous bucket

`SILENT` is dangerous because it is not empty and cannot be.  Three classes of
site keep their symbol name across the rename and therefore produce no
diagnostic at all:

  * `SHRPAGE` -- 59 sites.  `SHRTABLE.COPY` declares its own per-segment word
    and only a *comment* says it is an STE ("THE ENTRY IS THE SAME AS 'S*1
    SEGPAGE'").  Renaming `SEGPAGE` does not reach it.
  * `SEGENQ`, `PAGREF` -- names kept deliberately, values kept, **positions
    moved**.  A site naming only the flag assembles clean and tests the wrong
    bit.
  * `PAGTSWP`, `PAGBMP` -- `EQU`s whose *arithmetic* changed underneath them.
    Every use still assembles and now computes a different number.

So the assembler closes the majority of the class mechanically and this tool
names the remainder explicitly.  That remainder is the hand-work, and writing it
down is the difference between a gap and a surprise.

    python3 asmerr.py <build-log> [--mod DMKXXX] [--diags]

Log grammar (VM/370 `VMFASM` under Hercules, verified against `h1.log`):

    EXEC VMFASM DMKACO DMKLCL      <- module boundary
    APPLYING 'DMKACO XA0033DK A1'.
    ASMBLING DMKACO
      370000     6985          TM    SEGPAGE+3,SEGINV     <- flagged statement
    IFO188 *** UNDEFINED SYMBOL ***                       <- its diagnostic
    NUMBER OF STATEMENTS FLAGGED IN THIS ASSEMBLY =     2
"""
import collections
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

VMFASM = re.compile(r'^EXEC VMFASM (\S+)', re.M)
# A listing line echoed into the console log: update sequence, statement number,
# then the source.  The sequence field is blank for a statement that came from
# the base file rather than an update deck.
STMT = re.compile(r'^\s{2}(\d{0,6})\s+(\d+)([+\-]?)\s{2,}(.*)$')
DIAG = re.compile(r'^(IFO\d{3}) \*\*\* (.*?) \*\*\*')
FLAGGED = re.compile(r'NUMBER OF STATEMENTS FLAGGED IN THIS ASSEMBLY =\s*(\d+)')
NOFLAG = re.compile(r'NO STATEMENTS FLAGGED IN THIS ASSEMBLY')

# Symbols CORE.XA0033DK removes.  A reference to one of these is what the
# assembler is expected to flag; anything else it flags is a different problem
# and must not be quietly counted as part of this conversion.
RENAMED = {'SEGPAGE': 'SEGPTO', 'SEGPLEN': 'SEGPTL', 'SEGINV': 'SEGINVAL',
           'PAGCORE': 'PAGPFRA', 'PAGINVAL': 'PAGINV'}
# Symbols deliberately kept, whose MEANING moved anyway.  No diagnostic exists
# for these and none can.
KEPT_BUT_MOVED = {'SEGENQ': 'position: bit 25 is now the lowest PTO bit',
                  'PAGREF': 'position: PAGCORE+1 -> PAGPFRA+3',
                  'PAGTSWP': 'arithmetic: 16 entries of 2 -> 256 of 4',
                  'PAGBMP': 'arithmetic: derived from PAGTSWP',
                  'SHRPAGE': 'a separate declaration in SHRTABLE.COPY'}

Flag = collections.namedtuple('Flag', 'mod seq stmt text diag msg')


def harvest(path):
    """Every flagged statement in the log, with the module it belongs to."""
    mod, pending, flags, totals = None, None, [], {}
    for line in open(path, errors='replace'):
        line = line.rstrip('\n')
        m = VMFASM.match(line)
        if m:
            mod, pending = m.group(1), None
            continue
        m = DIAG.match(line)
        if m and pending:
            flags.append(Flag(mod, pending[0], pending[1], pending[2],
                              m.group(1), m.group(2)))
            pending = None
            continue
        m = STMT.match(line)
        if m:
            # A continuation line ('+' in the flag column) belongs to the macro
            # expansion of the statement above it, not to a new statement.
            pending = (m.group(1), m.group(2), m.group(4).rstrip())
            continue
        m = FLAGGED.search(line)
        if m and mod:
            totals[mod] = int(m.group(1))
        elif NOFLAG.search(line) and mod:
            totals[mod] = 0
    return flags, totals


def symbols(text):
    """Which renamed-away symbols a flagged statement names."""
    return [s for s in RENAMED if re.search(r'\b%s\b' % s, text)]


def main():
    args = sys.argv[1:]
    if not args:
        print(__doc__)
        return 2
    log = args[0]
    only = args[args.index('--mod') + 1] if '--mod' in args else None

    flags, totals = harvest(log)
    if not totals:
        print('### no assembly found in %s -- is the build still staging?' % log)
        return 2

    import dattab
    sweep = [s for s in dattab.scan(dattab.SRC) if s.verdict != 'ok']
    sweep_text = collections.defaultdict(list)
    for s in sweep:
        sweep_text[(s.mod, re.sub(r'\s+', ' ', s.text))].append(s)

    if only:
        flags = [f for f in flags if f.mod == only]
        sweep = [s for s in sweep if s.mod == only]

    ours = [f for f in flags if symbols(f.text)]
    other = [f for f in flags if not symbols(f.text)]

    print('%s: %d modules assembled, %d statements flagged'
          % (os.path.basename(log), len(totals), sum(totals.values())))
    print('  %d name a symbol CORE.XA0033DK renamed away (this conversion)'
          % len(ours))
    print('  %d do not -- unrelated diagnostics, read them separately' % len(other))
    print('  sweep predicted %d sites needing work in %d modules'
          % (len(sweep), len({s.mod for s in sweep})))
    print()

    # A site declared in a COPY or MACRO member is flagged under whichever
    # MODULE copies it, so the module names legitimately disagree.  Matching on
    # (module, text) alone would file those six sites as sweep holes, which is
    # the opposite of the truth.  So: exact key first, text-only second, and the
    # text-only matches are reported as what they are.
    by_text = collections.defaultdict(list)
    for s in sweep:
        by_text[re.sub(r'\s+', ' ', s.text)].append(s)

    matched, copied, missed = [], [], []
    for f in ours:
        norm = re.sub(r'\s+', ' ', f.text.strip())
        if (f.mod, norm) in sweep_text:
            matched.append(f)
        elif norm in by_text:
            copied.append((f, by_text[norm][0]))
        else:
            missed.append(f)

    flagged_keys = {(f.mod, re.sub(r'\s+', ' ', f.text.strip())) for f in ours}
    flagged_text = {re.sub(r'\s+', ' ', f.text.strip()) for f in ours}
    silent = [s for s in sweep
              if (s.mod, re.sub(r'\s+', ' ', s.text)) not in flagged_keys
              and re.sub(r'\s+', ' ', s.text) not in flagged_text]

    print('CONFIRMED %4d  flagged and predicted' % len(matched))
    if copied:
        print('  of which %d flagged under the module that COPYs the member the'
              % len(copied))
        print('  sweep attributes them to -- the same site, not a discrepancy')
    print('MISSED    %4d  flagged but NOT predicted -- the sweep has a hole'
          % len(missed))
    print('SILENT    %4d  predicted but NOT flagged -- no diagnostic exists'
          % len(silent))
    print()

    if missed:
        print('The sweep missed these.  Each one is a defect in dattab.py:')
        for f in missed:
            print('  %-7s %-6s %-6s %s' % (f.mod, f.seq or '-', f.stmt,
                                           f.text[:56]))
            print('          %s %s' % (f.diag, f.msg))
        print()

    by_field = collections.Counter(s.field for s in silent)
    if silent:
        print('Silent sites by field -- the hand-work, with why no diagnostic fires:')
        for fld, n in by_field.most_common():
            why = KEPT_BUT_MOVED.get(fld, 'name unchanged by CORE.XA0033DK')
            print('  %-9s %4d   %s' % (fld, n, why))
        print()
        unexpected = [f for f in by_field if f not in KEPT_BUT_MOVED]
        applied = "APPLYING 'CORE XA0033DK" in open(log, errors='replace').read()
        if unexpected and applied:
            print('  ### %s was renamed away yet produced no diagnostic.' % unexpected)
            print('  ### Either the module did not assemble or the deck did not apply.')
            print()
        elif unexpected:
            print('  (CORE XA0033DK was not applied in this run, so the renamed')
            print('   fields are still defined and nothing can be flagged yet.)')
            print()

    print('Per module (flagged / predicted):')
    mods = sorted(set(totals) | {s.mod for s in sweep})
    for m in mods:
        f = len([x for x in ours if x.mod == m])
        p = len([s for s in sweep if s.mod == m])
        if not f and not p:
            continue
        note = ''
        if m not in totals:
            note = '   <- NOT ASSEMBLED in this run'
        elif f == 0 and p:
            note = '   <- all silent'
        print('  %-9s %4d / %4d%s' % (m, f, p, note))

    if '--diags' in args:
        print('\nEvery diagnostic naming a renamed symbol:')
        for f in ours:
            print('  %-7s %-6s %-6s %-9s %s'
                  % (f.mod, f.seq or '-', f.stmt, f.diag, f.text[:50]))

    if other:
        print('\nDiagnostics NOT about this conversion (%d):' % len(other))
        seen = collections.Counter((f.diag, f.msg) for f in other)
        for (d, msg), n in seen.most_common(10):
            print('  %4d  %s %s' % (n, d, msg))

    return 1 if missed else 0


if __name__ == '__main__':
    sys.exit(main())
