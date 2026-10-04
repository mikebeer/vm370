# Building CMS, and why the loader must stay S/370

> **Status, 4 October 2026.** Confirmed in practice: CE's unmodified CMS IPLs and reaches `Ready;` under the converted CP, by `IPL 190` (M3b) and by `IPL CMS` with two concurrent sharers (M3c), EXEC2 and REXX running ([30-STATE.md](30-STATE.md), [33-FRAME-SHARING.md](33-FRAME-SHARING.md)). CMS needed no conversion, as predicted; what it did need was CP-side simulation that this note did not foresee — guest `SIO`/`TIO`/`SSK`/`ISK` are *operation* exceptions on ESA/390, not privileged-op, so `DMKPRV` had to be taught to route them (`I-199`), and its key simulation needed the ESA/390 table geometry (`I-200`, `I-202`; [28-IPL-WALLS.md](28-IPL-WALLS.md) walls 26–28). The loader stays S/370 and `DMKSAVNC`'s five sites stay `SIO`/`TIO`, exactly as argued. The build sequence shown is what `build.sh write` does. "M5 would need" stands, with one correction: M5 needs M2's AMODE 31 first, because CP at AMODE 24 aliases guest storage above 16 MB onto the low 16 MB (`I-208`); `DEF STOR 32M/64M` is accepted but only as bookkeeping.

Mike's question — what does creating CMS need, when CP and CMS are built at the
same time — has a short answer and a consequence that decides a piece of scope.

**Short answer: nothing new.** CMS needs no conversion for M1 through M4, and the
reason is worth being precise about, because "nothing" is the kind of claim that
is usually wrong.

## The two builds are the same build, twice

    094/CPLOAD.EXEC    &1 &2 &3 DMKLD00E LOADER      <- line 2
                       ... 177 CP modules ...
                       &1 &2 &3 LDT    DMKSAVNC

    093/CMSLOAD.EXEC   &1 &2 &3 DMKLD00E LOADER      <- line 2
                       ... 74 CMS modules ...
                       &1 &2 &3 LDT    DMSINIW

The same loader, with the **same SHA-256** in the catalogue
(`3081bc0156f19e…`), prepended to both lists. Only the terminator differs:
`DMKSAVNC` writes the CP nucleus, `DMSINIW` writes the CMS one.

## Why CMS needs no conversion

Three checks, all of which had to hold:

**CMS references none of the renamed PSA fields.** Measured across all 175
`.ASSEMBLE` members of `source/cms`: zero occurrences of `INTTIO`, `CHANID`,
`IOELPNTR`, `ECSWLOG` or `ECSWBYT3`. The rename that broke twelve CP modules
breaks no CMS module at all.

**CMS's S/370-only instructions are guest instructions, not real ones.** CMS
issues `TIO`×16, `SIO`×12, `SSK`×7 and `ISK`×1. None of them reaches hardware:
CMS runs in a virtual machine which CP presents as an S/370 machine through M4
(`I-36`), so CP **simulates** every one — `DMKPRV` for the privileged
instructions, `DMKCCW` for the channel programs it translates. That is exactly
the work the guest-lowcore decks were for: `DMKDSP`'s `G370TIO`, `DMKPRV`'s
`S370CHID`, `DMKCCH`'s `S370ECSW-PSA(4,R2)`.

**Nothing in the CMS build path runs on the converted machine.** The loader and
`DMSINIW` both run in the build IPL, in S/370 mode, on the unconverted system.

## The consequence: DMKLD00E must not be converted

This is a stronger argument than the one that stopped me first.

`DMKLD00E` is awkward to convert — 19 sites, no PSA symbols, and base registers
that shift through `USING RELDR,15,9`, `RELDR,12,9` and `RELDR,4,9`, so a module
larger than 8 KB with no single location addressable from every site. That was
reason enough to hesitate.

The real reason is simpler: **the loader is shared.** Converting it to ESA/390
would break the CMS nucleus build as well as the CP one, and CMS must keep being
built in S/370 form because it is an S/370 guest. So the loader stays S/370, and
its 19 channel sites leave the conversion scope entirely.

## Which makes the build sequence explicit

    1.  Hercules in S/370 mode
        IPL the standalone deck: DMKLD00E + CP TEXT + LDT DMKSAVNC
          -> DMKSAVNC writes the ESA/390 CP nucleus to DASD
        IPL the standalone deck: DMKLD00E + CMS TEXT + LDT DMSINIW
          -> DMSINIW writes the S/370 CMS nucleus

    2.  Hercules in ESA/390 mode
        IPL the CP nucleus, which reads itself in through DMKSAV's IPL entry
          -> CP runs, and runs CMS as an S/370 guest

Nothing in step 1 executes an ESA/390 instruction. Nothing in step 2 executes
the loader.

## And it splits DMKSAV down the middle

`DMKSAV` is the one module that appears on both sides, because it is both a
nucleus module and the `LDT` target:

| Entry | Seq | Runs | Architecture | Sites |
|---|---|---|---|---|
| `DMKSAV` CSECT | 00129000 | target machine, at IPL | **ESA/390** | 6 |
| `DMKSAVRS` | 00205000 | target machine, restore | **ESA/390** | — |
| `DMKSAVNC` | 00380000 | build machine, writes the nucleus | **S/370** | 5 |

So only six of its eleven channel sites are converted, and `DMKSAVNC`'s five stay
`SIO`/`TIO`. A module holding both forms is not a contradiction: the two paths
are never executed in the same IPL. `I-59`.

## What M5 would need

M5 is CMS in a 31-bit virtual machine, and that is where all of this changes:

* CMS itself converted — its 28 channel sites and 8 key sites become real work,
  plus whatever DAT assumptions it holds.
* `DMKPRV` taught to simulate `ISKE`, `SSKE` and `RRBE`, which it cannot today:
  its repertoire is X'08', X'09' and X'B213' (`I-46`).
* CP giving the guest a 31-bit mode, which is the guest-PSA work the `S370*`
  renames deliberately left in S/370 form.

None of that is needed to reach M3a or M4, which is the useful part of the
answer: CMS comes along for free until the point where it is meant to change.
