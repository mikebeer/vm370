#!/usr/bin/env python3
"""Five invariants every `./ R` must satisfy, checked before a build runs.

The 1 October verification build came back 180 modules clean of 192, and all
twelve remaining diagnostics were one of four mistakes -- none of them about DAT
semantics, all four mechanically detectable from the base source and the deck:

  LABEL-LOST   `DMKPGS` 00302000 is `PURCONT  L  R3,VMSEG`.  The replacement
               converted the instruction and did not carry the label, so three
               branches to `PURCONT` dangled.  `IFO188` x3.

  LABEL-DUP    The same deck emits `CKSEG EQU *` while replacing 01217000, but
               `CKSEG EQU *` lives at 01216000, which it does not replace.
               Defined twice.  `IFO196`.

  CONT-ORPHAN  `DMKCPP` 62000000 is `LA R8,L'PAGCORE(,R8) ... POINTER` with an
               `X` in **column 72**, and 62100000 is its continuation.
               Replacing the first card without the continuation left 62100000
               a standalone statement whose operand field was read as an
               opcode: `IFO054 INVALID OPERATION CODE`.  This is `R-04` from the
               other side -- not a marker written where it should not be, but
               one REMOVED where it was load-bearing.  `mkdeck.card()` asserts
               column 72 is blank on cards it WRITES, which is why the failure
               had to arrive through the records it does not write.

  SCOPE        `DMKCDB`, `DMKCDM` and `DMKDRD` reference `SEGINVAL` and
               `SEGSTOM`, which live in `CORE COPY`, and those three modules do
               not copy `CORE`.  `symchk.py` checks a deck's symbols for
               COLLISION and never for RESOLUTION, so it passed all three.
               `IFO188` x7 -- more than half the build's diagnostics.

Each check needs only the base `.ASSEMBLE`, the deck, and the module's `COPY`
statements, so all twelve diagnostics were available forty minutes before the
build started rather than fifty minutes after.

    python3 replchk.py [module ...]
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
LABEL = re.compile(r'^([A-Z@#$][A-Z@#$0-9]{0,7})\s')
COPYST = re.compile(r'^\s+COPY\s+(\S+)')
# A symbol reference: anything name-shaped in the operand field.  Deliberately
# loose -- a false candidate is cheap because it is then looked up, and a missed
# one is the failure this exists to catch.
NAME = re.compile(r'[A-Z@#$][A-Z@#$0-9]{0,7}')
# Register names, assembler keywords and anything that cannot be a symbol.
NOISE = set('''R0 R1 R2 R3 R4 R5 R6 R7 R8 R9 R10 R11 R12 R13 R14 R15
A AL AL1 AL2 AL3 AL4 C CL F H X B D P Z S V Y Q
EQU DS DC DSECT CSECT START END COPY MACRO MEND SPACE EJECT TITLE PRINT
USING DROP LTORG ORG CNOP ENTRY EXTRN WXTRN ISEQ MNOTE AIF AGO ANOP
GBLA GBLB GBLC LCLA LCLB LCLC SETA SETB SETC ACTR AREAD
ON OFF GEN NOGEN DATA NODATA NOSOURCE'''.split())


def records(path):
    """[(seq, text)] where text is columns 1-72."""
    out = []
    for line in open(path, errors='replace'):
        out.append((line[72:80].strip(), line[:72].rstrip('\n')))
    return out


def iscomment(t):
    return t.startswith('*') or t.lstrip().startswith('.*')


def continued(text):
    """Column 72 non-blank -- the next record continues this statement."""
    return len(text) >= 72 and text[71] != ' '


def known_member(name):
    """Is there a COPY or MACRO file of this name anywhere we look?"""
    for ext in ('COPY', 'MACRO'):
        for d in (SRC, os.path.join(SRC, '..', 'common'), UPDATES):
            if os.path.exists(os.path.join(d, '%s.%s' % (name, ext))):
                return True
    return False


def copies_of(path):
    """Members a COPY/MACRO file brings in itself (SAVE COPY copies further)."""
    out = []
    for _, t in records(path):
        if iscomment(t) or not t.strip():
            continue
        m = COPYST.match(t)
        if m and m.group(1) not in out:
            out.append(m.group(1))
    return out


def copies(base):
    """Every member whose symbols a module can see.

    `COPY <name>` is only half of it.  `DMKIOT` reaches the PSA not with
    `COPY PSA` but with a bare

             PSA                                                   01164000

    -- PSA is a MACRO, invoked.  Reading only COPY statements made the scope
    check report `IOINTPRM`, `CPCREG6` and `S370CHID` as unresolvable in modules
    that assembled perfectly, 45 false hits.  So an unlabelled statement whose
    opcode names a member file counts as bringing that member in, and nesting is
    followed, because `SAVE COPY` copies further members itself.
    """
    if not base.endswith('.ASSEMBLE'):
        return []
    out, seen, queue = [], set(), [base]
    while queue:
        path = queue.pop(0)
        for _, t in records(path):
            if iscomment(t) or not t.strip():
                continue
            m = COPYST.match(t)
            name = None
            if m:
                name = m.group(1)
            elif t[0] == ' ':
                tok = t.split()
                if tok and known_member(tok[0]):
                    name = tok[0]
            if not name or name in seen:
                continue
            seen.add(name)
            out.append(name)
            for ext in ('COPY', 'MACRO'):
                for d in (SRC, os.path.join(SRC, '..', 'common'), UPDATES):
                    q = os.path.join(d, '%s.%s' % (name, ext))
                    if os.path.exists(q):
                        queue.append(q)
    return out


def labels(path):
    syms = set()
    for _, t in records(path):
        if iscomment(t):
            continue
        m = LABEL.match(t)
        if m:
            syms.add(m.group(1))
    return syms


def member_symbols(member):
    """Symbols a COPY member defines -- base file PLUS any deck on it.

    The first version read only the base file, and so reported `PAGPFRA` as
    unresolvable in every module: `PAGPFRA` is not in CE's `CORE COPY`, it is
    added by this project's own `CORE.XA0033DK`.  A scope check that does not
    apply the decks it is checking sees the tree as it was, not as it will be
    assembled -- the same stale-artifact shape as I-140.
    """
    found = None
    for ext in ('COPY', 'MACRO'):
        for d in (SRC, os.path.join(SRC, '..', 'common'), UPDATES):
            p = os.path.join(d, '%s.%s' % (member, ext))
            if os.path.exists(p):
                found = labels(p) if found is None else found | labels(p)
    if found is None:
        return None
    for deck in glob.glob(os.path.join(UPDATES, '%s.XA*DK' % member)):
        for _, _, _, lines in deck_cards(deck):
            for l in lines:
                if iscomment(l):
                    continue
                m = LABEL.match(l)
                if m:
                    found.add(m.group(1))
    return found


def deck_cards(path):
    """[(op, frm, to, [source lines])] in deck order."""
    ops, cur = [], None
    for line in open(path, errors='replace'):
        m = CTL.match(line)
        if m:
            if cur:
                ops.append(cur)
            cur = [m.group(1), m.group(2), m.group(3) or m.group(2), []]
        elif cur is not None:
            cur[3].append(line[:72].rstrip('\n'))
    if cur:
        ops.append(cur)
    return ops


def check(mod):
    bad = []
    # A deck may sit on a COPY MEMBER rather than a module -- CORE, PSA,
    # RBLOKS, IOBLOKS, RDEVICE -- and those have no .ASSEMBLE.  The label and
    # continuation invariants apply to a member exactly as to a module.
    base = None
    for cand in ('%s.ASSEMBLE' % mod, '%s.COPY' % mod, '%s.MACRO' % mod):
        for d in (SRC, os.path.join(SRC, '..', 'common'), UPDATES):
            if os.path.exists(os.path.join(d, cand)):
                base = os.path.join(d, cand)
                break
        if base:
            break
    if not base:
        return [('NO-SOURCE', '', 'no source for %s as module or member' % mod)]
    recs = records(base)
    byseq = {int(s): i for i, (s, _) in enumerate(recs) if s.isdigit()}
    defined = {}                     # label -> record index
    refs = collections.defaultdict(list)
    for i, (s, t) in enumerate(recs):
        if iscomment(t):
            continue
        m = LABEL.match(t)
        if m:
            defined.setdefault(m.group(1), i)

    decks = sorted(glob.glob(os.path.join(UPDATES, '%s.XA*DK' % mod)))
    if not decks:
        return []

    replaced = set()
    newlabels = {}
    # ANCHOR-GONE: an anchor inside a range an EARLIER deck (lower number,
    # applied first) replaces or deletes is a record UPDATE no longer has,
    # and VMFASM stops on 'SEQUENCE NUMBER NOT FOUND' (i241: DMKPTR
    # XA0048DK anchored three ICMs the DAT deck XA0036DK had removed).
    taken = []                       # (a, b, deck) in application order
    for deck in decks:
        for op, frm, to, lines in deck_cards(deck):
            if op in 'RD':
                a, b = int(frm), int(to)
                for ta, tb, tdeck in taken:
                    if ta <= a <= tb or ta <= b <= tb:
                        bad.append(('ANCHOR-GONE', frm,
                                    '%s anchors %s-%s inside %s-%s, which %s '
                                    'already replaced' % (os.path.basename(deck),
                                    frm, to, ta, tb, os.path.basename(tdeck))))
                taken.append((a, b, deck))
                for n, i in byseq.items():
                    if a <= n <= b:
                        replaced.add(i)
            for l in lines:
                if iscomment(l):
                    continue
                m = LABEL.match(l)
                if m:
                    newlabels.setdefault(m.group(1), os.path.basename(deck))

            # CONT-ORPHAN: the last replaced record continues onto the next,
            # and the next is not itself replaced.
            if op in 'RD':
                last = max((i for i in range(len(recs))
                            if recs[i][0].isdigit()
                            and a <= int(recs[i][0]) <= b), default=None)
                # I-205: a deck may now write a continuation card itself
                # (mkdeck's trailing backslash puts the X in column 72).  If
                # the deck's LAST new card is continued, the old continuation
                # that follows is its continuation now, not an orphan.
                deck_continues = bool(lines) and len(lines[-1]) > 71 \
                    and lines[-1][71] != ' '
                if last is not None and continued(recs[last][1]) \
                        and not deck_continues:
                    nxt = last + 1
                    if nxt < len(recs) and int(recs[nxt][0] or 0) > b:
                        bad.append((
                            'CONT-ORPHAN', recs[last][0],
                            'column 72 is "%s", so %s continues this statement '
                            'and is NOT replaced -- it becomes a standalone '
                            'statement and the assembler reads its operand '
                            'field as an opcode'
                            % (recs[last][1][71], recs[nxt][0])))
                # the first replaced record is itself a continuation
                first = min((i for i in range(len(recs))
                             if recs[i][0].isdigit()
                             and a <= int(recs[i][0]) <= b), default=None)
                # ...and a deck whose new cards continue a surviving card are
                # that card's continuation; only a deck of plain cards orphans
                # it.  Comment cards do not count.
                newfirst = next((l for l in lines if not iscomment(l)), '')
                deck_is_cont = op == 'R' and newfirst[:15].strip() == '' \
                    and newfirst.strip() != ''
                if first and first - 1 >= 0 and continued(recs[first - 1][1]) \
                        and (first - 1) not in replaced and not deck_is_cont:
                    bad.append((
                        'CONT-ORPHAN', recs[first][0],
                        'this record CONTINUES %s, which is not replaced, so '
                        'the surviving first card loses its continuation'
                        % recs[first - 1][0]))

    # LABEL-LOST: a replaced record defined a label that the deck does not
    # redefine, and something still branches to it.
    for lab, i in defined.items():
        if i in replaced and lab not in newlabels:
            users = [recs[j][0] for j in range(len(recs))
                     if j != i and j not in replaced
                     and not iscomment(recs[j][1])
                     and re.search(r'\b%s\b' % re.escape(lab), recs[j][1][9:])]
            if users:
                bad.append(('LABEL-LOST', recs[i][0],
                            '%s was defined here and the replacement does not '
                            'redefine it; still referenced from %s'
                            % (lab, ' '.join(users[:4]))))

    # LABEL-DUP: the deck defines a label that survives on an unreplaced record.
    for lab, deck in newlabels.items():
        i = defined.get(lab)
        if i is not None and i not in replaced:
            bad.append(('LABEL-DUP', recs[i][0],
                        '%s is defined here and %s defines it again -- '
                        'IFO196 HAS BEEN PREVIOUSLY DEFINED' % (lab, deck)))

    # SCOPE: restricted to the symbols THIS PROJECT INTRODUCED.
    #
    # The first version tried to resolve every name in every operand and
    # reported 411 candidates, then 85 after the comment prose was excluded --
    # `XL32`, `FF000000`, `XAIO`, COPY operands, and symbols that reach a module
    # by routes this reader does not model.  Noise at that level is worse than
    # no check: the three real failures were in the list and invisible.
    #
    # The risk is not general.  It is specific and small: a symbol that did not
    # exist before this project added it, referenced from a module that cannot
    # see where it was added.  `SEGINVAL` and `SEGSTOM` went into `CORE COPY`,
    # and `DMKCDB`, `DMKCDM` and `DMKDRD` do not copy `CORE` -- seven of the
    # build's twelve diagnostics, from one mistake.  So resolve only the
    # introduced names, where every miss is real.
    # A label a deck writes because the record it replaces carried it --
    # DMKPTRAN on XA0046DK's new entry card -- is carried forward, not
    # introduced: it was an ENTRY every module could already CALL.  Only a
    # label the base of its own module does not define counts.
    introduced = set()
    for d in glob.glob(os.path.join(UPDATES, '*.XA*DK')):
        own = set()
        dmod = os.path.basename(d).split('.')[0]
        for cand in ('%s.ASSEMBLE' % dmod, '%s.COPY' % dmod, '%s.MACRO' % dmod):
            for sd in (SRC, os.path.join(SRC, '..', 'common'), UPDATES):
                q = os.path.join(sd, cand)
                if os.path.exists(q):
                    for _, txt in records(q):
                        mm = LABEL.match(txt) if not iscomment(txt) else None
                        if mm:
                            own.add(mm.group(1))
        for _, _, _, lines in deck_cards(d):
            for l in lines:
                if iscomment(l):
                    continue
                m = LABEL.match(l)
                if m and m.group(1) not in own:
                    introduced.add(m.group(1))
    reach = set(defined) | set(newlabels)
    members = list(copies(base))
    # A MACRO has no scope of its own: it expands inside the module that
    # invokes it, and every CP module invokes PSA.  TRANS already names
    # ASYSVM and VMSEG that way; XA0046DK's ATRL31 (I-216) is the first such
    # reference to a symbol a deck INTRODUCED, which is what this check
    # looks at, so the PSA is the one member a macro is given.
    if base.endswith('.MACRO') and 'PSA' not in members:
        members.append('PSA')
    # A deck may add a COPY of its own -- XA0044DK gives DMKCDB `COPY CORE`
    # so that GETKEY can name PAGTSWP -- and that widens the module's scope
    # exactly as a COPY in the base does (I-209).  Nested members follow.
    for deck in decks:
        for op, frm, to, lines in deck_cards(deck):
            for l in lines:
                m = COPYST.match(l)
                if m and m.group(1) not in members:
                    members.append(m.group(1))
                    for ext in ('COPY', 'MACRO'):
                        for d in (SRC, os.path.join(SRC, '..', 'common'), UPDATES):
                            q = os.path.join(d, '%s.%s' % (m.group(1), ext))
                            if os.path.exists(q):
                                members.extend(x for x in copies_of(q)
                                               if x not in members)
    for mem in members:
        syms = member_symbols(mem)
        if syms:
            reach |= syms
    for deck in decks:
        for op, frm, to, lines in deck_cards(deck):
            for l in lines:
                if iscomment(l):
                    continue
                parts = l[9:].split(None, 1)
                if len(parts) < 2:
                    continue
                for cand in NAME.findall(parts[1].split()[0].upper()):
                    if cand in reach or cand not in introduced:
                        continue
                    bad.append((
                        'SCOPE', frm,
                        '%s is referenced here but is defined only where %s '
                        'cannot see it -- %s copies %s'
                        % (cand, mod, mod, ' '.join(members) or 'nothing')))
    return bad


def main():
    mods = sys.argv[1:] or sorted(
        {os.path.basename(p).split('.')[0]
         for p in glob.glob(os.path.join(UPDATES, '*.XA*DK'))})
    counts = collections.Counter()
    for mod in mods:
        bad = [b for b in check(mod)]
        hard = [b for b in bad if not b[0].endswith('?')]
        soft = [b for b in bad if b[0].endswith('?')]
        if hard or soft:
            print('=== %s' % mod)
        for kind, seq, why in hard:
            counts[kind] += 1
            print('  %-12s %-9s %s' % (kind, seq, why))
        # SCOPE? is advisory: the member reader does not find every COPY file,
        # so it reports candidates rather than verdicts.  Deduplicated by name.
        seen = set()
        for kind, seq, why in soft:
            name = why.split()[0]
            if name in seen:
                continue
            seen.add(name)
            counts[kind] += 1
            print('  %-12s %-9s %s' % (kind, seq, why))
    print()
    for kind, n in counts.most_common():
        print('%-12s %d' % (kind, n))
    if not counts:
        print('all five invariants hold on every deck')
    return 1 if any(not k.endswith('?') for k in counts) else 0


if __name__ == '__main__':
    sys.exit(main())
