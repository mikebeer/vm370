#!/usr/bin/env python3
"""Convert the MCchat persona data (.bot / .nlu.json / knowledge_base.json) into the
compact RECFM F 80 record files the cREXX CHATBOT reads on CMS.

usage: mkdata.py <npc_chat data dir> <output dir> [--build N] [--only tchaika,galene] [--langs en,de]

Output (CMS file ids, written as  <fn>.<ft>  on the PC, fn/ft upper-cased):
    <NPC>   NLU<LG>   persona understanding (synonyms, crisis, intents)
    <NPC>   BOT<LG>   persona opening script
    CHATKB  DATA      knowledge base
    CHATDATA LIST     list of what was converted
"""
import json, os, sys, glob, argparse
sys.path.insert(0, os.path.dirname(__file__))
from cbcommon import clean, records, split_steps, REC


def semi(items):
    return ';'.join(items)


def nlu_records(npc, lg, d, build):
    r = []
    r.append('H ' + 'CHATBOT NLU %s %s build %s' % (npc, lg, build))
    for name, words in d.get('synonyms', {}).items():
        r += records('Y', clean(name + ';' + semi(words)))
    cr = d.get('crisis', {})
    for p in cr.get('phrases', []):
        r += records('P', clean(p))
    for w in cr.get('words', []):
        r += records('W', clean(w))
    for key, tag in (('fallback', 'F'), ('crisis_reply', 'X'), ('repeat_prefixes', 'R'),
                     ('library_intro', 'L'), ('continue_words', 'C')):
        for s in d.get(key, []):
            r += records(tag, clean(s))
    for name, it in d.get('intents', {}).items():
        ent = it.get('entity', '')
        go = it.get('go', '')
        r += records('I', clean('%s;%s;%s' % (name, ent, go)))
        anys = it.get('any', [])
        if anys:
            r += records('A', clean(semi(anys)))
        pr = it.get('pronouns', [])
        if pr:
            r += records('N', clean(semi(pr)))
        for s in it.get('say', []):
            r += records('S', clean(s))
        tpl = it.get('say_template', {})
        for si, (slot, opts) in enumerate(tpl.items(), 1):
            for o in opts:
                r += records('T', clean('%d;%s' % (si, o)))
    return r


def bot_records(text):
    r = []
    for line in text.replace('\r\n', '\n').split('\n'):
        s = line.strip()
        if not s or s.startswith('*'):
            continue
        r += records('B', clean(s))
    return r


def kb_records(kb):
    r = []
    for e in kb:
        r += records('E', clean('%s;%s;%s;%s' % (e.get('id', ''), e.get('scope', ''),
                                                  e.get('kind', ''), e.get('language', ''))))
        r += records('M', clean(e.get('title', '')))
        if e.get('subtopic'):
            r += records('U', clean(e['subtopic']))
        if e.get('source'):
            r += records('Q', clean(e['source']))
        if e.get('audio'):
            r += records('D', clean(e['audio']))
        if e.get('kind') == 'prompt':
            steps = split_steps(e.get('text', ''))
        else:
            steps = [e.get('text', '').strip()] if e.get('text', '').strip() else []
        for st in steps:
            r += records('X', clean(' '.join(st.split())))
    return r


def write(outdir, fn, ft, recs):
    for x in recs:
        assert len(x) <= REC, x
    path = os.path.join(outdir, '%s.%s' % (fn.upper(), ft.upper()))
    with open(path, 'w', newline='\n', encoding='ascii') as f:
        for x in recs:
            f.write(x.ljust(REC) + '\n')
    return path


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('src')
    ap.add_argument('out')
    ap.add_argument('--build', default='1')
    ap.add_argument('--only', default='')
    ap.add_argument('--langs', default='en,de')
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)
    only = [x for x in a.only.split(',') if x]
    langs = a.langs.split(',')
    listing = []
    for path in sorted(glob.glob(os.path.join(a.src, '*.nlu.json'))):
        base = os.path.basename(path)[:-len('.nlu.json')]
        npc, lg = base.rsplit('_', 1)
        if lg not in langs or (only and npc not in only):
            continue
        assert len(npc) <= 8, npc
        d = json.load(open(path, encoding='utf-8'))
        write(a.out, npc, 'NLU' + lg.upper(), nlu_records(npc, lg, d, a.build))
        bpath = os.path.join(a.src, base + '.bot')
        txt = open(bpath, encoding='utf-8').read() if os.path.exists(bpath) else ''
        write(a.out, npc, 'BOT' + lg.upper(), bot_records(txt) or ['B !...'])
        listing.append('%-8s %s' % (npc.upper(), lg.upper()))
    kbp = os.path.join(a.src, 'knowledge_base.json')
    if os.path.exists(kbp):
        kb = json.load(open(kbp, encoding='utf-8'))
        write(a.out, 'CHATKB', 'DATA', kb_records(kb))
    write(a.out, 'CHATDATA', 'LIST', ['%-80s' % ('* CHATBOT demo data, build %s' % a.build)] + listing)
    print('converted %d persona files' % len(listing))


if __name__ == '__main__':
    main()
