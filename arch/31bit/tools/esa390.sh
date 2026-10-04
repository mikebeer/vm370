#!/bin/bash
# esa390.sh <name> <steps.json>  -- one ESA/390 run driven by drive.py, with the
# architecture set in the config and VERIFIED from the log (I-115), the same
# contract diag.sh had, minus the fixed pauses.
C=/home/claude/vm370/scratchpad/VM370CE.V1.R1.2
R=/home/claude/vm370
N=$1; STEPS=$2
pgrep -x hercules >/dev/null && { echo "### hercules already running (I-63)"; exit 1; }
python3 -c "
import sys; sys.path.insert(0,'$R/arch/31bit/tools')
import mkrun; mkrun.archmode('$C/vm370ce.conf','ESA/390')"
python3 $R/arch/31bit/tools/drive.py "$C" "$N" "$STEPS" ${HERC:+--herc $HERC} ${HOLD:+--hold}
rc=$?
bad=$(python3 -c "
import sys; sys.path.insert(0,'$R/arch/31bit/tools')
import mkrun; print(mkrun.wrong_arch('$C/$N.log','ESA/390') or '')")
test -z "$bad" && echo "--- $N: ESA/390 confirmed" || { echo "### $N: $bad"; exit 1; }
exit $rc
