#!/usr/bin/env python3
"""M8.2: drive.py runs for the native build.
    mkrun.py full|units U1 U2..|link  > run.json
full: load the source and EXEC decks onto a freshly formatted CMSUSER 194
(accessed as A), compile everything, link.  units: decks already loaded,
recompile the units named (after a reload of the changed EXEC deck only)."""
import json, sys
R = []
def s(send, expect, t=60, cont=True, **k):
    d = {'send': send, 'expect': expect, 'timeout': t, 'cont': cont}; d.update(k); R.append(d)
def t(term, expect, tmo=120, cont=True, **k):
    d = {'term': term, 'expect': expect, 'timeout': tmo, 'cont': cont}; d.update(k); R.append(d)
RDY = 'Ready\\(|Ready;|CP ENTERED'
mode = sys.argv[1]
if mode == 'deck':   # deck FILE CMD... : load FILE onto A (194), type CMDs
    DECK, CMDS = sys.argv[2], sys.argv[3:]
load = mode in ('full', 'smoke')
s('ipl 6A1', 'DMKCPI966I|Start \\(\\(Warm', 180)
s('/', 'Ready|Start \\(\\(Warm|AUTO LOGON|\\?CP', 15)
s('/cold', 'DMKCPI966I|\\?CP', 90, settle=8)
s('/cp disc', 'DISCONNECT AT', 60, cont=False)
s('/logon maint cpcms noipl', 'Ready|LOGON AT|RECONNECT', 180, cont=False)
s('/cp def stor 16m', 'STORAGE =', 30)
s('/ipl 190', 'VM Community|Ready', 120, cont=False)
s('/', 'Ready|Start \\(\\(Warm|AUTO LOGON|\\?CP', 15)
s('/cp purge rdr cmsuser all', 'Ready|PURGED', 60)
s('/cp spool 00c class *', 'Ready', 60)
decks = ['crx82src.txt'] if load else [DECK] if mode == 'deck' else ['crx82mk.txt']
for d in decks:
    s('devinit 000c io/%s ascii eof trunc' % d, 'HHCPN098I|initialized', 30)
    s('/cp start 00c', 'Ready', 1800)
s('/cp q rdr cmsuser all', 'Ready|RDR|NO', 60)
t('', 'Online|ONLINE', 30)
t('logon cmsuser cmsuser noipl', 'LOGON AT', 60)
t('cp def stor 256m', 'STORAGE =', 30)
t('cp link maint 290 290 rr', 'Ready|DMK|CP', 30)
t('ipl 290', 'VM Community|DMS', 120)
t('', 'Ready', 60)
t('access 195 g', RDY)
if load:
    t('format 194 a', 'CONTINUE|DMSFOR', 60)
    t('yes', 'LABEL', 60)
    t('crx82', RDY, 600)
else:
    t('access 194 a', RDY)
t('access 191 b', RDY)
for d in decks:
    t('readcard *', RDY, 3600)
t('query disk', RDY)
t('highstor reset', RDY)
if mode == 'full':
    t('exec crx82mk', 'NOW LINK|BUILD OK|ERRORS \\*\\*\\*\\*\\*|DMSABN|DMSITP|CP ENTERED|DMSFRE', 36000)
    t('exec crx82lk', 'CRX82LK: DONE|DMSABN|DMSITP|CP ENTERED', 1800)
    for c in ('rxbvm82 -v', 'rxas82 -v', 'rxc82 -v'):
        t(c, RDY + '|DMSABN|DMSITP', 120)
elif mode == 'deck':
    for c in CMDS:
        t(c, RDY + '|DMSABN|DMSITP', 7200)
elif mode == 'link':
    t('exec crx82lk', 'CRX82LK: DONE|DMSABN|DMSITP|CP ENTERED', 1800)
    for c in ('rxbvm82 -v', 'rxas82 -v', 'rxc82 -v'):
        t(c, RDY + '|DMSABN|DMSITP', 120)
else:
    t('exec crx82mk ' + ' '.join(sys.argv[2:]), RDY + '|DMSABN|DMSITP|DMSFRE', 7200)
t('highstor query', 'HIGHSTOR')
t('cp logoff', 'LOGOFF AT', 60)
s('/cp shutdown', 'HHCCP011I|SHUTDOWN COMPLETE|SHUTDOWN', 40)
R.append({'send': 'exit'})
json.dump(R, sys.stdout, indent=1)
