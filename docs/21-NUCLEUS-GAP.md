# What stands between here and a CP nucleus

> **Status, 4 October 2026.** All four gap items are closed. The nucleus links, IPLs from DASD (M3a, 3 October) and runs CMS for two concurrent users (M3b, M3c, 4 October) — [30-STATE.md](30-STATE.md), [28-IPL-WALLS.md](28-IPL-WALLS.md) walls 1–29. The nine modules broken by the `PSA` rename all assemble and run; `VMFLOAD`, `LDFASM` and the configuration modules are driven by `build.sh` (`I-194` found that CE's `HDK` modules had never been reassembled, hence the `LDFASM` step). `DMKBTS` is `R-24`, not realised: the sourceless `TEXT` IPLs and runs CMS ([12-RISKS.md](12-RISKS.md)). The load list measured here was the wrong one — `094/CPLOAD.EXEC` (183 modules) is what `VMFLOAD` reads, not `194`'s 172 (`I-66`, [13-ISSUES.md](13-ISSUES.md)). The `ASMDMK` baseline and the pause lesson (`I-33`) stand; fixed-pause runs have since been replaced by `drive.py`, which polls the log.

27 September 2026. Measured, not estimated — by running CE's own `ASMDMK` across
every module it lists and reading `CPLOAD.EXEC`, the nucleus load list.

**The assembly question is closed. What remains is a link step nobody here has
ever run, nine modules we broke on purpose, and three generated configuration
modules nobody has looked at.**

## `ASMDMK DMKHRC`: 185 of 186 clean

`ASMDMK.EXEC` runs `VMFASM` over 186 members. Run against `DMKHRC` — whose
control file excludes `DMKLCL` from its `MACS` line and declares no `LCL AUXLCL`
level, so the `PSA` deck and `DMKLCL MACLIB` are invisible to it, giving a true
pre-change baseline:

| | |
|---|---|
| modules listed | 186 |
| **assembled** | **186** |
| `NO STATEMENTS FLAGGED` | **185** |
| flagged | **1** — `DMKRIO`, severity 4 |
| TEXT decks produced | **186** |

It took about 90 seconds of virtual CPU.

**The one flagged module is not a conversion problem.** `DMKRIO` is the generated
real-I/O configuration module, and all four diagnostics are the same MNOTE:

    RDEVICE ADDRESS=(170,16),DEVTYPE=3375,CLASS=DASD
        4,UNSUPPORTED DEVICE TYPE
    RDEVICE ADDRESS=(190,16),DEVTYPE=3390,CLASS=DASD
        4,UNSUPPORTED DEVICE TYPE

CE's site configuration declares 3375 and 3390 DASD that the `RDEVICE` macro does
not know. Severity 4, and **`DMKRIO TEXT CREATED`** — `VMFASM` reports it as an
error because the return code is non-zero, but the deck exists and the nucleus can
link. A pre-existing CE wrinkle, recorded as `I-34`.

**So essentially all of CP assembles on CE's own Assembler XF**, which retires the
last of the doubt `10-BUILD-ENVIRONMENT.md` created with its 132-of-201 figure —
a figure that was z390's all along
([`16-NATIVE-BASELINE.md`](16-NATIVE-BASELINE.md)).

## The nucleus load list

`194/CPLOAD.EXEC` lists **174 entries**: 172 modules, `LOADER` (`DMKLD00E`), and
a terminating `LDT DMKSAVNC` card that names the routine which writes the nucleus
page image.

| | |
|---|---|
| load-list modules | 172 |
| covered by `ASMDMK` | **171** |
| **not covered, and with no source anywhere** | **`DMKBTS`** |

`DMKBTS` is an *active* line in the load list. It has no `.ASSEMBLE` member in
`source/cp`, no deck in `maintenance/files`, and its only other mention in the
tree is a **commented-out** `SYM DMKBTS` line in `DMKSYM`, added by CE's
`HRC104DK`. Since CE ships a nucleus that IPLs, `VMFLOAD` evidently tolerates a
missing member. Recorded as `I-35`; not a blocker, but not understood either.

And 15 source members are outside `ASMDMK`, built by other EXECs — the `HDK*`
community modules by `LDFASM.EXEC`, plus `DMKGR[UVX]`, `DMKPE[CDQ]`, `MSSVS1/2`,
`DMTSYS`, `VRSIZE`. **This matters**: `DMKIOS` carries
`EXTRN HDKD7CIO` from CE's `HRC065DK` deck, so `HDKD7C` is a genuine link
dependency of the nucleus that `ASMDMK` alone does not produce. A nucleus build
needs `LDFASM` as well.

## So the gap, in four items

**1. Nine modules we broke on purpose.** The `PSA` rename leaves `DMKPRV`,
`DMKIOT`, `DMKCCH`, `DMKDSP`, `DMKDMP`, `DMKIOG`, `DMKEIG`, `DMKVMI` and
`DMKCKP` failing to assemble — every one I/O-interrupt or channel-error code, and
**all nine are in the nucleus load list**, including `DMKDMP`, which is not
standalone-only as I had assumed.

For a nucleus that **links**, these only need to *assemble*. None is on M1's
console path, and `R-03`'s own mitigation is to stub every logout site to
permanent error. That is mechanical: `INTTIO` → `IOSCHNO` at twenty sites, and
the `S370*` references stubbed or branched around.

**2. `VMFLOAD`, never run here.** `VMFLOAD CPLOAD DMKLCL` punches a loader deck
which `DMKLD00E` loads and `LDT DMKSAVNC` terminates by writing the nucleus page
image. Two unknowns: whether `VMFLOAD` resolves `TXTLCL` for modules carrying our
level while taking `TXTHRC` or `TEXT` for the rest — it reads the same control
file so it should, but `BUILDUTL.EXEC` hard-codes `DMKDIR TXTHRC A`, so the
assumption needs testing — and `DMKBTS`.

**3. `LDFASM` for the `HDK*` modules**, per the `EXTRN` above.

**4. The three generated configuration modules.** `DMKRIO` is in the load list;
`DMKSYS` and `DMKSNT` are its siblings. All three are CE-only and site-generated,
and `DMKRIO` describes the real I/O configuration — which is exactly what changes
when devices become subchannels. Entirely unexamined so far, and the place where
the device-address-to-subchannel mapping
([`20-DMKIOS-DESIGN.md`](20-DMKIOS-DESIGN.md)) will have to be reconciled with
the configuration that declares the devices.

## The distinction that matters

**A nucleus that links is close.** Items 1–3, and item 1 only to the level of
"assembles". Days.

**A nucleus that IPLs is M1 → M2 → M3a**, because `DMKCKP` and `DMKSAV` — two of
the nine — *are* the IPL read path, and they carry 70 of the 82 DAT references M1
deliberately avoided under strategy B. That is `R-09`, and it is why M3a exists as
a milestone in its own right.

Worth being explicit, because "we have a nucleus" would be easy to over-read: a
linked nucleus that has never been IPL'd proves the TEXT decks are mutually
consistent and nothing more.

## An operational lesson from this run

The `.rc` for this run carried `pause 3600` twice plus `pause 900` after
`asmdmk`, to be sure of covering an assembly I had estimated at 100 minutes. It
took 90 seconds. Hercules then sat idle for the remaining two hours of pauses
before reaching `/cp shutdown`, and with no panel tty, no `HTTPPORT` in the
config and only a 3270 port to talk to, **there is no way to shorten a pause once
the script is running** — short of killing the process, which is the one thing
that must not happen.

**Size pauses to the work and poll from outside**, rather than padding for the
worst case. The log is on the host side and can be watched continuously, so a
short pause with an outside poll loses nothing. `I-33`.
