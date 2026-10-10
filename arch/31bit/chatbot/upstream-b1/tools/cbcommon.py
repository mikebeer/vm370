"""Shared helpers for the CHATBOT data converter and deck builder (PC side)."""
import re

REC = 80            # CMS card image / RECFM F LRECL 80
CHUNK = REC - 2     # col 1 = record type, col 2 = '+' (continuation) or ' '

FOLD = {
    'ä': 'ae', 'ö': 'oe', 'ü': 'ue', 'Ä': 'Ae', 'Ö': 'Oe', 'Ü': 'Ue', 'ß': 'ss',
    'é': 'e', 'è': 'e', 'à': 'a', 'á': 'a', 'ç': 'c',
    '“': '"', '”': '"', '„': '"', '‘': "'", '’': "'",
    '–': '-', '—': '-', '…': '...', '•': '*', '→': '->',
    'ﬁ': 'fi', '­': '', ' ': ' ', ' ': ' ', '€': 'EUR',
    '²': '2', '°': ' deg',
}


def fold(s):
    """Fold text to the 7-bit subset that survives ASCII->EBCDIC->3270 intact."""
    out = []
    for c in s:
        if ord(c) < 128:
            out.append(c)
        else:
            out.append(FOLD.get(c, '?'))
    return ''.join(out)


def clean(s):
    s = fold(s)
    s = s.replace('\r', ' ').replace('\t', ' ')
    # '#' separates variants in the persona format, keep it; collapse control chars
    return ''.join(c if c >= ' ' else ' ' for c in s)


def records(tag, text):
    """Split `text` into <=CHUNK-char pieces; continuation records carry '+' in col 2.
    A piece never ends with a blank (trailing blanks are not significant on CMS);
    a following piece may start with one (col 3 onwards is significant)."""
    text = text.rstrip()
    if text == '':
        return [tag + ' ']
    out = []
    first = True
    while text:
        if len(text) <= CHUNK:
            piece, text = text, ''
        else:
            cut = CHUNK
            # prefer to cut before a blank so words stay whole
            sp = text.rfind(' ', 0, CHUNK + 1)
            if sp > CHUNK // 2:
                cut = sp
            piece, text = text[:cut], text[cut:]
            while piece.endswith(' '):          # move trailing blanks to the next piece
                text = ' ' + text if False else piece[-1] + text
                piece = piece[:-1]
        out.append(tag + (' ' if first else '+') + piece)
        first = False
    return out


def split_steps(text):
    """Port of NPCchat.gd _split_into_steps()."""
    paras = [p.strip() for p in text.split('\n\n') if p.strip()]
    if len(paras) > 1:
        return paras
    ms = list(re.finditer(r'\d+\.\s', text))
    if len(ms) <= 1:
        return [text.strip()]
    steps = []
    for i, m in enumerate(ms):
        end = len(text) if i == len(ms) - 1 else ms[i + 1].start()
        piece = text[m.start():end].strip()
        if piece:
            steps.append(piece)
    return steps if len(steps) > 1 else [text.strip()]
