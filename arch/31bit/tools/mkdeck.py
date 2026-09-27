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

    # ---------------------------------------------------------------- cards
    def _card(self, text, with_id):
        limit = TEXT_COL if with_id else ID_COL
        if len(text) > limit:
            raise ValueError('source text is %d columns, limit is %d:\n  %s'
                             % (len(text), limit, text))
        card = text.ljust(ID_COL) + (self.ident if with_id else '')
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

    def replace(self, frm, to=None, first=None, inc=100, lines=(), limit=None):
        self._seqcheck(first, inc, len(lines), limit)
        rng = '%s %s' % (frm, to) if to else '%s%s' % (frm, ' ' * 9)
        self.control('./ R %s $ %s %03d' % (rng, first, inc))
        for l in lines:
            self.source(l)

    def insert(self, after, first=None, inc=100, lines=(), limit=None):
        self._seqcheck(first, inc, len(lines), limit)
        self.control('./ I %s $ %s %03d' % (after, first, inc))
        for l in lines:
            self.source(l)

    def delete(self, frm, to=None):
        self.control('./ D %s%s' % (frm, ' ' + to if to else ''))

    # ---------------------------------------------------------------- output
    def write(self, path):
        with open(path, 'w') as f:
            for c in self.cards:
                f.write(c + '\n')
        return len(self.cards)


def aux(path, entries):
    """An AUX file lists update decks newest first: '<deck> V01 <description>'."""
    with open(path, 'w') as f:
        for deck, desc in entries:
            line = '%-8s V01 %s' % (deck, desc)
            if len(line) > WIDTH:
                raise ValueError('AUX line over 80 columns: ' + line)
            f.write(line.ljust(WIDTH) + '\n')


def verify(path):
    """Re-read a generated file and assert the layout, because asserting it at
    write time only proves the writer agreed with itself."""
    bad = []
    for n, line in enumerate(open(path), 1):
        line = line.rstrip('\n')
        if len(line) != WIDTH:
            bad.append((n, 'length %d' % len(line)))
        elif line[71:80].strip():
            bad.append((n, 'columns 72-80 not blank'))
    return bad


if __name__ == '__main__':
    print(__doc__)
    sys.exit(0)
