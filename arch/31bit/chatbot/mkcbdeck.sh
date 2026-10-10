#!/bin/bash
# mkcbdeck.sh OUT.txt -- VM/370plus: the reader deck for the CHATBOT service
# machine (the owner's MCchat persona bot, upstream-b1/).  The bot is compiled
# and linked here with the M8.1 cREXX (the one RXBVM8 runs) and travels as
# hex text (CHATBOT HEX, CBSETUP EXEC unhexes it); the EXECs, CHATBOT CONFIG
# and the persona data come from upstream-b1/deck/CHATBOT.DECK, with BOTCMD
# set to RXBVM8.
set -e
HERE=$(cd "$(dirname "$0")" && pwd); OUT=$(readlink -f "$1")
B=${CREXX_BIN:-/home/claude/crexx-host/bin}
W=$(mktemp -d); cp "$HERE/upstream-b1/src/chatbot.crexx" "$W/"
(cd "$W" && "$B"/rxc -i "$B" chatbot >/dev/null 2>chatbot.err && "$B"/rxas chatbot \
   && "$B"/rxlink -o chatbotx chatbot "$B"/library.rxbin)
python3 "$HERE/cbpatch.py" "$HERE/upstream-b1/deck/CHATBOT.DECK" "$W/CHATBOT.DECK"
python3 - "$W/chatbotx.rxbin" "$W/CHATBOT.DECK" "$OUT" <<'PY'
import sys
rx, deck, out = sys.argv[1:]
L = ['ID CHATBOT NAME CHATBOT']
h = open(rx, 'rb').read().hex().upper()
L.append(':READ  CHATBOT  HEX      A1')
L += [h[i:i + 78] for i in range(0, len(h), 78)]
for l in open(deck, encoding='latin-1').read().rstrip('\n').split('\n'):
    l = l.rstrip('\r')
    if l.startswith('BOTCMD '):
        l = 'BOTCMD RXBVM8 CHATBOT -a CMS'
    L.append(l)
L.append(':READ  CBSETUP  EXEC     A1')
L += ["/* CBSETUP EXEC -- unhex the bot (VM/370plus) */",
      "'UNHEX CHATBOT HEX A CHATBOT RXBIN A'",
      "IF RC = 0 THEN 'ERASE CHATBOT HEX A'", "EXIT RC"]
assert all(len(l) <= 80 for l in L)
open(out, 'w').write('\n'.join(L) + '\n')
print(len(L), 'cards')
PY
rm -rf "$W"
