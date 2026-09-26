# Two design hypotheses, checked against CP's source

26 September 2026. The proposal asserted two things from counting rather
than reading. Both have now been checked, and **both were wrong in the
direction of being too pessimistic.** Companion to 03-CP-INVENTORY.md, which
has the counts.

---

## 1. `DMKVAT` is probably the least of the DAT work, not the most

The proposal ranked `DMKVAT`'s shadow-table translation as "the hard one,
and the largest risk". That was asserted before reading it.

### CP is already parameterised by DAT architecture

`DMKVAT`'s own prologue:

    * REGISTER USAGE -
    *        GPR  9 = ARCHITECTURE CONTROL INDEX

R9 indexes a parameter table, `ARCHTECT`, loaded from `EXTCR0+1` — the
guest's CR0 byte 1, which holds the page and segment size controls. Thirty
references in `DMKVAT` are `something(R9)`:

    MAXSEGS   maximum segment-table length code
    SEGMASK   segment number mask
    SEGSHFT   shift count to justify the segment number
    PAGEMSK   page number mask
    PAGSHFT   shift count for the page number
    PAGINCR   increment of length for the segtable code
    PAGTLEN   maximum page-table length in bytes
    PTEINCR   SIZE OF PAGE TABLE ENTRY
    PINVBIT   PAGE-INVALID BIT IN PTE
    ZEROBIT   "MUST BE ZERO" BITS IN PTE

**The PTE size, the invalid bit position and the must-be-zero bits are
already parameters.** Those are three of the four things an ESA/390 PTE
differs in.

### And four of the eight variants already use fullword entries

`ARCHTECT`'s own comment:

    *        ARCHTECT IS INDEXED WITH C-REG 0, BYTE 1 VALUE AS FOLLOWS:
    *
    *        INDEX X'40' - SMALL PAGE, SMALL SEG, HALFWORD ENTRIES
    *              X'50' - SMALL PAGE, LARGE SEG, HALFWORD ENTRIES
    *              X'60' - SMALL PAGE, SMALL SEG, FULLWORD ENTRIES
    *              X'70' - SMALL PAGE, LARGE SEG, FULLWORD ENTRIES
    *              X'80' - LARGE PAGE, SMALL SEG, HALFWORD ENTRIES
    *              X'90' - LARGE PAGE, LARGE SEG, HALFWORD ENTRIES
    *              X'A0' - LARGE PAGE, SMALL SEG, FULLWORD ENTRIES
    *              X'B0' - LARGE PAGE, LARGE SEG, FULLWORD ENTRIES

and `CODE70` — small page, large segment, fullword entries:

    CODE70   DC    X'000FF800'        PAGEMSK
             DC    X'7FF00000'        SEGMASK
             DC    X'04',X'02'        PINVBIT, ZEROBIT
             DC    H'09',H'18',H'4'   PAGSHFT, SEGSHFT, PTEINCR
             DC    H'127',H'2048',H'128'  MAXSEGS, PAGTLEN, PAGINCR

**`SEGMASK X'7FF00000'` is bits 1-11 — 2,048 segments of 1 MB, which is a
31-bit address space.** `PTEINCR 4` is a fullword entry. And `PINVBIT
X'04'` applied to byte 2 of a fullword PTE is bit 21, which is exactly
where ESA/390 puts the page-invalid bit.

The index bit that selects fullword entries is **CR0 bit 10**,
`0x00200000` — the same bit stock Hercules rejects as a
translation-specification exception in S/370 mode, and the one the
Hercules/380 patch repurposes.

### What this means, carefully

CP's shadow-table machinery was written knowing about a fullword-PTE,
2,048-segment, 1 MB-segment variant. The geometry the ESA/390 conversion
needs is not a new concept to `DMKVAT`; it is an existing table row.

**Caveats, because this is too good to accept uncritically:**

  - The table entries existing does not prove the code paths were ever
    exercised. Untested variants in thirty-year-old code are normal, and
    `CODE60`/`CODE70` may be dead. Establishing whether any guest ever
    drove them is worth doing before relying on it.
  - The **segment table entry** format differences are *not* in the
    parameter set. `PINVBIT` and `ZEROBIT` govern the PTE only. The STE's
    `SEGPLEN` moving from bits 0-3 to bits 28-31, and its invalid bit from
    `X'01'` to `X'20'`, are in code rather than tables.
  - `PAGTLEN 2048` for `CODE70` implies 512 fullword entries per segment,
    where ESA/390's 1 MB segment of 4 KB pages needs 256. So the row is
    close to ESA/390 but not identical, and the difference needs
    understanding rather than patching.
  - The ECPS:VM hardware assists take `ARCHTECT` as an operand —
    `DMKVATZP DC X'E60B',S(ARCHTECT,0(R9))` and `DMKVATZS DC
    X'E60A',S(ARCHTECT,EXTSHCR1)`. A new architecture row would have to be
    understood by the assist too, or the assist disabled. The CE Hercules
    config already has `ECPSVM NO`, so this may be moot in practice, but it
    is a real coupling.

**Revised ranking**: the biggest DAT risk is not `DMKVAT`. It is the
**64 KB → 1 MB segment change and its effect on shared segments**
(`DMKATS`, named saved systems), because that is a compatibility decision
rather than a parameter, and no table row solves it.

---

## 2. The CAW/CSW shim survives contact with `DMKIOS`

The proposal claimed CP's CAW/CSW surface could be preserved by translating
only inside its I/O supervisor. That was a design sketch. It holds up.

### The instruction sites are few and uniform

Every S/370 I/O instruction in `DMKIOS`, with its line number:

     953   SIO   0(R1)     start the I/O operation
    2335   SIO   0(R1)     attempt to do sense
    1010   TIO   0(R1)     issue requested test I/O
    1104   TIO   0(R1)     clear status
    2284   TIO   0(R1)     see if it's really busy
    2299   TIO   0(R1)     is it busy?
    1021   HDV   0(R1)     issue requested halt I/O
    1275   HDV   0(R1)     try again to halt the device
    1233   TCH   0(R1)     prime for channel available interrupt
    1242   TCH   0(R1)     prime for channel available interrupt

**Ten sites, every one a single instruction with the same operand form** —
R1 holds the device address throughout. That is about as concentrated as a
conversion target gets.

### The CAW is built in two places

    926   BO    IOSRCAW        yes, use the restart CAW
    944   ST    R2,CAW         store in the channel address word
   1109   L     R2,CAW         reload address of CCWs from CAW
   1499   MVC   8(4,R14),CAW   save CAW
   2321   ST    R1,CAW         set up channel address word

Only 944 and 2321 *build* one. The rest read or save it.

### And the status surface stays untouched

Across all 201 CP modules:

    CSW (lowcore X'40')     800
    IOBCSW (IOBLOK copy)    409
    CAW (lowcore X'48')     347
    IOBCAW                  230
    VDEVCSW (virtual dev)   131
                           ----
                           1,917

**If the shim synthesises a CSW at `X'40'` after each `TSCH`, every one of
those references keeps working unchanged.** That is exactly what Hercules
does in the other direction for S/370 guests — `store_scsw_as_csw()` writes
at PSA+`X'40'` with prefixing applied, and `scsw2csw()` is a byte copy of
SCSW+4..11 with byte 0 overlaid.

So the honest estimate for CP's real I/O layer is **ten instruction sites
plus the interrupt entry**, not 1,917 references.

### The hard spots, now located precisely

    988   BC    4,IOSCC1       BRANCH IF CSW STORED
   1017   BC    4,TIOCC1       CC = 1    CSW STORED
   1029   BC    4,HIOCC1       CC = 1 CSW STORED
   1252   TM    CSW,X'04'      IS LOGOUT PENDING INDICATED ?

The first three are the **`SIO` condition-code contract**: `SIO` sets cc=1
with a CSW stored *synchronously*, and `SSCH` only queues the request. This
is the gap IBM added the initial-status-interruption facility for. (An earlier
version of this document said Hercules cannot prototype it because it ignores
`ORB5_I`. **That was wrong** — the facility has been in Hercules since version
1.39, November 1999, and Hyperion 4.x implements the deferred-condition-code
table with it. See `../arch/31bit/README.md`.) There are
roughly a dozen such condition-code branches, one cluster after each I/O
instruction.

The fourth is **channel logout**, replaced in XA by the ESW and ERW in the
IRB plus channel-report words from `STCRW`. The bit survives a copy; what
it points at does not.

Everything else in `DMKIOS` that touches status is decoding the device and
channel status *bytes*, and those are bit-for-bit identical between the CSW
and the SCSW — which is why Hercules uses one set of constants for both.

    1106   TM    CSW+4,DE            is access arm already there?
    1248   CLI   CSW+4,SM+CUE+BUSY   370X status = X'70'??
     642   TM    CSW+5,CDC+CCC+IFCC  was this a channel error?

None of those change.

---

## 3. CP already hand-encodes instructions its assembler does not know

The Milestone 0 macro technique is not novel — it is CP's own idiom.
Twenty-one sites across the tree use `DC X'E6nn',S(operands)` for the
ECPS:VM assist instructions:

    DMKCCW0  DC    X'E604',S(CCWDATA,CCWEXITS)
    DMKDSP0  DC    X'E60D',S(DSP0LIST,DSP0EXIT)
    DMKVATZP DC    X'E60B',S(ARCHTECT,0(R9))
    DMKVATZS DC    X'E60A',S(ARCHTECT,EXTSHCR1)
             DC    X'E603',S(DMKPTRPL,0(R2))
             DC    X'E614',S(MAXSIZE,BYTBL-1)

Opcodes `E602` through `E615`, in `DMKAPI`, `DMKCCW`, `DMKDSP`, `DMKFRE`,
`DMKPTR`, `DMKSCN`, `DMKUNT`, `DMKVAT` and `DMKVMA`.

So an `XAOPS` MACLIB emitting `DC X'B233',S(&ORB)` for `SSCH` is doing what
CP has always done, only tidier — a named macro rather than a raw constant,
so the mnemonic appears in the listing and the operand is checked.

---

## What this does to the estimate

Before reading the source, the proposal had:

  - `DMKVAT` shadow tables as the largest risk
  - 1,493 CAW/CSW references as the I/O surface
  - 3,600 `BAL`/`BALR` sites as an audit
  - 567 packed-address sites as a work item

After reading it:

  - `DMKVAT` is parameterised and may need a table row, not a rewrite
  - the I/O surface is **10 instruction sites plus a dozen condition-code
    branches**, because the shim preserves 1,917 references
  - `BAL`/`BALR` self-correct in 31-bit mode; only boundaries matter
  - the packed-address population is **582 `ICM`/`STCM` sites**, not 567
    mixed with CCW templates — the `AL3` ones are format-0 channel
    programs and stay

**What got harder, or at least clearer:** the 64 KB → 1 MB segment change
and shared segments; the `SIO` condition-code semantics, which no field
mapping fixes, though it is testable under Hercules after all; and channel
logout.

Three of those four are design decisions rather than code volume. That is a
better problem to have, but it means the next useful step is Adrian's
judgement rather than more counting.
