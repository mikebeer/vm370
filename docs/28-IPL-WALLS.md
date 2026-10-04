# The walls between a converted CP and a clean IPL

Started 28 September 2026, rewritten 1 October, re-measured 1 October (midday),
re-measured again 1 October 18:45 UTC,
again 2 October 12:10 UTC when wall 11 fell,
again 2 October 18:55 UTC, when walls 14 and 15 fell, wall 13 was
downgraded, and a Status column was added,
**and again 2 October 19:50 UTC, when CP was caught building its startup logo
correctly and wall 16 was re-characterised for the third time in one day.** Every
section that has been superseded says so where it stands rather than being
deleted, because the diff is the point of this file.
Extends **STATE.md** and **BUILD-CYCLE.md**. Read after GOTCHAS.md.

**This file is the version-controlled original; the project's copy is published
from it.** It answers one standing question — *what is between the current status
and an IPL without errors?* — and that answer has now been given three times with
three different numbers, so it belongs somewhere with a diff.

Seventeen walls so far, thirteen of them closed, one downgraded to "never was a
wall", one not CP's, and two open. Every one was located to a specific
instruction at a specific address rather than inferred, and **each was only
visible once the previous one fell** — which is the single most useful thing
this document records, because it is also why no estimate of "how much is left"
has ever survived contact.

The count itself is evidence for that last point: this file said "eleven walls"
for two days while walls 14 and 15 were already in the nucleus, waiting to be
reached. Wall 16 was then described three different ways in six hours (see its
section), which is the same lesson at a shorter timescale.

## The walls, in the order CP hit them

The **Status** column is the one to read first. It is deliberately not a
percentage: a wall is `closed` only when the failure it names is gone *and* the
run that proves it is in the build journal.

| # | Wall | How it presented | Found by | Status |
|---|---|---|---|---|
| 1 | The conversion executes, and S/370 rejects it | disabled wait `X'111111'`, `B234` = `STSCH` under `ARCHMODE S/370` | reading the PSW | **closed** |
| 2 | **BC-mode PSW is a third axis, never counted** | `Invalid IPL PSW: 00040000 00004470` — bit 12 zero | Hercules refused the IPL | **closed** |
| 3 | The standalone loader is itself S/370 I/O | `9D00 8000` = `TIO 0(R8)` in `DMKLD00E` | PSW at `X'44C2'` | **closed** |
| 4 | `XAIO` borrowed R15, a `USING` base in 54 modules | interruption code `X'15'`, operand exception | PoP + the trace | **closed** |
| 5 | Subchannels resolved but never enabled | `MSCH` count 0; cc 3 from every `SSCH` | counting MSCHs in the artifact | **closed** |
| 6 | The architecture probe clobbered R1 | exactly one device per module failed | register dump | **closed** |
| 7 | `DMKDMP` took the dump with `ISK` | `DMKDMP905W SYSTEM DUMP FAILURE` | `0934` at the failing address | **closed** |
| 8 | `SSK` sized storage at **zero**, and FRELOOP ate the nucleus | `C6D9C5C5` (`"FREE"`) every 16 bytes, incl. lowcore | breakpoint + arithmetic | **closed** |
| 9 | CP executes an ECPS:VM assist *before* probing for assists | `SCNRU` / `STEVL`, operation exception | `pgmtrace`, one run | **closed** |
| 10 | Our own DSECT grew; the block generator did not | `CPI001` — SYSRES not found | `dumpscan.py` on the dump | **closed** |
| 11 | **`CR0`'s translation format says 64 KB segments** — NOT the STDs, see the retraction below | `PRG018` = translation specification | Hercules's `dat.c`, a day late | **closed** 2 Oct 12:02 UTC |
| 12 | **Not a CP wall: the build environment is reclaimed mid-run** | Hercules, the driver and the watcher vanish together; the log ends on a normal `Ready;` | `uptime`, two hours late | **not CP's** — mitigated by sliced builds |
| 13 | ~~Privileged-operation exception on `SSM`, DAT on, in problem state~~ | `PSW=040D0000 0006D130`, `INST=8000D129` | SDL 4.9.1 + `pgmtrace` | **NOT A WALL — downgraded 2 Oct** |
| 14 | **A half-converted geometry group in `DMKPTR` `GETENTRY`** — one of five instructions converted, four left at 64 KB | silent hang: CP alive, in supervisor state, taking I/O interrupts, printing nothing, for five days | `abendmap.py` + arithmetic checked against a `savecore` | **closed** 2 Oct — `I-162` |
| 15 | **`N R7,=A(X'FFF0')` did two jobs on a halfword PTE** — strip flags *and* leave page×16 for `ACORETBL` | `ABEND PTR020`, "DMKPTRUC IS NEGATIVE", with a 30,669-line dump | `DMKPTRUC`/`DMKPTRP2` read out of the nucleus | **closed** 2 Oct — `I-163` |
| 16 | **The console's I/O completion never reaches `DMKCNS`**, so the queued startup messages never go out | nine CONTASKs queued and intact; `IOBCSW` zero in the console IOBLOK; `CONACTV` still set; breakpoint at `DMKCNSIN` never hit, while DASD interrupts ARE taken out of the wait | IOBLOK found by `IOBUSER`+`IOBCAW` cross-check; control-validated breakpoints; nucleus disassembly at the I/O new PSW | **CLOSED AS A HANG.** Two defects in series, both fixed: `I-174` (ORB interruption parameter) and `I-175` (the interrupt path read a CSW ESA/390 never stores). Measured after: `CSW X'40'` non-zero, `CONACTV` **clear**, `CONCNT` `002C`/`001E` instead of `0001`. The messages still do not reach the terminal — CP now abends in DMKPTR first (wall 18) — so this is not yet a working console |
| 17 | ~~A one-byte corruption of static nucleus data — `DMKCPI`'s logo reads `VM/380`~~ | it is CE's own `HRC370DK`: `MVI STMSG+7,C'8'  tell them this is System/380`, reached only when a `BSM` into AMODE 31 succeeds | breakpoint at the store, `am=31`, `INSTWRD1 = F8000000` | **NOT A WALL — retracted 2 Oct.** CE detecting that our conversion works — `I-173` |
| 18 | **Storage keys: `SSK` does not exist in ESA/390, and CP keys a 4 KB page as two 2 KB halves** | operation exception `CODE=0001 ILC=2` at `X'3DD78'`, `INST=0838  SSK 3,8`, then `DMKDMP908I … CODE PRG001`; `GR06=00EC4000` and `GR08=00EC4800` are 2 KB apart | `abendmap` brackets it inside DMKPTR, same module both sides; registers pin it to `DMKPTR 00643000` | **FIXED** — `I-177`; the two DMKPTR pairs collapse to `SSKE` and CP ran straight past, printing its whole banner. 57 key sites remain unconverted and unreached |
| 19 | **CP will not start without the interval timer, and 370-XA deleted it** | the full start-up banner, then `Turn on the Interval Timer` **181,775 times** | `DMKCPI` `TIMETEST` at 02785000 polls location `X'50'`; PoO Appendix F lists the interval timer as System/370-only | **OPEN — where CP stops now** — `I-178`; fix built, one card |

## Wall 20 — CLOSED, and the measurement that closed it

**Symptom.** CP printed its storage report, started the monitor, and accepted
nothing further. A terminal on another device got nothing either, which made it
look like a console defect for several hours.

**What it actually was.** Three defects in a chain, each hidden by the one in
front of it.

1. `I-183` — `DMKPGS`'s `NEXTSEG` advanced its segment-table pointer by one
   fullword (1 MB) and its virtual address by 64 KB, so they drifted by
   sixteen from the first iteration. Fixed, and the scan then terminated:
   `GR03` went from `00FFD400`, entry **256** of a 32-entry table, to
   `00FFD080`, the byte after entry 31.
2. `I-184` — six more cards in the same two loops, reached only once the loop
   could advance. Fixing `I-183` alone would have moved the hang three cards
   down.
3. `I-188` — and then the loop came back, in a different shape, and the cause
   was my own constant. `X'00F00000'` reaches sixteen segments; R1 climbed to
   `X'01000000'` and the next pass's `N` zeroed it, so R1 cycled 1–16 MB for
   ever while R3 climbed past the end of its table. The root cause underneath
   was `DMKBLD 00207000 SRDL R0,8`, which made the table sixteen times longer
   than the machine — a 64-byte unit holds sixteen entries in both
   architectures, but they now cover 16 MB instead of 1 MB.

**The instruments that settled it**, after a day of reading a decoded `ia=` line
off the Hercules panel and getting a different answer each time:

- `symtab.py` reads **CP's own symbol table** out of a `savecore` image.
  `DMKSYM` is a file of `SYM` macro calls, `SYM.MACRO` expands each to
  `DC CL8'&MODULE ',V(&MODULE)`, and `DMKCPI` writes the result as the first
  record of every dump. 261 entries, naming entry points rather than CSECTs.
  `X'3DA38'` → `DMKPTRAN + 0`; `X'C58'` → `DMKSVCIN + 0`; `X'63906'` →
  `DMKPGS + 2310`.
- `psa.py` reads the assigned storage locations and resolves each old PSW
  through it. The panel's `psw` command prints its decoded line and its hex
  line from two separate reads of a *running* CPU, so they disagree and neither
  is a measurement of a moment. The old PSWs were stored by the hardware at a
  defined instant. `X'20'` gave `000C2000 00063906` — the instruction after
  the `SVC 8`, which is the caller's identity and nothing else could supply it.
- **CP counted the loop itself.** `GR00 = 020FC4D9` is `DMKPTRCT`, incremented
  by `DMKPTRAN` cards `00291000`–`00293000`: **34,587,353** calls.

**What CP does now.** Everything above, plus:

```
15:29:50 AUTO LOGON   ***   AUTOLOG1 USERS = 002  BY  OPERATOR
DMKCPI966I Initialization complete
```

It returns to the dispatcher, runs the autolog list, builds a second virtual
machine, and says it is finished initialising.

---

## Wall 21 — `ISK`, and it is reached at once

```
PSW=000C1000 000008B4 INST=09FF   ISK   15,15   operation exception CODE=0001
15:29:50 DMKDMP908I SYSTEM FAILURE; CODE PRG001 PROCESSOR 00
```

`ISK` does not exist in ESA/390. `X'8B4'` is in `DMKPSA`'s fetch- and
store-protection check — `DMKPSAFP`, `DMKPSASP`, `DMKPSAFC`, `DMKPSASC` — which
CP runs whenever a virtual machine's instruction or channel program touches
storage and the real key must be verified. A second virtual machine had just
started, so the path had just become reachable. 54 instructions in 15 modules;
see `I-192`.

## The PoO table this project should have used as a checklist

Appendix F of the ESA/390 Principles of Operation, "Comparison between
System/370 and 370-XA", lists the assigned-storage locations that differ
between the two architectures. Three separate walls turned out to be one row of
it each, and each arrived as a surprise because the table was read one row at a
time instead of once as a list:

| field | System/370 | 370-XA | ours |
|---|---|---|---|
| Channel-status word | 64 (`X'40'`) | — | `I-175`, wall 16 — we synthesise it with `TSCH` |
| Channel-address word | 72 (`X'48'`) | — | **still open** — `s370only` flags it in `DMKLD00E` |
| Interval timer | 80 (`X'50'`) | — | `I-178`, wall 19 |
| Trace-table designation | 84 | — | not reached |
| Channel ID | 168 | — | `PSA.XA0001DK` renamed it `S370CHID` |
| IOEL address | 172 | — | renamed `S370IOEL` |
| Limited channel logout | 176 | — | renamed `S370ECSW` |
| Measurement byte | 185 | — | not reached |
| I/O address | 186 | — | the `INTTIO` rename, R-02 |
| Subsystem ID | — | 184 (`X'B8'`) | `I-174` |
| I/O-interruption parameter | — | 188 (`X'BC'`) | `I-174` |

And in the control registers: block-multiplexing control, storage-key-exception
control, page-fault-assist control, the **interval-timer subclass mask** (CR0.24)
and the channel masks (CR2) are all System/370-only, while
fetch-protection override and the new segment-table origin and length fields in
CR1 are 370-XA. `I-71` (CR6 as the I/O-interruption subclass mask) and `I-152`
(CR0's translation format) are two more rows of the same figure.

The remaining unticked rows are the honest answer to "what else is waiting":
the CAW at `X'48'`, the trace-table designation, and the measurement byte.


## Wall 18 — storage keys, and why it is not the opcode swap it looks like

CP reaches this only because `I-175` let it past wall 16. The failure is clean
and took one run to diagnose, because the registers name the card:

```
CPU0000: Operation exception CODE=0001 ILC=2
PSW=000C0000 0003DD78 INST=0838   SSK   3,8
GR03=00000000  GR06=00EC4000  GR08=00EC4800  GR12=0003DA48
```

`GR12` is DMKPTR's base and `abendmap` brackets `X'3DD78'` between
`DMKPTR ABEND 20` at −508 and `DMKPTR ABEND 8` at +1422 — same module both
sides. `GR08 − GR06` is exactly 2048, which pins it to `DMKPTR 00643000`:

```
00638000  S   R6,ACORETBL     GET PAGE ADDRESS/256
00639000  SLL R6,8            GET PAGE ADDRESS             -> GR06=00EC4000
00640000  LA  R8,2048(,R6)    GET ADDRESS OF 2ND HALF PAGE -> GR08=00EC4800
00641000  L   R3,SWPFLAG      GET USER'S KEYS IN LOW ORDER
00642000  N   R3,=A(X'F8F8')  CLEAR REF/CHANGE BITS        -> GR03=00000000
00643000  SSK R3,R8           SET KEY FOR 2'ND HALF PAGE   <-- fails here
00644000  SRL R3,8            JUSTIFY KEY FOR 1'ST HALF PAGE
00645000  SSK R3,R6           SET KEY FOR 1'ST HALF PAGE
```

Two key bytes in one halfword (`X'F8F8'`), two `SSK`s, and a shift between them
to get from one to the other. System/370 keys cover 2 KB; the PoO says the
370-XA facilities provide "key-controlled protection on **only 4K-byte
blocks**", contrasting with System/370 in the same sentence. So `SSKE` sets the
whole page's key in one instruction, the pair collapses, the `SRL R3,8`
disappears, and `SWPFLAG`'s two key bytes become one. That is the I-128
structural law again: S/370 packed something where ESA/390 has one slot.

This was predicted. `I-44` and [23-STORAGE-KEYS.md](23-STORAGE-KEYS.md) already
recorded that the pairs must collapse rather than translate, and that a third of
the family lives in DMKPTR, the page manager. A live abend on exactly such a
pair confirms that analysis rather than adding to it — and while writing this up
I briefly claimed those docs said the opposite, from memory rather than from the
file. Retracted before it was acted on; see `I-177`.

What is newly measured is which modules have **none**: DMKIOS, DMKIOT, DMKPGS
and DMKVAT are all zero. The I/O supervisor and the DAT-table modules are clear,
so the exposure is DMKPTR plus the command and simulation modules.


### Wall 17 is retracted, and what replaced it is good news

`HRC370DK` is CE's **System/380 architecture probe**, in `DMKCPI`:

```
* Since we support both System/380 and System/370 machines,
* let's see on which we are running, and adjust the version message accordingly.
         MVI   INSTWRD1,C'7'
         MVC   SAVEDPSW(8),PCNEWPSW    save program check new PSW
         MVC   PCNEWPSW(8),TRAPPER     set our own interrupt handler
         LA    R14,CHK3701
         ICM   R14,8,=X'80'            try to switch to 31-bit mode
         DC    X'0B0E'                 BSM R0,R14
* If we arrive here, the BSM instruction was valid and we are
* executing on a System/380 machine.
CHK3701  MVI   INSTWRD1,C'8'
         MVI   STMSG+7,C'8'            tell them this is System/380
```

**Our CP reaches `CHK3701`.** The breakpoint at the store fires with `am=31`,
`GR14 = 8006E0C2` (bit 0 set), and `INSTWRD1` at PSA `X'430'` reads `F8000000`.
So `VM/380` is not corruption — it is **CE detecting that our conversion
produced a 31-bit-capable machine**, and it is the most direct confirmation of
the AMODE-31 work this project has had.

Two things to keep. `INSTWRD1` byte 0 is a CE-maintained PSA flag for "is this
a 31-bit machine", and `DMKCNS` already reads it to choose its banner — existing
infrastructure. And `HRC065DK` (Logical Device Support) does
`L R8,INSTWRD1 -> LDEVCTL` while `HRC370DK` puts a character in byte 0: a flag
packed into the high byte of a pointer, which is **`I-128`'s law in CE's own
shipped code**. Latent here (bytes 1–3 are zero, LDEVs inactive), fatal to LDEV
support under AMODE 31.

How it was got wrong: the evidence for "corruption" was that all four
`C'VM/3?0 Community Edition'` literals read `VM/370`. True, and **incomplete** —
I searched for a corrupted *literal* and never for code that *modifies* one. The
modifying card is an `MVI`, which that search shape could not find. A
well-formed search for the wrong hypothesis.

**Walls 1–11, 14 and 15 are closed.** Wall 11 fell on 2 October at 12:02 UTC:
`PRG018` is gone after five days. Wall 12 is not CP's. **Wall 16 is where CP
stops now.**

### Wall 13 is downgraded, not closed

It was recorded as a wall on the strength of a privileged-operation exception on
`SSM`. The PSW that was quoted for it says otherwise and always did:
`040D0000` has `cmwp=D`, i.e. **bit 15 set — problem state** — and Hercules
printed the operand as `V:0006D131`, a *virtual* address. That is a virtual
machine executing `SSM`, which CP is supposed to intercept and virtualise in
`DMKPRV`; the exception is the mechanism, not a fault. On 2 October CP ran
**past** it to the dispatcher's wait in every run, which settles it. The entry
stays in the table with its original wording struck through, because a wall that
was never a wall is exactly the kind of thing this file exists to keep visible.

### Walls 14 and 15 are the same defect class, and it is ours

Both are groups of instructions that encode page geometry and must change
together — and in both, an earlier pass converted **one** member and left the
rest. That is worse than converting none: the arithmetic stays internally
consistent enough to produce a plausible address, so it fails as a hang or a
counter underflow rather than as an assembly error. Wall 14 cost five days for
three cards. `tools/geomchk.py` now sweeps for the class and reports a site only
where no deck of ours replaces its sequence number; it currently lists **15
PROVEN** unconverted sites, including the identical `16*2+8` swap-table
expression in `DMKCDB`, `DMKCDM` and `DMKPGS`. The class is not confined to
`DMKPTR` and wall 16 may well be another member of it.

A caution on reading the next section, **superseded 2 October 18:55 UTC and kept
for the diff**. It read: *"by the measure of what CP visibly does, it currently
does less than on 30 September — it prints nothing at all, where it used to
initialise fully and dump itself."* That held while wall 14 stood. With walls 14
and 15 closed, CP talks again: the wall-15 build printed
`DMKDMP908I SYSTEM FAILURE; CODE PTR020` and a complete 30,669-line dump ending
in `*** END OF DUMP ***`, so DMKDMP's whole path — abend, message, formatted
dump, converted printer — works end to end.

What has **not** been shown at any point is CP printing a *normal*
initialisation message. Every console line this project has ever seen came from
DMKDMP on the abend path. So in wall 16, silence is **not** evidence that
initialisation failed, and that asymmetry is the trap to avoid repeating: the
ordinary message path (`DMKQCNWT` → `DMKCNS`) has never been exercised
successfully, and until it has, "prints nothing" and "did nothing" are different
claims.

Walls 1–10 are closed, and for the record: Detail for each in `docs/13-ISSUES.md`; the entries
worth reading are **I-77**, **I-102**, **I-104**, **I-108**, **I-110**,
**I-114**, **I-116**, **I-162** and **I-163**.

## Wall 16 — characterised three times in one day, and the third is the one to act on

This section has been rewritten three times on 2 October. All three versions are
below, oldest last, because **the churn is the lesson**: each reading was
consistent with everything measured at the time and each was wrong about where
the defect was. Read the first one.

### Fifth and current, 3 October 07:50 UTC — both defects now named; the second is the CSW

Wall 16 is **two defects in series**. I-174 cleared the first: the ORB's
interruption parameter was zero, so no interrupt could be routed to a device.
The second is the symmetric omission to the one we fixed months of work ago on
the other path.

On System/370 an I/O interruption **itself stores a CSW** at `X'40'`. The
channel subsystem does not: the status stays in the subchannel and `TEST
SUBCHANNEL` is the only way to get it. We built that shim for the `SSCH` path —
`IOSXCC1` does `TSCH IOBIRB` and then synthesises the CSW — and **never for the
interrupt path**. `DMKIOT`'s interruption supervisor reads `CSW` at about forty
sites and `DMKIOT.XA0012DK` converted none of them.

| step | measured |
|---|---|
| the interrupt is taken | `IOSSID X'B8' = 00010004` — the console's subchannel, which only a real interrupt stores |
| the device is found correctly | `LH R1,X'BE'` at `X'6708'`, and `X'BE'` is `IOINTPRM+2`, exactly where I-174 writes the device address |
| the CSW CP then reads | `X'40' = 0000000000000000` |
| the status it saves | `IOBCSW = 00000000 00000000` |

So every status test reads zero, no unit status is ever seen, the IOBLOK is
never completed, `CONSTAT` keeps `CONACTV`, and `DMKCNSIN` never fires. That is
the whole of wall 16's remainder. **Fix built, not yet verified** — `I-175`.

Two retractions, both mine, and the second is the more useful:

* I spent a run of steps on `DMKIOSIN`, "the unconverted handler", at
  `DMKIOS.ASSEMBLE:436`, with eight live `INTTIO` references and no deck of
  ours covering sequence `00400000`–`00699999`. All of it true of the file and
  false of the build: `DMKIOS.R09587DK` says `./ * DMKIOSIN BEING MOVED INTO
  DMKIOT` and `./ D 418000 890000`. The handler is `DMKIOTIN`, in a module we
  had already converted. `DMKIOS.AUXR60` states it in one line I had not read:
  `R09587DK 602 SPLIT MODULE DMKIOS INTO DMKIOS AND DMKIOT`.
* I predicted `INTTIO` would resolve to `X'BA'`, the subchannel number, and
  that this was the defect. It resolves to `X'BE'`. The device lookup works.

What settled both was decoding the nucleus rather than reading more source, with
two independent anchors inside the same macro expansion — `IOOPSW+4 = X'3C'`
and `CSW = X'40'`, both known-correct — to prove the displacements were being
read right. The general lesson became `I-176` and a tool, `applied.py`: **our
scanners read the 1979 base file, which is not the file the assembler sees.**

### Fourth, 2 October 20:30 UTC — P0 answered: the completion never reaches `DMKCNS`

`I-169`. Every link measured, in order:

| step | measured |
|---|---|
| Hercules completes the write | subchannel `X'0004'` (device `0009`), `Stat=0C00`, CE+DE, no error |
| the console's IOBLOK | `X'056940'` — `IOBUSER = X'052870'` matches every CONTASK's `CONUSER`, and `IOBCAW = X'056340'` is exactly `CONTASK X'056328' + X'18'` = `CONCCW1` |
| **`IOBCSW`** | **zero** — no status recorded anywhere in CP |
| the written CONTASK | `CONSTAT = AA` — **`CONACTV` still set**, "active on real device" |
| breakpoint at `DMKCNSIN` (`X'FE40'`) | **never hit** |
| is CP deaf to I/O? | **no** — the I/O old PSW at `X'38'` *is* the enabled-wait PSW, and `IOSCHNO` reads `X'0056'` = device `06A1`, so DASD interrupts are taken out of the wait |
| `CR6` at the stop | `FF000000` — all eight interruption subclasses enabled |

So the defect is in **interrupt routing, not queue pointers**, which is precisely
the fork P0 was constructed to resolve. The messages are not the problem: nine
CONTASKs chain cleanly from `X'056328'` — the logo (`cnt=67`), `"Now 20:16:20
GMT"` (32), `DMKCPI971I` (44), `DMKCPI977I` (30) — every link valid, every
`CONUSER` identical.

`DMKCNSIN = X'FE40'` came from `IOBIRA` and is corroborated by the code there
(`LM R12,R13,…` / `LH R1,0(R10)` = `LH R1,IOBRADD`), matching DMKCNS's own
documented convention, *"GPR 10 = ADDRESS OF THE UNSTACKED IOBLOK"*. An earlier
attempt to place it by abend bracketing put it inside DMKSVC, which was wrong —
`abendmap`'s coverage is sparse in low storage and the bracket spans 142 KB.

**The next fork, ready to run.** The I/O new PSW at `X'78'` puts CP's
first-level I/O handler at **`X'6638'`**. A breakpoint there separates:

1. Hercules never presents subchannel `X'0004'` — then the console subchannel's
   PMCW enable/ISC is the suspect, which is wall 5's shape (`MSCH` count 0)
   surviving for the console after being fixed for DASD.
2. It is presented and CP's first-level handler drops it before `DMKIOT` routes
   it to `IOBIRA` — then the routing is CP's.

### Third and current, 19:45 UTC — CP builds its logo and `DMKCNS` writes one CONTASK

A breakpoint at `DMKQCNWT` (`AQCNWT` = `X'419F8'`, read from the PSA) is reached
with `GR00 = X'47'` — **71 bytes** — and `GR01 = X'6DD92'`. That storage reads:

```
R:0006DD90  85151515 15E5D461 F3F8F040 ...
            151515 "VM/370 Community Edition Version  1 Release  1.2
                    10/02/26 18:27:53" 1515
```

That is `STMSG` in `DMKCPI`, with today's date and time filled in by `DMKSAV`.
**CP builds its startup logo correctly — the furthest this project has ever
observed CP get.**

Scanning the whole nucleus for EBCDIC `VM/3` finds the logo text in **three**
places in CP free storage as well as the `DMKCPI` original, so the messages were
built, copied into CONTASKs *and* queued. The single CCW that reaches the
console is `09 056360 60 000001` — one byte of `X'40'` from `X'056360'`, a
**different** CONTASK 288 bytes before the first logo one. That is the leading
blank line VM/370 writes ahead of its logo.

So the defect is **neither** the message build **nor** `DMKQCN`: `DMKCNS` writes
the first CONTASK and never advances to the next. Everything else fits — the
write completes `Stat=0C00`, `CR6 = FF000000` *measured at the stop*, so no
interruption subclass is masked, CP takes the completion, finds the queue
unadvanced, and idles in the dispatcher's enabled wait.

Two corrections this made to the second version: the trailing-blank stripper is
**not** involved (the message ends in `X'15'`, not a blank, so `CLI 0(R15),C' '`
fails at once and the count stays 71), and "no read CCW" remains true but is no
longer the interesting fact.

### Second, 19:08 UTC — superseded: "CP writes an empty message"

Correct about the CCWs, wrong about the cause. It concluded the one-byte write
*was* the defect — an unfilled buffer with a length of 1 — and predicted a
length taken from the wrong place (`I-128`'s shape). The length was never wrong:
71 bytes were passed. The buffer it examined belonged to a different CONTASK.

### First, earlier — superseded: "CP prints nothing"

The facts that version measured are all still true and still worth having, but
the conclusion drawn from them ("CP is idle, or stuck before console I/O")
was wrong in both branches:


Measured 2 October, three runs, identical each time:

| | |
|---|---|
| PSW | `030E0000 00000000` — `sm=03`, `cmwp=E`, `am=24`, `ia=0` |
| state | **enabled** wait (W=1), supervisor, interrupts not masked |
| `GR12` / `GR13` | `00032BC0` / `00033BC0` — `DMKDSPCH`'s base pair, from `ADSPCH` in the PSA |
| `GR14` | `50034C98` — return address `X'34C98'`, just past DMKDSP's two-base range |
| `X'86'` | external interruption code `X'1004'` — clock comparator |
| varies run to run | `GR03` (a TOD value), `GR09` (`50`→`54`) |
| constant run to run | `GR04=9`, `GR05=5`, `GR07=165` |
| console output | **none** |
| `cold` sent to `0009` | delivered (`/(0009) cold`) and **ignored** — same wait, same registers |

### RESOLVED 2 October 19:08 UTC — CP is not silent, it writes one blank byte

Two readings were open: CP idle with undrained messages, or CP stuck before
console I/O existed. **Neither.** With CCW tracing armed *before* the IPL — which
`build.sh test` could not express until the `--` marker was added — the entire
console conversation is six CCWs (`I-165`):

```
0009: Halt subchannel
0009:CCW=0406DA80 20000020 => all zeros      sense, 32 bytes; Stat=0C00 Count=001F
0009:CCW=09056360 60000001 => 40EEEEEE EE..  WRITE, count 1; Stat=0C00
0009:CCW=03000000 20000001                   NOP;   Stat=0C00
```

Every CCW completes with `Stat=0C00` — CE+DE, no error. So the channel program
is right, the device is right, and the one byte CP writes is `X'40'`, an EBCDIC
blank. **The lone blank line in every run's output is CP's message.** The buffer
at `X'056360'` is still full of `X'EE'`, DMKFRE's `&FRETRAP` fill for allocated
storage that has never been written, so the text was never moved in and the
count was never set.

There is **no read CCW anywhere** — opcodes `04`, `09`, `03` only. CP never posts
a console read, so the `cold` typed at `0009` was discarded by the 3215 with no
error and no trace. That half is settled too.

So wall 16 is not "CP prints nothing". It is **CP writes an empty message**: a
correct channel program pointed at an unfilled buffer with a length of 1. A
length that collapses to 1 next to a buffer that is never filled is the
signature of a length read from the wrong place — `I-128`'s structural law, and
therefore the same class as walls 14 and 15.

**What the harness cost here.** Three runs armed `t+009` *after* `herc:ipl`,
recorded an empty trace, and that emptiness was read as "CP issues no I/O". It
was not evidence of anything. Two limitations, now fixed or written down:
`build.sh test` appended every caller spec after the ipl, so a trace could never
cover the IPL (fixed — specs before a literal `--` now precede it); and `test`
passes `--bare` to `mkrun`, which **omits the whole `BOOT` dialogue** — the null
line, `cold`, `cp disc`, `logon maint`. `--bare` is correct for its original
purpose, a standalone loader IPL with no operating system underneath, and wrong
for testing a CP nucleus.

## Next steps, in the order I would do them

Each step says what it would establish, not just what it would change, because
every "how much is left" estimate in this file has been wrong and the ones that
were least wrong came from measurements rather than plans.

### P0 — `DMKCNS`: find where the CONTASK queue stops advancing

The one open blocker. The queue has at least three messages on it and exactly
one CCW went out, so the question is narrow: after the first write completes,
what is supposed to dequeue the next CONTASK and why doesn't it?

Instrument, do not read: `b` at `DMKCNS`'s I/O-interrupt entry and at its
write-issue path, then compare the CONTASK chain pointers before and after. The
CONTASK addresses are already known (`X'056360'`, and logo copies at `X'056480'`
and `X'056620'`), so the chain can be walked out of a `savecore` directly.

**Expected outcome:** either CP never re-enters `DMKCNS` after the completion
(an interrupt-routing problem) or it re-enters and finds the chain wrong (a
queue-pointer problem). Those need different fixes and the measurement
distinguishes them in one run.

### P1 — wall 17: the one-byte store into the nucleus

`X'6DD99'` holds `'8'` where every source says `'7'`. One stray byte landing in
static nucleus data is worth more attention than its symptom suggests, because
the same misaddressed store could be landing elsewhere harmlessly today and
somewhere fatal tomorrow. `CPIVER`/`CPIREL`/`CPILEV` are filled from `HDKCPEID`
and `DMKCPICD` plus the time field are filled by `DMKSAV` — four stores into
that area, all near the corrupted byte. A watchpoint on `X'6DD99'`, or a
`savecore` before and after `DMKSAV` runs, identifies which.

It may share a root cause with wall 16; nothing measured says it does.

### P2 — extend `geomchk.py` to the shift classes

Free, no build. Today it knows shifts by 11 and 16 plus two mask families and
reports **15 PROVEN** unconverted sites. It does **not** know shifts by 4, 6 or
20, which is **93 further sites** across CP. Classify, do not convert: the
checker should emit module, sequence, instruction and a *candidate*
classification (address geometry, page count, table size, segment number, byte
offset, key granularity), and `SLL R1,4+4` in `DMKBLD` is the standing proof
that one instruction can hold two different pieces of arithmetic.

**Expected outcome:** a measured conversion list, which is the prerequisite for
P4 and the thing that tells us whether that work is 15 sites or 100.

### P3 — freeze this state as a regression point, which means fixing `I-164`

The current nucleus is worth far more than a source tree carrying another
hundred untested geometry edits: ESA/390 + the DAT conversion + a DASD IPL +
1,477 CCWs + a correctly built logo. `snapshot.py` currently **refuses** to
bless it, because it demands a deck `APPLYING` line and a `TXTLCL CREATED` for
all 40 patched modules and a sliced `spec` build only ever journals the two it
assembled. The tool needs a notion of *incremental on top of a valid snapshot*:
check the modules named in this run, inherit the rest from the parent manifest.

Until then the state is reproducible only as "`SNAP-DAT2` plus one `spec`
invocation", which works but is not a snapshot.

### P4 — central geometry EQUs, once P2 has classified the sites

`PAGSHFT`, `SEGSHFT`, `PTLSHFT`, `KEYSHFT` in `EQU COPY`, replacing only the
subset whose semantics really are geometry. The mechanism is right and matches
this project's existing practice for derived *lengths* (`PAGTSWP`, `PAGBMP`,
`PAGSWPE` in `CORE.XA0033DK`), which was never extended to *shifts* — all 161
are bare literals today.

Two cautions. First, named constants **do not find existing wrong values**; they
make future ones fail at assembly time. P2 finds the defects, so P2 strictly
comes first. Second, `EQU COPY` is copied broadly, so this forces a whole-CP
reassembly — and full builds are exactly what the container has reclaimed three
times (`I-146`), with `spec` unable to express "every module that copies EQU".
Pay that cost once, for the whole class, not per site.

### Not now

- **Patching Hercules** to instrument interrupt presentation. Breakpoints are
  control-validated and sufficient; `I-168` is about `t+ADDR-ADDR`, not about
  needing emulator changes. The standing rule holds: convert CP to the ESA
  interface rather than making the emulator accept S/370 behaviour.
- **The remaining 62 storage-key sites** and the 33 synchronous-channel sites.
  None is in the I/O or paging supervisor; 31 of the 33 are standalone
  utilities. They do not block CP coming up.
- **`DMKVAT`'s `ARCHTECT` table** (milestone B), `I-126` (215 strip sites, M2),
  `I-132` (278 three-byte fields, M5), real storage above 16 MB (M5).

## What CP does today

IPL 6A1 under `ARCHMODE ESA/390`, on a nucleus 32 update decks deep, built by
CE's own 1970s assembler:

- restores its nucleus page image, **sizes real storage correctly at 16 MB**,
  builds its CORTABLE, enumerates **and enables** its 949 subchannels,
- reads volume labels from its DASD and **resolves SYSRES by volume serial**,
- disables the ECPS:VM assists it cannot have and carries on,
- **prints on the operator console**,
- **writes a complete formatted dump of itself** — registers, control
  registers, TOD clock, 3.4 MB of storage — through a converted printer path,
  confirmed again on 2 October by a 30,669-line dump ending in
  `*** END OF DUMP ***`, and
- **builds its startup logo correctly** — `VM/370 Community Edition Version 1
  Release 1.2` with the date and time filled in by `DMKSAV` — copies it into
  CONTASKs and queues them for the console.

Confirmed from inside the machine: `GR01 = 01000000` (the storage size),
`CR6 = FF000000` (the I/O-interruption subclass mask), and the RDEVBLOK array
striding `X'60'` and abutting the RCUBLOKs exactly. Since 1 October the same
facts are confirmed on **two engines**, Hercules 3.13 and SDL 4.9.1, which agree
on all six compared values (`claude/HERCULES-4.md`).

## Wall 11, in detail — RETRACTED CAUSE, and what it actually was

**The diagnosis below is kept verbatim because it is wrong in an instructive
way.** It attributes `PRG018` to the segment table being in System/370 format.
The tables were genuinely wrong and converting them was genuinely necessary —
but they were **not the cause of the exception**, and converting them did not
clear it.

Hercules checks `CR0` at `[3.11.3.2]`, **before fetching a single table entry**:

    if ((regs->CR(0) & CR0_TRAN_FMT) != CR0_TRAN_ESA390)
        goto tran_spec_excp;

    CR0_TRAN_FMT    0x00F80000   bits 8-12, the translation format
    CR0_TRAN_ESA390 0x00B00000   1 MB segments, 4 KB pages

CE sets `CPCREG0 DC X'81800CC0'`, and `X'81800CC0' & X'00F80000'` is
**`X'00800000'`** — System/370 for 4 KB pages and **64 KB segments**. Two bits.

The proof is a converted nucleus whose tables were verified correct *first*, read
out of the stopped machine on 2 October: `CR1 = X'00FFC005'` (bit 0 clear, origin
`X'FFC000'` 4096-aligned), `STE 0 = X'00FFAC0F'` (bit 0 clear, PTO 64-aligned,
PTL 15), a page table of `00000000 00001000 00002000 00003000 …` — textbook
ESA/390 PTEs — **and the identical `PRG018` at the identical `LRA`.** One card,
`CPCREG0 DC X'81B00CC0'`, cleared it. `I-152`.

The lesson is about diagnosis rather than about `CR0`: a dump showed a wrong
value, the wrong value was real, and nobody asked whether it was the value the
hardware complains about **first**. The emulator's own source answers that in
four lines.

## Wall 11 as originally diagnosed — kept for the diff

`DMKDMP908I SYSTEM FAILURE; CODE PRG018`. The code is literal: **018 decimal is
`X'12'`, a translation-specification exception.**

    r 8C     00040012              ILC 2, code X'12'
    r 28     000C1000 0003D9F6     program old PSW -- DAT OFF

The failing instruction is four bytes back, and its two predecessors give it
away:

    03D9EE   B711 2010    LCTL  C1,C1,16(R2)    load the segment-table designation
    03D9F2   B170 1000    LRA   R7,0(,R1)       and translate
    03D9F6   4770 C05E    BNZ   ...

That is **`TRANS.MACRO`'s expansion**, verbatim, and `CR1 = 05FFC840` points at
CP's segment table, which reads

    FFC840   F00561D0  F00562A8  F0056380  F0056458  ...

System/370 STEs. The high nibble `F` is `SEGPLEN` — a page-table length of 16
pages for a 64 KB segment. Under ESA/390 those bits are part of the page-table
origin, the length lives in bits 28–31, and **bit 0 is unassigned and must be
zero.** It is 1 in every entry.

### Why this lands in M1 and not M2

M1's premise is *"DAT off, no paging"*, and the premise is **true** — the
program old PSW shows DAT disabled. It does not help. **`LRA` translates
explicitly, whatever the PSW says**, so the tables are consulted during
initialisation regardless.

`06-LEDGER.md`'s test 8 predicted this from the other direction a week earlier:
it found `LRA`'s *operand* truncated in 24-bit mode and used that to move
AMODE 31 into M2. The same property of the same instruction now pulls the
segment-table format into M1. **No site count changed — only the sequencing.**

---

## What is between here and `DMKCPI966I` — re-measured 18:45 UTC

The three earlier answers to this question were a guess, a sweep, and the
assembler's first verdict. This one is the assembler's **second** verdict, after
the conversion was written.

`CORE.XA0033DK` renames every DAT field with no alias, so an unconverted site
cannot assemble. The midday build raised **176 undefined-symbol diagnostics**
across 16 modules — one per site needing work. The build of 13:15 UTC, with the
conversion written, raised **none**:

```
CONFIRMED    0  flagged and predicted
MISSED       0  flagged but NOT predicted -- the sweep has a hole
COLLIDED     0  a symbol this conversion introduced, already defined
SILENT     176  predicted but NOT flagged -- no diagnostic exists
```

The modules did assemble, so every deck applied and every renamed site was
converted. **~700 cards across 23 modules in 53 update decks.**

That build's module accounting, which took three attempts to state correctly
(`I-147` — I reported the denominator as 198, then 192, and it is 186):

| | |
|---|---|
| modules assembled | **186** |
| OK — clean *and* an object deck | **180** |
| DEFECT — a diagnostic that is not an MNOTE | **5** |
| MISSING — no `TEXT`/`TXTLCL`/`TXTHRC` | **0** |
| MNOTE-only — `DMKRIO`, `I-34`'s 3375/3390 notes | **1** |

The five defects had nothing to do with ESA/390, and all four causes are now
asserted statically by `tools/replchk.py` before a build starts: a replacement
must carry forward any label it covers (`PURCONT`), must not define one that
survives on an unreplaced record (`CKSEG`), must take continuation cards with it
(`DMKCPP` 62000000 carried an `X` in **column 72**), and must only name symbols
the module can see (seven diagnostics from putting nine architecture constants in
`CORE COPY`, copied by 42 modules, instead of `EQU COPY`, copied by 179 of 192).
`I-143`. All four are fixed and the confirming build is in progress.

**So wall 11 is converted and assembles. It is not yet proven at run time**, and
nothing below should be read as claiming otherwise. The measurement that decides
it is the nucleus write and the IPL on both engines.

### Group 1 — RETRACTED: not 10 cards, 95 sites

**The figure in the previous version of this section was wrong, and the way it
was wrong matters more than the number.** It read:

> `DMKCPI` 1, `DMKPSA` 4, `DMKSAV` 5 — unchanged, and still a day.

Ten or eleven sites, specific enough to be believed, and quoted across several
sessions. It was three modules someone had looked at, written down as a total.
`22-S370-ONLY.md`, **in this same directory**, has held the real measurement all
along — 200 nucleus sites across 28 modules, taken from Hercules's own opcode
table. Two documents in one directory disagreeing by a factor of twenty, neither
mentioning the other. The tell was available: `DMKPSA` has **five** `ISK`s, not
four, and a count taken by reading is not off by one in a list of five. `I-141`.

`tools/privchk.py` now reports the **remainder** where `s370only.py` reports the
total, and the two were reconciled before either was trusted: with the deck
subtraction disabled they agree **199 against 200**, the single difference being
`STIDC`, missing from `privchk`'s opcode list until the check found it. Every
other opcode matches site for site — TIO 71, SIO 48, ISK 38, SSK 16, RRB 13,
HIO 5, HDV 4, TCH 3, CLRIO 1 — and both put the same four standalone utilities
outside the nucleus.

**95 sites remain, and the split matters more than the total.**

| | sites | where | on the IPL path? |
|---|---|---|---|
| **storage keys** | **62** | 14 modules, `DMKPTR` holding 23 | not for CP coming up; `DMKPSA`'s five are in the fetch/storage-protection checks, reached when a virtual machine touches storage, and `DMKPTR`'s 23 when paging starts |
| **synchronous channel** | **33** | `DMKLD00E` 19, `DMKVMI` 7, `DMKSAV` 5, `DMKCPI` 1, `DMKENT` 1 | **partly yes** |

`ISK`, `SSK` and `RRB` are `GENx370x___x___` in Hercules's opcode table — they do
not exist in ESA/390 at all, so each one executed is an operation exception.
Walls 7 and 8 were exactly this.

**The channel group cannot ride with the deferred multi-channel work, which is
what the previous version assumed.** `DMKLD00E` is the standalone loader that
loads the nucleus; it runs before CP exists. Its 19 sites are on the
*nucleus-write* path, which runs under `ARCHMODE S/370`, so they do not block
this IPL — they block ever loading a nucleus under ESA/390. `DMKSAV`'s five are
in `QDISK`, `SCPZCAW` and the sense-retry path, which is consistent with CP
already restoring its nucleus image successfully; its main restore path is
converted. `DMKCPI`'s is the sense to the IPL device.

### The storage-key family is cheaper than it looked, and provable first

CE sets `CPCREG0 DC X'81800CC0'` where base `PSA MACRO` has `X'80800CC0'`. The
added bit is `CR0_STORKEY_4K`, and Hercules tests it in exactly three places —
`insert_storage_key`, `reset_reference_bit` and `set_storage_key`, the **2 KB**
instructions — raising a special-operation exception when it is **off**, which is
the S/370 rule for models with the 4 KB-key feature. **CE therefore already runs
with 4 KB keys, and both halves of every paired operation already reach one key.**

That turns what looked like a design decision into an observation. CP keeps a key
per 2 KB half of its own accord (`SWPKEY1`, `SWPKEY2`) and packs both hardware
keys into one register against a two-byte mask, because `ISK` only loads bits
24-31. Reading replicates the one 4 KB key into both halves and yields the
*identical* register value; writing takes `SWPKEY1`, because the second `SSK`
already wins and already carries it. `DMKPRV` answers a guest `ISK` from
`SWPTABLE` rather than from hardware, so the guest keeps seeing its two distinct
keys either way. **No deviation to document — only register pressure per site.**
And because `ISKE`/`SSKE`/`RRBE` are valid in S/370 too, all 67 sites can be
converted and tested on CE **as it runs today**, before anything else moves.
`23-STORAGE-KEYS.md` has the detail; `I-142` records that I twice generalised one
site's answer into a rule before checking.

### Group 2 — the DAT tables: WRITTEN. 176 flagged sites converted, ~90 silent read

**Status as of 18:45 UTC: all 176 flagged sites are converted and the modules
assemble.** The text below is the midday analysis, kept because the measurements
and the reasoning still hold; where it describes work as outstanding, read it as
describing what was done. The one item in it that is **still open** is the `VMSEG`
readers, and that is now the largest known remaining item on the path to CP
coming up — see the estimate at the end.

| module | flagged | module | flagged |
|---|---|---|---|
| `DMKBLD` | 37 **converted** | `DMKCPP` | 6 |
| `DMKPGS` | 31 | `DMKRPA` | 6 |
| `DMKPTR` | 31 | `DMKCPI` | 5 **converted** |
| `DMKATS` | 23 | `DMKMCH` | 4 |
| `DMKCFG` | 16 | `DMKCDS` | 2 |
| `DMKVMA` | 13 | `DMKCFH`, `DMKVMD` | 1 each |

`DMKBLD` and `DMKCPI` are the two modules on CP's own initialisation path — the
ones that must be right before `LRA` can succeed. Both are converted (256 and 29
cards), and **both are awaiting their first assembly as this is written**, so
nothing here claims they work.

**What `DMKBLD` taught, and it is the number that matters:** 37 sites the
assembler named, **46 it could not**. The rename-without-aliases discipline
covers 45% of the work in that module; the rest is arithmetic and idiom around
the flagged sites, which has no diagnostic of any kind (`I-124`). Measured across
the 14 unconverted modules the silent work is about **90 candidates**, so the
remainder is roughly **229 changes** (`I-133`). The naive extrapolation from
`DMKBLD`'s ratio gives 310 and overstates, because `DMKBLD` is the *builder* and
carries allocation arithmetic the others only consume.

**The undesigned ABI item is settled, and the source settled it.** The old
version of this document said `DMKBLDRT`'s packed-address interface *"is reached
by SVC, so widening it is an ABI change across 24 callers"*, and made that the
question deciding whether group 2 was days or weeks. Sequence 00523000 documents
the field:

    *        BYTE 0-1 = FIRST ADDRESS TO RELEASE
    *             FIRST 4 BITS = 0, NEXT 8 BITS = SEGMENT, NEXT 4 = PAGE

Twelve bits of page number, split 8+4 for 64 KB segments and **4+8 for 1 MB
ones**. The field keeps its width and its meaning; only the split moves. **No
widening, and no ABI change** — seven shift and mask literals in two routines.

**A group-2 item that did not exist in the previous answer: the `VMSEG`
readers.** `I-128` is the structural law behind most of the silent work —
System/370 packs lengths and flags into the **high** byte of a pointer, which
24-bit address formation ignores, so a packed word is usable as an address with
nothing to strip; ESA/390 moves them to the **low** bits, which address formation
never ignores. Measured:

| | |
|---|---|
| `L`/`LCTL` of `VMSEG` | **92 sites, 40 modules** |
| of 30 classified: unmasked, needing a mask added | **16** |
| masked with a constant that must change | **14** |
| `IC Rn,VMSEG` reading the length from byte 0 | **9** |
| `LCTL C1,C1,VMSEG` — correct as written | the only safe form |

**None of these is flagged, because `VMSEG` is not renamed**, and unlike the
AMODE items below they are **live in M1**: the bits that stop being ignored are
the low ones, so AMODE 24 does not help. The remedy is the one that worked for
the DAT fields — rename `VMSEG` with no alias and let the assembler enumerate all
105 references — and it is a second rename pass, not a reading exercise.

### Group 3 — open, and genuinely not blocking a clean IPL

| Item | Why it does not block | Lands at |
|---|---|---|
| `I-94` `DMKOPRWT` vector nothing fills | blinds bootstrap errors; does not cause them | open, deliberately |
| TSCH polling deviation | works; deviates from PoP notes 4 and 5 | deferred, with multi-controller work |
| `XAIOFIND`'s one-entry device cache | ~507 full subchannel scans per IPL | performance only |
| `DMKAPI`'s `E612` assist | not in `CPLOAD` under AP=NO | if AP returns |
| **`I-126`: `LA Rn,0(,Rn)` — 215 sites, 79 modules** | AMODE 24 still truncates, so all 215 behave as today | **M2**, simultaneously |
| **`I-132`: three-byte address fields — 278 sites, 81 modules** | 24 bits is adequate below 16 MB | **M5**, as structure changes |

The last two are new, and they are the reason this section was re-measured rather
than edited. Both are invisible through a clean IPL and both are large:

* `I-126` is 215 instances of an **idiom**, documented in `DMKPGS` as
  `LA R3,0(,R3)  24 BIT ADDRESSING`. In AMODE 31 `LA` clears only bit 0, so
  every one of them stops stripping anything — not gradually, but at the
  instant the PSW changes, across 79 modules.
* `I-132` is 278 `ICM`/`STCM`/`CLM` with a three-byte mask. **Only 12 of the
  fields are declared `AL3`/`XL3`**; the rest are three bytes of a wider field
  reached by displacement, so no DSECT sweep finds them. A three-byte field has
  nowhere to put a 31-bit address, so unlike `I-126` these cannot be fixed by
  changing an instruction: all 278 are structure changes, each carrying
  `I-116`'s declaration-versus-generator hazard.

Neither belongs in M1 and neither was in anyone's count. They belong in
`WHAT-31BIT-NEEDS.md`.

## Wall 23 — CP executes data after `enable all`: a module nobody reassembled

```
HHCCP014I CPU0000: Data exception CODE=0007 ILC=2 DXC=01
PSW=000C0000 00F020D4 INST=20E8  LPDR 14,8
19:21:11 DMKDMP908I SYSTEM FAILURE; CODE PRG001 PROCESSOR 00   (another run, at 5640E)
```

Supervisor state, DAT off, and the PSW in the middle of free storage. The landing
site moved whenever a breakpoint was armed on it, which is the signature of a
value that depends on timing — so the destination could not be caught, and the
branch had to be found from its *source*. Three traces, each on one fixed
instruction or module, armed only after `cold`:

1. **w23g** — the dispatcher's unstack `BR R12` (`DMKDSP 01818000`, at `338D4`).
   Nine hits, all sane; the last went to `3D990` with R10 = the IOBLOK.
2. **w23h** — all of `DMKFRET`. It ran to completion correctly and returned.
   What it showed was the *caller's* state: R5 = block+X'20' before FRET was
   entered, and the fault PSW at R5+4 or R5+8 in every run.
3. The code at `3D990` reads `R5` from `IOBLOK+X'50'` and ends in `BR R5`.

`3D990` is not in `DMKSYM`, so `symtab.py` could not name it; the eyecatcher at
`3D5E0` reads `HDKD8C` — VM/370 CE's DIAGNOSE X'8C' module, reached from
`DMKGRFEN` when a 3270 is enabled. It appends its work area after `IOBLOK` with
`ORG ,`, and its compiled code reads `SAVERRET` at `X'50'`: an `IOBLOK` of
`X'48'` bytes, the old nine doublewords. Ours is 23. The reassembled `DMKIOS`
stores the CCW address there, and on completion `HDKD8C` branches to it.

**The cause is the build, not the code.** `ASMDMK EXEC` names 186 DMK modules
and nothing else; `CPLOAD` also loads `HDKD58 HDKD7C HDKD8C HDKCQU HDKCQA`. The
journal shows zero HDK assemblies — all five rode on CE's shipped TEXT decks
with the pre-conversion `IOBLOK` and `RDEVBLOK` layouts. `HDKD58` and `HDKD7C`
also allocate IOBLOKs 112 bytes too short for the ORB/IRB the new `DMKIOS`
writes, a second silent corruptor from the same omission. None of the five has
an S/370-only instruction; `build.sh full` now assembles them (`$HDKMODS`).
**CLOSED 02:33, 4 October.** The 19:42 full build was cut off at nine minutes;
the nucleus that proved it came from `i194build.sh` — SNAP-0828, the twenty
I-192 modules, then `stage asm:HDKD58 asm:HDKD7C asm:HDKD8C asm:HDKCQU
asm:HDKCQA`, then `write` (25 clean assemblies). Under ESA/390, with the
w21 dialogue:

```
/(0009) enable all            logo CCWs to 000A 001F 00C0-00C3, no abend
/(0009) query dasd
02:33:44 DASD 6A0 CP SYSTEM GCCBRX   000
02:33:44 DASD 6A1 CP OWNED  VM50-1   003      ... 17 DASD listed
/(0009) cp disc
02:33:51 DISCONNECT AT 02:33:51 GMT SUNDAY 10/04/26
/(0009) logon maint cpcms
DASD 19D LINKED R/W; R/O BY OPERATOR
DASD 19E LINKED R/W; R/O BY 002 USERS
LOGON AT 02:34:11 GMT SUNDAY 10/04/26
02:34:11 DMKDMP908I SYSTEM FAILURE; CODE FRE013 PROCESSOR 00
```

First typed operator command answered, first MAINT logon. `I-194` fixed. Before
the fix was known, the same evening had also tried the two things this wall
superficially suggested and both were correctly rejected by measurement rather
than argument: the PSA interrupt vectors (`psa.py`: all five new-PSWs point at
the right handlers) and the IOBLOK size (`IOBSIZE` is computed after the
XA0003DK insertion, so correctly built IOBLOKs are 23 doublewords). The symptom
that finally gave it away was the *size* in the traces: every freed block was
11 doublewords, `IOERSIZE`, and no DMK module frees one on that path.

## Wall 24 — FRE013 at `logon maint`

`FRE013` is `DMKFRET`'s FRETRAP (`HRC035DK`): `DMKFREE` plants `X'9AC7E5D5'`
in the doubleword past every block it hands out and `DMKFRET` checks for it. 013
means the block being returned has lost its sentinel — overrun from inside, or
returned with a different size than it was obtained with. After I-194 that is
the right alarm to expect: anything else still sized to the old `IOBLOK`, or
any `TSCH`/`STM` into an IOBLOK that was obtained short, trips exactly this.
**Cause found 02:50 (w24a).** The breakpoint on the `ABEND 13` SVC gave
FREESAVE: R0 = 392 doublewords (`PAGBMP/8`, one page+swap table block),
R1 = `6EEEEEA8`, R2 = R6 = `EEEEEEEE` — `DMKFRE`'s own `X'EE'` padding of a block
nobody wrote. One site in CP frees `PAGBMP/8`: `DMKCFG SHRSLOOP`, the named-system
IPL that MAINT's directory runs automatically at logon. It indexes the user's
segment table with `SYSHRSEG` from `DMKSNT`, and CMS is defined as
`SYSHRSG=(248,249,250)` — **S/370 64 KB segment numbers**. Index 248 into a
16-entry 1 MB segment table lands a kilobyte past it, in EE; the "old STE" is
garbage, and FRET's trap caught the free. `I-195`.

This is the first time CP has physically hit the shared-segment geometry change
that `04`/`05` analysed: CMS's three 64 KB segments are one ESA/390 segment, 15,
and sharing it whole would expose the private top megabyte of every 15–16 MB
machine. The fix is frame-level sharing (`05`), M3 — not a card. For the IPL
proof the wall is bypassed, not solved: `LOGON MAINT CPCMS NOIPL` (suppresses the
directory IPL), `DEF STOR 16M`, `IPL 190` — the CMS nucleus from the system disk,
no named system involved.

Measured 03:00 (w25b): `LOGON … NOIPL` logs on in 16 s, `DEF STOR 16M` answers
`STORAGE = 16384K`, and `IPL 190` runs about seventy seconds before `RPA001`.

## Wall 25 — RPA001 at `IPL 190`: DMKPTRAN builds 16-page tables for 1 MB segments

`DMKRPAGT` asked `DMKPTRAN` for virtual `X'20000'` and was told "addressing
exception" in a 16 MB machine (w26). The segment-fault path, traced (w27), shows
why: on the first fault in a segment `SEGEXA` computes the page range for
`DMKBLDRT,PARM=PAGTONLY` with IBM's 64 KB arithmetic — `SRL R2,16`, `SLL R1,16`,
`SLL R2,20` — so for `X'20000'` it asks for pages 32–47, sixteen of them, and
stores the resulting STE, PTL 0, into 1 MB segment 0. Page 32 is then past the
table: LRA CC3, `ADDEX`, CC2, `RPA001`. Three shifts fix it (`I-196`, in
XA0036DK): segment = address>>20, end = (seg+1)<<20, start page = seg<<24.
**CLOSED 05:06.** The first build did not carry the fix — `stage DMKPTR:XA0038DK`
copies only the deck it names, and the fix was in XA0036DK (`I-197`; `mkrun`
now stages every deck the AUXLCL lists). Rebuilt from the new derived snapshot
`SNAP-I196` (`I-198`) in ten minutes; `r 3DF16` reads `88200014 … 89100014`
and `IPL 190` runs on into the guest.

## Wall 26 — the guest's first instruction: `CP ENTERED; PROGRAM INTERRUPT LOOP`

```
/(0009) ipl 190
CP ENTERED; PROGRAM INTERRUPT LOOP
```

The IPL text was read into the virtual machine and dispatched — the first guest
instruction under this CP — and the guest program-checked at its own program-new
PSW. The expected cause is `I-79`'s third axis arriving where it was always going
to: CMS is a **BC-mode** virtual machine, CP dispatches it with its own PSW
format, and ESA/390 has no BC mode (bit 12 must be one). Under test (w31).

**Measured 05:16 (w31): not BC mode.** The guest PSW is EC (`070D0000`), and
the first guest program check is

```
Operation exception  PSW=070D0000 000203F4  INST=9C00D000  SIO 0(13)
```

CMS's IPL text issues `SIO`. S/370 made that a privileged-operation exception
in problem state, which CP intercepts and simulates; ESA/390 has no `SIO`, so it
is an **operation** exception, and DMKPRV's `OPSIM` reflects those to the guest
— whose program-new PSW is still zero. So the wall is the dropped S/370 opcodes
(SIO/SIOF, TIO/CLRIO, HIO/HDV, TCH/CLRCH, SSK, ISK, RRB) arriving as code 1
instead of code 2. `I-199`: DMKPRV's `CHEKPROB`, where IBM already takes SPKA
and IPK "as if priv op", now takes these seven the same way, with S/370's
problem-state semantics kept (code 2 reflected).

**CLOSED 05:40 (w32).** With I-199 the trace reads: `SIO` simulated, `TIO`
polled and simulated, six times as the IPL text reads the nucleus, then

```
Operation exception  PSW=070D0000 00F80A36  INST=089E  SSK 9,14
```

— **CMS's nucleus, DMSINS, executing at F80A36** under this CP, its `SSK`
simulated as well. The first CMS instructions on a 31-bit CP.

## Wall 27 — PRG006 in CP as CMS initialises

```
Specification exception CODE=0006 ILC=0
PSW=000CF0F0 00006698
05:40:24 DMKDMP908I SYSTEM FAILURE; CODE PRG006 PROCESSOR 00
DMKDMP907W SYSTEM DUMP FAILURE; FATAL I/O ERROR
```

ILC 0: an early PSW specification exception — a PSW loaded with `F0F0` in bits
16–31. Registers are DMKDSP's; `6698` is DMKIOTIN+64. Under measurement
(w33). And the dump failure is its own wall (`I-201`): DMKDMP cannot write to
6A1, so from here every abend's registers must come from Hercules.

**Cause found 06:00 (w35).** A breakpoint on CMS's first instruction, `F80A36`,
showed real `X'7A'` already `F0`, the instruction `SSK 9,14` with R9 = `F0`,
R14 = `3F000`, and guest page 0 at real `E78000` (so not a frame-0 mapping).
`DMKPRV SEGOK` locates the swap-table entry for a key instruction with S/370
geometry — byte 1 of the address as the segment, the high nibble of byte 2 as
the page — so `3F000` indexes STE 3, which is not built, and the key byte is
stored through a pointer loaded from −12: into the I/O new PSW, one half page
per byte. `I-200`, XA0041DK: segment = address>>20, page = bits 12–19, and the
two deferred R-12 real-key instructions on that path become ISKE/SSKE.

**CLOSED 06:33 (w37).** And with it, the IPL walls end where they were always
meant to:

```
/(0009) ipl 190
VM Community Edition V1 R1.2
Y (19E) R/O
Segment GCCLIB is not loaded because virtual machine memory is in use.
DMSITP141T PROTECTION EXCEPTION OCCURRED AT F30CB6 IN ROUTINE DMSREX.
CMS
/(0009) query disk
Label  CUU M  Stat  Cyl Type Blksize   Files  Blks Used-(%) Blks Left  Blk Total
MNT191 191 A   R/W   30 3350  800        334       3681-22      13419      17100
CMSDSK 190 S   R/O   59 3350  800        172      19537-58      14093      33630
MNT19E 19E Y/S R/O   70 3350  800        710      28263-71      11637      39900
Ready; T=0.01/0.01 06:33:42
```

**CMS reaches `Ready;` under VM/370+ running in ESA/390 mode**, 4 October
2026, 06:33 UTC, Hercules 3.13. MAINT, `LOGON … NOIPL`, `DEF STOR 16M`,
`IPL 190`. The minidisks are accessed through CP's SSCH path, the system
profile runs, a typed command is read and answered from the file system.

## Wall 28 — `DMSITP141T PROTECTION EXCEPTION` in the profile EXEC

CMS survives it and reaches `Ready;`, but the profile does not complete.
`DMSREX` at `F30CB6`. The first thing to test is R-12: CMS sets its 2 KB
half-page keys independently (16,104 SSKs simulated during this IPL) and the
new `SSKE` sets the 4 KB frame from one half. `I-202`.

The lesson belongs next to `I-111`: **the set of modules to reassemble is the
set CPLOAD loads, not the set an EXEC happens to name.** A stale object deck in
a load list fails exactly like a stale snapshot — convincingly, and late.

## Wall 13 — SUPERSEDED heading, kept for the diff: it is no longer where CP
stops, and it was never a wall (see the downgrade above)

Measured 2 October 12:02 UTC, on a nucleus built from 59 modules all assembling
clean (59 OK, 0 DEFECT, each run verified complete), written successfully
(`SYSTEM LOAD DECK COMPLETE`, `Nucleus loaded on VM50-1`, wait state `12`), and
IPLed under ESA/390 on SDL Hercules 4.9.1:

    HHC00801I Processor CP00: Privileged-operation exception interruption
    HHC02324I PSW=040D0000 0006D130  INST=8000D129  SSM  297(13)
    CR00=81B00CC0  CR01=00FFC005
    GR03=00FFC000  GR12=0006C008  GR13=0006D008

What this says:

* **`CR00 = 81B00CC0`** — wall 11's fix is live.
* **`CR01 = 00FFC005`** — the designation is in ESA/390 form and the hardware
  accepted it, along with the segment table and the page tables. CP is past the
  translation that used to fault.
* **`PSW = 040D0000`** — byte 0 `04` sets **bit 5: DAT ON**. Byte 1 `0D` sets
  bit 12 (ESA/390 mode, which is `wall 2`'s requirement met) and **bit 15:
  problem state.**
* **`SSM` is privileged**, so problem state alone explains the exception.

The open question is whose instruction it is, and it has exactly two answers:
CP's own code running with the problem-state bit wrongly set, or a virtual
machine's `SSM` that CP failed to intercept. Two facts bear on it and they point
different ways. `GR03 = 00FFC000` is the segment-table address, which is CP's own
table-walking idiom. But **CP emits no console messages at all** in this run — no
`DMKCPI957I`, no `DMKCPI966I` — so it has not finished initialising, and running
a virtual machine before announcing initialisation would be surprising.

`X'6D130'` is 436 KB in. The pre-conversion nucleus was 336 KB, but the
conversion grew CP's tables substantially — page tables from 32 bytes to 1024,
`PAGBMP` from 1048 to 3136 — so the address being past the old nucleus end is not
evidence either way until the new nucleus size is read from this build rather
than remembered from the last one.

## Wall 12 — not CP's: the build environment is reclaimed mid-run

Recorded here because it is what stopped progress on 1 October afternoon, and
because mistaking an environmental failure for a CP one is how a day goes.

Three verification builds died at 13 minutes, 4 minutes and 9 minutes, each
taking Hercules, the `nohup`'d driver and (the third time) the liveness watcher
together, each leaving a log that ends on a normal `Ready;` with no error. Memory
was 7.5 GB of 8 GB free, disk had 22 GB, the kernel log showed no kill, and the
Hercules script was complete. I added `setsid`, wrote a watcher, and reasoned
from three deaths and one 70-minute success that background work does not outlive
a foreground call.

**One command settled it, two hours late: `uptime` reported 39 minutes against
five hours of work.** The container is reclaimed and restarted. Files on disk
survive; processes do not. Nothing done to a background job survives that.

Two consequences, both now in the driver:

* **A long build is not a thing to protect, it is a thing to avoid.** `full`
  stages 104 files and assembles 186 modules in about seventy minutes. But the
  staleness report already names exactly what changed since the snapshot — 45
  inputs — and the snapshot holds the rest, so `build.sh spec` stages 49 files and
  assembles the 58 affected modules. `I-146`.
* **A reaped run must not be mistaken for a finished one.** `w()` waits for
  Hercules to *disappear* and returns success when it does, so a reaped run
  reached `chk` and `asmchk` looking healthy — 15 card files of 104, no
  assemblies, and therefore no diagnostics to find. That is a **false pass on the
  verification build for the whole conversion**, not merely lost time.
  `mkrun.incomplete()` now compares the log against `hercules.rc` — the script is
  what the run was *asked* to do — and `chk()` calls it first. `I-144`.

The reclaim is also why the 13:15 build's output no longer exists: each `full`
begins by restoring `SNAP-2`, and three restarts discarded 180 good modules to
redo four one-line fixes. `I-111`'s property, invoked carelessly.

## The estimate, stated honestly

**Revised 18:45 UTC.**

**Group 2 is written and now partly proven.** ~700 cards, 23 modules, 53 decks,
zero undefined-symbol diagnostics where there were 176, 59 modules assembling
clean, and — as of 2 October — **the DAT structures it produces are accepted by
the hardware**: the designation, the segment table and the page tables all pass
ESA/390 translation. What remains unproven is everything that happens after
translation succeeds, which is now where CP fails.

**Group 1 is not a day; it is 95 sites.** 62 storage-key, 33 channel. The
storage-key family is the one piece of this project that can be written **and
tested** before anything else moves, because `ISKE`/`SSKE`/`RRBE` are valid in
S/370 and CE already runs with 4 KB keys. That makes it the obvious next
substantial piece of work, not because it is small but because it is *provable*.

**The largest known item still blocking CP coming up is the `VMSEG` readers** —
92 `L`/`LCTL` sites in 40 modules, of 30 classified 16 needing a mask added and 14
carrying a constant that must change. None is flagged, because `VMSEG` is not
renamed; the remedy is the one that worked for the DAT fields, a second rename
pass with no alias so the assembler enumerates all 105 references.

**And the honest part: expect a wall 13 that is not on this list.** Eleven walls
have been found and every one was invisible until the previous one fell. Three
answers to "how much is left" have now been given and all three were wrong — the
first two by guessing, the third by quoting a document that disagreed with
another document in the same folder. Group 3 is not on the path to a clean IPL,
but two of its items are now sized for the milestones that own them.

**Group 2 is about 229 remaining changes**, and that figure deserves its
caveats. It is the assembler's 139 remaining flagged sites plus ~90 measured
silent candidates; the candidates each need reading, and the scan only knows the
patterns already learned. `DMKBLD` produced two that no rule would have predicted
— `S R9,F4` reaching `PAGSWP` through an assumed four-byte gap, and one
`SRL R1,8` serving both a CORTABLE index and a page-table entry because the two
strides happened to agree at 16. **The estimate is a floor on the reading, not a
ceiling on the work.**

What can be said without inventing a figure: **ten walls have fallen in four
days, nine of them in one day**, and every one was closed by a mechanical sweep
plus one build cycle. Wall 11 is the first that requires a **data-structure
change** rather than an instruction substitution, so it is the first that cannot
be closed by a sweep alone — and that, not the site count, is why it is
different. What replaces the sweep is a rename that makes the assembler the
checklist, and the measured answer is that this covers **45%** of the work. The
other 55% is read, with `block.py` narrowing the reading to one page per module.
