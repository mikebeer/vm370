#!/usr/bin/env python3
"""Wall-clock timestamps for the milestones in a run, so pauses can be tuned
on measurement instead of nerve.

Every pause in a generated rc is a fixed constant, and `mkrun.py`'s own comment
says why they are generous: an rc has no way to wait for a prompt, so the
margin is the only protection and a too-short pause once cost a 25-minute
build.  But the project also already has the better answer in place --
`boot_failed()`, `asmchk()` and the `00000012` check make a short pause fail
LOUDLY -- and with that in hand the margin is pure cycle time.  A build makes
twenty-odd runs and each pays the boot block's 244 seconds.

This watches a growing log and prints the wall-clock second at which each
marker first appears, which is the number a pause should be sized against.
Run it beside a build:

    python3 phase.py <log> <seconds> <marker>...

Markers are plain substrings.  It exits when the last one is seen or the time
is up, and prints the gaps, so what comes out is a table of what the run
actually needed rather than what it was given.
"""
import os
import sys
import time


def main():
    if len(sys.argv) < 4:
        print(__doc__)
        return 2
    path, limit, markers = sys.argv[1], int(sys.argv[2]), sys.argv[3:]
    pending = list(markers)
    seen = []
    t0 = time.time()
    # Start at the CURRENT end of file.  Reading from byte zero matched the
    # PREVIOUS run's log in its first pass and reported every milestone at
    # once -- an instrument reporting presence where there was none, which is
    # I-168 in the other direction.  `run()` archives the old log and creates a
    # new one, so a watcher started before that happens must also notice the
    # file shrinking and rewind.
    pos = os.path.getsize(path) if os.path.exists(path) else 0
    while pending and time.time() - t0 < limit:
        try:
            size = os.path.getsize(path)
            if size < pos:          # the log was replaced: start over
                pos = 0
            if size > pos:
                with open(path, errors='replace') as f:
                    f.seek(pos)
                    chunk = f.read()
                    pos = f.tell()
                for m in list(pending):
                    if m in chunk:
                        dt = time.time() - t0
                        seen.append((m, dt))
                        pending.remove(m)
                        print(f'{dt:7.1f}s  {m}', flush=True)
        except OSError:
            pass
        time.sleep(1)
    for m in pending:
        print(f'{"":7}   NOT SEEN: {m}', flush=True)
    if len(seen) > 1:
        print('--- gaps between milestones:')
        for (a, ta), (b, tb) in zip(seen, seen[1:]):
            print(f'    {tb - ta:7.1f}s  {a[:28]} -> {b[:28]}')
    return 0 if not pending else 1


if __name__ == '__main__':
    sys.exit(main())
