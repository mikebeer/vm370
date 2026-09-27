# The bootstrap chain's channel I/O

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
| `DMKCKP` | 23 | 16 | 4 |
| `DMKDMP` | 22 | 17 | 3 |
| `DMKLD00E` | 19 | tbd | — (3 absolute CAW refs) |
| `DMKSAV` | 11 | tbd | — |

Five of `DMKDMP`'s seventeen are free: `TIOIPL`, `DRAINEND`, `DOMONSIO`, `DOTIO`
and `GOTIO` already label the instruction the branch targets, so the branch only
needs the name it could have used all along.

Forward branches over unconverted code are correct as they stand and are left
alone — they belong to the 64-bit pass, which gets the full list of 912 from
`tools/selfrel.py`.
