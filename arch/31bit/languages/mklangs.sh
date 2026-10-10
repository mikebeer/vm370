#!/bin/sh
# mklangs.sh -- VM/370+: build the cREXX languages (BASIC, LOGO, Prolog,
# SNOBOL, Pascal, Lisp, Smalltalk, PL/M) as
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
rm -rf "$W"; mkdir -p "$W/common"
# each language compiles in a directory of its own: rxc reads the sibling
# sources of the current directory, and the languages share procedure names
cp "$HERE"/common/rxfloat.crexx "$HERE"/prolog/rxfs.crexx "$HERE"/prolog/crexxcallback.crexx "$W/common/"
(cd "$W/common" && for m in rxfloat rxfs crexxcallback; do
   "$B"/rxc -i "$B" $m >/dev/null 2>$m.err || { cat $m.err; exit 1; }
   "$B"/rxas $m; done) || exit 1
# build NAME FLAGS SOURCES... : compile each source in $W/NAME, link each
# main module with its imports and the library as $W/<main>x.rxbin
build() {
  name=$1; flags=$2; shift 2
  mkdir -p "$W/$name"
  for f in "$@"; do cp "$f" "$W/$name/"; done
  (cd "$W/$name" && for f in "$@"; do m=$(basename "$f" .crexx)
     "$B"/rxc $flags -i "$B;$W/common" $m >/dev/null 2>$m.err || { cat $m.err; exit 1; }
     "$B"/rxas $m; done) || exit 1
}
build basic "" "$HERE"/basic/basic.crexx
build logo "" "$HERE"/logo/logo.crexx
build prolog "" "$HERE"/prolog/prolog.crexx
build snobol "" "$HERE"/snobol/snobol.crexx
build smalltalk "" "$HERE"/smalltalk/smalltalk.crexx
build pascal -n "$HERE"/pascal/pascal.crexx "$HERE"/pascal/pasrt.crexx    # as their Makefiles: -n
build lisp -n "$HERE"/lisp/lisp.crexx
build plm -n "$HERE"/plm/plm.crexx "$HERE"/plm/plmrt.crexx
cd "$W"
C=$W/common
"$B"/rxlink -o basicx basic/basic $C/rxfloat "$B"/library.rxbin
"$B"/rxlink -o logox logo/logo "$B"/library.rxbin
"$B"/rxlink -o prologx prolog/prolog $C/crexxcallback $C/rxfloat $C/rxfs "$B"/library.rxbin
"$B"/rxlink -o snobolx snobol/snobol $C/rxfloat "$B"/library.rxbin
"$B"/rxlink -o smalltalkx smalltalk/smalltalk $C/rxfloat "$B"/library.rxbin
"$B"/rxlink -o pascalx pascal/pascal "$B"/library.rxbin
"$B"/rxlink -o pasrtx pascal/pasrt "$B"/library.rxbin
"$B"/rxlink -o lispx lisp/lisp "$B"/library.rxbin
"$B"/rxlink -o plmx plm/plm "$B"/library.rxbin
"$B"/rxlink -o plmrtx plm/plmrt "$B"/library.rxbin

# tests (compared as the upstream run_tests.sh do: trailing newlines ignored)
same() { [ "$(cat "$1")" = "$(cat "$2")" ]; }
fail=0
for src in "$HERE"/basic/tests/*.bas; do
  t=$(basename "$src" .bas); fl=""; in=/dev/null
  [ -f "$HERE/basic/tests/$t.flags" ] && fl=$(cat "$HERE/basic/tests/$t.flags")
  [ -f "$HERE/basic/tests/$t.in" ] && in="$HERE/basic/tests/$t.in"
  (cd "$HERE/basic/tests" && "$B"/rxvm "$W"/basicx -a $fl "$src" < "$in" > "$W/$t.out" 2>&1) || true
  same "$W/$t.out" "$HERE/basic/tests/$t.out" || { echo "BASIC FAIL $t"; fail=1; }
done
for src in "$HERE"/snobol/tests/*.sno; do
  t=$(basename "$src" .sno); fl=""; in=/dev/null
  [ -f "$HERE/snobol/tests/$t.flags" ] && fl=$(cat "$HERE/snobol/tests/$t.flags")
  [ -f "$HERE/snobol/tests/$t.in" ] && in="$HERE/snobol/tests/$t.in"
  "$B"/rxvm snobolx -a $fl "$src" < "$in" > "$W/sno_$t.out" 2>&1 || true
  same "$W/sno_$t.out" "$HERE/snobol/tests/$t.out" || { echo "SNOBOL FAIL $t"; fail=1; }
done
for src in "$HERE"/lisp/tests/*.lisp "$HERE"/lisp/tests/*.repl; do
  case "$src" in *.lisp) t=$(basename "$src" .lisp) ;; *) t=$(basename "$src" .repl) ;; esac
  in=/dev/null; [ -f "$HERE/lisp/tests/$t.in" ] && in="$HERE/lisp/tests/$t.in"
  case "$src" in
    *.lisp) (cd "$HERE/lisp/tests" && "$B"/rxvm "$W"/lispx -a "$src" < "$in") > "$W/lsp_$t.out" 2>&1 || true ;;
    *) (cd "$HERE/lisp/tests" && "$B"/rxvm "$W"/lispx < "$src") > "$W/lsp_$t.out" 2>&1 || true ;;
  esac
  same "$W/lsp_$t.out" "$HERE/lisp/tests/$t.out" || { echo "LISP FAIL $t"; fail=1; }
done
for src in "$HERE"/smalltalk/tests/*.st; do
  t=$(basename "$src" .st); in=/dev/null
  [ -f "$HERE/smalltalk/tests/$t.in" ] && in="$HERE/smalltalk/tests/$t.in"
  (cd "$HERE/smalltalk/tests" && "$B"/rxvm "$W"/smalltalkx -a -L "$HERE"/smalltalk/lib "$src" < "$in") > "$W/st_$t.out" 2>&1 || true
  same "$W/st_$t.out" "$HERE/smalltalk/tests/$t.out" || { echo "SMALLTALK FAIL $t"; fail=1; }
done
mkdir -p plmw
for src in "$HERE"/plm/tests/*.plm; do
  t=$(basename "$src" .plm); in=/dev/null
  [ -f "$HERE/plm/tests/$t.in" ] && in="$HERE/plm/tests/$t.in"
  cp "$src" plmw/
  (cd plmw && { "$B"/rxvm "$W"/plmx -a $t.plm prog.rxas && "$B"/rxas prog && \
    "$B"/rxvm prog "$W"/plmrtx -a < "$in"; }) > "$W/plm_$t.out" 2>&1 || true
  same "$W/plm_$t.out" "$HERE/plm/tests/$t.out" || { echo "PLM FAIL $t"; fail=1; }
done
mkdir -p pas
for src in "$HERE"/pascal/tests/*.pas; do
  t=$(basename "$src" .pas); in=/dev/null
  [ -f "$HERE/pascal/tests/$t.in" ] && in="$HERE/pascal/tests/$t.in"
  cp "$src" pas/
  { "$B"/rxvm pascalx -a pas/$t.pas pas/$t.rxas && "$B"/rxas pas/$t && \
    "$B"/rxvm pas/$t pasrtx -a < "$in"; } > "$W/pas_$t.out" 2>&1 || true
  same "$W/pas_$t.out" "$HERE/pascal/tests/$t.out" || { echo "PASCAL FAIL $t"; fail=1; }
done
"$B"/rxvm logox -a "$HERE"/logo/examples/tree.logo tree.svg > /dev/null
grep -q "<svg" tree.svg || { echo "LOGO FAIL"; fail=1; }
(cd "$HERE"/prolog && printf "consult('recur.pl')?\n\nhalt.\n" | "$B"/rxvm "$W"/prologx > "$W"/prolog.out 2>&1) || true
grep -qi "yes\|true" prolog.out || { echo "PROLOG FAIL"; cat prolog.out | head; fail=1; }
[ $fail = 0 ] && echo "mklangs: tests passed"

# the Linux bundle
R=$W/root
mkdir -p $R/usr/local/bin $R/usr/local/share/basic $R/usr/local/share/logo $R/usr/local/share/prolog \
  $R/usr/local/share/snobol $R/usr/local/share/pascal $R/usr/local/share/lisp \
  $R/usr/local/share/smalltalk $R/usr/local/share/plm
L=$HERE/../linux390/crexx/out
cp $L/rxc $L/rxas $L/rxvm "$B"/library.rxbin "$B"/rxcexits.rxbin $R/usr/local/bin/
cp -r "$B"/messages $R/usr/local/bin/
cp basicx.rxbin $R/usr/local/share/basic/basic.rxbin
cp -r "$HERE"/basic/examples $R/usr/local/share/basic/
cp logox.rxbin $R/usr/local/share/logo/logo.rxbin
cp "$HERE"/logo/examples/*.logo $R/usr/local/share/logo/
cp prologx.rxbin $R/usr/local/share/prolog/prolog.rxbin
cp "$HERE"/prolog/*.pl $R/usr/local/share/prolog/
cp snobolx.rxbin $R/usr/local/share/snobol/snobol.rxbin
cp -r "$HERE"/snobol/examples $R/usr/local/share/snobol/
cp pascalx.rxbin $R/usr/local/share/pascal/pascal.rxbin
cp pasrtx.rxbin $R/usr/local/share/pascal/pasrt.rxbin
cp "$HERE"/pascal/tests/*.pas $R/usr/local/share/pascal/
cp lispx.rxbin $R/usr/local/share/lisp/lisp.rxbin
cp -r "$HERE"/lisp/examples $R/usr/local/share/lisp/
cp smalltalkx.rxbin $R/usr/local/share/smalltalk/smalltalk.rxbin
cp -r "$HERE"/smalltalk/lib "$HERE"/smalltalk/examples $R/usr/local/share/smalltalk/
cp plmx.rxbin $R/usr/local/share/plm/plm.rxbin
cp plmrtx.rxbin $R/usr/local/share/plm/plmrt.rxbin
cp -r "$HERE"/plm/examples $R/usr/local/share/plm/
cp "$HERE"/basic/linux/basic "$HERE"/logo/linux/logo "$HERE"/prolog/linux/prolog \
   "$HERE"/snobol/linux/snobol "$HERE"/pascal/linux/pasc "$HERE"/lisp/linux/lisp "$HERE"/smalltalk/linux/smalltalk "$HERE"/plm/linux/plmc $R/usr/local/bin/
(cd $R && tar czf "$OUT"/lxcrexx.tgz --format=ustar --owner=0 --group=0 usr)
cp basicx.rxbin "$OUT"/basic.rxbin; cp logox.rxbin "$OUT"/logo.rxbin; cp prologx.rxbin "$OUT"/prolog.rxbin
cp snobolx.rxbin "$OUT"/snobol.rxbin; cp pascalx.rxbin "$OUT"/pascal.rxbin; cp pasrtx.rxbin "$OUT"/pasrt.rxbin; cp lispx.rxbin "$OUT"/lisp.rxbin
cp smalltalkx.rxbin "$OUT"/smalltalk.rxbin; cp plmx.rxbin "$OUT"/plm.rxbin; cp plmrtx.rxbin "$OUT"/plmrt.rxbin
ls -la "$OUT"
exit $fail
