#!/bin/bash
# The build cycle, with every check that one of today's failures taught us.
#
#   build.sh full  [snapshot]   restore, stage everything, VMFMAC, assemble all
#   build.sh quick <snapshot> <module>...   restore, reassemble named modules
#   build.sh write              VMFLOAD + CP IPL 00C -- writes the nucleus
#   build.sh test  [herc-spec]...           ESA/390 IPL, pgmtrace on
#
# It lives in the repository rather than the scratchpad because the PROCEDURE is
# the artifact: every ad-hoc copy of this logic grew a different hole, and the
# holes are what cost the time, not the CP code.
#
# The guards, each paid for once:
#   I-101  a COPY or MACRO NOT FOUND is fatal, not a warning
#   I-111  a snapshot is restored only if snapshot.py says valid AND current
#   I-112  boot_failed() -- a swallowed CP DISC makes every command fail as ?CP:
#   I-115  wrong_arch() -- a build is S/370, a test is ESA/390, verified from the log
#   I-117  the wait fails on timeout, and run() refuses a second instance
set -u
C=${CE:-/home/claude/vm370/scratchpad/VM370CE.V1.R1.2}
R=${REPO:-/home/claude/vm370}
T=$R/arch/31bit/tools
U=$R/arch/31bit/updates

py(){ python3 -c "
import sys; sys.path.insert(0,'$T')
$1"; }

w(){ for i in $(seq 1 1800); do test "$(pgrep -c hercules)" = "0" && return 0
       sleep 3; done
     echo "### w(): Hercules still running after 90 minutes -- refusing to go on"
     return 1; }

run(){ test "$(pgrep -c hercules)" = "0" || {
         echo "### run($1): a Hercules is ALREADY running -- refusing to start a second"
         pgrep -a hercules | head -3; return 1; }
       ( cd "$C" && setsid nohup hercules -f vm370ce.conf > "$1.log" 2>&1 </dev/null & )
       sleep 8; w; }

mk(){ python3 $T/mkrun.py "$C" "$@" >/dev/null || { echo "### mkrun failed"; return 1; }; }
arch(){ py "import mkrun; mkrun.archmode('$C/vm370ce.conf','$1')"; }

chk(){ local r; r=$(py "import mkrun; print(mkrun.boot_failed('$C/$1.log') or '')")
       test -z "$r" || { echo "### BOOT FAILED in $1: $r"; return 1; }
       r=$(py "import mkrun; print(mkrun.wrong_arch('$C/$1.log','$2') or '')")
       test -z "$r" || { echo "### $1: $r"; return 1; }
       echo "--- $1: reached CMS, $2 confirmed"; }

asmchk(){ python3 - "$C/$1.log" <<'PY' || return 1
import re, sys
t = open(sys.argv[1], errors='replace').read()
if 'NOT FOUND' in t:
    print('### a COPY or MACRO was NOT FOUND -- I-101'); sys.exit(1)
# asmdmk prints *** ERROR ASMBLING *** for ANY flagged statement, MNOTE 4
# included: CE's own DMKRIO declares 3375 and 3390 devices VM/370 R6 does not
# know and emits four severity-4 MNOTEs. The test is whether the deck exists.
bad = [m for m in re.findall(r'\*\*\* ERROR ASMBLING (\S+) \*\*\*', t)
       if ('%s TEXT CREATED' % m) not in t and ('%s TXTLCL CREATED' % m) not in t]
print('--- flagged but output created: benign' if not bad else '### MISSING: %s' % bad)
sys.exit(1 if bad else 0)
PY
}

restore(){ local snap=$1
  python3 $T/snapshot.py check "$C" "$snap"; local rc=$?
  case $rc in
    0) ;;
    2) echo "### $snap is stale -- restoring it anyway is only correct if you"
       echo "### reassemble the modules named above.  Use 'full', or 'quick' with them."
       test "${ALLOW_STALE:-no}" = yes || return 1 ;;
    *) echo "### refusing to restore $snap"; return 1 ;;
  esac
  rm -rf "$C/disks/shadows"; cp -r "$C/disks/$snap" "$C/disks/shadows"
  rm -f "$C/disks/shadows/MANIFEST.json"
  echo "--- restored $snap"; }

specs_all(){ local s=""
  for f in $U/*.XA*DK; do local b=$(basename $f); s="$s read:${b%%.*}:${b#*.}"; done
  for f in $U/*.AUXLCL; do s="$s read:$(basename $f .AUXLCL):AUXLCL"; done
  # PSA, RBLOKS and IOBLOKS are CP's OWN members, updated by their decks, so
  # there is no file to stage.  Only the four this project invented exist.
  for m in XABLOKS:COPY XAOPS:MACRO XAIO:MACRO XAIOB:MACRO; do
    s="$s read:${m%%:*}:${m#*:}"; done
  echo "$s"; }

case "${1:-}" in
full)
  w || exit 1
  snap=${2:-SNAP-2}
  arch S/370
  ALLOW_STALE=yes restore "$snap" || exit 1
  mk f1 $(specs_all) mac:DMKLCL "post:asmdmk dmklcl:300" || exit 1
  run f1 || exit 1; chk f1 S/370 || exit 1; asmchk f1 || exit 1
  echo "--- clean: $(grep -c 'NO STATEMENTS FLAGGED' $C/f1.log)"
  python3 $T/snapshot.py take "$C" "SNAP-$(date +%H%M)" "$C/f1.log"
  ;;
quick)
  w || exit 1
  snap=$2; shift 2
  arch S/370
  restore "$snap" || exit 1
  sp=""; for m in "$@"; do
    dk=$(cd $U && ls $m.XA*DK 2>/dev/null | head -1)
    test -n "$dk" || { echo "### no deck for $m"; exit 1; }
    sp="$sp $m:${dk#*.}"; done
  mk q1 $sp || exit 1
  run q1 || exit 1; chk q1 S/370 || exit 1; asmchk q1 || exit 1
  ;;
write)
  w || exit 1
  arch S/370
  mk n1 "cmd:cp purge rdr all:10" "cmd:cp spool punch to *:10" \
        "cmd:vmfload cpload dmklcl:180" "cmd:cp close punch:15" \
        "cmd:cp ipl 00c:150" || exit 1
  run n1 || exit 1; chk n1 S/370 || exit 1
  grep -E "Nucleus loaded|LOAD DECK COMPLETE|DISABLED WAIT" "$C/n1.log" | tail -3
  grep -q "00000012" "$C/n1.log" || { echo "### NUCLEUS WRITE FAILED"; exit 1; }
  ;;
test)
  w || exit 1
  shift || true
  arch ESA/390
  mk t1 --bare "herc:pgmtrace +1:3" "herc:pgmtrace +2:3" "herc:pgmtrace +5:3" \
     "herc:pgmtrace +6:3" "herc:ipl 6A1:200" "${@:-herc:stop:6}" \
     "herc:stop:6" "herc:psw:5" "herc:r 8C.10:5" "herc:gpr:6" || exit 1
  run t1 || exit 1
  r=$(py "import mkrun; print(mkrun.wrong_arch('$C/t1.log','ESA/390') or '')")
  test -z "$r" || { echo "### t1: $r"; exit 1; }
  echo "--- t1: ESA/390 confirmed"
  sed -n '/^pgmtrace/,$p' "$C/t1.log" | grep -vE "Pausing|Resuming|^$|HHCCD001I" | head -30
  arch S/370
  ;;
*)
  sed -n '2,20p' "$0"
  exit 2 ;;
esac
