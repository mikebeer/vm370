#!/bin/bash
# cycle.sh RUN [BASEJSON] [MODS]: build CP (if MODS given), run RUN with BASEJSON's
# steps, wait for it, print the kernel-log tail, the DMKVCS ring and the terminal.
S=/tmp/claude-0/-home-claude-vm370/0e789c93-0fd6-50d9-9e2c-c5456a7467b9/scratchpad
L=/home/claude/vm370/scratchpad/VM370CE.V1.R1.2
run=$1; base=${2:-lx64}; mods=$3
if [ -n "$mods" ]; then
  $S/bvat.sh $mods > $S/bvat.out 2>&1
  grep -q BUILD-DONE $S/bvat.out || { tail -5 $S/bvat.out; exit 1; }
  echo "build ok"
fi
[ "$S/$base.json" = "$S/$run.json" ] || cp $S/$base.json $S/$run.json
rm -f $S/$run.out
nohup $S/after.sh $S/$run.out sh -c "cd /home/claude/vm370 && arch/31bit/tools/esa390mb.sh 64 $run $S/$run.json" >/dev/null 2>&1 &
sleep 5
$S/waitrun.sh $S/$run.out 600
echo "=== kernel log"
python3 $S/gklog.py $L/$run.gdump 2>/dev/null | grep -v '^.\{0,7\}$' | sed -n '/NR_IRQS/,$p' | head -${LOGN:-40}
echo "=== ring"
python3 $S/vcsring.py $L/$run.log 2>/dev/null | tail -${RINGN:-12}
echo "=== terminal"
grep -a -v '^00[0-9A-F]\{6\}' $L/$run.term.log | sed -n '/STORAGE =/,$p' | grep -v '000206 MVC' | head -${TERMN:-40}
