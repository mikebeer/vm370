#!/usr/bin/env python3
"""Generate a Hercules .rc and the card files for one CE verification run.

Hand-staging the card files cost two ten-minute runs.  An UPDATE deck read
through CP's real card reader needs a leading **ID card**

    ID MAINT NAME DMKEIG XA0008DK

or CP has no user to spool the file to: the reader starts, reports
`RDR 00C STARTED SYSTEM`, and `Q RDR ALL` still says `NO RDR FILES`.  The
symptom appears at `READCARD` as `READER EMPTY OR NOT READY`, which reads like
a device problem and is not one.  I-41.

Two further rules are baked in, both learned the same way:

  * `READCARD` takes the **first** entry of `Q RDR ALL`, so stale spool files
    silently substitute themselves for the deck you meant to read.  Every run
    purges the reader first.  I-26.
  * The printer spool accumulates across runs and the first `CP START 00E`
    flushes all of it into one file -- 66 spool files and 110,052 lines, once.
    Every run purges the printer too.  I-31.

    python3 mkrun.py <ce-dir> <runN> [spec ...]

Each spec is one of:

    MODULE:DECK           stage MODULE.DECK and MODULE.AUXLCL, then VMFASM it
    read:MEMBER:FILETYPE  stage and read a plain member, assemble nothing
    mac:LIBNAME           VMFMAC that library
    asm:MODULE            VMFASM a module already on disk
    cmd:<text>[:<secs>]   run one CMS command, default 10 seconds

Specs run in the order given, so a `read:` of a macro, then `mac:DMKLCL`, then
`asm:` of something that uses it, is a complete sequence.  Hand-editing the
generated rc is how run33 was lost -- CMS dropped to CP READ and every later
command came back `?CP: READCARD` -- so extra work goes through a spec.

`cmd:` is the general escape hatch that keeps that rule enforceable.  It exists
because of run45, when two Hercules instances were started on one pack -- the
second of them by me, after the first appeared not to have launched -- and both
IPLed and wrote concurrently.  Checking the damage needed `Q DISK` and
`LISTFILE`, which no spec could express, and the temptation was to edit the rc
by hand again.  Commands run before the VMFMAC/VMFASM block, which is where a
check of the disk belongs anyway.  I-63.
"""
import os
import sys

UPDATES = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                       '..', 'updates')

# Pauses are sized to the work rather than padded: a VMFASM of a nucleus module
# takes 45-70 seconds of emulated CPU on this host, a READCARD about 8.  I-33.
#
# The null line after IPL answers DMKWRM's start-type prompt in the normal case,
# where warm-start data exists and a default start is wanted.  `cold` follows it
# because when the previous run did NOT shut down cleanly there is no warm data,
# CP asks
#
#     DMKWRM920I NO WARM START DATA; CKPT START FOR RETRY
#     Start ((Warm|Force|COLD|CKPT) (DRain) (DIsable) (NOAUTOlo)) or (SHUTDOWN):
#
# and a blank line does not satisfy it -- CP re-prompts, and every later command
# in the run is swallowed by the prompt with no error anywhere.  run45 lost a
# full IPL to exactly that.  Sending `cold` afterwards is harmless when CP did
# start (it reaches OPERATOR as an unknown command) and answers the prompt when
# it did not, so the rc is now self-healing after an interrupted run.  I-64.
BOOT = """panrate 1000
pause 3
ipl 6A1
pause 40
/
pause 12
/cold
pause 30
/cp disc
pause 15
/logon maint cpcms
pause 32
/
pause 18
/cp purge rdr all
pause 10
/cp purge printer all
pause 10
/cp spool 00c class *
pause 8
"""


def card(text):
    if len(text) > 80:
        raise ValueError('card over 80 columns: ' + text)
    return '%-80s\n' % text


def main():
    ce, run = sys.argv[1], sys.argv[2]
    specs = [a for a in sys.argv[3:] if not a.startswith('--')]

    rc = [BOOT]
    n = 0
    asm = []
    mac = []
    cmd = []
    for spec in specs:
        parts = spec.split(':')
        if parts[0] == 'mac':
            mac.append(parts[1])       # emitted after CPACC, which it needs
            continue
        if parts[0] == 'asm':
            asm.append(parts[1])
            continue
        if parts[0] == 'cmd':
            # split(':', 2) so the command keeps any colon of its own and an
            # optional trailing pause stays separable
            rest = spec.split(':', 2)[1:]
            text = rest[0]
            secs = int(rest[1]) if len(rest) > 1 and rest[1].isdigit() else 10
            cmd.append((text, secs))
            continue
        if parts[0] == 'read':
            member, filetype = parts[1], parts[2]
            files = [(filetype, '%s.%s' % (member, filetype))]
            mod = member
        else:
            mod, deck = parts
            asm.append(mod)
            files = [(deck, '%s.%s' % (mod, deck)),
                     ('AUXLCL', '%s.AUXLCL' % mod)]
        for ft, src in files:
            path = os.path.join(UPDATES, src)
            if not os.path.exists(path):
                raise SystemExit('missing deck: ' + path)
            io = 'r%02d' % n
            with open(os.path.join(ce, 'io', io + '.txt'), 'w') as f:
                f.write(card('ID MAINT NAME %s %s' % (mod, ft)))
                for line in open(path):
                    f.write(card(line.rstrip('\n')))
            # devinit then START: the reader must be re-started after each
            # file is attached, per CE's own operating practice.
            rc.append('devinit 000c io/%s.txt ascii eof trunc\n'
                      'pause 8\n'
                      '/cp start 00c\n'
                      'pause 14\n'
                      '/readcard %s %s a\n'
                      'pause 20\n' % (io, mod.lower(), ft.lower()))
            n += 1

    # CPACC is VMSETUP CP; VMFMAC and VMFASM both depend on it, so it comes
    # first however the specs were ordered.
    for text, secs in cmd:
        rc.append('/%s\npause %d\n' % (text, secs))
    rc.append('/cpacc\npause 25\n')
    for lib in mac:
        rc.append('/vmfmac %s %s\npause 70\n' % (lib.lower(), lib.lower()))
    for mod in asm:
        rc.append('/vmfasm %s dmklcl\npause 95\n' % mod.lower())
    rc.append('/cp shutdown\npause 25\nexit\n')

    with open(os.path.join(ce, 'hercules.rc'), 'w') as f:
        f.write(''.join(rc))
    print('%d card files, %d modules to assemble: %s'
          % (n, len(asm), ' '.join(asm)))
    print('cd %s && nohup hercules -f vm370ce.conf > %s.log 2>&1 &'
          % (ce, run))
    return 0


if __name__ == '__main__':
    sys.exit(main())
