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
    cmd:<text>[:<secs>]   run one CMS command BEFORE the assemblies
    post:<text>[:<secs>]  run one CMS command AFTER them
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
import re

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
# The margins below were widened on 30 Sep after a run lost 25 minutes to a
# race this block cannot see.  CE auto-logs OPERATOR, AUTOLOG1, CPWATCH,
# CMSBATCH and WAKEUP at IPL, and each one writes to the OPERATOR console.  A
# `CP DISC` issued while that storm is still running is SWALLOWED -- no error --
# so the machine is still OPERATOR when `LOGON MAINT` arrives, LOGON is invalid
# when already logged on, and CMS never comes up.  Every later command then
# returns `?CP: READCARD`, which is the symptom this file's own docstring warns
# about.  On a quiet machine `AUTOLOG1 DONE - LOGGING OFF` lands ~18 s before
# `cold`; on a busy one it lands after `logon`.  Same script, different load.
#
# Timing cannot be made sufficient, only likely, because an rc has no way to
# wait for a prompt -- so `boot_failed()` below is the real fix and these
# numbers only make it rare.  I-112.
BOOT = """panrate 1000
pause 3
ipl 6A1
pause 70
/
pause 15
/cold
pause 30
/cp disc
pause 35
/logon maint cpcms
pause 45
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
    # I-205: a deck may continue a statement on purpose, and mkdeck writes
    # exactly 'X' there when told to.  Anything else in column 72 is still the
    # accident this guard exists for (R-04: a comment box's closing '*').
    deliberate = (len(text) >= 72 and text[71] == 'X'
                  and not text.startswith('*') and not text.startswith('./'))
    if len(text) >= 72 and text[71] != ' ' and not deliberate:
        raise ValueError(
            'column 72 is the continuation column and is not blank%s.  XF will '
            'read the next card as a continuation and flag IT, not this one:\n'
            '  %s\n  %s^' % (src, text, ' ' * 71))
    return '%-80s\n' % text


# What each kind of command prints when it is done.  The rc's pauses were
# sized to the slowest case ever seen (I-33, I-148, I-193); a build spent
# 15 s per card file and 75 s per VMFASM waiting for work that takes 1 s
# and 40 s.  With an expect pattern the wait ends when the log says so, and
# the timeout is only a cap -- generous, because reaching it is a failure
# the post-checks (incomplete, asmchk) report, not a pacing choice.
EXPECTS = [
    # A BUILD boots CE's own S/370 nucleus, which asks nothing and prints
    # DMKCPI966I within a second; the ESA/390 nucleus asks 'Start ((Warm'.
    # The two console lines that follow are the rc's answers to that prompt
    # and cost nothing when there is none.
    (r'^ipl ',                r'DMKCPI966I|Start \(\(Warm',        180),
    (r'^/$',                  r'Ready|Start \(\(Warm|AUTO LOGON|CP', 15),
    (r'^/cold$',              r'DMKCPI966I|AUTO LOGON|\?CP|CP',      15),
    (r'^/cp disc',            r'DISCONNECT AT',                     60),
    (r'^/logon ',             r'Ready|LOGON AT|RECONNECT',          180),
    (r'^/cp purge',           r'Ready',                             60),
    (r'^/cp spool',           r'Ready',                             60),
    (r'^devinit ',            r'HHCPN098I|initialized',             30),
    (r'^/cp start',           r'Ready',                             60),
    (r'^/readcard',           r'Ready',                             120),
    (r'^/cpacc',              r'Ready',                             120),
    (r'^/vmfmac',             r'Ready',                             600),
    (r'^/vmfasm',             r'Ready',                             900),
    (r'^/asmdmk',             r'Ready',                             1800),
    (r'^/vmfload',            r'Ready|SYSTEM LOAD DECK COMPLETE',   600),
    (r'^/cp shutdown',        r'HHCCP011I|SHUTDOWN COMPLETE|SHUTDOWN', 40),
    (r'^/cp ipl 00c',         r'00000012|DISABLED WAIT',            300),
    (r'^/cp ',                r'Ready',                             120),
]


def steps_from_rc(text):
    """drive.py steps for an rc: the pauses become expects (EXPECTS above);
    a command no pattern knows keeps its pause as a settle."""
    steps, pending = [], None
    for raw in text.split('\n'):
        line = raw.strip()
        if not line or line.startswith('#') or line == 'panrate 1000':
            continue
        if line.startswith('pause '):
            if pending is not None and 'expect' not in pending:
                pending['settle'] = int(line.split()[1])
            continue
        if line == 'exit':
            steps.append({'send': 'exit'})
            pending = None
            continue
        st = {'send': line}
        for pat, exp, to in EXPECTS:
            if re.match(pat, line):
                st['expect'] = exp
                st['timeout'] = to
                st['cont'] = True
                break
        steps.append(st)
        pending = st
    return steps


def main():
    ce, run = sys.argv[1], sys.argv[2]
    # Clear the staging directory first.  A previous, LARGER run leaves io
    # files behind, and `iochk` then compares them against decks that have
    # since changed and refuses the run -- which is correct of it, and the
    # reason it refused here was a stale `DMKLCL.EXEC` from a 49-file run
    # lingering into an 11-file one.  Leftovers from a bigger run are the same
    # stale-artifact shape as I-131, I-138 and I-140, one directory further in.
    import glob as _glob
    for _old in _glob.glob(os.path.join(ce, 'io', 'r*.txt')):
        os.remove(_old)
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
    post = []
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
        if parts[0] == 'post':
            # `cmd:` runs before the VMFASM block, which is right for setting an
            # assembly up and wrong for consuming its output: a VMFLOAD issued
            # as a `cmd:` punches the PREVIOUS assembly's TEXT.  Reverting
            # DMKSAV needed an erase, an assembly and a VMFLOAD in that order,
            # which no ordering of `cmd:` can express.  I-84.
            rest = spec.split(':', 2)[1:]
            text = rest[0]
            secs = int(rest[1]) if len(rest) > 1 and rest[1].isdigit() else 10
            post.append((text, secs))
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
            # I-197.  Stage EVERY XA deck the module's AUXLCL names, not only
            # the one on the spec.  `DMKPTR:XA0038DK` used to copy XA0038DK
            # and the AUXLCL and leave XA0036DK on the pack as whatever the
            # snapshot held -- so the I-196 fix, regenerated into XA0036DK,
            # was applied by name (`APPLYING 'DMKPTR XA0036DK A1'`) from the
            # OLD copy, iochk reported no drift because it only knows staged
            # files, and the nucleus still had SRL R2,16 at 3DF18.  A build
            # cycle to learn that the spec names a module, not a deck.
            files = [('AUXLCL', '%s.AUXLCL' % mod)]
            seen = set()
            for line in open(os.path.join(UPDATES, '%s.AUXLCL' % mod)):
                d = line.split()[0] if line.split() else ''
                if d.startswith('XA') and d not in seen:
                    seen.add(d)
                    files.insert(0, (d, '%s.%s' % (mod, d)))
            if deck not in seen:
                raise SystemExit('%s: %s is not in %s.AUXLCL' % (spec, deck, mod))
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
            # 8 + 14 + 20 was 42 seconds of waiting per file to cover work the
            # log shows completing in 0.01 seconds -- `Ready; T=0.01/0.01`,
            # including the readcard of a 272-card deck.  Over 49 files that is
            # 34 minutes of pause, and this container is reclaimed at every turn
            # boundary (I-146), so the pauses were the reason a build could not
            # finish inside one call.  Cut to a third.  This is only safe because
            # `incomplete()` now counts `HAS BEEN READ` against the readcards
            # issued: a pause that turns out too short fails loudly instead of
            # applying a TRUNCATED update deck, which is far worse than a slow
            # build.  The vmfasm pauses are NOT touched -- those cover real work
            # and the 30-to-70 correction above is a scar.  I-148.
            rc.append('devinit 000c io/%s.txt ascii eof trunc\n'
                      'pause 3\n'
                      '/cp start 00c\n'
                      'pause 5\n'
                      '/readcard %s %s a\n'
                      'pause 7\n' % (io, mod.lower(), ft.lower()))
            n += 1

    # CPACC is VMSETUP CP; VMFMAC and VMFASM both depend on it, so it comes
    # first however the specs were ordered.
    # CPACC first, then commands: VMFLOAD needs 194 accessed to find the TEXT
    # decks, and nothing a `cmd:` might do is harmed by the CP disks being
    # there.  The VMFMAC/VMFASM block still follows, so a command can set
    # something up for an assembly.
    if '--bare' not in sys.argv:
        # 25 -> 15.  Measured at 8 seconds on 3 October (pacing.py over
        # n1.log), and a failed CPACC is caught loudly: every later readcard
        # and vmfasm fails and `asmchk` says so.  I-193.
        rc.append('/cpacc\npause 15\n')
    for text, secs, guest in cmd:
        rc.append('%s%s\npause %d\n' % ('/' if guest else '', text, secs))
    for lib in mac:
        rc.append('/vmfmac %s %s\npause 90\n' % (lib.lower(), lib.lower()))
    for mod in asm:
        rc.append('/vmfasm %s dmklcl\npause 75\n' % mod.lower())
    for text, secs in post:
        rc.append('/%s\npause %d\n' % (text, secs))
    if '--bare' in sys.argv:
        rc.append('exit\n')          # no CP to shut down
    else:
        rc.append('/cp shutdown\npause 25\nexit\n')

    with open(os.path.join(ce, 'hercules.rc'), 'w') as f:
        f.write(''.join(rc))
    # The same dialogue as drive.py steps: each command waits for the answer
    # the log shows instead of for a number of seconds.  build.sh run() uses
    # this when it exists; hercules.rc stays as the record incomplete() reads.
    import json
    with open(os.path.join(ce, '%s.json' % run), 'w') as f:
        json.dump(steps_from_rc(''.join(rc)), f, indent=1)
    print('%d card files, %d modules to assemble: %s'
          % (n, len(asm), ' '.join(asm)))
    print('cd %s && nohup hercules -f vm370ce.conf > %s.log 2>&1 &'
          % (ce, run))
    return 0


if __name__ == '__main__':
    sys.exit(main())


def archmode(conf, mode, mb=None):
    """Set ARCHMODE and the three settings that must move with it.

    `mb` overrides MAINSIZE for a deliberate size sweep and is otherwise None,
    which keeps the matched pair below.  An override is a MEASUREMENT, not a
    new default: it must be set back, and `build.sh sizes` does that in a trap
    so an interrupted sweep cannot leave the config on some other machine.
    Every ESA/390 measurement this project reports is against 16 MB unless it
    says otherwise, because I-157 was exactly the cost of not knowing which
    machine a number came from.

    Flipping ARCHMODE alone leaves CE's config self-contradictory, and Mike
    caught it: `CPUMODEL 4381` is a S/370 4381, a machine that does not exist
    in ESA/390, so STIDP would report a S/370 processor to an ESA/390 CP; and
    `ECPSVM YES` declares the ECPS:VM assists, whose E6xx opcodes are
    GENx370x -- S/370 only -- so in ESA/390 the declaration is at best a
    no-op and at worst a confounder, because CP detects the assists by taking
    a program check and recovering.

    Neither caused the cc=3 that was under investigation when he asked (that
    was XAIODEV = 0000, I-88), which is exactly why they were worth fixing
    separately rather than in the middle of a diagnosis.  S/370 runs keep
    CE's shipped values so the control stays a control.  I-89.

    MAINSIZE moves too, and it cannot be the same number in both.  S/370 is
    24-bit: 16 MB is the architectural ceiling, so the build machine stays at
    CE's shipped 16.  ESA/390 is 31-bit and the whole point of the project, so
    it gets 256 -- which is also a live test of CP's own storage sizing, since
    `DMKCPI957I Storage size = 16384 K` is DETECTED at IPL rather than
    generated.  CP will very likely still stop at 16 MB until the storage-key
    and page-table work is done; what matters now is that it does not break.
    """
    import re
    want = {'S/370':   [('ARCHMODE', 'S/370'),   ('CPUMODEL', '4381'),
                        ('ECPSVM', 'YES'),       ('MAINSIZE', '16')],
            # ESA/390 was 256 MB until 2 October, and that was wrong in a way
            # that cost most of a day's diagnosis.  `R-25` keeps Hercules at
            # **16 MB real** on purpose: real storage above 16 MB is M5, and it
            # is deferred.  Giving the ESA/390 test machine 256 MB tested M1 on
            # an M5 machine, and the visible effect was a CP that looped inside
            # DMKFRE with free storage exhausted -- a wall I diagnosed at length
            # and reported, which the harness had manufactured.  Setting it to 16
            # moved the loop out of DMKFRE entirely.  The two sizes must match
            # until M5, or every ESA/390 measurement is of a different machine
            # from the one the milestone describes.  I-157.
            'ESA/390': [('ARCHMODE', 'ESA/390'), ('CPUMODEL', '3090'),
                        ('ECPSVM', 'NO'),        ('MAINSIZE', '16')]}[mode]
    if mb is not None:
        want = [(k, str(mb) if k == 'MAINSIZE' else v) for k, v in want]
    text = open(conf).read()
    for key, val in want:
        text = re.sub(r'(?m)^%s\s+\S+.*$' % key, '%-15s %s' % (key, val), text)
    open(conf, 'w').write(text)
    return mode


def boot_failed(log):
    """Did the machine reach CMS?  Read the log and say so, loudly.

    An rc cannot branch, so a boot race cannot be prevented -- but it can be
    DETECTED, and detection is what was missing.  A swallowed `CP DISC` leaves
    the machine at the OPERATOR console in CP mode, and from there every command
    the run issues comes back `?CP: <verb>`: 48 card reads, a VMFMAC and an
    `asmdmk` of 186 modules, all failing identically, in a log that scrolls
    convincingly for 25 minutes and contains nothing.  Three separate times in
    one day this project has been handed a plausible log from a run that did
    nothing -- a stale nucleus, a fall-through `.rc`, and this -- so the check
    belongs in the driver rather than in whoever is reading.

    Returns a reason string, or None if the boot looks good.  I-112.
    """
    try:
        text = open(log, errors='replace').read()
    except OSError as e:
        return 'log unreadable: %s' % e
    if '?CP: LOGON' in text:
        return ('LOGON was refused -- CP DISC was swallowed by the auto-logon '
                'storm and the machine is still OPERATOR, so CMS never started')
    if '?CP: READCARD' in text:
        return 'READCARD reached CP, not CMS -- the machine is not in CMS'
    if 'LOGON AT' not in text:
        return 'no "LOGON AT" in the log -- MAINT never logged on'
    return None


def arch_of(log):
    """The architecture mode Hercules actually reported for a run.

    Added 30 Sep after three diagnostics in a row were read as evidence while
    running in the WRONG mode.  A driver resets ARCHMODE to S/370 when it
    finishes, because the next build needs S/370; a diagnostic run afterwards
    that forgets to set ESA/390 IPLs the converted nucleus on a S/370, where it
    dies on its first converted instruction.  The symptom is not an error -- it
    is `PSW=00000000 40000000` (CPU stopped, no PSW loaded) and an instruction
    trace containing NOTHING, which reads exactly like "execution never reaches
    this range" and was taken for that twice.

    So the mode is read back from the log rather than assumed from the config,
    for the same reason `boot_failed` reads the boot back: the only trustworthy
    statement about a run is one the run itself made.  I-115.
    """
    import re
    try:
        text = open(log, errors='replace').read()
    except OSError as e:
        return 'log unreadable: %s' % e
    m = re.findall(r'architecture mode ([A-Za-z0-9/]+)', text)
    return m[-1] if m else None


def wrong_arch(log, want):
    """Reason string if `log` did not run in `want`, else None.  I-115."""
    got = arch_of(log)
    if got is None:
        return 'log never reported an architecture mode'
    if got != want:
        return 'ran in %s, not %s -- any trace or PSW from it is void' % (got, want)
    return None


def incomplete(ce, run):
    """Did the run do everything its own script asked for?  I-144.

    `w()` waits for Hercules to DISAPPEAR and returns success when it does, so it
    cannot tell "finished" from "killed".  On 1 October the process group was
    reaped 13 minutes into a `full` build, 15 card files of 104 read and no
    module assembled.  Had the driver survived that kill it would have gone on to
    `chk` and `asmchk`, found no diagnostics -- because there were no assemblies
    to produce any -- and printed a clean verdict on a build that did 14% of its
    work.  A FALSE PASS on the verification build for the whole DAT conversion,
    which is a worse outcome than any of the six earlier checks-that-cannot-fail,
    because those only cost time.

    Neither existing check looks at completeness: `boot_failed` reads the boot and
    `asmchk` reads diagnostic severity.  So compare the log against the SCRIPT
    rather than against an expectation -- the script is what the run was asked to
    do, and it is written by the same `mk` that wrote the log's inputs, so no
    number has to be remembered anywhere.

    Returns None if the run accounted for itself, or a sentence saying what is
    missing.
    """
    import os
    rc = os.path.join(ce, '%s.rc' % run)       # drive.py's copy of the script
    if not os.path.exists(rc):
        rc = os.path.join(ce, 'hercules.rc')
    lg = os.path.join(ce, '%s.log' % run)
    if not os.path.exists(rc) or not os.path.exists(lg):
        return 'no %s.log or hercules.rc to compare' % run
    want_cards = want_asm = want_vmfasm = 0
    for line in open(rc, errors='replace'):
        t = line.strip()
        if t.startswith('/readcard'):
            want_cards += 1
        elif t.startswith('/asmdmk'):
            want_asm += 1
        elif t.startswith('/vmfasm'):
            want_vmfasm += 1
    got_cards = got_asm = 0
    shut = False
    for line in open(lg, errors='replace'):
        if 'readcard' in line:
            got_cards += 1
        if 'asmdmk' in line:
            got_asm += 1
        if 'CP SHUTDOWN' in line.upper() or 'SYSTEM SHUTDOWN' in line.upper():
            shut = True
    # `?CP: VMFASM` means the command went to CP and CP did not know it -- the
    # virtual machine is in CP READ and CMS is not running, so EVERY command in
    # the script is being rejected and the run does nothing.  On 2 October a
    # whole slice ran this way: `?CP: LOGON`, `?CP: READCARD`, `?CP: VMFMAC`,
    # then ten `?CP: VMFASM`, a clean Hercules shutdown, and `chk` passed it,
    # because `boot_failed()` looks for a boot that did not happen rather than
    # for commands that were refused.  I-112's shape again -- 48 identical card
    # failures over 25 minutes -- and the third time a run has reported success
    # while doing nothing.  One rejected command is enough to void a run.
    # Only OUR commands count.  The first version voided any run containing
    # `?CP:` at all and would have thrown away a perfectly good one: CP's own
    # IPL dialogue produces `?CP: COLD` before the logon, which is noise, not
    # failure.  A check that is too strict destroys good evidence as surely as
    # one that is too lax accepts bad -- and I had just written this check to
    # catch a run that did nothing, then nearly used it to discard a run that
    # did everything.
    FATAL = ('LOGON', 'READCARD', 'CPACC', 'VMFMAC', 'VMFASM', 'VMFLOAD',
             'ACCESS', 'LINK', 'ERASE', 'COPYFILE')
    rejected = [line.strip() for line in open(lg, errors='replace')
                if '?CP:' in line
                and line.split('?CP:')[1].strip().split()[0].upper() in FATAL]
    if rejected:
        return ('%d command(s) were rejected by CP -- CMS is not running and '
                'the script is talking to CP READ, so nothing in this run '
                'happened; first was %r'
                % (len(rejected), rejected[0][-40:]))

    # Every readcard must have produced a `RDR FILE nnnn HAS BEEN READ`.  With
    # the pauses cut, this is what stands between a fast build and a silently
    # truncated deck.
    read_ok = sum(1 for line in open(lg, errors='replace')
                  if 'HAS BEEN READ' in line)
    if got_cards and read_ok < got_cards:
        return ('%d readcard(s) were issued and only %d file(s) reported HAS '
                'BEEN READ -- a card file was not fully read, so a deck may '
                'have been applied truncated; raise the pauses'
                % (got_cards, read_ok))
    if got_cards < want_cards:
        return ('the script asked for %d card files and the log shows %d -- the '
                'run did not finish, so every check after this one would be '
                'measuring a fraction of the work' % (want_cards, got_cards))
    # Count the PER-MODULE assemblies too.  The first version counted
    # `/readcard` and `/asmdmk` and not `/vmfasm`, which is the mechanism the
    # sliced build actually uses -- so it reported COMPLETE on a run reclaimed
    # after 15 of 19 modules.  Fourth false pass in three days, and this one from
    # the check written to stop the other three.  I-154.
    got_vmfasm = sum(1 for line in open(lg, errors='replace')
                     if 'ASMBLING' in line)
    if got_vmfasm < want_vmfasm:
        return ('the script asked for %d module assembly(s) and the log shows '
                '%d -- the run was cut short, so the modules after the last one '
                'named still hold their PREVIOUS object deck'
                % (want_vmfasm, got_vmfasm))

    if got_asm < want_asm:
        return ('the script asked for %d assembly pass(es) and the log shows %d'
                % (want_asm, got_asm))
    if want_asm and not shut:
        return ('every card was read and every assembly ran, but the log has no '
                'shutdown -- Hercules did not exit on its own, so the run may '
                'have been cut short after the last thing checked here')
    return None


def ipl_progress(ce, run, core=None):
    """One comparable line of "how far did CP get" for a size sweep.

    The same four measurements for every machine size, so the sizes can be
    compared rather than described.  Deliberately NOT a pass/fail: wall 16 is
    open, so every size is expected to end in the dispatcher's enabled wait and
    the interesting signal is whether each one gets that far by the same route.

      ccw     channel programs traced on the IPL volume -- the bulk of IPL work
      msgs    CP console messages, which until wall 16 falls means abends only
      logo    copies of the EBCDIC startup logo found in CP FREE storage, i.e.
              did CP build and queue its startup messages
      psw     final PSW, which says enabled wait vs abend wait vs running

    `core` is a savecore image covering free storage; without one the logo
    column reads `-` rather than `0`, because absent evidence and measured
    absence are different things and conflating them cost this project two
    wrong conclusions on 2 October (I-165, I-168).
    """
    import os
    import re
    lg = os.path.join(ce, '%s.log' % run)
    try:
        text = open(lg, errors='replace').read()
    except OSError as e:
        return 'no log: %s' % e
    ccw = len(re.findall(r'HHCCP048I', text))
    msgs = sorted(set(re.findall(r'DMK[A-Z]{3}[0-9]{3}[A-Z]', text)))
    psw = re.findall(r'^psw (sm=.*)$', text, re.M)
    logo = '-'
    if core and os.path.exists(core):
        d = open(core, 'rb').read()
        # EBCDIC 'VM/3', counted only in CP free storage: the nucleus's own
        # copies are template text and would be counted at every size.
        logo = d[0x40000:0x80000].count(b'\xe5\xd4\x61\xf3')
    return ('ccw=%-5d logo=%-3s msgs=%-28s psw=%s'
            % (ccw, logo, ','.join(msgs) or 'none', psw[-1] if psw else '?'))
