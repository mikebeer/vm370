#!/bin/bash
# esa390mb.sh <mb> <name> <steps.json>  -- as esa390.sh, with Hercules MAINSIZE
# set to <mb> for this run only (M4b measurements: real storage above 16 MB).
# MAINSIZE goes back to 16 when the run ends, however it ends (trap), because
# every other measurement in this project is against 16 MB (I-157).
C=/home/claude/vm370/scratchpad/VM370CE.V1.R1.2
R=/home/claude/vm370
MB=$1; N=$2; STEPS=$3
pgrep -x hercules >/dev/null && { echo "### hercules already running (I-63)"; exit 1; }
py() { python3 -c "import sys; sys.path.insert(0,'$R/arch/31bit/tools'); $1"; }
trap 'py "import mkrun; mkrun.archmode(\"$C/vm370ce.conf\", \"ESA/390\")"; echo "--- MAINSIZE restored to 16"' EXIT
py "import mkrun; mkrun.archmode('$C/vm370ce.conf','ESA/390', mb=$MB)"
grep -E "^MAINSIZE" $C/vm370ce.conf
python3 $R/arch/31bit/tools/drive.py "$C" "$N" "$STEPS" ${HERC:+--herc $HERC} ${HOLD:+--hold}
rc=$?
bad=$(py "import mkrun; print(mkrun.wrong_arch('$C/$N.log','ESA/390') or '')")
test -z "$bad" && echo "--- $N: ESA/390 confirmed, MAINSIZE $MB" || { echo "### $N: $bad"; exit 1; }
exit $rc
