#!/bin/sh
# mklangs.sh -- VM/370+: build the cREXX languages (BASIC, LOGO, Prolog) as
# linked RXBINs with the PC cREXX, run their tests, and pack the Linux
# bundle (the s390 31-bit cREXX tools from ../linux390/crexx plus the
# languages) as OUT/lxcrexx.tgz.
#   mklangs.sh OUTDIR
# The RXBINs are UTF-8 (the cross-built M8.1 RXBVM8 on CMS, and Linux).
set -e
HERE=$(cd "$(dirname "$0")" && pwd)
B=${CREXX_BIN:-/home/claude/crexx-host/bin}
OUT=$(mkdir -p "$1" && cd "$1" && pwd)
W=$OUT/work
rm -rf "$W"; mkdir -p "$W"
cp "$HERE"/common/rxfloat.crexx "$HERE"/basic/basic.crexx "$HERE"/logo/logo.crexx \
   "$HERE"/prolog/prolog.crexx "$HERE"/prolog/crexxcallback.crexx "$HERE"/prolog/rxfs.crexx "$W"/
cd "$W"
for m in rxfloat rxfs crexxcallback basic logo prolog; do
  "$B"/rxc -i "$B;." $m >/dev/null 2>$m.err || { cat $m.err; exit 1; }
  "$B"/rxas $m
done
"$B"/rxlink -o basicx basic rxfloat "$B"/library.rxbin
"$B"/rxlink -o logox logo "$B"/library.rxbin
"$B"/rxlink -o prologx prolog crexxcallback rxfloat rxfs "$B"/library.rxbin

# tests
fail=0
for src in "$HERE"/basic/tests/*.bas; do
  t=$(basename "$src" .bas); fl=""; in=/dev/null
  [ -f "$HERE/basic/tests/$t.flags" ] && fl=$(cat "$HERE/basic/tests/$t.flags")
  [ -f "$HERE/basic/tests/$t.in" ] && in="$HERE/basic/tests/$t.in"
  (cd "$HERE/basic/tests" && "$B"/rxvm "$W"/basicx -a $fl "$src" < "$in" > "$W/$t.out" 2>&1) || true
  cmp -s "$W/$t.out" "$HERE/basic/tests/$t.out" || { echo "BASIC FAIL $t"; fail=1; }
done
"$B"/rxvm logox -a "$HERE"/logo/examples/tree.logo tree.svg > /dev/null
grep -q "<svg" tree.svg || { echo "LOGO FAIL"; fail=1; }
(cd "$HERE"/prolog && printf "consult('recur.pl')?\n\nhalt.\n" | "$B"/rxvm "$W"/prologx > "$W"/prolog.out 2>&1) || true
grep -qi "yes\|true" prolog.out || { echo "PROLOG FAIL"; cat prolog.out | head; fail=1; }
[ $fail = 0 ] && echo "mklangs: tests passed"

# the Linux bundle
R=$W/root
mkdir -p $R/usr/local/bin $R/usr/local/share/basic $R/usr/local/share/logo $R/usr/local/share/prolog
L=$HERE/../linux390/crexx/out
cp $L/rxc $L/rxas $L/rxvm "$B"/library.rxbin "$B"/rxcexits.rxbin $R/usr/local/bin/
cp -r "$B"/messages $R/usr/local/bin/
cp basicx.rxbin $R/usr/local/share/basic/basic.rxbin
cp -r "$HERE"/basic/examples $R/usr/local/share/basic/
cp logox.rxbin $R/usr/local/share/logo/logo.rxbin
cp "$HERE"/logo/examples/*.logo $R/usr/local/share/logo/
cp prologx.rxbin $R/usr/local/share/prolog/prolog.rxbin
cp "$HERE"/prolog/*.pl $R/usr/local/share/prolog/
cp "$HERE"/basic/linux/basic "$HERE"/logo/linux/logo "$HERE"/prolog/linux/prolog $R/usr/local/bin/
(cd $R && tar czf "$OUT"/lxcrexx.tgz --owner=0 --group=0 usr)
cp basicx.rxbin "$OUT"/basic.rxbin; cp logox.rxbin "$OUT"/logo.rxbin; cp prologx.rxbin "$OUT"/prolog.rxbin
ls -la "$OUT"
exit $fail
