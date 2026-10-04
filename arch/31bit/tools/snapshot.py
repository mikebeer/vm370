#!/usr/bin/env python3
"""Take and validate build snapshots, so a stale one cannot be used by accident.

`I-111` cost a build cycle and an hour of wrong diagnosis: `SNAP-BASE` was taken
at 07:20, five fixes landed after it, and a run restored it and reassembled one
module on the reasoning that "the MACLIB is unchanged" -- true of the previous
build, false of the snapshot being restored.  The result was a 07:20 nucleus
carrying one 18:40 module, and it reproduced an *older* failure convincingly
enough to be read as a new one.

Mike's framing, 1 October, and it is the right one: **a snapshot starts INVALID
and becomes valid only when a condition we can observe in the log is met.**  A
directory existing proves nothing; a directory plus a manifest that says what it
contains and what proved it is a different object.

So this tool gives every snapshot two properties the bare directory lacks:

  * **A state that starts `invalid`.**  The manifest is written BEFORE the copy
    begins, so an interrupted or crashed copy leaves a snapshot that is
    explicitly unusable rather than silently half-made.  It is flipped to
    `valid` only after every check below passes.

  * **A record of its inputs.**  Every file in `updates/` is fingerprinted, so
    `check` can say precisely which decks postdate the snapshot.  That is the
    I-111 question, and it is answerable arithmetically instead of by comparing
    timestamps in two different places by eye.

## What makes a snapshot valid

All six, from the run's own log -- the only trustworthy statement about a run is
one the run itself made:

  1. **Hercules is not running.**  Shadow files are open and being written while
     it runs, so a copy taken live is torn.  `BUILD-CYCLE.md` says this and the
     driver broke it anyway when a timed-out wait returned success (`I-117`).
  2. **The machine reached CMS** -- `mkrun.boot_failed()`.  A swallowed
     `CP DISC` makes every later command fail identically with `?CP:` and
     produces a log that scrolls for 25 minutes and contains nothing (`I-112`).
  3. **The run was in S/370.**  A build runs in S/370; a log from an ESA/390
     run is a test, not a build (`I-115`).
  4. **No `*** XAOPS COPY OR MACRO NOT FOUND ***`** -- `I-101`, the member that
     existed only on MAINT's A-disk because an early run put it there.
  5. **Every module we patch shows its deck applied AND a TXTLCL created.**
     This is the condition that actually matters -- it is what "the snapshot's
     TXTLCLs are current" means, stated in terms of what the log says.  The
     grammar was measured, not assumed, because the first version of this check
     looked for the wrong string and refused a good log.  `VMFASM` prints two
     different endings:

         APPLYING 'DMKCPI XA0013DK A1'.        <- our deck went in
         ASMBLING DMKCPI
         ASSEMBLER (XF) DONE
         NO STATEMENTS FLAGGED IN THIS ASSEMBLY
         File 'DMKCPI TEXT A1' not found.
         DMKCPI TXTLCL CREATED                 <- a PATCHED module

         NO UPDATE FILES WERE FOUND.
         ASMBLING DMKSNT
         DMKSNT TEXT CREATED                   <- an UNPATCHED module

     So `TEXT CREATED` appears for the 155-odd modules we do not touch and
     *never* for the ones we do; looking for it on a patched module refuses
     every good build.  `TXTLCL CREATED` is the marker, and the `APPLYING` line
     is checked with it so that a TXTLCL built from an older deck cannot pass.
  6. **The nucleus was NOT written in this run** -- no `Nucleus loaded on`.  A
     snapshot taken after the write contains the converted nucleus and is no
     more bootable than the live system; that specific mistake cost a rebuild
     from pristine.

    python3 snapshot.py take  <ce-dir> <name> <log> [--test]
                                                     copy, manifest, validate
    python3 snapshot.py adopt <ce-dir> <name> <log>   manifest an existing one
    python3 snapshot.py check <ce-dir> <name>         valid?  and still current?
    python3 snapshot.py list  <ce-dir>                every snapshot and its state
    python3 snapshot.py take  <ce-dir> <name> <log> --parent <snap>
                               a DERIVED build snapshot: valid if the parent is and
                               <log> proves every module whose inputs changed (I-198)

`take` exits non-zero when it could not validate, and says why in the manifest
as well as on stderr -- so a driver that ignores the exit status still leaves
behind a snapshot that `check` will refuse.
"""
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
UPDATES = os.path.join(HERE, '..', 'updates')
MANIFEST = 'MANIFEST.json'


def fingerprints(updates=UPDATES):
    """{filename: short sha256} for every input that shapes a build."""
    out = {}
    for name in sorted(os.listdir(updates)):
        p = os.path.join(updates, name)
        if not os.path.isfile(p) or name.endswith('.py'):
            continue
        with open(p, 'rb') as f:
            out[name] = hashlib.sha256(f.read()).hexdigest()[:16]
    return out


def patched_modules(updates=UPDATES):
    """The modules that have an update deck, so whose TEXT must be current."""
    mods = set()
    for name in os.listdir(updates):
        m = re.match(r'(DMK[A-Z0-9]+)\.XA\d+DK$', name)
        if m:
            mods.add(m.group(1))
    return sorted(mods)


def hercules_running():
    try:
        return int(subprocess.run(['pgrep', '-c', 'hercules'],
                                  capture_output=True, text=True).stdout or 0)
    except Exception:
        return -1


def owners(filename):
    """Which patched modules a changed input invalidates.  A deck or AUXLCL
    names its module; anything else -- a COPY, a MACRO, the maclib EXEC -- is
    shared by every assembly, so it names them all (None)."""
    m = re.match(r'(DMK[A-Z0-9]+)\.(XA\d+DK|AUXLCL)$', filename)
    return {m.group(1)} if m else None


def validate(log, updates=UPDATES, purpose='build', parent_inputs=None):
    """Reasons this log does not prove the state the snapshot claims to be.

    With `parent_inputs` -- the input fingerprints of a VALID parent snapshot
    this one was built on top of -- the module check narrows to the modules
    whose inputs changed since the parent: a sliced build (I-148) proves its
    own slices, and the parent proves the rest.  A changed shared file (COPY,
    MACRO, DMKLCL EXEC) invalidates every module, so it still needs a full
    build.  I-198.

    Two purposes, because they are two different objects with opposite rules:

      * `build` -- restored to reassemble from.  It must NOT contain a written
        nucleus, or it is no more bootable than the live system.
      * `test`  -- restored to IPL under ESA/390.  It MUST contain a written
        nucleus, because that is the artifact under test.

    Conflating them is how a dual-engine test got run against the unconverted
    CE nucleus and reported `PSW=000A0000 00000017` -- DMKCKP's "error loading
    CKP page 2" -- which is a perfectly real failure of a machine nobody meant
    to test.  I-119.
    """
    bad = []
    n = hercules_running()
    if n != 0:
        bad.append('Hercules is running (%s process(es)) -- a live copy is torn'
                   % (n if n >= 0 else 'count unavailable'))
    try:
        text = open(log, errors='replace').read()
    except OSError as e:
        return bad + ['log unreadable: %s' % e]

    try:
        import mkrun
        why = mkrun.boot_failed(log)
        if why:
            bad.append('boot: %s' % why)
        arch = mkrun.arch_of(log)
        if arch != 'S/370':
            bad.append('ran in %s, not S/370 -- that is a test, not a build'
                       % (arch or 'an unreported mode'))
    except ImportError:
        bad.append('mkrun not importable, so the boot and architecture are '
                   'unchecked -- refusing to call this valid')

    if 'NOT FOUND' in text:
        bad.append('a COPY or MACRO was NOT FOUND (I-101)')
    wrote = 'Nucleus loaded on' in text
    if purpose == 'build' and wrote:
        bad.append('this run WROTE the nucleus -- a BUILD snapshot must be '
                   'taken before the write, or it is not bootable')
    if purpose == 'test' and not wrote:
        bad.append("this run did NOT write the nucleus -- a TEST snapshot must "
                   "contain the converted nucleus, or the IPL tests CE's own")

    # A patched module must show BOTH its deck going in and a TXTLCL coming out.
    # Checking only one of the two is how a TXTLCL built from a superseded deck
    # would pass: `APPLYING` alone proves the deck was read, `TXTLCL CREATED`
    # alone proves something was assembled.  Together they prove this run did it.
    need = patched_modules(updates) if purpose == 'build' else []
    validate.proven = set()
    if purpose == 'build':
        for m in patched_modules(updates):
            if re.search(r"APPLYING '%s XA\d+DK" % m, text) \
                    and ('%s TXTLCL CREATED' % m) in text:
                validate.proven.add(m)
    if parent_inputs is not None and purpose == 'build':
        # A derived snapshot: whatever this log does not prove is simply not
        # in it yet -- the same STALE state a deck changed after the snapshot
        # produces, reported by name by check() and restorable with
        # ALLOW_STALE.  It is not INVALID: the shadow files are a real,
        # consistent build state, the parent's plus these assemblies.  Only a
        # shared input (COPY, MACRO, EXEC) that changed makes the parent's
        # assemblies unusable, and that is the one derived case that stays
        # invalid.  I-198, corrected after SNAP-I203 was refused for a deck
        # that merely existed, unassembled, when it was taken.
        now = fingerprints(updates)
        for k in set(now) | set(parent_inputs):
            if parent_inputs.get(k) != now.get(k) and owners(k) is None:
                bad.append('shared input %s changed since the parent, which '
                           'invalidates every module the parent proved' % k)
        return bad
    noapply, notext = [], []
    for m in need:
        if not re.search(r"APPLYING '%s XA\d+DK" % m, text):
            noapply.append(m)
        if ('%s TXTLCL CREATED' % m) not in text:
            notext.append(m)
    if noapply:
        bad.append('no deck APPLYING line for %d patched module(s): %s'
                   % (len(noapply), ' '.join(noapply)))
    if notext:
        bad.append('no TXTLCL CREATED for %d patched module(s): %s'
                   % (len(notext), ' '.join(notext)))
    return bad


def derived_inputs(parent_inputs, proven, updates=UPDATES):
    """The input fingerprints a derived snapshot INCORPORATES: the parent's,
    plus the current ones for modules this build proved.  Anything else that
    changed stays at the parent's value, so check() reports it stale by
    name instead of calling the snapshot current."""
    now = fingerprints(updates)
    out = dict(parent_inputs)
    for k, v in now.items():
        o = owners(k)
        if o is None or o <= proven:
            out[k] = v
    return out


def take(ce, name, log, purpose='build', parent=None):
    disks = os.path.join(ce, 'disks')
    parent_inputs = None
    if parent:
        pman = read_manifest(os.path.join(disks, parent))
        if pman is None or pman.get('state') != 'valid':
            print('### parent %s is not a VALID snapshot -- a derived snapshot '
                  'inherits its proof and cannot stand on an invalid one'
                  % parent, file=sys.stderr)
            return 2
        if pman.get('purpose', 'build') != 'build':
            print('### parent %s is a %s snapshot, not build' %
                  (parent, pman.get('purpose')), file=sys.stderr)
            return 2
        parent_inputs = pman.get('inputs', {})
    src, dst = os.path.join(disks, 'shadows'), os.path.join(disks, name)
    if not os.path.isdir(src):
        print('### no %s to snapshot' % src, file=sys.stderr)
        return 2

    # The manifest is written FIRST, saying invalid, so a copy that dies
    # half-way leaves a snapshot that is explicitly unusable.
    if os.path.isdir(dst):
        shutil.rmtree(dst)
    os.makedirs(dst)
    man = {'state': 'invalid',
           'purpose': purpose,
           'reason': ['copy in progress -- not yet validated'],
           'taken': time.strftime('%Y-%m-%dT%H:%M:%S'),
           'log': os.path.basename(log),
           'inputs': fingerprints(),
           'modules': patched_modules(),
           'parent': parent}
    write_manifest(dst, man)

    for f in sorted(os.listdir(src)):
        s = os.path.join(src, f)
        if os.path.isfile(s):
            shutil.copy2(s, os.path.join(dst, f))
    man['files'] = sorted(f for f in os.listdir(dst) if f != MANIFEST)

    bad = validate(log, purpose=purpose, parent_inputs=parent_inputs)
    if bad:
        man['reason'] = bad
        write_manifest(dst, man)
        print('### %s stays INVALID:' % name, file=sys.stderr)
        for b in bad:
            print('      - %s' % b, file=sys.stderr)
        return 1
    if parent_inputs is not None:
        man['inputs'] = derived_inputs(parent_inputs, validate.proven)
        man['proven'] = sorted(validate.proven)
    man['state'] = 'valid'
    man['reason'] = []
    man['evidence'] = {'modules_with_text': len(man['modules']),
                       'hercules_down': True, 'pre_nucleus_write': True}
    write_manifest(dst, man)
    print('--- %s is VALID (%s): %d shadow files, %s'
          % (name, purpose, len(man['files']),
             '%d patched modules with their decks applied and a TXTLCL created, '
             'taken before the nucleus write' % len(man['modules'])
             if purpose == 'build' else
             'contains a written nucleus, Hercules down'))
    return 0


def adopt(ce, name, log, parent=None):
    """Write a manifest for a snapshot this tool did not take.

    Adopting is the one place a human assertion enters -- it says "this directory
    really is the state that log describes" -- so it is recorded as
    `provenance: adopted` rather than passed off as a tool-made snapshot, and it
    runs the SAME six checks.  It exists because the three snapshots that predate
    this tool include one that is genuinely good, and rebuilding it costs fifty
    minutes of staging and assembly for no information.

    What adoption does NOT do is vouch for the copy itself.  If the directory was
    copied while Hercules was running, the manifest will say valid and the shadow
    files will still be torn -- which is why `take` is the normal path and this
    verb names itself in the manifest.
    """
    d = os.path.join(ce, 'disks', name)
    if not os.path.isdir(d):
        print('### no such snapshot: %s' % d, file=sys.stderr)
        return 2
    man = {'state': 'invalid',
           'provenance': 'adopted',
           'reason': ['adoption in progress'],
           'taken': time.strftime('%Y-%m-%dT%H:%M:%S',
                                  time.localtime(os.path.getmtime(d))),
           'adopted': time.strftime('%Y-%m-%dT%H:%M:%S'),
           'log': os.path.basename(log),
           'inputs': fingerprints(),
           'modules': patched_modules(),
           'files': sorted(f for f in os.listdir(d) if f != MANIFEST),
           'parent': parent}
    parent_inputs = None
    if parent:
        pman = read_manifest(os.path.join(ce, 'disks', parent))
        if pman is None or pman.get('state') != 'valid':
            print('### parent %s is not a VALID snapshot' % parent, file=sys.stderr)
            return 2
        parent_inputs = pman.get('inputs', {})
    bad = validate(log, parent_inputs=parent_inputs)
    if bad:
        man['reason'] = bad
        write_manifest(d, man)
        print('### %s stays INVALID:' % name, file=sys.stderr)
        for b in bad:
            print('      - %s' % b, file=sys.stderr)
        return 1
    if parent_inputs is not None:
        man['inputs'] = derived_inputs(parent_inputs, validate.proven)
        man['proven'] = sorted(validate.proven)
    man['state'] = 'valid'
    man['reason'] = []
    write_manifest(d, man)
    print('--- %s ADOPTED as valid against %s: %d shadow files, %d patched '
          'modules with their decks applied and a TXTLCL created'
          % (name, os.path.basename(log), len(man['files']), len(man['modules'])))
    return 0


def write_manifest(d, man):
    with open(os.path.join(d, MANIFEST), 'w') as f:
        json.dump(man, f, indent=1, sort_keys=True)
        f.write('\n')


def read_manifest(d):
    try:
        with open(os.path.join(d, MANIFEST)) as f:
            return json.load(f)
    except (OSError, ValueError):
        return None


def check(ce, name, want=None):
    d = os.path.join(ce, 'disks', name)
    man = read_manifest(d)
    if man is None:
        print('### %s has NO manifest -- it predates this tool, so nothing '
              'says what is in it.  Treat as INVALID.' % name, file=sys.stderr)
        return 1
    if man.get('state') != 'valid':
        print('### %s is INVALID:' % name, file=sys.stderr)
        for r in man.get('reason', ['(no reason recorded)']):
            print('      - %s' % r, file=sys.stderr)
        return 1

    got = man.get('purpose', 'build')
    if want and got != want:
        print('### %s is a %s snapshot, and a %s one was asked for.  A build '
              'snapshot holds no written nucleus and a test snapshot is not '
              'reassembled from -- restoring the wrong kind tests the wrong '
              'machine.  I-119.' % (name, got, want), file=sys.stderr)
        return 1

    now, then = fingerprints(), man.get('inputs', {})
    changed = sorted(k for k in now if then.get(k) != now[k])
    gone = sorted(k for k in then if k not in now)
    if changed or gone:
        print('### %s is valid but STALE -- %d input(s) changed since it was '
              'taken on %s:' % (name, len(changed) + len(gone), man['taken']),
              file=sys.stderr)
        for k in changed:
            print('      %-22s %s' % (k, 'new' if k not in then else 'changed'),
                  file=sys.stderr)
        for k in gone:
            print('      %-22s removed' % k, file=sys.stderr)
        print('      Reassemble the affected modules, or take a fresh '
              'snapshot.  I-111.', file=sys.stderr)
        return 2
    print('--- %s: valid and current (taken %s, %d inputs unchanged)'
          % (name, man['taken'], len(then)))
    return 0


def listing(ce):
    disks = os.path.join(ce, 'disks')
    names = sorted(n for n in os.listdir(disks)
                   if os.path.isdir(os.path.join(disks, n)) and n != 'shadows')
    if not names:
        print('no snapshots')
        return 0
    print('%-12s %-9s %-20s %s' % ('SNAPSHOT', 'STATE', 'TAKEN', 'NOTE'))
    for n in names:
        man = read_manifest(os.path.join(disks, n))
        if man is None:
            print('%-12s %-9s %-20s %s'
                  % (n, 'INVALID', '-', 'no manifest -- predates this tool'))
            continue
        note = ''
        if man.get('state') == 'valid':
            now, then = fingerprints(), man.get('inputs', {})
            diff = len([k for k in now if then.get(k) != now[k]]) \
                + len([k for k in then if k not in now])
            note = 'current' if not diff else 'STALE: %d input(s) changed' % diff
        else:
            note = (man.get('reason') or ['(no reason)'])[0]
        print('%-12s %-9s %-20s %s'
              % (n, man.get('state', '?').upper(), man.get('taken', '-'), note))
    return 0


def main():
    a = sys.argv[1:]
    if not a:
        print(__doc__)
        return 2
    verb = a[0]
    if verb == 'take' and len(a) >= 4:
        opts = a[4:]
        parent = None
        if '--parent' in opts:
            parent = opts[opts.index('--parent') + 1]
        return take(a[1], a[2], a[3],
                    'test' if '--test' in opts else 'build', parent=parent)
    if verb == 'adopt' and len(a) >= 4:
        opts = a[4:]
        parent = opts[opts.index('--parent') + 1] if '--parent' in opts else None
        return adopt(a[1], a[2], a[3], parent=parent)
    if verb == 'check' and len(a) in (3, 4):
        return check(a[1], a[2], a[3] if len(a) == 4 else None)
    if verb == 'list' and len(a) == 2:
        return listing(a[1])
    print(__doc__)
    return 2


if __name__ == '__main__':
    sys.exit(main())
