#!/bin/bash
# M5g: GCCLIB31 sources + build EXEC + test as one reader deck for CMSUSER
# (READCARD * with 195 accessed as A).  $1 = gcclib checkout, $2 = deck.
set -e
H=$(cd $(dirname $0) && pwd)
python3 $H/mk31.py ${1:-/home/claude/adesutherland/cms-370-gcclib} $H/src
args=()
for f in $H/src/*; do args+=("$f"); done
for f in $H/cms/*; do args+=("$f"); done
python3 $H/../crexx/mkdeck.py ${2:-$H/gcclib31.txt} "${args[@]}"
