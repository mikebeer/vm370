#!/bin/sh
# Compile and assemble crexx/chatbot.crexx with the PC toolchain (rxc, rxas) into a work dir.
# usage: build.sh <crexx build bin dir> <out dir>
BIN=${1:?cREXX bin dir}; OUT=${2:?out dir}
HERE=$(cd "$(dirname "$0")/.." && pwd)
mkdir -p "$OUT" && cp "$HERE/crexx/chatbot.crexx" "$OUT/chatbot.crexx" && cd "$OUT" || exit 1
"$BIN/rxc" chatbot 2>&1 | grep -v '^Warning' ; "$BIN/rxas" chatbot && ls -l chatbot.rxbin
