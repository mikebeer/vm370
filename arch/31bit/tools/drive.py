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


class Terminal:
    """A line-mode console on Hercules' console port: telnet with every
    option declined, so Hercules attaches it to a 1052/3215 device rather
    than treating it as a 3270.  Output is appended to a log file as it
    arrives, so the same poll-the-file wait works for both consoles."""
    IAC, DONT, DO, WONT, WILL = 255, 254, 253, 252, 251
    SB, SE, TTYPE = 250, 240, 24

    def __init__(self, path):
        self.path = path
        self.sock = None
        self.buf = b''
        open(path, 'w').close()

    def connect(self, port):
        import socket, threading
        self.sock = socket.create_connection(('127.0.0.1', port), timeout=10)
        self.sock.settimeout(0.5)
        t = threading.Thread(target=self._reader, daemon=True)
        t.start()

    def _reader(self):
        while self.sock:
            try:
                data = self.sock.recv(4096)
            except Exception:
                continue
            if not data:
                break
            out = bytearray()
            data = self.buf + data
            self.buf = b''
            i = 0
            while i < len(data):
                c = data[i]
                if c == self.IAC and i + 1 < len(data) and data[i + 1] == self.SB:
                    # subnegotiation: IAC SB ... IAC SE.  Hercules 3.13 asks
                    # TERMINAL-TYPE SEND and takes `DEC-VT100` as a line-mode
                    # console (Mike's note); anything 327x would make it a 3270.
                    j = data.find(bytes([self.IAC, self.SE]), i + 2)
                    if j < 0:
                        self.buf = data[i:]
                        break
                    sub = data[i + 2:j]
                    if sub[:2] == bytes([self.TTYPE, 1]):   # TERMINAL-TYPE SEND
                        self._send_raw(bytes([self.IAC, self.SB, self.TTYPE, 0]) +
                                       b'DEC-VT100' + bytes([self.IAC, self.SE]))
                    i = j + 2
                    continue
                if c == self.IAC and i + 2 < len(data):
                    cmd, opt = data[i + 1], data[i + 2]
                    if cmd == self.DO:
                        rep = self.WILL if opt == self.TTYPE else self.WONT
                        self._send_raw(bytes([self.IAC, rep, opt]))
                    elif cmd == self.WILL:
                        self._send_raw(bytes([self.IAC, self.DONT, opt]))
                    i += 3
                    continue
                if c == self.IAC and i + 1 < len(data):
                    i += 2
                    continue
                out.append(c)
                i += 1
            with open(self.path, 'ab') as f:
                f.write(bytes(out))

    def _send_raw(self, b):
        try:
            self.sock.sendall(b)
        except Exception:
            pass

    def send(self, line):
        self.sock.sendall(line.encode('latin-1') + b'\r\n')

    def close(self):
        try:
            s, self.sock = self.sock, None
            s.close()
        except Exception:
            pass


def drive(ce, name, steps, herc='hercules', hold=False):
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

    def wait_file(path, pattern, start, timeout):
        rx = re.compile(pattern, re.M)
        deadline = time.time() + timeout
        while time.time() < deadline:
            try:
                with open(path, errors='replace') as f:
                    f.seek(start)
                    if rx.search(f.read()):
                        return True
            except OSError:
                pass
            time.sleep(1)
        return False

    def wait_for(pattern, start, timeout):
        return wait_file(log, pattern, start, timeout)

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

    # The second terminal.  Mike: "only operator can issue shutdown. you
    # should do the tests on the other terminal".  The config has `000A 1052`:
    # a plain telnet connection to CNSLPORT that declines every TN3270
    # negotiation is attached to it as a line-mode console.  The operator
    # stays on 0009; the test user logs on here; `shutdown` is typed on 0009.
    # Steps with "term" instead of "send" go to this terminal and their
    # `expect` is matched against what it printed (<name>.term.log).
    term = None
    tlog = os.path.join(ce, name + '.term.log')
    if any('term' in st for st in steps):
        term = Terminal(tlog)
        term.connect(3270)
        time.sleep(1)

    ok = True
    for st in steps:
        if 'term' in st:
            st = dict(st, send=st['term'])
            tpos = os.path.getsize(tlog)
            term.send(st['term'])
            if 'expect' in st:
                hit = wait_file(tlog, st['expect'], tpos, st.get('timeout', 90))
                print('%s T %-40s %s %s' % (stamp(), st['term'][:40],
                                            'ok' if hit else '### TIMEOUT',
                                            st['expect'] if not hit else ''))
                if not hit:
                    ok = False
                    if st.get('cont'):
                        continue
                    print(tail(tlog))
                    break
            else:
                time.sleep(st.get('settle', 2))
                print('%s T %-40s settled %ss' % (stamp(), st['term'][:40], st.get('settle', 2)))
            line = st['term']
            continue
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
                if st.get('cont'):
                    # A measurement step: the pattern not appearing IS the
                    # finding, and the steps that follow take the readings.
                    continue
                print(tail(log))
                break
        else:
            time.sleep(st.get('settle', 2))
            print('%s %-42s settled %ss' % (stamp(), line[:42], st.get('settle', 2)))
    if hold:
        # Keep the system up for an interactive relay: Mike types CP/CMS
        # lines in the chat, they land here as files in <ce>/relay/, and the
        # consoles' logs carry the answers.  `op:` prefixes go to the
        # operator's 0009 via Hercules; everything else to the terminal.
        # A file named `stop` ends the hold; CP is then shut down and
        # Hercules exits as in every run.
        rdir = os.path.join(ce, 'relay')
        os.makedirs(rdir, exist_ok=True)
        for f in os.listdir(rdir):
            os.remove(os.path.join(rdir, f))
        print('--- %s holding; relay dir %s' % (name, rdir), flush=True)
        n = 0
        while True:
            if os.path.exists(os.path.join(rdir, 'stop')):
                break
            files = sorted(f for f in os.listdir(rdir) if f.endswith('.cmd'))
            for f in files:
                path = os.path.join(rdir, f)
                text = open(path).read().rstrip('\n')
                os.remove(path)
                for cmdline in text.split('\n'):
                    n += 1
                    if cmdline.startswith('op:'):
                        send(cmdline[3:])
                    elif term:
                        term.send(cmdline)
                    print('%s relay %d: %s' % (stamp(), n, cmdline), flush=True)
                    time.sleep(1)
            time.sleep(1)
    if term:
        term.close()
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
    hold = False
    if '--hold' in a:
        hold = True
        a.remove('--hold')
    ce, name, stepfile = a
    steps = json.load(open(stepfile))
    return drive(ce, name, steps, herc, hold)


if __name__ == '__main__':
    sys.exit(main())
