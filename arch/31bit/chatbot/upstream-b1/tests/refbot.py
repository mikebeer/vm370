"""Reference implementation of autoloads/bot.gd understand() in Python -- a literal
translation, reading the ORIGINAL .nlu.json files.  Used only to cross-check the
cREXX port (tests/crosscheck.py): same message sequence in, same intent out."""
import json

FUZZY_MIN_LENGTH = 4
PRONOUN_CARRYOVER_BONUS = 50


def normalise(text):
    out = text.lower()
    for a in ("'", "’", "‘", "`"):
        out = out.replace(a, "")
    for a, b in (("ä", "ae"), ("ö", "oe"), ("ü", "ue"), ("ß", "ss"), ("é", "e"), ("-", " ")):
        out = out.replace(a, b)
    clean = []
    for ch in out:
        ok = ch == " " or ch == "_" or ("a" <= ch <= "z") or ("0" <= ch <= "9") or (ord(ch) > 127 and ch.isalpha())
        clean.append(ch if ok else " ")
    s = "".join(clean)
    while "  " in s:
        s = s.replace("  ", " ")
    return s.strip()


def tokens(text):
    return [w for w in normalise(text).split(" ") if len(w) > 1]


def edit_distance(a, b):
    if a == b:
        return 0
    if not a:
        return len(b)
    if not b:
        return len(a)
    rows = [[0] * (len(b) + 1) for _ in range(len(a) + 1)]
    for i in range(len(a) + 1):
        rows[i][0] = i
    for j in range(len(b) + 1):
        rows[0][j] = j
    for i in range(1, len(a) + 1):
        for j in range(1, len(b) + 1):
            cost = 0 if a[i - 1] == b[j - 1] else 1
            best = min(rows[i - 1][j] + 1, rows[i][j - 1] + 1, rows[i - 1][j - 1] + cost)
            if i > 1 and j > 1 and a[i - 1] == b[j - 2] and a[i - 2] == b[j - 1]:
                best = min(best, rows[i - 2][j - 2] + 1)
            rows[i][j] = best
    return rows[len(a)][len(b)]


def fuzzy_equal(token, target):
    if token == target:
        return True
    if len(token) < FUZZY_MIN_LENGTH or len(target) < FUZZY_MIN_LENGTH:
        return False
    if target.startswith(token) and len(token) >= len(target) - 3:
        return True
    if token.startswith(target) and len(target) >= 4:
        return True
    allowed = 1 if max(len(token), len(target)) < 8 else 2
    return edit_distance(token, target) <= allowed


class Ref:
    def __init__(self, nlu_path):
        self.nlu = json.load(open(nlu_path, encoding="utf-8"))
        self.last_topic = ""
        self.last_intent = ""

    def match_strength(self, group, toks):
        words = self.nlu.get("synonyms", {}).get(group, [group])
        best = 0
        for t in toks:
            for w in words:
                if fuzzy_equal(t, w):
                    best = max(best, len(w))
        return best

    def is_crisis(self, text):
        flat = normalise(text)
        cr = self.nlu.get("crisis", {})
        for p in cr.get("phrases", []):
            if normalise(p) in flat:
                return True
        toks = tokens(text)
        for w in cr.get("words", []):
            for t in toks:
                if fuzzy_equal(t, normalise(w)):
                    return True
        return False

    def is_continuation(self, toks):
        words = self.nlu.get("continue_words", [])
        for t in toks:
            for w in words:
                if fuzzy_equal(t, normalise(w)):
                    return True
        return False

    def carryover(self, toks):
        lt = self.last_topic
        intents = self.nlu.get("intents", {})
        if lt == "" or lt not in intents:
            return ""
        pro = intents[lt].get("pronouns", [])
        if not pro:
            return ""
        if self.match_strength(lt, toks) > 0:
            return ""
        for t in toks:
            for p in pro:
                if fuzzy_equal(t, normalise(p)):
                    return lt
        return ""

    def understand(self, text):
        """returns (kind, intent_name, score, repeated)"""
        if self.is_crisis(text):
            self.last_intent = ""
            return ("crisis", "", 0, False)
        toks = tokens(text)
        target = self.carryover(toks)
        best, best_score = "", 0
        intents = self.nlu.get("intents", {})
        for name, it in intents.items():
            if name.startswith("_"):
                continue
            score = 0
            for g in it.get("any", []):
                score += self.match_strength(g, toks)
            if it.get("entity", name) == target:
                score += PRONOUN_CARRYOVER_BONUS
            if score > best_score:
                best, best_score = name, score
        if best == "" and self.last_intent != "" and self.last_intent in intents and self.is_continuation(toks):
            best, best_score = self.last_intent, 1
        if best != "":
            it = intents[best]
            repeated = best == self.last_intent
            entity = it.get("entity", best)
            src = intents.get(entity, it)
            self.last_topic = entity if src.get("pronouns", []) else ""
            self.last_intent = best
            return ("intent", best, best_score, repeated)
        self.last_intent = ""
        return ("nomatch", "", 0, False)
