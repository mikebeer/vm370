#!/bin/bash
# waitfor.sh <seconds> <shell-condition>
# Poll once a second and return the moment the condition is true, rather than
# sleeping a fixed block and checking afterwards.  A fixed `sleep 115` wastes
# half its interval on average, and a build cycle has fifteen or twenty of
# them.  Prints how long it actually waited, so the logs show the real cost of
# each step instead of the padding.
n=$1; shift
t0=$SECONDS
for i in $(seq 1 "$n"); do
  if eval "$*"; then echo "--- waited $((SECONDS-t0))s"; exit 0; fi
  sleep 1
done
echo "--- TIMED OUT after $((SECONDS-t0))s: $*"; exit 1
