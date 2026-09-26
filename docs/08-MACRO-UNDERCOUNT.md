# The macro undercount, quantified — and what it turned up instead

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
working; a site doing it to *truncate an address* wants the wide one. The 217
sites each need classifying into which they are, and that is real work — but
it is enumerable work with a known population, which is what the inventory
previously could not say about anything macro-related.

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
