# The storage-key family: not low-hanging fruit

> **Status, 4 October 2026.** The family is converted on every path CMS exercises and `R-12` is settled by measurement, not by the plan in "R-12 decided" below. Hercules `pgmtrace +1` decoded all 16,305 guest `SSK`s during a CMS IPL and profile: CMS sets both 2 KB halves of a page alike, so one ESA/390 key per 4 KB frame reproduces what the guest asked for; the `SWPKEY1 ≠ SWPKEY2` counter was never needed (`I-202`, [13-ISSUES.md](13-ISSUES.md)). Wall 28 — the REXX `DMSITP141T` protection exception — looked like this family and was not: `DMKPRV SEGOK` (XA0036DK) computed the STO in R6, the guest address the two `LRA`s needed, so `ISK`/`SSK` worked the wrong frame ([28-IPL-WALLS.md](28-IPL-WALLS.md)). Guest `ISK`/`SSK` are simulated with `ISKE`/`SSKE` in `DMKPRV` (XA0041DK); `DISPLAY K` was converted (XA0044DK, `I-209`). `privchk.py` reports 6 key sites left, in `DMKCDM` and `DMKPTR`, none on a path reached so far. `DMKPRV`'s missing `ISKE`/`SSKE`/`RRBE` simulation (`I-46`) is still M5 work. The analysis of what the instructions differ in, the 4 KB verification and the three site classes stand; see [30-STATE.md](30-STATE.md) for position.

I proposed this as the cheap win — 67 sites, `ISK`→`ISKE`, `SSK`→`SSKE`,
`RRB`→`RRBE`, all three replacements valid in S/370 as well as ESA/390, so
convertible and testable on the system as it runs today. Reading Hercules's
implementations and then CP's actual usage shows the first half of that is
right and the word "cheap" is wrong.

## What the replacements actually differ in

| | `ISK R1,R2` | `ISKE R1,R2` |
|---|---|---|
| Format | RR | RRE |
| Address | `GR_L(r2) & 0x00FFF800` — **24-bit, 2K block** | `GR(r2) & ADDRESS_MAXWRAP_E` — full 31-bit, 4K block |
| Alignment | bits 28-31 must be zero, else specification exception | none |
| Key fetched | `get_2K_storage_key` | `get_4K_storage_key` |
| BC mode | clears bits 29-31 of R1 | no adjustment |
| Result | `GR_LHLCL(r1)`, bits 24-31 | same |

`SSK` masks identically. `RRB` masks identically **and** is S-format,
`D2(B2)`, where `RRBE` is RRE, `R1,R2`.

## The finding that matters, and what it does not mean

**All three S/370 key instructions mask the operand address to 24 bits.**

    pageaddr = regs->GR_L( r2 ) & 0x00FFF800;          /* 24-bit, 2K block */
    pageaddr = APPLY_PREFIXING( pageaddr, regs->PX );  /* real -> absolute */

The operand is a **real** address, because storage keys belong to real frames.
So the limit is on real storage, and Mike's question is the right one: it does
**not** block a 31-bit CMS.

A guest's 31-bit virtual address space is produced by DAT -- segment and page
tables -- and the real frames backing those pages can all sit below the line.
CMS could run with a full 31-bit virtual address space on a 16 MB host, with
`ISK`/`SSK` untouched and CP paging as it does today.

I first wrote that this family was "a prerequisite for the project's purpose".
That was wrong, and the correction matters because it changes the order of
work:

| Goal | Needs this family? |
|---|---|
| M5 -- CMS in a 31-bit virtual machine | **No.** DAT, plus `DMKPRV` simulation below |
| CP using real storage above 16 MB | **Yes**, and `SWPTABLE`, and `R-01`/`R-02` |
| A guest that issues `ISKE`/`SSKE`/`RRBE` | **Yes**, in `DMKPRV` specifically |

So the family belongs *with* the real-storage work, not ahead of everything
else.  The four `INTTIO` modules, which unblock M3a, come first.

**This is sequencing, not scope.**  Real storage above 16 MB is a project goal
(Mike, 27 September): the machine is meant to have much more virtual storage
*and* more than 16 MB real, so this family is required work, third in order
behind the `INTTIO` group and the bootstrap chain.  Nothing here is optional,
and `R-25`'s "keep Hercules at 16 MB real" is a gate to be lifted once the
conversion lands, not a decision to stay below the line.

## What a 31-bit guest actually needs: DMKPRV

Guest storage keys are not held in hardware at all.  CP keeps them in the swap
table:

    SWPKEY1  DS  1X   S*3 VIRTUAL STORAGE KEY, 1ST 2048 BYTES
    SWPKEY2  DS  1X   S*4 VIRTUAL STORAGE KEY, 2ND 2048 BYTES

`DMKPRV` simulates the guest's instruction against those and issues a real
`ISK`/`SSK` only to synchronise the backing frame.  Its entry points state its
whole repertoire:

    ENTRY DMKPRVEK    INST COUNT FOR X'08'   SSK
    ENTRY DMKPRVIK    INST COUNT FOR X'09'   ISK
          CLI  VMINST,X'B2'   VIRT. RRB?

X'08', X'09' and X'B213'.  **A 31-bit CMS issuing `ISKE`, `SSKE` or `RRBE`
finds no case there**, so M5 needs DMKPRV extended -- guest-facing work with
nothing to do with CP's own key management, and not previously counted in the
67 sites.

`SWPKEY1`/`SWPKEY2` also puts the 2 KB pairing in the **data structure**, so
collapsing to one 4 KB key is a `SWPTABLE` change and not only an instruction
change.  That makes the `DMKPTR` work larger than its 23 sites suggest.

## Why it is not cheap

CP does not treat a 4 KB page as one keyed unit. It treats it as **two 2 KB
halves with two keys**, and says so:

    DMKPTR   ISK   R1,R14         STORAGE KEY FOR 1ST HALF OF PAGE
             ISK   R1,R14         INSERT 2ND KEY
             RRB   0(R6)          MAKE SURE BITS RESET FOR SELECT.
             RRB   2048(R6)       . .

ESA/390 has **one key per 4 KB frame**. Each extended instruction therefore
does in one operation what the pair does in two, and the paired structure has
to collapse rather than be translated site by site. Seven sites carry an
explicit `2048` displacement; more are paired without one, by incrementing a
register between the two operations. Each pair is a small piece of reasoning
about which half's key was authoritative — which is `R-01` and `R-02` again.

`RRB`→`RRBE` is the worst of the three: the effective address moves out of a
base-displacement operand and into a register, so every one of `DMKPTR`'s 13
sites needs an address materialised first, and therefore a spare register in
the page manager's tightest code.

## Where the sites are

The first version of this table said 67 sites in 17 modules. It was counted
against the **base** files, before `applied.py` existed, so it counted cards the
APAR chain deletes and missed none that it adds — the `I-168` error in the
direction that overstates work. Counted against the source the assembler
actually sees, on 3 October:

| Module | Sites | Mnemonics |
|---|---|---|
| `DMKPTR` | 15 | `RRB`×11 `ISK`×4 |
| `DMKCCW` | 8 | `SSK`×4 `ISK`×4 |
| `DMKMCH` | 5 | `ISK`×3 `SSK`×2 |
| `DMKPSA` | 5 | `ISK`×5 |
| `DMKCDS` | 4 | `ISK`×2 `SSK`×2 |
| `DMKCDB` `DMKCDM` `DMKCFH` `DMKDGD` `DMKPRV` `DMKVMA` `DMKVMD` | 2 each | |
| `DMKDIB` `DMKUNT` `DMKVCA` | 1 each | |
| **Total** | **54** | across 15 modules |

`DMKDMP` and `DMKCPI` have none: their sites are in cards the chain removed.
`DMKPTR` is still the largest share and still the page manager.

## What each site needs, determined site by site

Read on 3 October, when wall 21 made this the blocking work rather than
deferred work. Three classes, and the first two are the bulk.

**Class 1 — the mnemonic and nothing else.** The result layout did not move:
`ISK` returns bits 24-27 access control, 28 fetch-protect, 29 reference, 30
change, and so does `ISKE`. So every mask below one of these sites survives
unchanged — `F8` for fetch, `F240` for the key, `F2` for change,
`=A(X'FFFFF8')` for "clear ref and change". And `X2048BND  GET MASK FOR BITS
8-20` stays too, because `ISKE` takes its block from bits 1-19 of the operand
and **ignores** bits 20-31, where S/370's `ISK` required bits 29-31 to be zero
or took a specification exception. A 2 KB-aligned address is still legal; it
just names the 4 KB page containing it. Sites: `DMKPSA` all five,
`DMKCCW 01157000` and `03631000`, `DMKCDB 01428000`, `DMKCDM 01140000`, and the
singletons in `DMKDIB`, `DMKUNT`, `DMKVCA`.

**Class 2 — a half-page pair that collapses.** The shape is always the same:
read or set the key, `LA Rx,2048(,Rx)`, do it again. One 4 KB key makes the
second operation read or write the same byte, so the pair becomes one
instruction. Where the second is a *read*, leaving it in place is behaviour-
preserving — it returns the same key and sets the same condition code — which
is why `DMKPSA`'s `DMKPSACC` pair was converted in place rather than deleted,
to keep the change set on the critical path reviewable. Where the second is a
*write*, it must go, because the two writes come from two different source
bytes: `DMKCCW 00973000` loads a **packed halfword of two keys** from
`SWPFLAG`, masks it `X'F8F8'`, `SSK`s the low byte into the second half,
shifts right 8, and `SSK`s the high byte into the first. Converted, that is
`SRL R15,8` then one `SSKE` — the first half's key for the whole page, which is
exactly the convention `I-177` set in `DMKPTR`. Sites: `DMKCCW 00973000`-
`00979000` and `03584000`-`03589000`, `DMKCDS 00882000`-`00888000`,
`DMKVMA 00209000`-`00213000` (whose `CHGBITS` mask of `X'00000202'` tests the
change bit in both byte positions and becomes a plain `F2`),
`DMKVMD 00908000`-`00912000` and `DMKCDB`/`DMKCDM`'s first site each — those
three build a key **pair** for display, so the honest conversion presents the
one real key twice and keeps the display format.

**Class 3 — `DMKPTR`'s `RRB` block, which is a design question and not an
edit.** Two reasons. First, mechanics: `RRB` is SI-format with a storage
operand, so `RRB 2048(R6)` carries its displacement in the instruction, and
`RRBE` is RRE with only a register — there is nowhere to put the 2048, so every
displaced `RRB` needs an `LA` first or needs to disappear. Second, and the real
difficulty: this code maintains `SWPKEY1` and `SWPKEY2`, CP's **virtual
back-up keys**, one per 2 KB half, from the two real keys. With one real key
there is one real reference/change pair and two virtual ones to feed. The
defensible answer is to set both back-up keys from the single key — a 4 KB
page's reference and change state does apply to both of its halves — but that
is a decision about what a guest sees, which is `R-12`, and it wants writing
down before it is coded. The block is also intricate in its own right:
`BC 8+4,STKEY2+4` branches into the middle of an instruction, `BALR R14,0`
is used to park a condition code, and the `BZ *+8` offsets all shift when a
pair collapses.

**`DMKPTR` is a third of it**, and `DMKPTR` is the page manager — the module
whose correctness the whole 31-bit exercise depends on. That is the opposite of
a low-risk starting point.

## The one thing that *is* cheap, and it is worth a lot

`ISKE`, `SSKE`, `RRBE` and `IVSK` are all `GENx370x390x900`: valid in S/370,
ESA/390 and z/Architecture alike. So unlike every channel-family change, this
work can be **written and tested on CE exactly as it runs today**, in S/370
mode, before anything else moves. A converted `DMKPTR` can be proved against
the current system rather than against a system that does not boot yet.

That is a real and unusual advantage. It just is not the same claim as "cheap".

## Prior art already in the tree

CE sets `CPCREG0 DC X'81800CC0'` — byte 0 is `X'81'`, and `CR0_STORKEY_4K` is
`0x01000000`, so **CE already runs with the 4 KB storage-key control on**
(`I-29`, deck `HRC004DK`, applied to `DMKAPI` `DMKCLK` `DMKCPI` `DMKPSA` `EQU`
`PSA`). `DMKPTR` is not among those six, so it still issues paired 2 KB
operations against a machine configured for 4 KB keys — redundant rather than
wrong, because Hercules resolves both granularities against one key array.

Two consequences. The 2 KB/4 KB semantic gap is **already bridged in CE's
configuration**, so collapsing the pairs should be behaviour-preserving rather
than behaviour-changing. And `HRC004DK` is worth reading before writing
anything: it is six decks of IBM-era work on exactly this question.

## The 4 KB claim, verified rather than inferred

The section above infers from `CPCREG0 DC X'81800CC0'` that CE already runs with
4 KB keys. That inference is **correct**, and it is worth showing why, because
the bit's name in Hercules — `CR0_STORKEY_4K`, commented *"Storkey exception
control"* — reads as though it might mean the opposite.

Base `PSA.MACRO` has `X'80800CC0'`; CE's own `PSA.HRC004DK` changes it to
`X'81800CC0'`. The single bit added is `0x01000000`, which `esa390.h` defines as
`CR0_STORKEY_4K`. Hercules tests it in exactly three places, and the three are
`insert_storage_key`, `reset_reference_bit` and `set_storage_key` — `ISK`, `RRB`
and `SSK`, the **2 KB** instructions, not the extended ones:

    if (!(regs->CR( 0 ) & CR0_STORKEY_4K))
        program_interrupt( regs, PGM_SPECIAL_OPERATION_EXCEPTION );

So on a machine whose keys cover 4 KB blocks, the bit is what *permits* `ISK`,
`SSK` and `RRB` at all, and they then address the 4 KB key with the 2 KB
sub-address ignored. That is the S/370 architecture's own rule for models with
the 4 KB-key feature, and it means **CE's paired operations already both reach
the same key today**. Redundant, exactly as stated, and not merely because
Hercules happens to keep one key array.

## The consequence: both halves of the conversion are behaviour-preserving

This settles a question that looked like a design decision and is not one. The
two directions are not symmetric, and neither needs a deviation.

**Reading** — `DMKPTR` 00539000 and 01012000 pack two keys into one register,
because `ISK` only loads bits 24-31, and test them with a two-byte mask:

    ISK   R1,R14         STORAGE KEY FOR 1ST HALF OF PAGE
    LA    R14,2048(R14)  INCREMENT TO 2ND HALF PAGE
    SLL   R1,8           SAVE KEY
    ISK   R1,R14         INSERT 2ND KEY
    N     R1,=A(X'0202') CLEAR ALL BUT CHANGE BITS

Both `ISK`s already return the same key. So one `ISKE`, **replicated into both
bytes**, leaves the mask, the branch and every downstream store untouched and
produces the identical register value. Not a conservative approximation — the
same answer.

**Writing** — `DMKPTR` 00643000 writes two *independent* guest keys, which the
guest set itself through simulated `SSK`:

    L     R3,SWPFLAG     GET USER'S KEYS IN LOW ORDER
    N     R3,=A(X'F8F8') CLEAR REF/CHANGE BITS
    SSK   R3,R8          SET KEY FOR 2'ND HALF PAGE
    SRL   R3,8           JUSTIFY KEY FOR 1'ST HALF PAGE
    SSK   R3,R6          SET KEY FOR 1'ST HALF PAGE

Replication is meaningless here — there is nothing to replicate *from*. But
since both `SSK`s already address one key, **the second one wins today**, and
the second one carries `SWPKEY1`. So a single `SSKE` from `SWPKEY1` is not a
choice between the two guest keys: it is what the hardware already holds.

`SWPKEY1` and `SWPKEY2` stay as independent guest state either way, because
`DMKPRV` answers a guest `ISK` out of `SWPTABLE` rather than from hardware. The
guest keeps seeing its two distinct keys. Only real protection enforcement is
coarse, and it is already coarse.

**So the earlier framing of this as "a small piece of reasoning about which
half's key was authoritative" overstates it.** The question is answered by the
machine CE already runs on: reading replicates, writing takes `SWPKEY1`, and
both reproduce current behaviour exactly. What remains is per-site care about
*register pressure and control flow*, which is real work, and not a semantic
decision at each pair.

This also raises the value of step 2 below from a sanity check to the thing that
makes the whole family provable: if `ISK` and `ISKE` agree on CE as this
predicts, all 67 sites can be converted and tested in S/370 mode, before
anything else moves.

## R-12 decided, and the part of it that is empirical

`R-12` has been open since 27 September as *"choose deliberately between
simulating 2 KB semantics in `DMKPRV` and exposing 4 KB"*, deferred to M4. Wall
21 made it blocking instead: `DMKPTR`'s eleven `RRB`s and `DMKPRV`'s two sites
cannot be converted without it. Reading `DMKPRV` settles most of it, and splits
the rest into two very different residues.

**What `DMKPRV` already does.** A guest's `ISK` is a privileged instruction, so
CP intercepts it. `DMKPRV 00930000`-`00946000`:

    SLR  R1,R1          INDEX TO SWPKEYS
    TM   2(R3),X'08'    EVEN OR ODD HALF-PAGE?
    BZ   HALFONE
    LA   R1,1(0,0)      ODD
    HALFONE LRA R2,0(0,R6)
    ISK  R4,R2          GET REAL KEY
    ...
    IC   R9,SWPKEY1(R1) GET KEY FROM SWPTABLE
    OR   R9,R4          ...PLUS REAL KEY

So the guest's **access-control key and fetch-protect bit** have never come
from hardware at all. They come from `SWPKEY1` or `SWPKEY2`, indexed by which
2 KB half the guest named — CP's own software record, one byte per half. Only
the **reference and change bits** are taken from the real key and OR'd in.

That divides R-12 cleanly.

**The access keys are not affected.** `SWPTABLE` is CP-private and the pair of
bytes stays. A guest setting different keys on the two halves of a page keeps
working exactly as it did, because that was always simulated. Nothing to
decide, and the half of R-12 that sounded hardest is not a problem.

**The reference and change bits lose their per-half resolution, in the safe
direction.** One real key means one R/C pair for 4 KB, so CP must report the
same bits for both halves. That **over-reports**: a page shows changed when
only the other half changed. A guest then writes a page it need not have
written — a performance loss. It can never under-report, which is the failure
that would matter: a guest told "unchanged" that skipped a write would lose
data, and that cannot arise, because the real change bit is set if either half
was written.

**The one genuine loss is in the real key CP sets, not the one it reports.**
`DMKCCW`, `DMKDGD` and `I-177`'s `DMKPTR` all take `SWPKEY1` — the first half's
byte — and `SSKE` it over the whole page. When the two halves carry different
access keys, hardware then enforces the first half's on both, and if `SWPKEY1`
is the *less* restrictive of the two, an access to the second half that should
fail will succeed. **Under-protection**, which is the wrong direction, and no
choice of single byte avoids it: access keys are not ordered, so there is no
"more restrictive" one to pick.

**So the decision is to measure rather than guess.** The cases where it matters
are exactly those where a guest sets `SWPKEY1 ≠ SWPKEY2` on a page, and that is
a condition CP can test at the moment it sets them. The plan: *(superseded — see
status note: measured by tracing the guest's `SSK`s instead)*

1. Keep the `SWPKEY1`/`SWPKEY2` pair and `DMKPRV`'s per-half indexing exactly
   as they are. The guest's view of its access keys does not change.
2. Report the single real R/C pair for both halves. Over-reporting, documented.
3. Take `SWPKEY1` for the real key, as the three converted sites already do —
   **and count the times the two bytes differ.** A counter in `DMKPTR`, in the
   same shape as `DMKPTRCT`, which `I-188` showed is exactly how to measure
   something CP does millions of times.
4. If that counter stays zero under CMS and under an OS/VS guest, R-12 is
   closed empirically and nothing more is owed. If it does not, the fallback is
   known but expensive: give such a page a real key no guest PSW key matches,
   so every access to it traps into CP's software check.

The `I-177` deck comment already states the expectation — *"a guest that set
both halves the same, which is every guest CP itself creates, sees no change at
all"* — and step 3 turns that expectation into a number. That is the difference
between this and the version of R-12 that has been open for a week: not a
better argument, a detector.

## Order of work

1. Read `HRC004DK`'s six decks.
2. Prove the granularity claim on CE rather than from Hercules's source: a
   test module that does `ISK` and `ISKE` against the same frame and prints
   both, the way `XATEST` closed M0. If they agree, the pairs can collapse
   safely.
3. Convert the 39 sites outside `DMKPTR` first — `ISK`/`SSK` only, mostly
   unpaired, mechanical once step 2 is settled.
4. Convert `DMKPTR` last and on its own, including the 11 `RRB`→`RRBE`
   register problem.

Revised on 3 October, because wall 21 reordered it. `DMKPSA`'s five went first
and alone, ahead of everything else, for one reason: `ISK` at `X'8B4'` is what
abends CP now, within a second of a second virtual machine existing, so those
five are the difference between a system that initialises and a system that
runs. Steps 1 and 2 were skipped for them — step 2's granularity claim is
already settled three ways (the PoO's *"only 4K-byte blocks"*, `XAOPS.MACRO`'s
own *"PROVEN BY EXECUTION IN 11-storage-keys.rc"*, and `I-177` shipping an
`SSKE`), and none of DMKPSA's five is a write, so no collapse decision was
needed. Then `DMKCCW`, `DMKCDS`, `DMKVMA`, `DMKVMD` as one change set, then
`DMKPTR` on its own with `R-12` written down first.
