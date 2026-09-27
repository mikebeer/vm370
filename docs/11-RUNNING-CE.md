# Running VM/370 CE in the container — and what it closed

27 September 2026. `10-BUILD-ENVIRONMENT.md` split the work into three tiers
and concluded that **tier 3 — the native CE build — was the one thing this
environment could not provide.** That is no longer true. VM/370 CE now IPLs
headless here, CMS runs, MAINT logs on, and files are readable.

Two things followed immediately: a long-open question was answered, and it
answered in a way that **inverted a conclusion**.

## It runs

The distribution's own `vm370ce.conf` works unchanged against Hercules 3.13
built from source (`10-BUILD-ENVIRONMENT.md` has the build notes). No X, no
3270 emulator, no terminal.

    VM/370 Community Edition Version  1 Release  1.2
    DMKCPI971I System is Uniprocessor generated
    DMKUDR476I System Directory loaded from volume VM50-1
    DMKCPI957I Storage size = 16384 K, Nucleus = 336 K,
               Dynamic Paging = 14788 K, Trace Table = 240 K

### The mechanism: `/` in the `.rc` file

Hercules sends any `.rc` line beginning with `/` to the integrated console at
`0009`, and the log shows it going in as `/(0009) …`. That is the whole trick —
CP and CMS can be driven from a script with no interactive terminal at all.

    panrate 1000
    pause 3
    ipl 6A1
    pause 20
    /warm                    answer CP's start prompt
    pause 25
    /cp disc                 disconnect OPERATOR
    pause 6
    /logon maint cpcms       log MAINT on at the same console
    pause 22
    /                        blank line past CMS's first read
    pause 10
    /type user direct a
    pause 45
    /cp shutdown
    pause 10
    exit

`/cp disc` then `/logon maint cpcms` comes from the distribution's own
`batch/autologmaint.rc`, which is also where MAINT's password is published.

### Four things that cost a cycle each

**Shut CP down cleanly.** `/cp shutdown`, then Hercules `exit` — never a
`timeout` that kills the process. A killed run leaves the warm-start area
inconsistent and the next IPL has to cold-start. The clean path prints
`DMKCKP960I System WARM START data saved`.

**A fresh extraction has no warm-start data**, so the first IPL must answer
`cold` (or `cold drain`); `warm` returns
`DMKWRM920I NO WARM START DATA; CKPT START FOR RETRY` and re-prompts. After one
clean shutdown, `warm` works.

**The disks come out of the zip read-only**, so Hercules opens them
`readonly` and a warm start cannot write its checkpoint. `chmod u+w` on
`disks/` and `io/` first. This is a disposable copy; the original zip stays
untouched.

**Timing is real and unforgiving.** Commands sent before CP finishes
initialising are swallowed — `?CP: LISTFILE` means CP got a CMS command because
the virtual machine was not running CMS yet. `DMKCPI966I Initialization
complete` has to have appeared before the first `/logon`.

**And OPERATOR cannot IPL CMS.** Its directory entry gives it 2 MB, while CE's
CMS saved system has shared segments at 15.5 MB, so the segments fall outside
the machine. `cp define storage 16m` first, or log on as a user that already has
15 MB — which is what MAINT is for.

## What it closed: `USER DIRECT`, and segment 15 is not benign

`USER DIRECT A1` is on MAINT's 191 disk, and `04-SHARED-SEGMENTS.md` had one
open caveat that needed it:

> The private-page analysis uses *saved* pages, not run-time storage. A virtual
> machine defined with more storage than its saved system uses could have
> private pages anywhere below its size, including inside segment 14 or 15.
> **This is the one check that could make segment 15 stop being benign.**

It does. The `USER` statement carries default and maximum storage, and across
44 entries:

| Default size | Machines |
|---|---|
| 15 MB | **8** — `ASSIST`, `BREXX`, `FORTRAN`, `CMSUSER`, `GCCCMS`, `MAINT`, `MAINTC`, `WAKEUP` |
| 14 MB | 2 — `KICKS`, `MECAFF` |
| 16 MB | 1 — `XNET` |
| 8 MB | 8 |
| 2 MB | 11 |
| 4 MB | 2 |
| 512 KB | 2 — `CMS67`, `CMS67M` |

**Twenty-one machines can be defined up to 16 MB.** So private storage
routinely occupies 14–16 MB — precisely where CMS's shared segments sit
(`CMSSEG` at 15.0 MB, `CMS` at 15.5–15.7 MB).

Under VM/370-style segment sharing at 1 MB, making segment 15 common would
expose the private storage of most machines on the system. **The collision is
real, and `04`'s "segment 15 is the false alarm" was wrong.**

### Which makes the CP-67 route necessary, not preferable

`05-CP67-PRIOR-ART.md` argued for frame-level sharing on grounds of elegance
and precedent, and `09-frame-sharing.rc` proved it works. This makes it the
**only** viable route: frame-level sharing never marks a segment common, so the
overlap simply does not arise. An open caveat closing against the alternative
is the strongest form of confirmation available.

Two smaller observations from the same file. `CMS67 512K 8M` and
`CMS67M 512K 16M` — CP-67's CMS runs in a **512 KB** machine, consistent with
its named saved system being 19 pages and sharing nothing
(`../heritage/cp67/README.md`). And MAINT's `15M 16M` is why MAINT can IPL CMS
where OPERATOR cannot.

## What it unlocks: tier 3

`10-BUILD-ENVIRONMENT.md` said the native build — CMS, `ASSEMBLE`, `LOAD`,
`GENMOD`, the disk images — was needed to turn converted source into TEXT decks
and a bootable nucleus, and was the one tier unavailable here. **It is available
now.** MAINT is logged on with `CMSDSK 190`, `MNT19E 19E` and `MNT29D 19D`
accessed, which is where the toolchain lives.

So the "development here, integration with Adrian" split in that document is
obsolete. Both can happen in this container. What still needs Adrian is the
pinned OSMACRO/DOSMACRO libraries for the ~24 modules that reference OS/VS
macros — and possibly not even that, if those libraries are on one of the CE
disks.

**That is the M1 blocker gone.** M1 step 1 is `MACLIB GEN XALIB XAOPS` and step
3 is "assemble the nine modules and collect the errors". Both are now
executable.

## Caution

This runs against a **writable copy** of the CE disks. Every earlier warning in
this repository about bare-metal tests and writable packs applies with more
force now, because CP is genuinely writing: spool, paging, the warm-start area.
Work on a disposable extraction, keep the distribution zip pristine, and shut
down cleanly every time.
