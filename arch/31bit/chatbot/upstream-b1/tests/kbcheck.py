#!/usr/bin/env python3
"""Check the cREXX knowledge-base fallback against a literal Python translation of
KnowledgeBase.gd search() + the fallback in bot.gd understand(), on the (folded) data.
Queries are built from the KB's own words; only messages the intent matcher leaves
unclaimed are compared.  usage: kbcheck.py <nlu dir> <data dir> <rxbin> <rxvm> <lib> [n]"""
import sys, os, json, re, random
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'tools'))
from refbot import Ref, normalise, tokens
from cbcommon import fold, split_steps
from spoolsim import Sim

STOP = {"en": "want wants wanted would could should does doing have having this that with about your you the and for how what can get from into onto between there here just only were was been when then than".split(),
        "de": "will willst moechte moechtest wollen kann kannst habe hast haben diese dieser dieses ueber dein deine und der die das fuer wie was dann dort hier nur waren wurde wenn".split()}

def ref_search(kb, query, scope, lang):
    q = normalise(query)
    if q == "":
        return None
    stop = STOP.get(lang, STOP["en"])
    qw = [w for w in q.split(" ") if len(w) > 2 and w not in stop] or [q]
    cands = [(i, e) for i, e in enumerate(kb) if e['scope'] in (scope, 'general')]
    same = [c for c in cands if c[1]['language'] == lang]
    pool = same if same else cands
    best = None
    for i, e in pool:
        hay = ' ' + normalise(e['title'] + ' ' + e.get('subtopic', '') + ' ' + e['text']) + ' '
        sc = sum(len(w) for w in qw if (' ' + w + ' ') in hay)
        if sc >= 3 and (best is None or sc > best[0]):
            best = (sc, i)
    return None if best is None else best[1] + 1       # 1-based ordinal like the cREXX side

def main():
    src, data, rxbin, rxvm, lib = sys.argv[1:6]
    n = int(sys.argv[6]) if len(sys.argv) > 6 else 200
    kb = json.load(open(os.path.join(src, 'knowledge_base.json'), encoding='utf-8'))
    for e in kb:
        e.setdefault('text', ''); e.setdefault('subtopic', ''); e.setdefault('title', '')
        for k in ('title', 'subtopic', 'text', 'scope', 'kind', 'language'):
            if k in e:
                e[k] = fold(e[k])
    rnd = random.Random(99)
    bad = total = compared = 0
    for npc, lg in (('tchaika', 'de'), ('tchaika', 'en'), ('opux', 'en'), ('elena', 'de')):
        ref = Ref(os.path.join(src, '%s_%s.nlu.json' % (npc, lg)))
        pool = [e for e in kb if e['scope'] in (npc, 'general')]
        msgs = []
        while len(msgs) < n:
            e = rnd.choice(pool)
            ws = [w for w in normalise(e['title'] + ' ' + e['text']).split(' ') if len(w) > 3]
            if len(ws) < 3: continue
            k = rnd.randint(1, 3)
            msgs.append(' '.join(rnd.sample(ws, k)))
        sim = Sim('/tmp/kbc/%s_%s' % (npc, lg), data, rxbin, rxvm, lib, config=['SEED 3', 'DEFNPC ' + npc, 'DEFLANG ' + lg])
        sim.run([('KB', '/DEBUG ON')])
        replies = sim.run([('KB', m) for m in msgs])
        for m, rep in zip(msgs, replies):
            total += 1
            kind, name, score, rpt = ref.understand(m)
            if kind != 'nomatch':
                continue
            exp = ref_search(kb, m, npc, lg)
            if exp is None:
                for t in tokens(m):
                    exp = ref_search(kb, t, npc, lg)
                    if exp: break
            got = re.findall(r'kb=(\d+)', rep or '')
            got = int(got[-1]) if got else -1
            compared += 1
            if (exp or 0) != got:
                bad += 1
                if bad <= 15:
                    print('MISMATCH %s_%s %r expected kb=%s got kb=%s' % (npc, lg, m, exp, got))
        print('%s_%s done' % (npc, lg), flush=True)
    print('messages %d, compared (unclaimed by intents) %d, mismatches %d' % (total, compared, bad))
    sys.exit(1 if bad else 0)
main()
