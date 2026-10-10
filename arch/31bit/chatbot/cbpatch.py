#!/usr/bin/env python3
"""cbpatch.py IN.DECK OUT.DECK -- VM/370plus changes to the upstream CHATBOT
deck (BREXX on VM/370 CMS).  Each change is asserted, so an upstream change
is noticed.  The list is reported back upstream (VM370PLUS.TXT)."""
import sys

P = [
    # BREXX has no UPPER() built-in
    ("    if upper(word(c, 1)) = 'FROM' & k = 0 then do",
     "    if translate(word(c, 1)) = 'FROM' & k = 0 then do"),
    # no WAKEUP on VM/370: CP SLEEP instead of a busy wait (and WAKEUP is
    # tried once only, not on every round)
    ("  'WAKEUP +' || right(interval, 6, '0') || ' (RDR QUIET'\n"
     "  if rc = 1 | rc = 28 | rc < 0 then do   /* no WAKEUP command here       */\n"
     "    if \\nowake then say 'CHATBOT: WAKEUP not available, polling (busy)'\n"
     "    nowake = 1\n"
     "    t1 = time('S')\n"
     "    do while elapsed(t1) < interval\n"
     "      nop\n"
     "    end\n"
     "  end",
     "  if \\nowake then 'WAKEUP +' || right(interval, 6, '0') || ' (RDR QUIET'\n"
     "  if nowake | rc = 1 | rc = 28 | rc < 0 then do  /* VM/370: CP SLEEP */\n"
     "    if \\nowake & loud then say 'CHATBOT: no WAKEUP, CP SLEEP' interval\n"
     "    nowake = 1\n"
     "    'CP SLEEP' interval 'SEC'\n"
     "  end"),
    ("    'WAKEUP +000002 (RDR QUIET'\n"
     "    if rc = 1 | rc = 28 | rc < 0 then do   /* no WAKEUP: short busy wait */\n"
     "      t1 = time('S')\n"
     "      do while elapsed(t1) < 2\n"
     "        nop\n"
     "      end\n"
     "    end",
     "    'CP SLEEP 2 SEC'                  /* VM/370plus: no WAKEUP */"),
    # VM/370 CP has no TERMINAL CONMODE
    ("'CP TERM CONMODE 3270'", "/* (no CP TERM CONMODE on VM/370) */"),
    # BREXX's EXECIO writes each line at its own length: a fixed record
    # format (F 80, F 8) fails with FSWRITE rc 15 on any shorter line
    ("'EXECIO' queued() 'DISKW CHAT REQ A 1 F 80 (FINIS'",
     "'EXECIO' queued() 'DISKW CHAT REQ A (FINIS'"),
    ("'EXECIO' nq 'DISKW CHATBOT CBQUEUE A 1 F 8 (FINIS'",
     "'EXECIO' nq 'DISKW CHATBOT CBQUEUE A (FINIS'"),
    # the caller's RC is not set by an internal routine; BREXX's EXIT
    # wants a number: ASK's RETURN value is in RESULT
    ("  call ask line\n  exit rc", "  call ask line\n  exit result"),
]

src, out = sys.argv[1:]
d = '\n'.join(l.rstrip('\r').rstrip() for l in open(src, encoding='latin-1').read().split('\n'))
for a, b in P:
    assert a in d, 'upstream changed: ' + a.split('\n')[0]
    d = d.replace(a, b)
open(out, 'w', encoding='latin-1').write(d)
