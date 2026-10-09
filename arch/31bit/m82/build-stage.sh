#!/bin/bash
# M8.2: stage (prep.py), compile on the PC (pre.sh), derive the 8-character
# names (names.py), stage again with them renamed, compile again.
set -e
cd "$(dirname "$0")"
S=${SP:-/tmp/claude-0/-home-claude-vm370/0e789c93-0fd6-50d9-9e2c-c5456a7467b9/scratchpad}
ST=$S/m82stage; O=$S/m82pre
rm -rf $ST $O; python3 prep.py $ST; ./pre.sh | tail -3
python3 names.py $O $ST names.txt
rm -rf $ST $O; python3 prep.py $ST names.txt; ./pre.sh | tail -5
