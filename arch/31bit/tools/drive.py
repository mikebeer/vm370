#!/usr/bin/env python3
"""Drive a Hercules run step by step, sending each command only when the log
shows the previous one has been answered.

`mkrun.py` writes an `rc` file of commands with fixed pauses between them, and
Hercules plays it blind.  Every pause had to cover the slowest case ever seen,
so a CMS dialogue took eight minutes of waiting for about two minutes of work,
and a line typed before CP had its console read outstanding was silently
discarded (the 3215 gotcha), which cost w25, w36 and w43 in one night.  Mike
asked twice that waiting be a one-second poll, not a number.  This is that.

Hercules reads panel commands from stdin when stdin is not a terminal.  So the
driver opens a pipe to it, tails the log it writes, and for each step sends the
line and then polls the log once a second until the step's `expect` pattern
appears AFTER the point at which the line was sent.  A step with no pattern
settles for a stated number of seconds instead -- used only where CP prints
nothing on success, and the number is then the measured need, not a margin.

    python3 drive.py <ce-dir> <name> <steps.json>  [--herc <binary>]

steps.json is a list of objects:

    {"send": "ipl 6A1",   "expect": "Start \\\\(\\\\(Warm",  "timeout": 120}
    {"send": "/cold",     "expect": "DMKCPI966I",          "timeout": 120}
    {"send": "/enable all",                                "settle": 4}
    {"send": "exit"}

`send` lines go to Hercules verbatim; a leading `/` is Hercules' own prefix for
the integrated console, so guest commands are written as they always were.
The log is <ce-dir>/<name>.log, as diag.sh wrote it, so every other tool reads
it unchanged.  A timeout prints the log tail and ends the run with `exit`, so
the pack is never left with Hercules up (I-63).
"""
import json
import os
import re
import subprocess
import sys
import time


def tail(path, n=25):
    try:
        with open(path, errors='replace') as f:
            return ''.join(f.readlines()[-n:])
    except OSError:
        return ''


def drive(ce, name, steps, herc='hercules'):
    log = os.path.join(ce, name + '.log')
    if os.path.exists(log):
        os.remove(log)
    out = open(log, 'w')
    p = subprocess.Popen([herc, '-f', 'vm370ce.conf'], cwd=ce,
                         stdin=subprocess.PIPE, stdout=out, stderr=out,
                         text=True, bufsize=1, start_new_session=True)
    t0 = time.time()
    stamp = lambda: '%6.1fs' % (time.time() - t0)

    def wait_for(pattern, start, timeout):
        rx = re.compile(pattern, re.M)
        deadline = time.time() + timeout
        while time.time() < deadline:
            with open(log, errors='replace') as f:
                f.seek(start)
                if rx.search(f.read()):
                    return True
            time.sleep(1)
        return False

    def send(line):
        p.stdin.write(line + '\n')
        p.stdin.flush()

    # Hercules is ready when the CPU thread reports its architecture mode.
    if not wait_for(r'HHCCP003I CPU0000 architecture mode', 0, 60):
        print('### Hercules did not come up; tail:\n' + tail(log))
        p.kill()
        return 2
    print('--- %s hercules up %s' % (name, stamp()))

    ok = True
    for st in steps:
        pos = os.path.getsize(log)
        line = st['send']
        send(line)
        if 'expect' in st:
            hit = wait_for(st['expect'], pos, st.get('timeout', 90))
            print('%s %-42s %s %s' % (stamp(), line[:42],
                                      'ok' if hit else '### TIMEOUT',
                                      st['expect'] if not hit else ''))
            if not hit:
                ok = False
                print(tail(log))
                break
        else:
            time.sleep(st.get('settle', 2))
            print('%s %-42s settled %ss' % (stamp(), line[:42], st.get('settle', 2)))
    if line != 'exit':
        send('exit')
    try:
        p.wait(timeout=90)
    except subprocess.TimeoutExpired:
        print('### hercules did not exit; killing')
        p.kill()
    out.close()
    print('--- %s done %s, log %s' % (name, stamp(), log))
    return 0 if ok else 1


def main():
    a = sys.argv[1:]
    herc = 'hercules'
    if '--herc' in a:
        herc = a[a.index('--herc') + 1]
        del a[a.index('--herc'):a.index('--herc') + 2]
    if len(a) != 3:
        print(__doc__)
        return 2
    ce, name, stepfile = a
    steps = json.load(open(stepfile))
    return drive(ce, name, steps, herc)


if __name__ == '__main__':
    sys.exit(main())
