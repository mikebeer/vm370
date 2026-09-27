# The storage-key family: not low-hanging fruit

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

| Module | Sites | Mnemonics |
|---|---|---|
| `DMKPTR` | 23 | `RRB`×13 `ISK`×6 `SSK`×4 |
| `DMKCCW` | 8 | `SSK`×4 `ISK`×4 |
| `DMKMCH` | 5 | `ISK`×3 `SSK`×2 |
| `DMKPSA` | 5 | `ISK`×5 |
| `DMKCDS` | 4 | `ISK`×2 `SSK`×2 |
| `DMKDMP` | 4 | `ISK`×4 |
| `DMKCDB` `DMKCDM` `DMKCFH` `DMKDGD` `DMKPRV` `DMKVMA` `DMKVMD` | 2 each | |
| `DMKCPI` `DMKDIB` `DMKUNT` `DMKVCA` | 1 each | |
| **Total** | **67** | across 17 modules |

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

## Order of work

1. Read `HRC004DK`'s six decks.
2. Prove the granularity claim on CE rather than from Hercules's source: a
   test module that does `ISK` and `ISKE` against the same frame and prints
   both, the way `XATEST` closed M0. If they agree, the pairs can collapse
   safely.
3. Convert the 44 sites outside `DMKPTR` first — `ISK`/`SSK` only, mostly
   unpaired, mechanical once step 2 is settled.
4. Convert `DMKPTR` last and on its own, including the 13 `RRB`→`RRBE`
   register problem.
