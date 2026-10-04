# The bootstrap chain's channel I/O

> **Status, 4 October 2026.** Done and proven by execution: `DMKCKP` and `DMKSAV`'s IPL-side entries write and read the nucleus (`IPL 6A1` → `Start ((Warm…`, M3a, 3 October), `LOGOFF` and `SHUTDOWN` checkpoint cleanly, and CP IPLs and runs CMS on both Hercules 3.13 and 4.9.1 (`I-204`; [30-STATE.md](30-STATE.md), [28-IPL-WALLS.md](28-IPL-WALLS.md)). `DMKLD00E` was left S/370 on purpose and stays so — it runs only on the build machine ([26-BUILDING-CMS.md](26-BUILDING-CMS.md)); the "19 sites, 7 branches" work in its last section was never done and is not planned. `DMKDMP`'s conversion assembles and the `STSCH` lookup is in place, but the first real abend dump under ESA/390 failed (`DMKDMP907W`, `I-201`, open — [13-ISSUES.md](13-ISSUES.md)), so abend registers come from Hercules for now. The shim design, the condition-code table, the R0 rule and the self-relative-branch finding (`I-67`, `coverage.py`, `deckscan.py`) all stand.

`DMKCKP`, `DMKDMP`, `DMKLD00E` and `DMKSAV` drive the channel themselves rather
than through `DMKIOS`, because they run before the scheduler exists or after it
has stopped. Between them they hold **77 of CP's 133 channel sites**, and they
are the reason M3a is not reachable by converting `DMKIOS` alone.

## One idiom, seventy-seven times

    TIOSYS   ST    R0,CAW         SET UP CAW
    TIOSYS1  TIO   0(R2)          CLEAR DEVICE
             BNZ   *-4
             SIO   0(R2)          START
             BNZ   TIOSYS
             TIO   0(R2)          TEST
             BC    6,*-4          LOOP IF BUSY OR STATUS STORED
             CLC   CSW+4(2),=AL1(CE+DE,0) SUCCESSFULL READ

Converting that by hand seventy-seven times is seventy-seven chances to get a
condition code backwards, which is what `R-01` and `R-02` are about. So the
reasoning lives in `XAIO.MACRO` — `XASIO`, `XATIO`, `XAHIO` and a device-address
lookup — and each site becomes one line.

## Three decisions that keep the diff small

**The `CAW` stores stay.** The CAW is now an ordinary word of CP's storage, and
`XASIO` reads the CCW address straight out of it. Every `ST Rx,CAW` and
`MVC CAW+1(3),...` keeps working untouched.

**The CSW tests stay.** `XATIO` rebuilds a CSW at the architected location from
the IRB — `IRB+8` is unit status, `+9` channel status, `+10` the residual count.
So every `CLC CSW+4(2),=AL1(CE+DE,0)`, `TM CSW+4,UC` and `MVC SAVECSW(12),CSW`
is unchanged, and that is most of each module. Only the *instructions* convert,
not the status logic. The same shim is already proven in `DMKIOS` (`IOSXCC1`).

**The CCWs stay.** Format-0 CCWs (`R-27`) are the S/370 layout byte for byte, so
all 240 static CCW statements in the nucleus are untouched — including the
self-relative ones, `CCW X'08',*-8-DMKCKP+X'800',0,0`, because CCWs keep both
their layout and their eight bytes.

## Why writing a CSW at X'40' is architecturally safe, not just convenient

The shim writes a CSW at the architected CSW location and reads the CAW from
X'48', which looked like a pragmatic reuse of storage. The ESA/390 assigned
storage layout says it is better than that — those words are **reserved for
S/370 and untouched by ESA/390 hardware**:

    /*040*/ DBLWRD csw;       /* Channel status word (S370)*/
    /*048*/ FWORD  caw;       /* Channel address word(S370)*/
    /*0A8*/ FWORD  chanid;    /* Channel id (S370)         */
    /*0AC*/ FWORD  ioelptr;   /* I/O extended logout (S370)*/
    /*0B0*/ FWORD  lcl;       /* Limited chan logout (S370)*/
    /*0B8*/ FWORD  ioid;      /* I/O interrupt device id   */
    /*0BC*/ FWORD  ioparm;    /* I/O interrupt parameter   */

Three consequences worth having in writing.

The CSW and CAW are ours to use as scratch: no ESA/390 hardware writes either,
so the shim cannot be overwritten under it. That also legitimises `DMKLD00E`'s
`ZCSW EQU 64` / `ZCAW EQU 72` and its three `ST 2,72` by absolute address — they
are storing into a word the architecture leaves alone.

The three fields the `PSA` rename marked `S370CHID`, `S370IOEL` and `S370ECSW`
are exactly the three the architecture itself marks `(S370)`, at X'A8', X'AC'
and X'B0'. The rename agreed with the architecture without having consulted it.

And `IOSSID` at X'B8' with `IOINTPRM` at X'BC' match `ioid` and `ioparm`
precisely, so `MVC SAVEDEV(8),IOSSID` in `DMKCKP` saves the right eight bytes.

## The condition-code inversion, written once

| | cc0 | cc1 | cc2 | cc3 |
|---|---|---|---|---|
| `SIO` | started | CSW stored | busy | not operational |
| `SSCH` | started | status pending | busy | not operational |
| `TIO` | **available** | CSW stored | busy | not operational |
| `TSCH` | **IRB stored** | **no status pending** | — | not operational |

`SIO` and `SSCH` already agree on cc0, cc2 and cc3, and their cc1 differs in
wording only — both mean "go and look at the status".

`TIO` and `TSCH` have cc0 and cc1 **inverted**. `TIO` cc0 means the device is
free; `TSCH` cc1 means nothing is pending, which is the same fact. `XATIO` swaps
them back, so the branches around each site are left exactly as they were.

The subtlety that makes the loops still terminate: `BC 7,*-4` after a `TIO` means
"keep testing until the device is clear", and it works because `TIO` *consumes*
the status it reports. `TSCH` consumes it too, so the loop behaves identically.

## Setting a condition code is harder than it looks

Two bugs in the first draft of `XAIO`, both of the class the macro exists to
prevent:

* `LTR R15,R15` with R15 = 1 sets **cc2, not cc1**. "CSW stored" was being
  reported as "busy". Correct sequence is `LA R15,1` then `LCR R15,R15`, whose
  negative result gives cc1.
* **Nothing in the `LTR` family can set cc3 at all.** The not-operational path
  was reporting cc2. `TM` against an all-ones byte is the only way.

## R0 must stay zero

Every caller has `USING PSA,R0` in force, so `CAW` and `CSW` resolve as
displacements off R0 — and the macros reference both *before* restoring
registers. The first draft used R0 as the subchannel counter in the lookup and
would have returned it non-zero, silently displacing every lowcore reference in
the expansion by the subchannel number. R15 is the counter now, and the device
number is matched with `CLC`, so R0 is never touched at all.

## Why the lookup scans rather than reading RDEVSSID

`DMKCPI` fills `RDEVSSID` for every device (`XA0013DK`), so reading it would be
cheaper. The lookup scans subchannels with `STSCH` anyway, because **`DMKDMP`
runs after an abend**, when CP's control blocks are exactly what cannot be
trusted. A dump that needs a healthy `RDEVBLOK` in order to write itself is no
use on the occasion you need it. The cost is up to 256 `STSCH`s per distinct
device, cached after the first, in code that runs once.

## Self-relative branches

`R-26`. Every backward `*-n` that spans a converted instruction becomes a label
**in the same deck**, because after conversion it would land inside a macro
expansion — assembling perfectly and branching to a garbage boundary, with no
diagnostic anywhere.

| Module | I/O sites | backward branches spanning them | `INTTIO` |
|---|---|---|---|
| `DMKCKP` | **25** | 16 | 4 |
| `DMKDMP` | **22 channel + 4 key** | 17 | 3 |
| `DMKLD00E` | 19 (out of scope) | — | — (3 absolute CAW refs) |
| `DMKSAV` | 11, of which 6 convert | — | — |

The two bold figures are corrections. `DMKCKP` was counted as 23 by hand and
converted 23, so the two the count never included — a `TIO` at 00733000 and an
`SIO` at 00742000 — stayed S/370 **inside the drain loop whose `HIO` at
00726000 had just been converted**. `DMKDMP` kept an `SIO` at 00769000 whose
own cc0 target `TIOIPL` was converted, and a `PRSIO` at 01161000 between two
converted sites. Each would have taken an operation exception on the
instruction after one that had just been converted, and each assembled
perfectly.

Nothing caught it for three commits, because every check in the project
answered a different question. `tools/coverage.py` now closes that gap by
diffing `s370only.py`'s site list against each deck's own `./ R` and `./ D`
ranges, and `tools/deckscan.py` checks the punched object deck, which is
ground truth. `I-67`.

Five of `DMKDMP`'s seventeen are free: `TIOIPL`, `DRAINEND`, `DOMONSIO`, `DOTIO`
and `GOTIO` already label the instruction the branch targets, so the branch only
needs the name it could have used all along.

Forward branches over unconverted code are correct as they stand and are left
alone — they belong to the 64-bit pass, which gets the full list of 912 from
`tools/selfrel.py`.

## DMKLD00E: three suspected problems, one real

`DMKLD00E` is the nucleus loader — the first CP code that runs — and it looked
like the hardest of the four. Checking each worry in turn, only one survived.

**It has no PSA symbols.** True, and it is the real problem. `DMKLD00E` defines
its own `ZCSW EQU 64` and `ZCAW EQU 72` and also stores by absolute address,
`ST 2,72` three times (`I-53`). `XAIO`'s subroutines reference `CAW` and `CSW`,
which would not resolve there.

*Fix:* `XAIOWORK` now takes `CAW=` and `CSW=` keyword parameters defaulting to
`CAW` and `CSW`, so `DMKLD00E` invokes `XAIOWORK CAW=ZCAW,CSW=ZCSW`. The names
are needed only by the subroutines, and `XAIOWORK` is what emits them, so they
are ordinary keyword parameters — no `GBLC`, no per-call-site clutter, and the
other three modules are unaffected.

*And the absolute stores need no change at all.* `ZCAW EQU 72` is X'48', which
the ESA/390 assigned-storage layout reserves for S/370 and never writes. So
`ST 2,72` is storing into a word the architecture leaves alone, and `XAIO` reads
the same word. Unlike `DMKCKP`'s `184`, this one is harmless.

**It has no register equates.** False. `COPY EQU` at seq 02916000 brings
`R0`-`R15`, and Assembler XF's second pass resolves the forward references. None
of the four bootstrap modules defines them locally; all four get them from
`EQU.COPY`.

**Its bare register numbers will not fit the macro.** False. `XAIO` expands
`LR R1,&DEV`, and `&DEV` is substituted textually, so `XASIO 2` assembles
exactly as `XASIO R2` does. `DMKLD00E`'s `0(2)`, `0(8)` and `0(1)` need only the
register number carried across.

**What is left** is ordinary work *(superseded — see status note; the loader
stays S/370)*: 19 sites, 7 backward branches to label, and
two oddities to leave alone deliberately — `BC 1,*-8` at 00421000, which spans
back over a `TM ZCSW+4,X'10'` onto the `TIO` and so does need a label; and
`LPSW *-8` at 02090000, which loads a PSW from eight bytes before itself. That
last one is not near any converted instruction, so it stays, and it belongs to
the 64-bit pass along with the other 905.
