#!/usr/bin/env python3
"""Drive a Hercules run step by step, sending each command only when the log
shows the previous one has been answered.

`mkrun.py` writes an `rc` file of commands with fixed pauses between them, and
Hercules plays it blind.  Every pause had to cover the slowest case ever seen,
so a CMS dialogue took eight minutes of waiting for about two minutes of work,
and a line typed before CP had its console read outstanding was silently
discarded (the 3215 gotcha), which cost w25, w36 and w43 in one night.  Mike
asked twice that waiting be a one-second poll, not a number.  This is that.

Hercules 3.13 does NOT read panel commands from a pipe on stdin -- the first
two driven runs proved that, nothing sent arrived -- but its HTTP server takes
them: GET /cgi-bin/tasks/syslog?command=<text> runs a panel command exactly as
if typed.  So the driver starts Hercules with HTTPPORT set, posts each step's
line there, and polls the log once a second until the step's `expect` pattern
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
it unchanged.  A timeout prints the log tail, shuts CP down (`cp shutdown`, then `shutdown`)
and ends the run with `exit`, so the pack is never left with Hercules up (I-63)
and CP never dies under a running Hercules.
"""
import json
import os
import re
import shutil
import subprocess
import sys
import time
import urllib.parse
import urllib.request

PORT = 8081


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
    # mkrun leaves a hercules.rc full of commands and pauses that Hercules
    # runs at start-up, colliding with ours (the first driven run IPLed twice
    # and ignored `exit` while the rc was mid-pause).  Replace it with the one
    # line we want run unattended.
    with open(os.path.join(ce, 'hercules.rc'), 'w') as f:
        f.write('panrate 1000\n')
    # The HTTP server is the command channel.  Run from a copy of the config
    # with HTTPPORT added, so the build's own config is untouched.
    conf = os.path.join(ce, 'drive.conf')
    shutil.copy(os.path.join(ce, 'vm370ce.conf'), conf)
    with open(conf, 'a') as f:
        f.write('HTTPPORT %d NOAUTH\n' % PORT)
    out = open(log, 'w')
    p = subprocess.Popen([herc, '-f', 'drive.conf'], cwd=ce,
                         stdin=subprocess.DEVNULL, stdout=out, stderr=out,
                         text=True, bufsize=1, start_new_session=True)
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
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
        url = 'http://127.0.0.1:%d/cgi-bin/tasks/syslog?' % PORT + \
            urllib.parse.urlencode({'command': line, 'msgcount': '0'})
        for attempt in range(5):
            try:
                opener.open(url, timeout=10).read()
                return
            except Exception as e:
                err = e
                time.sleep(1)
        raise RuntimeError('could not send %r: %s' % (line, err))

    # Hercules is ready when its HTTP listener is up.
    if not wait_for(r'HHCHT006I Waiting for HTTP requests', 0, 60):
        print('### Hercules did not come up; tail:\n' + tail(log))
        p.kill()
        return 2
    print('--- %s hercules up %s' % (name, stamp()))

    ok = True
    for st in steps:
        pos = os.path.getsize(log)
        if 'rreg' in st:
            # Dump storage at an address held in a register: take the LAST
            # GRnn= value printed so far (a `gpr` step before this one), 24-bit
            # it, add an offset, and send `r addr.len`.  This is the one thing a
            # pre-written script could never do -- follow a pointer.
            reg = st['rreg'].upper().replace('R', 'GR')
            if len(reg) == 3:
                reg = reg[:2] + '0' + reg[2]
            vals = re.findall(reg + r'=([0-9A-F]{8})', open(log, errors='replace').read())
            if not vals:
                print('%s rreg %s: no gpr output to read' % (stamp(), st['rreg']))
                ok = False
                break
            addr = (int(vals[-1], 16) & 0xFFFFFF) + st.get('offset', 0)
            line = 'r %X.%X' % (addr, st.get('len', 64))
            st = dict(st, send=line, expect=r'R:%08X' % addr)
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
        # Mike: "/shutdown and exit is the proper way to end a VM Hercules
        # session".  A run that stopped short still shuts CP down before
        # Hercules leaves: `cp shutdown` works from any logged-on class-A
        # user (MAINT) and `shutdown` from the operator; send both forms and
        # wait for the disabled wait state CP enters when it is done.
        pos = os.path.getsize(log)
        send('/cp shutdown')
        if not wait_for(r'HHCCP011I|SHUTDOWN COMPLETE', pos, 30):
            send('/shutdown')
            wait_for(r'HHCCP011I|SHUTDOWN COMPLETE', pos, 30)
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
