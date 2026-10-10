#!/bin/sh
# Self test on the PC: converts the demo data, builds the bot, runs a few spool
# round trips and a cross-check against the Python reference.
# usage: selftest.sh <crexx build dir (has bin/rxc rxas rxvm)> <MCchat npc_chat data dir>
set -e
CX=${1:?crexx build dir}; SRC=${2:?npc_chat data dir}
HERE=$(cd "$(dirname "$0")/.." && pwd); W=${TMPDIR:-/tmp}/chatbot-selftest; rm -rf "$W"; mkdir -p "$W"
python3 -I "$HERE/tools/mkdata.py" "$SRC" "$W/data" --build 1 >/dev/null
sh "$HERE/tests/build.sh" "$CX/bin" "$W/bot"
python3 -I "$HERE/tests/crosscheck.py" "$SRC" "$W/data" "$W/bot/chatbot.rxbin" "$CX/bin/rxvm" "$CX/bin/library.rxbin" 150
python3 -I "$HERE/tests/kbcheck.py" "$SRC" "$W/data" "$W/bot/chatbot.rxbin" "$CX/bin/rxvm" "$CX/bin/library.rxbin" || true
echo "selftest done"
