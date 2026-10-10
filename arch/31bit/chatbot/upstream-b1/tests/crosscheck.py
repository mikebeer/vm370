#!/usr/bin/env python3
"""Cross-check the cREXX engine against refbot.py (a literal translation of bot.gd).

For each persona/language a long, seeded message sequence is generated from the
persona's own data (synonyms, typos, pronoun follow-ups, crisis words, repeats,
random word salads) and sent to the compiled cREXX bot in ONE batch for one
sender.  Every reply ends with a  [dbg kind= intent= score= rep=]  line; kind,
intent, score and repeat flag must equal the reference for every message.

usage: crosscheck.py <nlu json dir> <converted data dir> <chatbot.rxbin> <rxvm> <library.rxbin> [n_per_persona] [personas]
"""
import sys, os, json, random, re, glob
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from refbot import Ref, normalise
from spoolsim import Sim

def typo(w, rnd):
    if len(w) < 4:
        return w
    k = rnd.choice(['swap', 'drop', 'dup', 'sub'])
    i = rnd.randrange(1, len(w) - 1)
    if k == 'swap':
        return w[:i] + w[i + 1] + w[i] + w[i + 2:]
    if k == 'drop':
        return w[:i] + w[i + 1:]
    if k == 'dup':
        return w[:i] + w[i] + w[i:]
    return w[:i] + rnd.choice('aeiounrst') + w[i + 1:]

def gen(nlu, rnd, n):
    syn = nlu['synonyms']
    words = [w for ws in syn.values() for w in ws if re.fullmatch(r"[a-z0-9' ]+", w)]
    msgs = []
    intents = {k: v for k, v in nlu['intents'].items() if not k.startswith('_')}
    names = list(intents)
    filler = ['please', 'tell me', 'and', 'what about', 'so', 'hmm', 'the', 'my', 'i think']
    while len(msgs) < n:
        c = rnd.random()
        if c < 0.30:                          # an intent's own synonym(s), maybe with filler
            it = intents[rnd.choice(names)]
            parts = []
            for g in it.get('any', []):
                ws = syn.get(g, [g])
                if ws:
                    parts.append(rnd.choice(ws))
            m = ' '.join(parts)
            if rnd.random() < .4: m = rnd.choice(filler) + ' ' + m
            msgs.append(m)
        elif c < 0.50:                        # typos
            it = intents[rnd.choice(names)]
            ws = []
            for g in it.get('any', []):
                ws += syn.get(g, [g])
            if ws:
                msgs.append(' '.join(typo(rnd.choice(ws).split(' ')[0], rnd) for _ in range(rnd.randint(1, 2))))
        elif c < 0.62:                        # pronoun follow-up after an entity
            ents = [k for k, v in intents.items() if v.get('pronouns')]
            if ents:
                e = intents[rnd.choice(ents)]
                msgs.append(rnd.choice(rnd.choice(syn.get(e['any'][0], e['any']) if False else [e['any'][0]] ) and [e['any'][0]]) if False else rnd.choice(syn.get(e.get('any', [''])[0], words)))
                msgs.append(rnd.choice(e['pronouns']) + ' ' + rnd.choice(['where', 'who', 'is', 'happened to', 'what about']))
        elif c < 0.70:                        # word salad
            msgs.append(' '.join(rnd.choice(words) for _ in range(rnd.randint(1, 5))))
        elif c < 0.75:                        # crisis
            cr = nlu.get('crisis', {})
            pool = cr.get('phrases', []) + cr.get('words', [])
            if pool:
                p = rnd.choice(pool)
                msgs.append(p if rnd.random() < .6 else typo(p.replace(' ', ''), rnd))
        elif c < 0.82:                        # continuation / repeat
            cw = nlu.get('continue_words', ['more'])
            msgs.append(rnd.choice(cw) if rnd.random() < .5 else 'tell me ' + rnd.choice(cw))
        elif c < 0.88 and msgs:               # exact repeat
            msgs.append(msgs[-1])
        elif c < 0.94:                        # punctuation / case / hyphen noise
            m = rnd.choice(words)
            msgs.append(rnd.choice([m.upper() + '?!', "I'm " + m + '...', m.replace(' ', '-'), '  ' + m + ' , ' + rnd.choice(words)]))
        else:                                 # no-match chatter
            msgs.append(' '.join(rnd.choice(['zxq', 'blorp', 'frumble', 'kwyjibo', 'plugh']) for _ in range(rnd.randint(1, 3))))
    return [m.strip() for m in msgs if m.strip()][:n]

def main():
    src, data, rxbin, rxvm, lib = sys.argv[1:6]
    n = int(sys.argv[6]) if len(sys.argv) > 6 else 300
    only = sys.argv[7].split(',') if len(sys.argv) > 7 else None
    rnd = random.Random(20261010)
    total = bad = 0
    for path in sorted(glob.glob(os.path.join(src, '*.nlu.json'))):
        base = os.path.basename(path)[:-9]
        npc, lg = base.rsplit('_', 1)
        if only and npc not in only:
            continue
        nlu = json.load(open(path, encoding='utf-8'))
        msgs = gen(nlu, rnd, n)
        work = os.environ.get('XC_WORK', '/tmp/xc') + '/' + base
        sim = Sim(work, data, rxbin, rxvm, lib, config=['SEED 3', 'CRISIS YES', 'WIDTH 72', 'DEFNPC ' + npc, 'DEFLANG ' + lg])
        sim.run([('XCHECK', '/DEBUG ON')])
        replies = sim.run([('XCHECK', m) for m in msgs])
        ref = Ref(path)
        for mi, (m, rep) in enumerate(zip(msgs, replies)):
            kind, name, score, repeated = ref.understand(m)
            exp = 'kind=%s intent=%s score=%d rep=%d' % (kind, name, score, 1 if repeated else 0)
            got = re.findall(r'\[dbg ([^\]]*)\]', rep or '')
            got = re.sub(r' kb=\d+', '', got[-1]) if got else '(none)'
            total += 1
            if got != exp:
                bad += 1
                if bad <= 25:
                    print('MISMATCH %s: %r\n   expected %s\n   got      %s' % (base, m, exp, got))
                    print('   history: %r' % (msgs[max(0, mi - 6):mi],))
        print('%-12s %4d messages' % (base, len(msgs)), flush=True)
    print('TOTAL %d  mismatches %d' % (total, bad))
    sys.exit(1 if bad else 0)

main()
