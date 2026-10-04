#!/usr/bin/env python3
"""Generate IBM VM/370 UPDATE decks with guaranteed column discipline.

R-04 is that column-sensitive source gets corrupted by tooling, and it is a
realised risk, not a hypothetical: renaming CP's `TRACE` macro to `CPTRACE`
pushed each line's change marker into column 72, the continuation column, and
the macro began failing with "continuation line < 16 characters". Two
characters.

An UPDATE deck is the safer vehicle -- it never rewrites an existing line, it
inserts and replaces whole records -- but the deck itself is column-sensitive,
so this generator enforces the layout rather than trusting a text editor.

Card layout, measured from CE's own decks (094/DMKIOS.HRC065DK,
094/PSA.HRC004DK):

    columns  1-63   source text
    columns 64-71   the update identifier, e.g. XA00001DK
    columns 72-80   blank -- UPDATE fills 73-80 with generated sequence numbers

Control cards:

    ./ I <anchor> $ <first-new-seq> <increment>          insert after anchor
    ./ R <from> [<to>] $ <first-new-seq> <increment>     replace a range
    ./ D <from> [<to>]                                   delete a range

Every card is exactly 80 bytes. The generator asserts that, asserts the source
text fits in 63 columns, and asserts that generated sequence numbers stay below
the next surviving anchor -- which is the failure mode R-22 describes.
"""
import glob
import os
import re
import sys

ID_COL = 63          # zero-based: identifier occupies columns 64-71
TEXT_COL = 61        # source text stops here, leaving a 2-column gutter before
                     # the identifier -- CE's own decks leave one, and text that
                     # runs up against the id is unreadable in a listing
WIDTH = 80


class Deck:
    def __init__(self, ident):
        if len(ident) > 8:
            raise ValueError('update identifier must be 8 characters or fewer')
        self.ident = ident
        self.cards = []
        self._claimed = []      # (first_seq, last_seq) for the overlap check
        self._last_anchor = None  # ascending-order check, see _anchor()

    # ---------------------------------------------------------------- cards
    CONT = '\\'       # a source line ending in a backslash is a CONTINUED card

    def _card(self, text, with_id):
        # A continued statement needs a non-blank in column 72.  R-04 is the
        # record of what happens when that column is written by accident; this
        # is the one way to write it on purpose, and it is spelt out at the
        # call site rather than inferred from the text.  I-205.
        cont = with_id and text.endswith(self.CONT)
        if cont:
            text = text[:-1].rstrip()
        limit = TEXT_COL if with_id else ID_COL
        if len(text) > limit:
            raise ValueError('source text is %d columns, limit is %d:\n  %s'
                             % (len(text), limit, text))
        card = text.ljust(ID_COL) + (self.ident if with_id else '')
        card = card.ljust(ID_COL + 8) + ('X' if cont else '')
        card = card.ljust(WIDTH)
        assert len(card) == WIDTH, len(card)
        self.cards.append(card)

    def control(self, text):
        self._card(text, with_id=False)

    def source(self, text):
        self._card(text, with_id=True)

    @staticmethod
    def comment(text, indent='*  '):
        """Word-wrap prose into assembler comment lines that fit the card.

        Hand-wrapping comments to 61 columns is exactly the fiddly,
        error-prone work that R-04 is about, and it cost several iterations
        before this existed.  Pass a paragraph; get cards back.
        """
        out, line = [], indent
        for word in text.split():
            cand = line + ('' if line == indent else ' ') + word
            if len(cand) > TEXT_COL:
                out.append(line.rstrip())
                line = indent + word
            else:
                line = cand
        if line.strip() != indent.strip():
            out.append(line.rstrip())
        return out

    # ------------------------------------------------------------ operations
    def _anchor(self, seq):
        """UPDATE scans the file once, forward, so control cards must be in
        ascending anchor order.  A card out of order is not diagnosed as such:
        UPDATE has already read past the record and reports

            SEQUENCE NUMBER '00524000' NOT FOUND.

        which reads as a wrong anchor and sends you looking through the base
        file and the PTF decks for a record that is sitting right there.  Cost
        one ten-minute run.  I-45.
        """
        if self._last_anchor is not None and int(seq) <= int(self._last_anchor):
            raise ValueError(
                'control card for %s follows %s: UPDATE reads the file once, '
                'forward, so cards must be in ascending anchor order and this '
                'one would be reported as NOT FOUND' % (seq, self._last_anchor))
        self._last_anchor = seq

    def _seqcheck(self, first, inc, count, limit):
        """A deck that numbers past the next surviving record corrupts the
        file's ordering, and UPDATE will not always say so.  R-22."""
        last = int(first) + inc * (count - 1)
        if limit is not None and last >= int(limit):
            raise ValueError(
                'generated sequence %08d would reach or pass the next '
                'surviving record %s -- reduce the increment or renumber'
                % (last, limit))
        self._claimed.append((int(first), last))

    @staticmethod
    def _seq8(first):
        """A sequence number is an EIGHT-COLUMN field, so it is zero-padded.

        Generators compute the first new number arithmetically, and
        `str(int('01045000') + 100)` is `'1045100'` -- seven digits.  UPDATE
        reads columns 73-80 as the key, so a short number is a DIFFERENT key
        from the one intended and sorts elsewhere, which silently corrupts
        the ordering seen by any LATER update level.  It does not show up in
        this assembly, because the records replaced are still the right ones:
        54 of 173 control cards carried a short number and every affected
        module assembled with NO STATEMENTS FLAGGED.  That is exactly why it
        has to be caught here rather than by reading a deck.  R-22, I-103.
        """
        s = str(first)
        if not s.isdigit() or len(s) > 8:
            raise ValueError('sequence number must be up to 8 digits: %r'
                             % (first,))
        return s.zfill(8)

    def replace(self, frm, to=None, first=None, inc=100, lines=(), limit=None):
        first = self._seq8(first)
        self._anchor(frm)
        self._seqcheck(first, inc, len(lines), limit)
        rng = '%s %s' % (frm, to) if to else '%s%s' % (frm, ' ' * 9)
        self.control('./ R %s $ %s %03d' % (rng, first, inc))
        for l in lines:
            self.source(l)

    def insert(self, after, first=None, inc=100, lines=(), limit=None):
        first = self._seq8(first)
        self._anchor(after)
        self._seqcheck(first, inc, len(lines), limit)
        self.control('./ I %s $ %s %03d' % (after, first, inc))
        for l in lines:
            self.source(l)

    def delete(self, frm, to=None):
        self._anchor(frm)
        self.control('./ D %s%s' % (frm, ' ' + to if to else ''))

    # ---------------------------------------------------------------- output
    def write(self, path):
        with open(path, 'w') as f:
            for c in self.cards:
                f.write(c + '\n')
        return len(self.cards)


def next_seq(source, anchor):
    """The sequence number of the record following `anchor` in `source`.

    `Deck._seqcheck` refuses generated numbers that reach the next surviving
    record, but it can only check against the limit it is given -- and a limit
    read off the screen is a guess.  XA0013DK numbered 01930100 to 01931100
    against a limit of 01951000 taken from a nearby literal, and walked straight
    over a real record at 01931000.  UPDATE reported it, the assembler flagged
    `IFO025 STATEMENT OUT OF SEQUENCE` from DMKCPI's own `ISEQ 73,80`, and the
    deck was wrong in a way the generator was built to prevent.

    So derive the limit instead of quoting one.  I-52.

        limit=next_seq(SRC + '/DMKCPI.ASSEMBLE', '01930000')
    """
    seqs = []
    for line in open(source, errors='replace'):
        s = line[72:80].strip()
        if s.isdigit():
            seqs.append(s)
    try:
        return seqs[seqs.index(anchor) + 1]
    except (ValueError, IndexError):
        raise ValueError('anchor %s is not in %s, or is its last record'
                         % (anchor, source))


def aux(path, entries):
    """An AUX file lists update decks newest first: '<deck> V01 <description>'.

    MERGES with what is already there rather than replacing it.  The AUXLCL is
    what `VMFASM` reads, so a deck missing from it is a deck that is never
    applied -- and the module then fails to assemble with every site it was
    meant to fix.  Two generators writing the same module's AUXLCL used to mean
    whichever ran last won: a DAT deck added to `DMKVMA` before the ECPS loop
    was silently dropped from the file, and `deckchk.py` could not see it,
    because that tool globs the deck FILES.  Cost would have been a 35-minute
    build.  I-138.

    Order is preserved -- newest first, with the new entries ahead of the old --
    and a repeated deck identifier updates its description in place rather than
    appearing twice.
    """
    old = []
    if os.path.exists(path):
        for line in open(path):
            line = line.rstrip()
            if not line:
                continue
            parts = line.split(None, 2)
            if len(parts) == 3 and parts[1] == 'V01':
                old.append((parts[0], parts[2].rstrip()))
    seen, merged = set(), []
    for deck, desc in list(entries) + old:
        if deck in seen:
            continue
        seen.add(deck)
        merged.append((deck, desc))
    # VMFASM applies the LAST line first and the first line last, so the
    # order of this file IS the order of application.  Generator order is
    # not a safe proxy: DMKVMA's AUXLCL ended up with XA0045DK at the bottom,
    # applied before XA0036DK whose anchors it had deleted (I-213).  Our XA
    # decks are numbered in the order they were written and each later one
    # anchors on what the earlier ones left, so sort them: highest first.
    def key(e):
        m = re.match(r'XA(\d+)DK$', e[0])
        return (0, -int(m.group(1))) if m else (1, 0)
    merged.sort(key=key)
    with open(path, 'w') as f:
        for deck, desc in merged:
            line = '%-8s V01 %s' % (deck, desc)
            if len(line) > WIDTH:
                raise ValueError('AUX line over 80 columns: ' + line)
            f.write(line.ljust(WIDTH) + '\n')


def auxcheck(deckdir):
    """Every generated deck must be LISTED in its module's AUXLCL.

    The invariant that `aux()`'s merge is there to maintain, asserted separately
    so that a future generator cannot break it quietly.  Returns a list of
    (deck file, reason).
    """
    bad = []
    for path in sorted(glob.glob(os.path.join(deckdir, '*.XA*DK'))):
        base = os.path.basename(path)
        member, ident = base.split('.', 1)
        auxp = os.path.join(deckdir, '%s.AUXLCL' % member)
        if not os.path.exists(auxp):
            bad.append((base, 'no %s.AUXLCL at all' % member))
            continue
        if ident not in open(auxp).read():
            bad.append((base, '%s.AUXLCL does not list it, so VMFASM will '
                              'never apply it' % member))
    return bad


def verify(path):
    """Re-read a generated file and assert the layout, because asserting it at
    write time only proves the writer agreed with itself."""
    bad = []
    for n, line in enumerate(open(path), 1):
        line = line.rstrip('\n')
        if len(line) != WIDTH:
            bad.append((n, 'length %d' % len(line)))
        elif line[72:80].strip():
            bad.append((n, 'columns 73-80 not blank'))
        elif line[71] not in ' X':
            bad.append((n, 'column 72 is %r, not blank or X' % line[71]))
    return bad


if __name__ == '__main__':
    print(__doc__)
    sys.exit(0)
