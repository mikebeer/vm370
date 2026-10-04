# The macro undercount, quantified — and what it turned up instead

> **Status, 4 October 2026.** The measurement stands and was borne out:
> `TRANS` was converted once and its sites followed, in the DAT conversion of
> [29-DAT-CONVERSION.md](29-DAT-CONVERSION.md). Of the seven `PSA` constants,
> `CPCREG0` was changed to the ESA/390 translation format (`X'81B00CC0'`,
> `PSA.XA0001DK`) and the rest are as they were: the 24-bit masks `XPAGNUM`,
> `X2048BND` and `XRIGHT24` have not been widened, because CP still runs
> AMODE 24 — guest storage above 16 MB aliases onto the low 16 MB (`I-208`) —
> and their widening belongs with the 215 `LA` strip sites (`I-126`) in the
> open M2 work. The class-D flag relocation has likewise not been started.
> Current position in [30-STATE.md](30-STATE.md); issues in
> [13-ISSUES.md](13-ISSUES.md).

26 September 2026. `06-LEDGER.md` named this the largest unquantified risk in
the inventory: every instruction count is a floor, because a statement parser
cannot see what a macro emits. `TRANS` was found by accident and hides an
`LCTL`, an `LRA` and a branch at each of 174 sites; `CALL` hides 4,104
linkages. Nobody had established what else was hidden.

Now measured, with `../arch/31bit/tools/macroexp.py`, which extracts what each
macro body can emit and resolves nesting transitively — `SWTCHVM` calls
`CHARGE`, so its cost is not local.

**Two answers. The one I was looking for is reassuring. The one I was not is
the useful one.**

---

## 1. The instruction undercount is bounded, and it is one macro

Of CP's **59 macros, only 10 can emit anything architecture-dependent at
all**, and weighted by how often each is actually invoked across the 201
`.ASSEMBLE` members:

| Macro | Sites | Hidden arch instructions | Hidden S/370 I/O |
|---|---|---|---|
| `TRANS` | 174 | **522** (`LCTL` ×348, `LRA` ×174) | — |
| `CLRIO` | 1 | — | 1 |
| everything else | — | 0 | 0 |

**`TRANS` is the entire undercount.** Its body carries two `LCTL`s — one for
the simple case, one for `VMSEG-VMBLOK(R15)` — plus the `LRA`, so each site
hides three.

So the corrected totals are:

    architecture-sensitive instructions   538 counted + 522 hidden = 1,060
    S/370 I/O instructions                179 counted +   1 hidden =   180

And the hidden half is **one macro that was already identified, already
understood, and already the plan's answer**: convert `TRANS` once and 174
sites follow.

### The negatives matter as much

**49 of 59 macros emit nothing architecture-dependent.** Including every one
that had been a worry:

- **`CALL`, 4,104 invocations — clean.** Confirms by measurement what
  02-CP-VERIFIED.md argued from reading: it emits
  `L R15,=A(&SUBR+X'80000000')`, and bit 0 is the bit ESA/390 leaves free.
- **`SWTCHVM`, 101 invocations — clean.** 07-M1-WORKLIST.md flagged this as
  unread and suspicious, since switching virtual machine context is where PSW
  and control-register handling would hide. It emits a `TM`, a branch, an
  `LA`/`SLR`, a `BALR` to `DMKLOKSW`, and a nested `CHARGE`. No `LPSW`, no
  `LCTL`.
- **`LOCK` (89), `GOTO` (274), `SAVE`, `RETURN`, `ENTER`, `EXIT` — all
  clean.**

That closes the question. The answer to "what else is hidden" is: essentially
nothing.

---

## 2. But macros hide architecture-dependent *data*, and nobody was looking

`PSA.MACRO` — the lowcore definition, invoked by **171 of 201 modules** —
contains seven named constants. Six of them are architecture-dependent, and
**no instruction count could ever have found them**, because they are `DC`
statements in a DSECT generator.

| Constant | Value | Refs | Why it changes |
|---|---|---|---|
| `XPAGNUM` | `X'00FFF000'` | **73** | Page-number mask, 24-bit. Must widen to `X'7FFFF000'` — this is the mask that breaks for every above-the-line address |
| `CPCREG0` | `X'81800CC0'` | 38 | **CP's own control register 0.** Bits 8–12 must become `10110` for ESA/390 |
| `XRIGHT16` | `X'0000FFFF'` | 38 | 16-bit mask. Probably device addresses — needs checking, may be fine |
| `X2048BND` | `X'00FFF800'` | 25 | **2 KB boundary mask.** Storage keys go 2 KB → 4 KB, so this becomes `X'7FFFF000'` |
| `XRIGHT24` | `X'00FFFFFF'` | 23 | 24-bit address mask → `X'7FFFFFFF'` |
| `X40FFS` | `X'40FFFFFF'` | 18 | Flag in bit 1 plus a 24-bit address — a packed address constant, and bit 1 *is* an address bit under ESA/390 |
| `NOADD` | `X'FF000000'` | 2 | High-byte mask |

**217 references to seven constants, with one definition site each.**

`CPCREG0` is corroborated by execution: the CR13 investigation measured a live
CP's real CR0 as `81800CC0`, one bit from this documented value. So this is
the constant CP actually loads, and it is precisely what
`01-dat-tables.rc` had to get right — CR0 bits 8–12 = `10110`, checked before
any DAT table is read.

`X40FFS` deserves particular attention. It packs a flag into bit 1 and an
address into bits 8–31. Bit 1 is a genuine address bit under ESA/390, so this
is the `SAVE.COPY` problem Adrian found, in constant form — and unlike the 582
`ICM`/`STCM` sites, it is one definition.

---

## 3. What this does to the estimate

**Better shaped, not smaller.** The work did not shrink; it concentrated.

Before: 538 architecture-sensitive instructions counted, an unknown number
hidden, and no way to bound the unknown.

After: 1,060 total, of which 522 are one macro, plus **six constants with 217
reference sites and one definition point each.**

Six constants in one macro is a far better problem than 217 scattered
literals. Change `PSA.MACRO` and every reference inherits the fix.

**With one caveat that should not be glossed over.** Widening a mask changes
behaviour everywhere the old width was load-bearing rather than incidental. A
site doing `N R1,XRIGHT24` to *clear flags* wants the narrow mask to keep
working; a site doing it to *truncate an address* wants the wide one.

## The classification, done

27 September, with `../arch/31bit/tools/constclass.py`. Two signals used
together: the instruction form, which is mechanical, and **the comment**, which
is what actually distinguishes a count from an address — CP comments nearly
every line, and no amount of instruction analysis would tell `GET THE TIMEOUT
COUNT` from `ISOLATE ENDING PAGE NO.`

| Class | Sites | Action |
|---|---|---|
| **A** | 38 | one definition change, every site follows |
| **B** | 121 | widen the definition, every site follows |
| **C-safe** | 34 | leave alone — a genuine 16-bit quantity |
| **C-break** | 4 | 16 bits no longer holds it — per-site fix |
| **D** | 20 | a flag in bits 0–7 — relocate it, a design decision |

**24 of 217 need individual attention. Four definition changes carry the other
193.**

### A — `CPCREG0` is not a constant, and that collapses 38 sites to one

The biggest-looking item turns out to be the smallest. `CPCREG0` is a **live
CR0 save area in lowcore**, not a read-only value:

    DMKCLK 318   STCTL C0,C0,CPCREG0  SAVE IN REAL 0 FOR CP
    DMKCLK 193   STCTL C0,C0,CPCREG0  DITTO IN PSA
    DMKCPU 273   LCTL  C0,C0,CPCREG0  LOAD ORIGINAL CONTROL REG 0

`DC X'81800CC0'` is only its *initial* value; thereafter CP stores the live CR0
into it and reloads it. So the 21 `LCTL` and 8 `STCTL` sites are save/restore
pairs that keep working unchanged whatever CR0 contains. **The work is one
initial value** — bits 8–12 to `10110` — not 38 sites.

### B — three masks widen, and 121 sites follow

    XPAGNUM   X'00FFF000' -> X'7FFFF000'   73 sites
    X2048BND  X'00FFF800' -> X'7FFFF000'   25 sites   (and 2 KB -> 4 KB keys)
    XRIGHT24  X'00FFFFFF' -> X'7FFFFFFF'   23 sites

Every one is a storage-address extraction whose upper bits were zero only
because addresses were 24-bit. `X2048BND` changes twice over: widened *and*
re-granularised, since storage keys go from 2 KB to 4 KB.

### C — `XRIGHT16` is mostly safe, and I would have cleared it wrongly

I had assumed a 16-bit mask stays a 16-bit mask. 34 of 38 sites do —
`ISOLATE BYTE COUNT`, `GET THE TIMEOUT COUNT`, `ISOLATE THE MSG NUMBER`,
`MASK ALL BUT CCW COUNT FIELD`, `SAVE ERROR CODE ONLY`. Counts and codes are
16 bits because of what they are, not because of the address width.

**Three are not:**

    DMKCDM  992   N  R4,XRIGHT16   TEST FOR SEG BOUND START
    DMKCFG  726   N  R2,XRIGHT16   ISOLATE ENDING PAGE NO.
    DMKCFG  732   N  R1,XRIGHT16   CLEAR OUT FIRST ADDRESS

A segment boundary needs 20 bits with 1 MB segments; a page number needs 19
with a 31-bit space. Both silently truncate at 16.

**And one is a false positive worth recording**, because it shows the limit of
the method: `DMKSSP 159  N ...,XRIGHT16  IS THERE A CONSOLE ADDRESS` is a
**device** address, which is 16 bits and stays 16 bits. The word "address"
cannot distinguish a storage address from a device address, so the tool
over-reports and the four hits need reading rather than trusting.

### D — 20 sites where a flag occupies an address bit

`X40FFS X'40FFFFFF'` and `NOADD X'FF000000'` are not masks to widen. They are
flags living in bits 0–7, which become address bits:

    DMKCPB  723   N    R1,X40FFS            BLANK HIGH BYTE
    DMKCDB 1437   ICM  R2,B'1000',X40FFS    FLAG TO FRET BUFFER, NOT RTN
    DMKCPS  282   O    R1,NOADD             INDICATE THIS IS AN OFFLINE REQ.
    DMKUDR  731   O    R9,NOADD             SET UP END OF LISTING

The `ICM Rx,B'1000',X40FFS` form inserts only byte 0 — it **sets bit 1 as a
flag**. Widening the mask would not help; the flag needs a new home. This is
Adrian's `SAVE.COPY` finding in constant form, and unlike the 582 `ICM`/`STCM`
sites it is 20 places with two definitions.

**These 20 are the only genuine design work in the whole 217.**

---

## Method and limits

**Upper bounds, deliberately.** Macro bodies are full of conditional assembly
— `AIF`, `AGO`, `SETB` — so not every instruction in a body is emitted at
every invocation. `TRANS`'s two `LCTL`s are alternatives, for instance, so 174
sites probably emit 174 `LCTL`s rather than 348. What this computes is what
*could* be hidden, which is the right quantity for closing a risk. The
statement-parser floor and this ceiling bracket the truth.

**`DC` is treated as a possible instruction, not ignored.** CP hand-encodes
instructions its assembler does not know — `DMKVATZP DC X'E60B',S(ARCHTECT,
0(R9))` is an ECPS:VM assist — so a `DC` whose first operand is a hex literal
is reported rather than skipped. That is how the seven constants surfaced.
It is also exactly the idiom `XAOPS.MACRO` uses, so the same blindness will
apply to converted code: **an `SSCH` written as `DC X'B233',S(...)` is
invisible to any tool that counts opcodes.** Worth remembering when the
inventory is re-run after conversion starts.

**Nesting is resolved transitively but not conditionally.** If a macro calls
another only on one branch, this still counts the callee's full contribution.

**Only CP's own `.MACRO` library is covered** — 59 members. Macros defined
inside `.COPY` members, or system macros from `OSMACRO`, are not analysed.
`06-LEDGER.md` lists CMS's 139 `.MACRO`/`.COPY` members as a separate open
item, and the same tool will run against them.
