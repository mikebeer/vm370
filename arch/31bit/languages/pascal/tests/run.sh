#!/bin/sh
# Compile and run every tests/*.pas program and compare with tests/NAME.out.
# A tests/NAME.in file, if present, is fed to the program as standard input.
#   tests/run.sh            run all tests
#   tests/run.sh --update   rewrite the .out files from the current output
HERE=$(cd "$(dirname "$0")" && pwd)
PASC="$HERE/../pasc"
pass=0; fail=0
for src in "$HERE"/*.pas; do
  name=$(basename "$src" .pas)
  if [ -f "$HERE/$name.in" ]; then in="$HERE/$name.in"; else in=/dev/null; fi
  out=$("$PASC" "$src" < "$in" 2>&1)
  if [ "$1" = "--update" ]; then
    printf '%s\n' "$out" > "$HERE/$name.out"
    echo "updated $name"
    continue
  fi
  if [ "$out" = "$(cat "$HERE/$name.out")" ]; then
    pass=$((pass+1)); echo "ok    $name"
  else
    fail=$((fail+1)); echo "FAIL  $name"
    printf '%s\n' "$out" | diff - "$HERE/$name.out" | head -10
  fi
  rm -f "$HERE/$name.rxas" "$HERE/$name.rxbin"
done
[ "$1" = "--update" ] && exit 0
echo "$pass passed, $fail failed"
[ $fail = 0 ]
