# M1: the work list

> **Status, 4 October 2026.** M1 is done (3 October): CP IPLs in ESA/390 mode
> and answers a typed command, against the tightened criterion in
> [../arch/31bit/README.md](../arch/31bit/README.md), not the "one console
> message" this list opens with. It was done by **strategy A** — IPL from DASD,
> as CE does — not the strategy B chosen below; the choice was never recorded
> at the time and is accounted for in `01-PROPOSAL.md` §6 and
> [30-STATE.md](30-STATE.md). Steps 4–6 became the twenty-two walls of
> [28-IPL-WALLS.md](28-IPL-WALLS.md) (`DMKIOS XA0004DK`, `DMKCNS XA0021DK`,
> `DMKCPI XA0013DK`, `DMKCKP`, `DMKSAV`, …). Everything in "What M1 explicitly
> defers" has since been done except AMODE 31: CP still runs 24-bit, so guest
> storage above 16 MB aliases onto the low 16 MB (`I-208`, the open M2 work;
> [13-ISSUES.md](13-ISSUES.md)). The lowcore analysis and the per-module
> table stand as the measurement they were.

26 September 2026. M1 is *CP IPLs in ESA/390 mode and writes one console
message* — DAT off, no paging, no guests. This turns that sentence into an
ordered work list with measured quantities, because nothing else in the plan
unblocks M1 and it is the first milestone that involves changing CP.

Measurements from `../arch/31bit/tools/archdep.py`, run against Adrian's
tree. Every count is a **floor** — the parser cannot see macro-generated
instructions, and `TRANS` alone hides an `LCTL`, an `LRA` and a branch per
site.

## The chain, from the source's own prologues

    DMKLDR  ---LDT card--->  DMKSAVNC     writes a page image of the nucleus
    IPL  --->  DMKCKP  ---BALR--->  DMKSAVRS   restores that image
    DMKSAVRS  ---GOTO--->  DMKCPINT   (DMKCPI, GPR10 = IPL device address)
    DMKCPI  --->  DMKQCNWT  --->  DMKCNSIC  --->  DMKIOS  --->  interrupt
                                                                  |
                                                            DMKCNSIN

`DMKCPI`'s prologue names `DMKQCNWT` as "WRITE MESSAGES TO OPERATOR'S
CONSOLE", so that call is M1's target: everything before it must work,
nothing after it matters yet.

## Two strategies, and the measured difference

**A. IPL from DASD, as CE does today.** Requires `DMKCKP` and `DMKSAV` to
work, because they are what reads the nucleus in.

**B. Load the nucleus with `loadcore` and `restart` into `DMKCPINT`.** The
method every test in this repository already uses, and the one Adrian's
`wide/` uses. It skips the IPL read entirely.

| | modules | lines | S/370 I/O | arch insns | DAT refs | CAW/CSW |
|---|---|---|---|---|---|---|
| **B: `loadcore`** | 9 | 13,371 | **43** | 74 | **12** | 318 |
| A: IPL from DASD | 12 | 16,132 | 79 | 93 | 82 | 384 |
| All of CP | 201 | 157,498 | 179 | 538 | 492 | 1,917 |

**Strategy B is the right first move**, and the DAT column is why: 12
references against 82. *(superseded — see status note)* `DMKCKP`, `DMKSAV` and `DMKBLD` carry 70 of the 82,
and `DMKBLD`'s are all about building the system's segment and page tables —
which M1 does not need, because DAT is off. Deferring those three modules
keeps M1 to the PSW, lowcore, control-register and console questions, which
is what it exists to isolate.

It also halves the I/O burden: 43 instructions against 79.

## The distinction that changes the estimate

**43 I/O instructions is not 43 pieces of work, because most of them are on
paths M1 never takes.** `DMKCPI`'s 21, read individually:

     546  SIO  DO SENSE TO THE IPL DEVICE
    1233  HIO  ISSUE HIO
    1241  TIO  TO CLEAR HEX 70 STATUS
    1242  TIO  FROM 3705
    1243  TIO  (CODE FOR 3705 ONLY)
    1244  TIO
    1257  TIO  TIO
    1284  SIO  ATTEMPT THE "RELEASE"
    1299  TIO  IF CONDITION-CODE 0,
    1350  SIO  ISSUE SIO
    1362  TIO  ISSUE TIO
    1419  SIO  START THE READ
    1444  SIO  SUSPEND IMMEDIATE
    1450  TIO  CHECK OUT STATUS,CC=0
    1458  TIO  DRAIN FOR CE/DE
    1848  SIO  ISSUE SENSE COMMAND
    1867  TIO  CLEAR THE SUBCHANNEL
    2001  TIO  MAKE SURE IT EXISTS
    2005  TIO  TEST DEVICE
    2008  SIO  START SENSE TO DEVICE
    2040  TIO  TEST FOR SENSE END

The `1233`–`1299` cluster is 3705 communications-controller handling — one
comment says "CODE FOR 3705 ONLY" — and `1419`–`1458` reads like the 370x
load path. With a 3215 console and no DASD volumes to mount, M1 executes
almost none of it.

**So the work splits in two, and the halves need different things:**

- **Must *work*:** the console path. `DMKQCNWT` → `DMKCNSIC` → `DMKIOS` →
  interrupt → `DMKCNSIN`. Every instruction on it has to be correct.
- **Must *assemble*:** everything else in the resident nucleus. An `SIO` on
  an untaken path still has to get through the assembler, which is what
  `XAOPS.MACRO` is for, but it does not have to be semantically right yet.

That distinction is the difference between M1 being a fortnight and a
quarter, and it is why M0 mattered.

## Per-module, in dependency order

| Module | Lines | S/370 I/O | arch | DAT | CAW/CSW | What M1 needs of it |
|---|---|---|---|---|---|---|
| `DMKPSA` | 399 | 2 | 7 | 0 | 7 | **Lowcore layout.** The one genuinely new surface — see below. |
| `DMKIOS` | 1,872 | 10 | 4 | 0 | 85 | The ten instruction sites, and the CSW shim. Must work. |
| `DMKIOT` | 984 | 5 | 8 | 1 | **113** | Interrupt entry. Must work. Reads lowcore for the device. |
| `DMKCNS` | 1,973 | 5 | 0 | 0 | 58 | Builds the console CCWs. Must work. **Zero arch instructions.** |
| `DMKQCN` | — | 0 | 0 | 0 | 0 | **Architecture-clean.** Nothing to do. |
| `DMKSCN` | — | 0 | 0 | 0 | 0 | **Architecture-clean.** Nothing to do. |
| `DMKFRE` | 920 | 0 | 6 | 0 | 0 | Free storage. Six control-register instructions. |
| `DMKDSP` | 2,235 | 0 | 18 | 2 | 17 | Dispatcher. 18 arch instructions, mostly `LPSW`/`LCTL`. |
| `DMKCPI` | 3,388 | 21 | 31 | 9 | 38 | Largest single item. Mostly must-assemble, not must-work. |

**`DMKQCN` and `DMKSCN` come out clean** — no S/370 I/O, no
architecture-sensitive instructions, no DAT fields. Two modules on the
critical path that need nothing at all is worth knowing before planning
around them.

## Lowcore is the one genuinely new surface

`PSA.MACRO`, 688 lines, invoked by **171 of 201 modules** — so a change here
touches almost everything. Offsets computed from the macro, honouring its
`ORG` redefinitions:

    CHANID     X'A8'   STIDC result -- S/370 only, no equivalent
    IOELPNTR   X'AC'   I/O Extended Logout pointer -- S/370 only
    ECSWLOG    X'B0'   Limited Channel Logout -- S/370 only
    INTKFLIN   X'B8'   "IO INTERRUPT KEY, FLAGS, INTERFACE..."
    INTTIO     X'BA'   "IO INTERRUPT DEVICE ADDRESS (HALFWORD)"

ESA/390 puts the subsystem id as a fullword at `X'B8'` and the interruption
parameter at `X'BC'`. So `INTKFLIN` already sits on that exact fullword, and
**`INTTIO` at `X'BA'` is its low halfword — which under ESA/390 is the
subchannel number**, since the subsystem id is `X'0001'` in the high halfword
and the subchannel in the low. Test 7 confirmed this by execution.

**`INTTIO` therefore neither moves nor changes width; its meaning changes
from device address to subchannel number.** That makes `DMKIOT`'s interrupt
entry a lookup rather than a relayout, and CP already chains `RDEVBLOK` by
device address. The three fields above it — `CHANID`, `IOELPNTR`, `ECSWLOG` —
are the ones with nothing to map to, and all three are channel-logout or
`STIDC` machinery that the channel subsystem replaces outright.

## The order to attack it

1. ~~**`XAOPS.MACRO` into the build.**~~ **DONE, 27 September.**
   `MACLIB GEN XALIB XAOPS` produced all twelve members and CE's Assembler XF
   assembled `XATEST` — which contains `SSCH` — with `HIGHEST SEVERITY WAS 0`.
   See `14-M0-CLOSED.md`, which also records the card-reader import recipe every
   step below needs.
2. **`PSA.MACRO`**: add the ESA/390 names at `X'B8'`/`X'BC'`, keep `INTTIO`
   where it is, and mark `CHANID`/`IOELPNTR`/`ECSWLOG` as S/370-only so
   anything still referencing them fails loudly rather than reading garbage.

   **As an `AUXLCL` update deck, not an edit to base source.** CE stacks three
   update levels — `LCL` over `HRC` over `TEXT AUXR60` — and the local one is
   empty and reserved for exactly this. `594/DMKLCL.CNTRL` already declares it,
   and `EXEC VMFASM PSA DMKLCL` builds it. This keeps base source untouched,
   makes the conversion a reviewable delta, and largely retires `R-04`. See
   `15-UPDATE-LEVELS.md`. Note `R-22`: `UPSTREAM.md` records that `PSA`'s
   sequence-number increment already needed special handling, so this member is
   one of the anchor-fragile ones.

   **DONE, 27 September.** Delivered as `PSA.XA0001DK`, applied last over
   thirteen existing update levels, built into `DMKLCL MACLIB` with
   `VMFMAC DMKLCL DMKLCL`. Five of six pre-registered predictions held; the
   sixth found `I-30`. `DMKIOG` and `DMKPRV` fail on the renamed S/370 fields
   and `DMKIOT`/`DMKDSP` on `INTTIO`, exactly as intended, while eleven other
   modules stay clean. See `19-M1-STEP2.md`.
3. ~~**Assemble the nine modules unchanged** and collect the errors.~~ **DONE,
   27 September, and the error list is empty.** All nine assemble on CE with
   `CPACC` then `VMFASM <module> DMKLCL`, every one reporting
   `NO STATEMENTS FLAGGED IN THIS ASSEMBLY`. The DAT five are clean too, so M2
   has a baseline as well. That is the best available outcome: every error from
   here on is ours. See `16-NATIVE-BASELINE.md`.
4. **`DMKIOS`**: the ten sites plus the CSW shim after `TSCH`. The pattern is
   already proven by tests 5, 6 and 7.
5. **`DMKIOT`**: interrupt entry, `INTTIO` as a subchannel number, and
   **CR6** — without which no interruption is ever presented and CP hangs
   after writing its message, which test 7 demonstrated.
6. **`DMKCPI`** last, and only the paths M1 takes.

## What M1 explicitly defers

- All DAT table work — `CORE`, `DMKPTR`, `DMKPGS`, `DMKBLD`, `TRANS`. M2.
- **AMODE 31.** M1 runs 24-bit throughout. Per `08-lra.rc`, AMODE 31 is a
  prerequisite for translating above-the-line *virtual* addresses, so it
  belongs with the DAT work in M2, not here.
- Shared segments — M3, per `05-CP67-PRIOR-ART.md`.
- `DMKCKP`, `DMKSAV`, and the whole IPL-from-DASD path — strategy B above.
- The stand-alone utilities: `DMKFMT`, `DMKDMP`, `DMKLD00E`, `DMKDIR`,
  `DMKDDR`. Roughly 71 of CP's 179 I/O instructions live there and none of
  it is needed to boot.

## The honest risk in this plan

**The counts are floors.** 350 macro invocations in the M1 set — 279 `CALL`,
44 `LOCK`, 40 `GOTO`, 10 `TRANS`, 7 `SWTCHVM` — and the parser sees none of
what they expand to. `CALL` is known safe (bit 0). `TRANS` is known and only
appears 10 times here. `LOCK` and `SWTCHVM` have not been read at all, and
`SWTCHVM` by its name switches virtual machine context, which is exactly
where PSW and control-register handling would hide.

Step 3 above — assemble and collect errors — is the cheapest way to find out,
which is why it comes before any module is edited.
