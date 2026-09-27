# M1 step 4: what DMKIOS's ten I/O sites actually become

27 September 2026. `03-CP-INVENTORY.md` and the `arch/31bit` README both say
**"I/O is ten instruction sites, not 1,493 references"** — every S/370 I/O
instruction in `DMKIOS` is a single instruction with the same `0(R1)` operand, so
a shim synthesising a CSW leaves all 1,917 CAW/CSW references working.

Reading all ten confirms the locality claim exactly. It also shows the framing
**understates the semantic work**, in a way worth correcting before writing code:
the ten sites are ten *decisions*, not ten substitutions, and two of them are not
conversions at all.

## The ten sites, as they are

    953   SIO   0(R1)     START THE I/O OPERATION
    2335  SIO   0(R1)     ATTEMPT TO DO SENSE
    1010  TIO   0(R1)     ISSUE REQUESTED TEST I/O
    1104  TIO   0(R1)     YES - CLEAR STATUS
    2284  TIO   0(R1)     SEE IF IT'S REALLY BUSY
    2299  TIO   0(R1)     IS IT BUSY ?
    1021  HDV   0(R1)     ISSUE REQUESTED HALT I/O
    1275  HDV   0(R1)     TRY AGAIN TO HALT THE DEVICE
    1233  TCH   0(R1)     PRIME FOR CHANNEL AVAILABLE INT.
    1242  TCH   0(R1)     PRIME FOR CHANNEL AVAILABLE INT.

Ten instructions, one operand form, confirmed. And six condition-code branches
depend on a CSW having been stored: `988`, `1017`, `1029`, `2338` as `BC 4,…` and
`1253`, `1269` as `BO` after a logout test.

## What each group becomes

| Group | Sites | Becomes | Difficulty |
|---|---|---|---|
| `SIO` | 2 | `SSCH` + ORB + the cc1 shim | mechanical, plus the shim |
| `TIO` "is it free?" | 1 | **`STSCH`** and test SCSW activity control | condition code inverts |
| `TIO` "get/clear status" | 3 | `TSCH` | close to direct |
| `HDV` | 2 | `HSCH`, with cc0 re-read per site | semantic, needs care |
| `TCH` | 2 | **deleted** | no equivalent exists |

### `SIO` → `SSCH`: the operand meaning inverts

    IOSTCAW  ST    R2,CAW              store the CCW address in the CAW
             LH    R1,IOBRADD          real DEVICE address into R1
             SIO   0(R1)
             BC    8,IOSCC0            started
             BC    4,IOSCC1            CSW stored
             BC    1,IOSCC3            not operational
             (fall through = cc2, busy)

For `SIO`, **R1 carries the device address and the operand is unused**. For
`SSCH`, **R1 carries `X'0001'` in the high halfword and the subchannel number in
the low, and the operand is the ORB address.** The two swap roles, which means
neither `LH R1,IOBRADD` nor `ST R2,CAW` survives:

- `ST R2,CAW` becomes a store of the CCW address into the ORB's word at +8.
  The rest of the ORB is a template: interruption parameter, `flag5 = X'80'`
  (format-1), **`LPM = X'80'`** — not `X'00'`, which `SSCH` reads as "no path
  available" rather than "any path", proven in test 5.
- `LH R1,IOBRADD` becomes a load of a **subsystem-identification word**, which
  has to come from somewhere.

**Condition codes 0, 2 and 3 map directly.** `SSCH` cc0 = accepted, cc2 = busy,
cc3 = not operational, and CP's three branches want exactly those. **Only cc1
differs**, and that is the whole of the `SIO` gap: `SIO` cc1 means *"here is your
CSW, now"*; `SSCH` cc1 means *"status is pending, go and fetch it"*.

### Where the subchannel number comes from

This is the one genuinely new piece of design, and it is not in any existing
document.

Subchannel numbers are **not derivable from device addresses** — Hercules assigns
them in device-definition order, as real hardware assigns them at
configuration. So CP has to learn the mapping, exactly as MVS/XA did: walk the
subchannels with `STSCH` at initialisation and read each PMCW's device number.

The result belongs in `RDEVBLOK`, which CP already chains by device address, so
the lookup path exists. **Stored as a full word rather than a halfword** —
`X'0001'` in the high halfword and the subchannel in the low — so the site
becomes one instruction with no arithmetic:

    L     R1,RDEVSSID         subsystem id: X'0001' || subchannel

rather than a load, a shift and an OR. That is a new field in `RDEVBLOK`, so a
second `AUXLCL` deck against the block definition, and a new initialisation loop
in `DMKCPI` — which is M1 step 6 and was already going to be touched.

**`IOBRADD` stays as it is.** It is the real device address and 21 other places
still want it; nothing about this change makes it wrong.

### The CSW shim, and what it must actually fill

`TIOCC1` and `HIOCC1` are the shim's consumers, and they show precisely which
bytes matter:

    TIOCC1   CLI   CSW+4,SM+CUE+BUSY   370X STATUS = X'70' ??
             TM    CSW,X'04'           IS LOGOUT PENDING INDICATED ?
             CLI   CSW+4,SM+BUSY       CONTROL UNIT BUSY ?
             CLI   CSW+4,BUSY          IS THE DEVICE BUSY ?

So the shim maps, after a `TSCH` into an IRB:

| CSW byte | From |
|---|---|
| `CSW+4` device status | the SCSW's device-status byte |
| `CSW+5` subchannel status | the SCSW's subchannel-status byte |
| `CSW+6,7` residual count | the SCSW's count |
| `CSW+1,2,3` CCW address | the SCSW's CCW address, minus 8 |
| **`CSW` byte 0 bit `X'04'`** | **nothing — see below** |

`TM CSW,X'04'` is the **logout-pending** bit, and that is `R-03`: the ESA/390
channel subsystem has no limited channel logout. Its replacement is the ESW and
ERW in the IRB plus `STCRW`, which report different things at a different time.
For M1 the shim leaves that bit **always zero**, so `BO IOSCCSET` is never taken
and those two paths become dead — deliberately, and noted, because a stub that
silently reports "no logout" is the safe direction: it loses error detail, it does
not invent it.

### `TIO` splits, because one of its uses inverts

`TIO` cc0 means *the device is free*. `TSCH` cc0 means *status was pending and has
been cleared*. **Those are close to opposites**, so a blanket `TIO` → `TSCH` is
wrong at the site that asks "is it free?":

    IOSQTIO  TIO   0(R1)
             BC    8,IOSDVFRE     CC = 0   DEVICE IS FREE
             BC    4,TIOCC1       CC = 1   CSW STORED
             BC    1,IOSCC3       CC = 3   NOT OPERATIONAL
             B     IOSQBSY        (cc2) queue until the channel is free

"Is it free" is an **activity** question, and in ESA/390 that is `STSCH` followed
by a test of the SCSW's activity-control and status-control fields — not `TSCH`,
which would *clear* pending status as a side effect of asking.

The other three `TIO` sites genuinely want status and are content for it to be
cleared — `1104` is even commented `YES - CLEAR STATUS` — so those are `TSCH`.

### `HDV` → `HSCH`, with the condition codes re-read per site

    IOSQHIO  HDV   0(R1)
    HIOBR    BC    8,IOSCBUSY     CC = 0 CONTROL UNIT BUSY
             BC    4,HIOCC1       CC = 1 CSW STORED
             BC    1,IOSCC3       CC = 3 NOT OPERATIONAL

CP reads `HDV` cc0 as *control unit busy*. `HSCH` cc0 means *the halt was
accepted*. Those are not the same statement, so this is not a branch-table
rewrite — each of the two sites needs its flow re-derived. The second site
(`1275`, `HIORLOOP`) retries a halt up to sixteen times and rejoins `HIOBR`, so
the two share a fate.

### `TCH` is deleted, not converted

Both `TCH` sites are preceded by `LH R1,RCHADD` — a **channel** address — and
both are commented `PRIME FOR CHANNEL AVAILABLE INT.`

ESA/390 has no channels to test and no channel-available interruption. The
channel subsystem queues a start request itself and reports cc2 when a subchannel
is busy; there is no host-visible "channel free again" event to prime for. The
surrounding machinery — `RCHSTAT,RCHBUSY`, `IOSRSTCH`, the channel queue and
`RCHQCNT` — is modelling something the hardware now does.

**So two of the ten sites disappear, and take a mechanism with them.** That is
the largest single simplification available in this conversion, and also the one
most likely to be got wrong by deleting too much: the channel queue also
serialises CP's own bookkeeping, and a subchannel that answers cc2 still needs
the IOBLOK requeued somewhere. M1 does not exercise any of it — one console
device, never busy — so the M1 move is to leave the queueing code in place and
make the `TCH` sites unconditionally take the "channel free" path.

## Correcting the inventory's framing

"Ten instruction sites" is right about *where* and understates *what*. The honest
version:

> Ten sites, in one module, with one operand form — so the conversion is local.
> Two are `SSCH` plus a shim, three are `TSCH`, one inverts into `STSCH`, two are
> `HSCH` with flows that need re-deriving, and two are deleted along with the
> channel-available mechanism they serve. The CAW/CSW shim then leaves 1,917
> references working, which is the part that was never in doubt.

The locality is the good news, and it is real. The claim that was doing too much
work is the implication that locality means mechanism-preserving.

## What step 4 needs, in order

1. `RDEVSSID` — a fullword in `RDEVBLOK`, as an `AUXLCL` deck against the block
   definition.
2. The ORB template and the CCW-address store, replacing `ST R2,CAW`.
3. `IOSCSW` — the shim: `TSCH` into an IRB, synthesise the CSW at `X'40'`, leave
   the logout bit zero. One subroutine, called from each cc1 path.
4. The two `SIO` sites, then the four `TIO`, then the two `HDV`.
5. The two `TCH` sites forced to the free path.
6. The subchannel-discovery loop in `DMKCPI` — step 6, and the reason step 4
   cannot be tested end-to-end before it.

Steps 1–5 are a deck against `DMKIOS` plus one against `RDEVBLOK`'s definer.
Step 6 is why `DMKIOS` will assemble long before it runs.
