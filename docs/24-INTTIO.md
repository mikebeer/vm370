# The INTTIO group: one symbol, two unrelated jobs

`INTTIO EQU INTKFLIN+2` is the S/370 I/O interruption code at X'BA', the
interrupting device address. Eighteen sites in four nucleus modules reference
it, and the reason a blind rename was refused is now precise rather than
cautious: **the field is doing two different jobs**, and only one of them is
about hardware.

## Group A — CP passing a value to itself (4 sites)

    DMKVMI  00806000   STH   R13,INTTIO      SET IPL DEVICE ADDRESS IN EXT MODE
    DMKCKP  00208000   LH    R0,INTTIO       GET SYS IPL ADDRESS
    DMKCKP  00274370   STH   R1,INTTIO       Place as i/o interrupt code
    DMKDMP  00777000   STH   R15,INTTIO      SAVE IPL DEVICE ADDRESS

The instruction before `DMKVMI`'s is `STH R13,IPLPSW+2`, chosen by mode: in BC
mode the I/O interruption code is in the PSW, in EC mode at X'BA'. So CP is
**mimicking the hardware**, writing the IPL device address wherever a real I/O
interruption would have left it, so that later code finds it in the architected
place.

Nothing about ESA/390 requires that, and CP already has the field it should
have used:

    SYSIPLDV DS    1H -      P*3  DEVICE ADDRESS OF SYSTEM IPL DEVICE

It is in the PSA, `DMKCPI` sets it at its seq 00484000 — `STH R10,SYSIPLDV
SAVE UNIT ADDRESS OF IPL'ED DEVICE` — and six places read it, including
`HDKCQA`, `DMKDMP` and `DMKCKP` itself, two lines above one of the sites above:

    DMKCKP  00274360   LH    R1,SYSIPLDV     Get the IPL device address
    DMKCKP  00274370   STH   R1,INTTIO       Place as i/o interrupt code

So that pair reads the right field and then copies it into the wrong one. These
four sites are not a translation problem at all: three become `SYSIPLDV` and one
is deleted. Under ESA/390 X'BA' falls inside the subsystem-identification word,
so a device address stored there would corrupt it — which is exactly what the
no-alias rename was for.

## Group B — reading what the hardware stored (14 sites)

`DMKIOT`'s ten, plus `DMKCKP` 00772000 and 01495500 and `DMKDMP` 00722000 and
01151000, all read a device address the hardware left after a real interruption.
`DMKDMP`'s is labelled `DSKIOINT EQU * HERE UPON HARDWARE I/O INTERRUPT` and
`DMKCKP`'s is `IOINT EQU *`, the I/O new PSW's target.

ESA/390 presents no device address. It stores the subsystem ID at X'B8', the
**interruption parameter** at X'BC', and hands over the rest through `TSCH`.

### The interruption parameter is CP's to choose

That is what makes this tractable. From Hercules:

    channel.c   memcpy( dev->pmcw.intparm, orb->intparm, ... )   /* SSCH sets it  */
    io.c:284    memcpy( dev->pmcw.intparm, pmcw.intparm, ... )   /* MSCH sets it  */
    channel.c   FETCH_FW( *ioparm, dev->pmcw.intparm )           /* every interrupt */

It lives **in the subchannel**, not in the request, so it is presented on
unsolicited interruptions as well as on ones CP started.

So CP puts the real device address in the low half of each subchannel's
interruption parameter, and reads it back at `IOINTPRM+2`. Every site becomes a
displacement change, every existing device-address comparison keeps working, and
`DMKSCNRU` lookups are untouched. No reverse-lookup table, no scan.

`MSCH` must set the enable bit and the parameter **together**, because a
subchannel reset clears both — Hercules zeroes `intparm` in the same block that
clears `PMCW5_E`, `PMCW4_ISC`, `pnom` and `lpum`. Any path that re-enables a
subchannel must re-establish the parameter.

### A better design, deliberately not taken

Putting the **RDEVBLOK address** in the parameter instead would hand the
interrupt handler its control block directly and remove a `DMKSCNRU` scan per
interruption — strictly better than what S/370 offered, which only ever gave a
device address to look up. It also changes control flow at every site. The
device address is a drop-in; the pointer is a redesign. Recorded here so the
cheaper choice is not later mistaken for the best one.

## What this does to the order

Mike's order was INTTIO, then the bootstrap chain, then storage keys. Group B
splits it, because `DMKCKP` and `DMKDMP` set their own interruption parameter in
the ORB of their own standalone `SSCH` — so their `INTTIO` sites **cannot** be
converted before their channel I/O is. They are one piece of work, not two.

| Increment | Modules | Clears |
|---|---|---|
| A | `DMKVMI` → `SYSIPLDV` | `DMKVMI` entirely (1 site) |
| B | `DMKIOT` → `IOINTPRM+2`, plus `DMKCPI`'s `STSCH`/`MSCH` discovery | `DMKIOT` (10 sites) |
| bootstrap | `DMKCKP`, `DMKDMP` — `INTTIO` **and** `SIO`/`TIO`/`HIO` in one pass each | both, once |

Increment B's deck is half of M1 step 5 on its own: it is correct once something
writes the parameter, and until then it reads a field nobody sets. That is
acceptable while M1's test is that the nucleus assembles, but it must not be
mistaken for a working interrupt path — the `DMKCPI` half is what makes it true.
