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
    mac:LIBNAME           VMFMAC that library, restaging its EXEC member list
    asm:MODULE            VMFASM a module already on disk
    cmd:<text>[:<secs>]   run one CMS command, default 10 seconds
    herc:<text>[:<secs>]  run one Hercules command, default 8 seconds

`--punch <file>` attaches the card punch ahead of the IPL; see below for why
that is the only place it can go.

Specs run in the order given, so a `read:` of a macro, then `mac:DMKLCL`, then
`asm:` of something that uses it, is a complete sequence.  Hand-editing the
generated rc is how run33 was lost -- CMS dropped to CP READ and every later
command came back `?CP: READCARD` -- so extra work goes through a spec.

`cmd:` is the general escape hatch that keeps that rule enforceable.  It exists
because of run45, when two Hercules instances were started on one pack -- the
second of them by me, after the first appeared not to have launched -- and both
IPLed and wrote concurrently.  Checking the damage needed `Q DISK` and
`LISTFILE`, which no spec could express, and the temptation was to edit the rc
by hand again.  I-63.

Commands run **after** `CPACC` and before the `VMFMAC`/`VMFASM` block, so a
`cmd:` can use the CP maintenance disks -- `VMFLOAD` needs 194 accessed to find
the `TEXT` decks -- and can also set something up for an assembly that follows.
"""
import os
import sys

UPDATES = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                       '..', 'updates')

# Pauses are sized to the work rather than padded, and the sizes here are
# MEASURED rather than estimated -- which took two goes.  `Ready; T=` gives CPU
# and total seconds for each command:
#
#     asmdmk dmklcl      T=35.31/65.81   all 186 nucleus modules
#     vmfasm dmkcpi      T= 0.53/1.08    the largest single module
#     vmfasm dmkcns      T= 0.22/0.43
#
# BUT `T=` is CMS's VIRTUAL CPU time, not wall clock, and I read it as wall
# clock and cut the pause to 30 -- after which two runs issued `vmfasm` and
# reached `cp shutdown` before the assembly had printed anything.  Emulated
# wall time is what the pause has to cover, and that lies somewhere between 30
# and 95 seconds, so 75 with the old 95 as the known-good fallback.  The
# lesson of I-33 stands; the number I derived from it did not.
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


def card(text, src=''):
    """One 80-column card, with column 72 asserted blank.

    Column 72 is the continuation column.  A character there makes Assembler XF
    read the NEXT card as a continuation, and the next card then fails with
    `IFO026 CHARACTERS APPEAR BETWEEN THE BEGIN AND CONTINUE COLUMNS` -- an
    error that names the wrong card and says nothing about column 72.

    `mkdeck.py` has enforced this for generated decks since R-04.  Hand-written
    files staged with `read:` had no such check, and `XAIOB.MACRO` arrived with
    a 72-column comment box whose closing `*` sat exactly there.  Same failure,
    new door.  I-74.
    """
    if len(text) > 80:
        raise ValueError('card over 80 columns%s: %s' % (src, text))
    if len(text) >= 72 and text[71] != ' ':
        raise ValueError(
            'column 72 is the continuation column and is not blank%s.  XF will '
            'read the next card as a continuation and flag IT, not this one:\n'
            '  %s\n  %s^' % (src, text, ' ' * 71))
    return '%-80s\n' % text


def main():
    ce, run = sys.argv[1], sys.argv[2]
    skip = set()
    for i, a in enumerate(sys.argv):
        if a == '--punch':
            skip.add(i + 1)
    specs = [a for i, a in enumerate(sys.argv[3:], 3)
             if not a.startswith('--') and i not in skip]

    # `--bare` omits the CMS boot entirely, for a STANDALONE ipl: loading the
    # punched CP deck through the card reader runs DMKLD00E and DMKSAVNC with
    # no operating system underneath, so there is nothing to log on to and
    # nothing to purge.  Everything still comes from specs rather than a
    # hand-edited rc, which is the rule run33 taught.
    rc = [] if '--bare' in sys.argv else [BOOT]

    # `--punch <file>` attaches the card punch AFTER the IPL and before the
    # specs.  Getting a deck out of CP takes TWO runs and the reason is not
    # obvious: VMFLOAD's spool file is not queued when VMFLOAD ends, it is
    # queued when CP SHUTS DOWN.  So `CP START 00D` in the same run finds an
    # empty queue and punches nothing, and the deck comes out during the NEXT
    # run instead.
    #
    # Neither the config nor a pre-IPL devinit survives to catch it.  Both were
    # tried.  With CE's own line
    #
    #     000D    3525    io/punch.txt ascii
    #
    # 18,894 records went into that ascii punch and were lost; pointing that
    # same line at a binary file did not help either, and a `devinit` placed
    # ahead of BOOT is undone by the IPL's system reset -- the run reported
    # `PUN 00D START FOR OUTPUT` for 18,894 records and produced no file at
    # all.  Only a devinit issued after the IPL takes.  So the shape that
    # works is: run N does the VMFLOAD and shuts down; run N+1 devinits the
    # punch after IPL and issues `CP START 00D CLASS A NOSEP`.
    #
    # NO `ascii` operand: an object deck is EBCDIC, and the translation would
    # mangle every TXT record while leaving the ESD card names readable, so a
    # corrupted deck would still scan as if it were fine.  I-78.
    if '--punch' in sys.argv:
        rc.append('devinit 000d %s\npause 10\n'
                  % sys.argv[sys.argv.index('--punch') + 1])
    n = 0
    asm = []
    mac = []
    cmd = []
    for spec in specs:
        parts = spec.split(':')
        if parts[0] == 'mac':
            mac.append(parts[1])       # emitted after CPACC, which it needs
            # VMFMAC builds the library from <lib> EXEC, which IS the member
            # list, so rebuilding without refreshing that list silently builds
            # the OLD set.  run56 added XAIOB.MACRO, read it, rebuilt DMKLCL
            # and got `IFO078 UNDEFINED OP CODE` on every XAB* -- because the
            # EXEC on the A-disk still named six members, not seven.  Staging
            # it here makes that impossible rather than remembered.  I-74.
            specs.append('read:%s:EXEC' % parts[1])
            continue
        if parts[0] == 'asm':
            asm.append(parts[1])
            continue
        if parts[0] == 'herc':
            # A raw Hercules command, no leading `/`.  `devinit 000d <file>`
            # with no `ascii` gives a BINARY punch, which object decks need --
            # CE's own config has `000D 3525 io/punch.txt ascii`, and an
            # EBCDIC-to-ASCII translation would mangle every TXT record while
            # leaving the ESD card names readable, so the corruption would look
            # like success.
            rest = spec.split(':', 2)[1:]
            text = rest[0]
            secs = int(rest[1]) if len(rest) > 1 and rest[1].isdigit() else 8
            cmd.append((text, secs, False))
            continue
        if parts[0] == 'cmd':
            # split(':', 2) so the command keeps any colon of its own and an
            # optional trailing pause stays separable
            rest = spec.split(':', 2)[1:]
            text = rest[0]
            secs = int(rest[1]) if len(rest) > 1 and rest[1].isdigit() else 10
            cmd.append((text, secs, True))
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
                    f.write(card(line.rstrip('\n'), ' in ' + src))
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
    # CPACC first, then commands: VMFLOAD needs 194 accessed to find the TEXT
    # decks, and nothing a `cmd:` might do is harmed by the CP disks being
    # there.  The VMFMAC/VMFASM block still follows, so a command can set
    # something up for an assembly.
    if '--bare' not in sys.argv:
        rc.append('/cpacc\npause 25\n')
    for text, secs, guest in cmd:
        rc.append('%s%s\npause %d\n' % ('/' if guest else '', text, secs))
    for lib in mac:
        rc.append('/vmfmac %s %s\npause 90\n' % (lib.lower(), lib.lower()))
    for mod in asm:
        rc.append('/vmfasm %s dmklcl\npause 75\n' % mod.lower())
    if '--bare' in sys.argv:
        rc.append('exit\n')          # no CP to shut down
    else:
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
