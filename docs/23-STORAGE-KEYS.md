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

## The finding that matters

**All three S/370 key instructions mask the operand address to 24 bits.** CP
physically cannot read or set a storage key above the 16 MB line with `ISK`,
`SSK` or `RRB`, whatever else is converted. The extended forms have no such
limit.

So this family is not risk-reduction ahead of the real work. It is a
**prerequisite for the project's purpose**: a virtual machine with storage
above the line has frames whose keys CP could not manage at all. It belongs on
M1's critical path, not in a cleanup pass.

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
