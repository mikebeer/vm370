#!/bin/bash
# The build cycle, with every check that one of today's failures taught us.
#
#   build.sh full  [snapshot]   restore, stage everything, VMFMAC, assemble all
#   build.sh quick <snapshot> <module>...   restore, reassemble named modules
#   build.sh write              VMFLOAD + CP IPL 00C -- writes the nucleus
#   build.sh test  [spec]... [-- [spec]...]   ESA/390 IPL; specs before `--` precede the ipl
#   build.sh sizes [mb]...      sweep MAINSIZE, same four measurements each
#   build.sh dual  <snapshot> [spec]...     the SAME test on 3.13 AND 4.9.1
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
# Two engines. 3.13 stays the BUILD machine -- known-good, and every measurement
# this project has made is against it.  4.9.1 is a second opinion on
# architectural fidelity, never a replacement: see claude/HERCULES-4.md.
HERC3=${HERC3:-hercules}
HERC4=${HERC4:-/home/claude/herc4/install/bin/hercules}
T=$R/arch/31bit/tools
U=$R/arch/31bit/updates

py(){ python3 -c "
import sys; sys.path.insert(0,'$T')
$1"; }

# `pgrep -f`, not `pgrep -c`, and the reason is specific and dangerous.
# Hercules 4.9.1 RENAMES ITS MAIN THREAD, so the process `comm` is
# `impl_thread` and `pgrep -c hercules` -- which matches comm -- returns 0 while
# 4.9.1 is running normally.  `pgrep -f` matches the command line and finds it.
#
# Blind to engine 4, this harness did three wrong things at once: `w()` returned
# immediately, `run()` archived each log MID-RUN so every engine-4 log was
# truncated at whatever CP had printed so far, and `dual` then reported "0 CP
# messages" and declared the engines in disagreement when they agree.  Worst of
# all, the guard below is what stops a SECOND Hercules starting on the same
# pack, which is I-63 -- so with engine 4 that protection was simply off.
# I-180.
herc_running(){ pgrep -f '[h]ercules -f' | wc -l; }
w(){ for i in $(seq 1 1800); do test "$(herc_running)" = "0" && return 0
       sleep 3; done
     echo "### w(): Hercules still running after 90 minutes -- refusing to go on"
     return 1; }

# $2 is the engine, defaulting to 3.13.  The log name carries the engine so the
# two runs of a dual test cannot overwrite each other -- a confusion that would
# be indistinguishable from the engines agreeing.
run(){ local eng=${2:-$HERC3}
       test "$(herc_running)" = "0" || {
         echo "### run($1): a Hercules is ALREADY running -- refusing to start a second"
         pgrep -af '[h]ercules -f' | head -3; return 1; }
       # Keep the previous log.  The name is fixed per verb, so every `full`
       # used to overwrite the last one -- and a build log is not a transcript,
       # it is the MEASUREMENT: asmerr.py and deckchk.py both read it, and the
       # 190-diagnostic log that established the 176/176/0 reconciliation was
       # destroyed by the next run that depended on it.  I-131.
       if test -f "$C/$1.log"; then
         mkdir -p "$C/logs"
         mv "$C/$1.log" \
            "$C/logs/$1-$(date -r "$C/$1.log" +%Y%m%d-%H%M%S).log"
       fi
       # `mk` copied every deck into io/rNN.txt.  A deck regenerated between
       # then and now is NOT in this build, and the log will not say so -- it
       # reports `readcard dmkpgs xa0036dk a` either way, and the diagnostics
       # belong to the old cards while every deck-reading tool reports on the
       # new ones.  Third door onto the same stale-artifact failure as I-131
       # and I-138; refuse rather than measure the wrong thing.  I-140.
       python3 "$T/iochk.py" "$C" || {
         echo "### run($1): re-run 'mk' (or restage those files) first"; return 1; }
       ( cd "$C" && setsid nohup "$eng" -f vm370ce.conf > "$1.log" 2>&1 </dev/null & )
       sleep 8; w
       # Append to the journal, so the next snapshot can be validated against
       # everything since the restore rather than against this slice alone.
       test -f "$C/$1.log" && cat "$C/$1.log" >> "$C/build.journal"
       return 0; }

mk(){ # Four invariants on every ./ R, checked before 50 minutes are spent on a
      # build that would report them as assembler diagnostics instead: a
      # replacement must carry forward any label it covers, must not define one
      # that survives on an unreplaced record, must take continuation cards with
      # it, and must only name symbols the module can actually see.  All twelve
      # diagnostics of the 1 October build were one of these four.  I-143.
      # A member we update that is not named in DMKLCL.EXEC produces a deck
      # that is generated, verified, staged, read -- and inert.  I-149.
      python3 $T/wirechk.py >/dev/null 2>&1 || {
        echo "### wirechk: a member we update is not wired into DMKLCL.EXEC"
        python3 $T/wirechk.py; return 1; }
      python3 $T/replchk.py >/dev/null 2>&1 || {
        echo "### replchk: the decks break an invariant -- see below"
        python3 $T/replchk.py; return 1; }
      python3 $T/mkrun.py "$C" "$@" >/dev/null || { echo "### mkrun failed"; return 1; }; }
arch(){ py "import mkrun; mkrun.archmode('$C/vm370ce.conf','$1')"; }

chk(){ local r
       # FIRST, before anything else is read out of the log: did the run do what
       # its own script asked?  w() waits for Hercules to DISAPPEAR and cannot
       # tell "finished" from "killed", so a reaped run reaches here looking
       # healthy -- 15 card files of 104, no assemblies, and therefore no
       # diagnostics for asmchk to find.  A false pass, not lost time.  I-144.
       r=$(py "import mkrun; print(mkrun.incomplete('$C','$1') or '')")
       test -z "$r" || { echo "### $1 DID NOT COMPLETE: $r"; return 1; }
       r=$(py "import mkrun; print(mkrun.boot_failed('$C/$1.log') or '')")
       test -z "$r" || { echo "### BOOT FAILED in $1: $r"; return 1; }
       r=$(py "import mkrun; print(mkrun.wrong_arch('$C/$1.log','$2') or '')")
       test -z "$r" || { echo "### $1: $r"; return 1; }
       echo "--- $1: reached CMS, $2 confirmed"; }

asmchk(){ python3 - "$C/$1.log" <<'PY' || return 1
import re, sys
t = open(sys.argv[1], errors='replace').read()
if 'NOT FOUND' in t:
    print('### a COPY or MACRO was NOT FOUND -- I-101'); sys.exit(1)

# This check had TWO defects that cancelled into a plausible-looking result, and
# the cancellation is why it survived.  I-137.
#
#   1. It knew `TEXT CREATED` and `TXTLCL CREATED` but not `TXTHRC CREATED`, so
#      a module whose highest update level is HRC -- most of them, since only
#      the modules this project patches get an LCL deck -- was reported MISSING
#      even when its deck was built.  Five false positives.
#   2. It treated "flagged but output created" as benign.  That is right for an
#      MNOTE 4 (I-34's four 3375/3390 warnings) and CATASTROPHIC for
#      `IFO188 UNDEFINED SYMBOL`: assembler XF emits the instruction with the
#      symbol resolved as ZERO, so `L R3,SEGPAGE` becomes `L R3,0`, the TEXT
#      deck exists, and VMFLOAD will build a nucleus out of it.  Eleven false
#      negatives, DMKPTR with 35 flagged statements among them.
#
# So severity is the test, not the existence of output.  An MNOTE prints as
# `IFO197 *** MNOTE ***`; everything else is an error that makes the deck a lie.
mods = re.findall(r'\*\*\* ERROR ASMBLING (\S+) \*\*\*', t)
created = set(re.findall(r'^(\S+) (?:TEXT|TXTLCL|TXTHRC) CREATED', t, re.M))
missing = [m for m in mods if m not in created]

# Per-module diagnostics, so an error names the module it is in.
errs = {}
mod = None
for line in t.splitlines():
    m = re.match(r'^EXEC VMFASM (\S+)', line)
    if m:
        mod = m.group(1); continue
    d = re.match(r'^(IFO\d{3}) (?:\*\*\* )?(.*?)(?: \*\*\*)?\s*$', line)
    if d and mod and d.group(1) != 'IFO197':
        errs.setdefault(mod, []).append(d.group(1))

if missing:
    print('### NO OBJECT DECK: %s' % sorted(set(missing)))
if errs:
    print('### REAL DIAGNOSTICS (an object deck may exist and be WRONG):')
    for m in sorted(errs):
        print('###   %-8s %d  %s' % (m, len(errs[m]),
                                     ' '.join(sorted(set(errs[m])))))
if not missing and not errs:
    n = len(re.findall(r'IFO197', t))
    print('--- clean: %d MNOTE(s) only, every deck created' % n)
sys.exit(1 if (missing or errs) else 0)
PY
}

restore(){ local snap=$1 want=${2:-}
  python3 $T/snapshot.py check "$C" "$snap" $want; local rc=$?
  case $rc in
    0) ;;
    2) echo "### $snap is stale -- restoring it anyway is only correct if you"
       echo "### reassemble the modules named above.  Use 'full', or 'quick' with them."
       test "${ALLOW_STALE:-no}" = yes || return 1 ;;
    *) echo "### refusing to restore $snap"; return 1 ;;
  esac
  rm -rf "$C/disks/shadows"; cp -r "$C/disks/$snap" "$C/disks/shadows"
  rm -f "$C/disks/shadows/MANIFEST.json"
  # Start a fresh BUILD JOURNAL.  `snapshot.py take` validates a snapshot
  # against ONE log, because a `full` build is one Hercules run.  A sliced build
  # (I-146) is nine runs and `run()` archives each log as the next begins
  # (I-131), so no single log holds more than its own slice and the snapshot was
  # refused with "no deck APPLYING line for 37 patched module(s)" -- three of
  # this project's own guards combining into a false negative (I-155).  The
  # journal is the evidence for everything done since this restore, derived by
  # appending each finished log rather than reconstructed from whichever logs
  # survive.  A nucleus write lands in it too, which is correct: after a write
  # the state is no longer a BUILD state, and snapshot.py says so.
  : > "$C/build.journal"
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
  # Every COPY MEMBER goes in, always, whatever modules were named.  A member
  # is not a module -- it is assembled into the ones that copy it -- so naming
  # modules alone stages their decks against the PREVIOUS version of CORE and
  # EQU, and the result is a nucleus half-built from two different DSECTs.
  # The members are cheap: six files against a hundred and four.  I-146.
  sp=""
  for f in $U/*.XA*DK; do b=$(basename $f); m=${b%%.*}
    test -f /home/claude/vmce/source/cp/$m.ASSEMBLE && continue
    sp="$sp read:$m:${b#*.} read:$m:AUXLCL"; done
  for m in XABLOKS:COPY XAOPS:MACRO XAIO:MACRO XAIOB:MACRO; do
    sp="$sp read:${m%%:*}:${m#*:}"; done
  for m in "$@"; do
    dk=$(cd $U && ls $m.XA*DK 2>/dev/null | head -1)
    test -n "$dk" || { echo "### no deck for $m"; exit 1; }
    sp="$sp $m:${dk#*.}"; done
  mk q1 $sp || exit 1
  run q1 || exit 1; chk q1 S/370 || exit 1; asmchk q1 || exit 1
  ;;
spec)
  # The minimal build: restore, stage ONLY the inputs that changed since the
  # snapshot, and reassemble only the modules that need it.  `full` stages 104
  # files and assembles 186 modules in about seventy minutes, and this container
  # is reclaimed out from under a run that long -- three times on 1 October, with
  # files surviving and processes not (`uptime` said 39 minutes while the day's
  # work was five hours old).  So the fix is not to protect the long run, it is
  # not to need one.  `quick` cannot express this because it requires every named
  # module to HAVE a deck, and 38 of these need reassembly only because CORE's
  # DSECT moved under them.  I-146.
  w || exit 1
  snap=$2; shift 2
  arch S/370
  ALLOW_STALE=yes restore "$snap" || exit 1
  mk q1 "$@" || exit 1
  run q1 || exit 1; chk q1 S/370 || exit 1; asmchk q1 || exit 1
  echo "--- clean: $(grep -c 'NO STATEMENTS FLAGGED' $C/q1.log)"
  ;;
reset)
  # Restore the snapshot and nothing else, so a sliced build has one known
  # baseline and the slices that follow do not rewind it.  I-148.
  arch S/370
  ALLOW_STALE=yes restore "${2:-SNAP-2}" ${3:-} || exit 1
  ;;
stage)
  # One SLICE of staging, no restore, so progress accumulates on the disk.
  # The container is reclaimed at every turn boundary (`I-146`), so nothing
  # survives outside a single foreground call: ~10 minutes, less a 2-minute CMS
  # boot, at ~28s per card file, is about 13 files.  Four slices plus an
  # assembly run beats one 70-minute build that cannot finish.  I-148.
  shift
  arch S/370
  mk s1 "$@" || exit 1
  run s1 || exit 1; chk s1 S/370 || exit 1
  echo "--- slice staged $# spec(s)"
  ;;
asmonly)
  # The assembly pass over modules already on the disk, no restore, no staging.
  shift
  arch S/370
  sp=""; for m in "$@"; do sp="$sp asm:$m"; done
  mk a1 $sp || exit 1
  run a1 || exit 1; chk a1 S/370 || exit 1; asmchk a1 || exit 1
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
  # Specs go AFTER the ipl by default.  A literal `--` splits them: everything
  # before it is emitted BEFORE `ipl 6A1`, everything after it afterwards.
  #
  #     build.sh test "herc:t+009:3" -- "herc:stop:40"
  #
  # This exists because CCW tracing armed after the ipl records nothing -- the
  # IPL is the part worth tracing, and for three runs on 2 October `t+009` was
  # switched on only to be followed immediately by `stop`, which produced an
  # empty trace that looked like "CP issued no I/O" and was not evidence of
  # anything.  `pgmtrace` was always before the ipl; nothing else could be.
  #
  # Note what this does NOT fix: `--bare` below omits mkrun's whole BOOT
  # dialogue, so nothing answers CP's
  #     Start ((Warm|Force|COLD|CKPT) (DRain) (DIsable) (NOAUTOlo)):
  # prompt.  That is right for a standalone loader IPL, which has no operating
  # system underneath and nothing to log on to, and wrong for a CP nucleus.
  # Answer it with a `cmd:` spec until there is a verb that does it properly --
  # and remember that a line typed at a 3215 with no outstanding read is
  # DISCARDED with no error and no trace, so `cold` arriving unanswered proves
  # nothing on its own.
  w || exit 1
  shift || true
  arch ESA/390
  pre=(); post=(); seen=no
  for a in "$@"; do
    if test "$a" = "--"; then seen=yes; continue; fi
    if test $seen = no; then pre+=("$a"); else post+=("$a"); fi
  done
  # With no `--`, every spec is a post spec, exactly as before.
  if test $seen = no; then post=("${pre[@]}"); pre=(); fi
  test ${#post[@]} -gt 0 || post=("herc:stop:6")
  mk t1 --bare "herc:pgmtrace +1:3" "herc:pgmtrace +2:3" "herc:pgmtrace +5:3" \
     "herc:pgmtrace +6:3" ${pre[@]+"${pre[@]}"} "herc:ipl 6A1:200" \
     "${post[@]}" \
     "herc:stop:6" "herc:psw:5" "herc:r 80.20:5" "herc:gpr:6" \
     "herc:cr:6" || exit 1
  # `cr` is dumped at the STOP, not only where pgmtrace happens to fire.  Until
  # 2 October the only control registers in any log came from the early SSM
  # program exception, and CR6 was read from THERE and quoted as the state at
  # the final wait -- an inference presented as a measurement.  CR6 is the
  # I/O-interruption subclass mask and the whole "did CP take the interrupt?"
  # question turns on it, so it is now captured where the question is asked.
  run t1 || exit 1
  r=$(py "import mkrun; print(mkrun.wrong_arch('$C/t1.log','ESA/390') or '')")
  test -z "$r" || { echo "### t1: $r"; exit 1; }
  echo "--- t1: ESA/390 confirmed"
  sed -n '/^pgmtrace/,$p' "$C/t1.log" | grep -vE "Pausing|Resuming|^$|HHCCD001I" | head -30
  arch S/370
  ;;
sizes)
  # Sweep MAINSIZE and report the SAME four measurements for each, so the
  # machines can be compared rather than described.  No rebuild: only the
  # Hercules config changes, so a size is about four minutes.
  #
  # Why this is worth running now: the DAT conversion is geometry-dependent and
  # every ESA/390 measurement so far has been against exactly one machine size.
  # A size that reaches the same place by the same route is evidence the
  # conversion is not tuned to 16 MB; a size that stops earlier is a cheap find.
  #
  # MAINSIZE is restored to 16 in a trap, because an interrupted sweep that
  # left the config on another size would make every later measurement a
  # measurement of a different machine -- which is I-157, and it cost a day.
  #
  # The DEFAULT SIZES ARE 4 8 12 16 AND THAT IS NOT ARBITRARY.  CE generates
  # `SYSCOR RMSIZE=16384K` (DMKSYS), and DMKCPI takes the SMALLER of the real
  # machine and the SYSGEN size:
  #
  #     L  R1,=A(DMKSYSRM)    real machine size
  #     L  R15,=A(DMKSYSRV)   SYSGEN specified size
  #     C  R1,0(,R15)
  #     BNH *+8               low or equal -- use ACTUAL main storage
  #     L  R1,0(,R15)         high -- use SYSGEN size
  #
  # So above 16 MB CP CLAMPS ITSELF TO 16384K and a 24 or 32 MB run measures
  # Hercules, not CP: same CP storage size, same geometry, just unused real
  # storage.  The first sweep was written as `8 16 24 32` and half of it would
  # have been wasted.  Genuinely testing above 16 MB needs RMSIZE regenerated,
  # which is M5.
  #
  # The pause after `ipl` is 100s, not the 200s the assembly path uses.  That
  # number covers 30-95 seconds of emulated assembly work (see BOOT above); a
  # bare IPL settles well inside 100 and the sweep is four runs, so the
  # difference is minutes.
  w || exit 1
  shift || true
  trap 'py "import mkrun; mkrun.archmode('"'"'$C/vm370ce.conf'"'"', '"'"'S/370'"'"')"; echo "--- MAINSIZE restored"' EXIT
  for mb in ${@:-4 8 12 16}; do
    py "import mkrun; mkrun.archmode('$C/vm370ce.conf', 'ESA/390', $mb)"
    mk t1 --bare "herc:pgmtrace +1:3" "herc:pgmtrace +2:3" "herc:pgmtrace +5:3" \
       "herc:pgmtrace +6:3" "herc:t+6a1:3" "herc:ipl 6A1:200" "herc:stop:15" \
       "herc:savecore $C/core-$mb.bin 0 7FFFF:12" \
       "herc:psw:5" "herc:gpr:6" "herc:cr:6" >/dev/null || exit 1
    run t1 >/dev/null || exit 1
    a=$(py "import mkrun; print(mkrun.wrong_arch('$C/t1.log','ESA/390') or 'ESA/390 ok')")
    printf '%6s MB  %s\n' "$mb" "$(py "import mkrun; print(mkrun.ipl_progress('$C','t1','$C/core-$mb.bin'))")"
    test "$a" = "ESA/390 ok" || echo "         !! $a"
    cp "$C/t1.log" "$C/size-$mb.log"
  done
  ;;
dual)
  # Run the SAME test on both engines from the SAME starting state.  The restore
  # between them is not optional: an ESA/390 IPL writes warm-start data, so the
  # second engine would otherwise start from the first one's end state and any
  # difference could be the state rather than the engine.
  w || exit 1
  snap=${2:-SNAP-2}; shift 2 2>/dev/null || shift $# 
  arch ESA/390
  for eng in 3 4; do
    case $eng in 3) B=$HERC3;; 4) B=$HERC4;; esac
    test -x "$B" -o -n "$(command -v "$B")" || { echo "### engine $eng not found: $B"; exit 1; }
    ALLOW_STALE=yes restore "$snap" test >/dev/null || exit 1
    # Engine 4 needs one thing turned off before it can be compared at all.
    # HERC_DETECT_PGMINTLOOP is a *Hercules* facility, not an architectural one,
    # and in 4.x it TERMINATES THE EMULATOR when CP's abend re-IPL loops, where
    # 3.13 merely stops the CPU with HHCCP016I.  Left on, engine 4 exits 12
    # seconds in, never reaches `stop`, and prints no PSW or registers -- which
    # looks exactly like a disagreement and is not one.  I-120.
    pre=""; test $eng = 4 && pre="herc:facility disable HERC_DETECT_PGMINTLOOP:3"
    # Storage is read on 16-BYTE BOUNDARIES on purpose: 4.x prints the containing
    # line with the requested bytes offset inside it, so `r 8C.10` and `r 80.20`
    # produce differently shaped output.  Aligned, both engines print whole lines
    # and the comparison is by address.
    mk d$eng --bare ${pre:+"$pre"} "herc:pgmtrace +1:3" "herc:pgmtrace +2:3" \
       "herc:pgmtrace +5:3" "herc:pgmtrace +6:3" "herc:ipl 6A1:200" "$@" \
       "herc:stop:6" "herc:psw:5" "herc:r 80.20:5" "herc:r 20.20:5" \
       "herc:gpr:6" || exit 1
    run d$eng "$B" || exit 1
    echo "--- engine $eng ($("$B" --version 2>&1 | grep -oE '[0-9]+\.[0-9]+[0-9.]*' | head -1)): $(grep -c 'INST=' $C/d$eng.log) traced, $(grep -cE 'DMK[A-Z]{3}[0-9]' $C/d$eng.log) CP messages"
  done
  arch S/370
  echo
  python3 $T/dualdiff.py "$C/d3.log" "$C/d4.log"
  ;;
*)
  sed -n '2,20p' "$0"
  exit 2 ;;
esac
