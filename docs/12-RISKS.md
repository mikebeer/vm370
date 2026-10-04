# Risk register

> **Status, 4 October 2026.** This register has not been re-scored since
> 27 September, and most of what it scored has since happened or been retired:
> M0, M1, M3a, M3b and M3c are done, M2's tables are done, M4 is largely done,
> only M2's AMODE 31 (`I-208`) and M5 are open ([30-STATE.md](30-STATE.md),
> [../arch/31bit/README.md](../arch/31bit/README.md)). The maintained
> risk-to-milestone mapping is now the table in
> [18-TRACEABILITY.md](18-TRACEABILITY.md), and the defects are in
> [13-ISSUES.md](13-ISSUES.md) and [28-IPL-WALLS.md](28-IPL-WALLS.md). The
> scoring scheme, the silent-failure rule and the descriptions stand as the
> record of what was feared. Per risk, against the traceability table:
>
> - **R-01** — retired for the tables by M2 (`XA0033`–`0037DK`); still carried for the AMODE 31 work.
> - **R-02** — realised repeatedly on the way (walls 1–22) and retired by M1: CP accepts a typed command.
> - **R-03** — retired by M1; the console and DASD paths run on the ESW/IRB.
> - **R-04** — retired by M1; every change is an update deck from `mkdeck`, gated by `replchk`.
> - **R-05** — retired: no ABI change was needed, `DMKBLDRT`'s halfword was re-split and widened in place (`I-185`).
> - **R-06** — retired by M3c ([33-FRAME-SHARING.md](33-FRAME-SHARING.md)); the last-sharer bookkeeping is increment 2, open.
> - **R-07** — retired for the tables by M2.
> - **R-08** — retired by M3b: unmodified CMS reaches `Ready;`, EXEC2 and REXX run.
> - **R-09** — retired by M3a: `IPL 6A1` from the nucleus `DMKSAV` wrote.
> - **R-10** — open; M5 not started, and now also waits on M2's AMODE 31.
> - **R-11** — no longer the case: 43 update levels, and the CP they build IPLs.
> - **R-12** — measured, not argued: CMS sets both 2 KB halves alike (16,305 `SSK`s), one key per frame is adequate; `DISPLAY K` converted (`I-209`).
> - **R-13** — moot; z390 is out of the build.
> - **R-15** — open, carried to M2's AMODE 31 with the 215 `LA` strip sites (`I-126`).
> - **R-16** — continuous; mitigation holds (pristine extraction, `build.sh` snapshots).
> - **R-18** — not realised; continuous.
> - **R-19** — retired by M1; the counts were floors and the walls found the rest.
> - **R-20** — not realised; CP runs with console, sixteen packs and autologged users, but no dedicated test was built.
> - **R-21** — continuous; 3.13 and 4.9.1 agree (`I-204`).
> - **R-22** — retired by M1; fired once as predicted and was caught by `mkdeck`.
> - **R-23** — stands at its downgraded weight.
> - **R-24** — not realised; the nucleus with the sourceless `DMKBTS.TEXT` IPLs and runs CMS.
> - **R-25** — the key family is converted (`ISKE`/`SSKE` in `DMKPRV` and the paging path); real storage above 16 MB stays deferred to M5 and Hercules stays at 16 MB real (`I-157`).
> - **R-26** — mitigated as each module was decked; no wall was traced to a self-relative branch.
> - **R-27** — mitigated: format 0 kept, and every channel program in CP runs unconverted.
> - ~~R-14~~, ~~R-17~~ — closed 27 September, as already shown below.

27 September 2026. Risks are **forward-looking**: things that may happen and
would cost us if they did. Anything that has *already* happened is a defect and
lives in [13-ISSUES.md](13-ISSUES.md) instead. That boundary is what keeps both
lists useful — a risk register full of things that already went wrong cannot be
prioritised.

This supersedes the four-item ranking that used to sit in
`../arch/31bit/README.md` under "The risk order changed". Milestones are
separate: see that README's milestone table.

**Scoring.** Probability and Impact are Low / Medium / High, scored 1 / 2 / 3.
Weight = P × I, so 1–9.

| Weight | Band | Meaning |
|---|---|---|
| 9 | **critical** | plan around it explicitly |
| 6 | **high** | needs a named mitigation before the milestone that carries it |
| 3–4 | moderate | watch, mitigate cheaply |
| 1–2 | low | accept, revisit if evidence changes |

**Impact is judged on the conversion, not on the emulator.** A risk whose
failure mode is *silent* is scored one level higher than the same damage
announced loudly, because the cost is the debugging, not the bug. CR6 is why
(see R-02).

---

## Register

| ID | Risk | Description | P | I | W | Mitigation | Status |
|---|---|---|---|---|---|---|---|
| **R-01** | Geometry in bare shift literals | 70 hard-coded shift amounts across twelve modules encode the 64 KB/1 MB segment and halfword/fullword PTE geometry as bare numeric literals. No symbol rename touches them; a missed one yields a *correct-looking* translation to the wrong page. | H | H | **9** | **Enumerated 27 Sep: [R01-SHIFT-SITES.md](R01-SHIFT-SITES.md)**, all 70 with module, line, sequence anchor and the module's own comment, produced by `../arch/31bit/tools/shifts.py` so it is re-runnable against a moving tree. Four symbols cover them — `PAGSHFT` 4→8, `SEGSHFT` 16→20, `PTLSHFT` 6→10, `KEYSHFT` 11→12 — and naming them is M2's first act, before any geometry changes. One compound site (`DMKBLD` 232, `SLL R1,4+4`) needed reading rather than substitution and is resolved in the table. | **enumerated** |
| **R-02** | Silent-gate omissions | A required control bit omitted, with no diagnostic and a symptom that looks like success. **Probability raised M→H on 27 Sep against realised instances** ([18-TRACEABILITY.md](18-TRACEABILITY.md)): CR0 translation format, `PMCW5_E`, CR6, and `I-06` — a page-table entry filled with `X'20'`, leaving the invalid bit clear so every unmapped page was a *valid* entry aliased to real page 0. Four of the same shape is not "Medium probability of another". `I-08` is a fifth, in a milestone definition rather than in code. | H | H | **9** | Keep a gates checklist in `../arch/31bit/tests/hardware/`; make every milestone exit criterion require *progress past* the observable, never the observable itself (see I-08). Assert CR0/CR6/PMCW enable at every CP entry during M1–M2. | open *(superseded — see status note)* |
| **R-03** | Channel logout has no equivalent | `TM CSW,X'04'` and friends survive a copy; what they point at does not. The ESW/ERW in the IRB plus `STCRW` replace `CHANID`, `IOELPNTR` and `ECSWLOG`, which have nothing to map to. | H | M | **6** | Map every logout site; stub all of them to "permanent error" for M1–M2 so the paths assemble and fail loudly; implement ESW/ERW properly only when a real device error needs diagnosing. | open *(superseded — see status note)* |
| **R-04** | Column-sensitive source corrupted by tooling | CP source is strictly column-sensitive: columns 1–71 are code, 72 is continuation, 73–80 carry `@V40759`-style change markers. Any script touching 217 constant sites or 70 shift literals can push markers into column 72. | H | M | **6** | **Largely neutralised by writing the conversion as an `AUXLCL` update level** ([15-UPDATE-LEVELS.md](15-UPDATE-LEVELS.md)): update decks insert, delete or replace whole records anchored on the sequence numbers in 73–80 and never rewrite a line in place, so the `TRACE`→`CPTRACE` failure mode cannot occur. Residual applies only to tooling that does edit base source. **Exercised 27 Sep and it fired twice**: `tools/mkdeck.py` refused a 64-column comment line and a sequence-number overflow that would have reached the next surviving record (an `R-22` instance). No longer mitigated only in principle. | **mitigated** |
| **R-05** | `DMKBLDRT` ABI change | Its parameter is a packed halfword that cannot express a 31-bit range. Eight callers. | H | M | **6** | Known and bounded: widen the parameter, fix eight sites, in M2. Counted, so it cannot be forgotten. | open *(superseded — see status note)* |
| **R-06** | Frame sharing needs new bookkeeping | The CP-67 route shares frames rather than page tables, so shared frames need locking and reference counting that a single shared page table got for free. This is the one piece of work the CP-67 finding *added*. | H | M | **6** | `DMKPTR` already tracks sharing per frame (`CORFLAG,CORSHARE`, 84 refs) and counts resident shared pages, so the substrate is at the right granularity. Isolate in M3b (see I-10) so a failure has one source. | open *(superseded — see status note)* |
| **R-07** | STE flag-collision invariant unenforced | `SEGMIG X'10'` collides with ESA/390's common-segment bit and `SEGENQ X'40'` with the lowest `PTO` bit. Survivable only because CP happens to set both exclusively when the pointer is zero — an accident, not a rule. `12-ste-flags.rc` showed that without `SEGINV` the hardware walks a page table in lowcore. | M | H | **6** | Turn the accident into an explicit, asserted invariant at every site that sets either flag. `12-ste-flags.rc` is the regression test and already measures both directions. | open *(superseded — see status note)* |
| **R-08** | S/370-mode guest regression | A 31-bit CP that cannot run an unmodified S/370-mode guest has failed by definition. 24-bit is the reference implementation, not a museum piece. | M | H | **6** | M3 is exactly this test. `ARCHTECT`'s eight rows, indexed from the *guest's* CR0 (`IC R9,EXTCR0+1`), are the mechanism that makes it possible — they exist to shadow whatever DAT format a virtual machine selects. Keep `arch/24bit/` as the differential baseline. | open *(superseded — see status note)* |
| **R-09** | No budgeted route to a bootable nucleus | M1 uses strategy B — `loadcore` plus `restart` into `DMKCPINT` — deferring `DMKCKP`, `DMKSAV` and the IPL-from-DASD path. Those three modules carry 70 of the 82 DAT references M1 avoided, so the deferral is real work postponed, not work removed. | M | H | **6** | Assign it to a milestone (I-11). It belongs after M2, because its DAT content is exactly what M2 establishes. Budget it as a milestone in its own right rather than as M3 overhead. | open *(superseded — see status note)* |
| **R-10** | CMS stage 2 unowned | M0–M4 give no guest a single extra byte. The 18 MB heap needs CMS converted, which has no milestone number, no work list, and 126 `DIAGNOSE` references whose parameter lists carry addresses. | M | H | **6** | Number it M5 now, with the measured survey attached: 4 architecture-sensitive instructions in 139 macro members, zero S/370 I/O, 7 inline 24-bit literals across 175 modules against CP's 217. Probably small — but "probably small and unnumbered" is how work goes missing. | open |
| **R-11** | Analysis outruns implementation | Thirteen tests, thirteen documents, and zero lines of CP changed. Findings are measured against a moving CE tree, so they go stale; and the marginal analysis is now worth less than the first edited line. | H | M | **6** | Hard rule: no new analysis document until M1 step 1 has been executed. `heritage/vm370ce/` snapshots guard against staleness. Remaining open tests (R-20, R-12) are explicitly ranked below starting M1. | open *(superseded — see status note)* |
| **R-12** | Guest-visible storage-key semantics *(prior art found)* | Keys go 2 KB → 4 KB. `SWPKEY1`/`SWPKEY2`, `SWPREF1/2`, `SWPCHG1/2` collapse pairwise across 55 references — and it reaches `DMKPRV`, because a guest reading its own keys through `ISK` expects 2 KB semantics. This is guest-visible, not just paging code. | M | M | **4** | **Decided 3 October** — see `23-STORAGE-KEYS.md`, "R-12 decided". Reading `DMKPRV` showed the hard-sounding half is not a problem: a guest's access-control key and fetch-protect bit have never come from hardware, they come from `SWPKEY1`/`SWPKEY2` indexed by half-page, so that pair stays and the guest's view of its own keys is unchanged. Reference and change lose per-half resolution but only **over-report**, which costs a page write and cannot lose data. The one genuine loss is the real key CP sets from `SWPKEY1` alone: with unequal halves, hardware enforces the first half's key on both, and that is under-protection with no safe single byte to choose. So the decision is a **detector** rather than an argument — count the times `SWPKEY1 != SWPKEY2`, in the shape of `DMKPTRCT`, and close this empirically if the count stays zero. Fallback if not: a real key no guest PSW key matches, forcing every access through CP's check. **And CE has already done part of it**: update level `HRC004DK`, "ENABLE SUPPORT FOR 4K STORAGE KEYS", across six members including `PSA` and `DMKPSA` (`I-29`). Start by reading those decks. | open |
| **R-13** | z390 built-ins shadow CP macros | z390 directives silently shadow same-named CP macros: the macro is ignored and its operands parsed as something else. `TRACE` was found only because it happened to fail. A collision that *doesn't* fail produces a false `rc=0`. | M | M | **4** | Mechanical cross-check of CP's 59 macro names against z390's directive list before trusting any clean assembly. Cheap, and not yet done (I-05). | open |
| **R-14** | ~~OSMACRO/DOSMACRO unavailable~~ | ~24 modules reference OS/VS macros (`MSSCOM`, `MODESET`, `WAITT`, `OSVSCOM`, `NUCON`, `VSCOMM`, `ACTDCB`) that are pinned build assets and not in Git. | M | M | **4** | Search CE's own disks first — now possible, since CE runs here. **CLOSED 27 Sep** — they ship with CE. `OSMACRO` (13,227 records), `OSMACRO1` (14,496), `DOSMACRO` (4,105) and `TSOMAC` (8,158) are all on `CMSDSK 190`, and `DMKLNK`, `DMKCFG`, `DMKDSB` and `DMKIMG` — which reference `MSSCOM`, `OSVSCOM` and `NUCON` — assemble clean. Nothing to download, nothing to ask for. See [16-NATIVE-BASELINE.md](16-NATIVE-BASELINE.md). | **closed** |
| **R-15** | Constant sites needing per-site judgment | 217 reference sites to six architecture-dependent constants in `PSA.MACRO` — `XPAGNUM` (73), `CPCREG0` (38), `X2048BND` (25), `XRIGHT24` (23), `X40FFS` (18). Classification found they are not uniform: of 38 `XRIGHT16` sites, 3 break and 1 is a false positive. | M | M | **4** | Classification is complete, so the residual is per-site review at the sites flagged, not at all 217. `CPCREG0` is *not* a constant — it is a live CR0 save area — and must be treated as such. | open |
| **R-16** | Corrupting the CE distribution | Bare-metal tests build their own channel programs with no operating system to stop them addressing the wrong subchannel. One near-miss already: a write command reached subchannel `0000` with a writable CE pack attached, and only the device rejecting the command code prevented a write. CP also writes continuously when running — spool, paging, warm start. | M | M | **4** | Disposable extraction; distribution zip stays read-only; `herc.conf` attaches one device and no DASD; `/cp shutdown` then `exit`, never a killed process. | mitigated |
| **R-17** | ~~CE's assembler rejects `XAOPS`~~ | The macros use `DC X'B233',S(&ORB)` to make an S-format address constant resolve through the active `USING`. Validated under z390 — which is not CE's `ASSEMBLE`. | L | H | **3** | **CLOSED 27 Sep** — see [14-M0-CLOSED.md](14-M0-CLOSED.md). `MACLIB GEN XALIB XAOPS` produced all twelve members and CE's Assembler XF assembled `XATEST` with `HIGHEST SEVERITY WAS 0` and 139 records read from the library. All seven S-type displacements are arithmetically exact. Probability was correctly judged Low: this is CP's own idiom. | **closed** |
| **R-18** | `wide/` supersedes the 31-bit route | If `VMCE-WIDE-PLAN.md` has selected a direct 64-bit route, the ordering argument is wrong and M1–M4 are misdirected. | L | H | **3** | One question to Adrian. And largely self-mitigating: the channel subsystem arrived with 370-XA and z/Architecture did not touch it, and page/segment geometry is identical at 4 KB/1 MB — so the two most expensive pieces carry forward unchanged either way. | open |
| **R-19** | Counts are floors | The statement parser cannot see macro-generated instructions, so every count is a lower bound. | L | M | **2** | Largely closed: of 59 macros only 10 emit anything architecture-dependent, and weighted by invocation `TRANS` is the entire undercount (522 instructions). M1 step 3 — assemble nine modules and diff the errors against the predicted counts — is the detector, and it runs before any module is edited. | mitigated |
| **R-20** | Multiple-device interrupt behaviour | An interruption arriving while another is pending, ISC with more than one class, and `DMKIOT`'s queue walk are untested. The only untested item left on the I/O path. | L | M | **2** | Build the test when a reason appears. Probability is Low because the likely finding is that the channel subsystem queues correctly; explicitly ranked below starting M1. | open |
| **R-23** | ~~The analysis tree is a snapshot, not a checkout~~ | Raised on two proofs, and the stronger one has collapsed. `I-35` was my own retraction, not a real upstream/local divergence: CE's `maintenance/source-catalog.json` records `DMKBTS` as `bootstrap-only` with `source: null`, so nothing is missing. And `UPSTREAM.md` — which I had not read — dates and hashes the tree: imported 20 September 2026 from `VM370CE.V1.R1.2.zip` (SHA-256 `7772e914…`), 630 members compared against native `UPDATE` output on CE's own disks, per-member `bootstrap_sha256`. What survives is `I-30` alone, one unexplained line in one module. | L | M | **2** | Downgraded from weight 6. The mitigation stands and is cheap: CE's own `VMFASM` output is the authority for anything load-bearing. Quote `UPSTREAM.md`'s import date and archive hash when a count leaves this repository. | mitigated |
| **R-24** | `DMKBTS` is in the nucleus and cannot be converted | CE ships `DMKBTS` as the object deck `194/DMKBTS.TEXT` with no source (`I-35`), and all four load lists — `CPLOAD`, `VRLOAD`, `APLOAD`, `APVRLOAD` — include it. It is registered in CP's symbol table via `DMKSYM`'s `SYM DMKBTS`, and **no module in CP source references it**, so what it does is unknown. If it touches lowcore fields the `PSA` rename moved, or issues `SIO`/`TIO`/`HIO`, it will misbehave on ESA/390 and there is no source to fix. | M | H | **6** | Diagnosable without source: dump `194/DMKBTS.TEXT` from CE and read its ESD and RLD records — the `EXTRN`s reveal whether it calls `DMKIOS`, and the address constants reveal lowcore displacements below X'200'. Do that before M3a, not after the first IPL. If it proves to be I/O-bearing, the fallback is to drop it from the load list and find out what breaks. | open |
| **R-25** | `ISK`/`SSK` silently read the wrong frame above 16 MB | The 24-bit mask is not a check: `pageaddr = GR_L(r2) & 0x00FFF800` **truncates**. A real frame address above 16 MB is not rejected, it is folded back into the low 16 MB, so `DMKPRV`'s `ISK R4,R2` returns a different frame's key and its `SSK R9,R2` sets one. Same class of silent-wrong as storing a device address into a subchannel-number field, with no assembler to catch it and no interruption to signal it. It only bites once real storage exceeds 16 MB, which is precisely the configuration this project exists to reach. | M | H | **6** | **Real storage above 16 MB is a project goal, not an option** (Mike, 27 September), so this is a temporary gate to be lifted rather than a constraint to live with: the key family must be converted, and until it is, the Hercules configuration stays at 16 MB real. Large *virtual* storage is unaffected and can come first. Because the extended forms are valid in S/370 too, the conversion can be written and proved at today's storage size, so the sequencing costs nothing — but the gate must not be mistaken for a decision to stay below the line. | open |
| **R-26** | Self-relative branches break silently over converted code | The bootstrap modules poll with `BNZ *-4` and `BC 6,*-4`, which lands exactly on the preceding `TIO`. Any ESA/390 replacement is longer than four bytes — `SSCH`/`TSCH` need an SSID loaded and an ORB or IRB named — so after conversion a `*-4` lands **inside** the replacement. It assembles perfectly and branches to a garbage instruction boundary. There is no diagnostic for it at all: not the assembler, not the loader, and at execution only a wild program check with no obvious cause. The four bootstrap modules carry **46** such branches (`DMKCKP` 15+3, `DMKDMP` 11+1, `DMKLD00E` 5+1, `DMKSAV` 6+4) — but `tools/selfrel.py` finds **912 across 127 nucleus modules**, and that is the number that matters for 64-bit. This pass converts I/O instructions only, so only I/O polling loops are at risk now. A z/Architecture pass converts data movement *everywhere* — `L` becomes `LG`, RX becomes RXY, four bytes become six — at which point **every one of the 912 is suspect**, forward and backward alike, because a `*+8` that skipped two instructions now skips into the middle of one. The worst are not the round numbers: `*-1` ×33 in DMKFMT and ×4 in DMKCCW address a byte *inside* an instruction, `*+4096` in DMKVSP is a page-boundary trick, and `*-193` in DMKRSP and DMKCSO reaches back into a table. | H | H | **9** | Every `*-n` within reach of a converted site becomes a named label **in the same deck** that converts the site — never a follow-up. The count above is the upper bound to work through, and a module is not done until its `*-n` count is zero or each survivor is shown to target unconverted code. `tools/selfrel.py` does the enumeration. **Remove every `*-n` in any module this project touches, whether or not it is near a converted site**, because each one removed now is one fewer landmine for the 64-bit pass, and the marginal cost while the module is already open is close to zero. | open |
| **R-27** | CCW format mismatch is silent and total | The ORB's `ORB5_F` bit selects the CCW layout. **Format 0** is `code, addr(3), flags, count` — the S/370 layout byte for byte. **Format 1** is `code, flags, count, addr(4)`. Both are eight bytes, so a mismatch is not a length error and **nothing diagnoses it**: the command code still reads correctly and the flags, count and data address are all taken from the wrong bytes. Every CCW in CP is format 0, and there are hundreds of them. I set `ORB5F` in `DMKIOS`'s `ORBTMPL` **and** in `XAIO`, and wrote "CP ALWAYS SETS THIS" in `XABLOKS` — wrong three times, in code that assembled clean and was reported as verified. | H | H | **9** | Leave `ORB5_F` **zero**. Format 0 means every existing channel program works unconverted, which is the single largest simplification found so far. The price is a 24-bit CCW data address, so channel programs reach only the low 16 MB: a gate to lift when real storage grows past 16 MB, alongside `R-25` — and **IDAWs are not an escape**: the architecture makes an IDAW above 16 MB a channel program check when the CCW format is 0 (SA22-7201-05 p. 16-25, as enforced in Hercules). So format 1 is the only route, affecting 240 static CCW statements in 23 nucleus modules plus what `DMKCCW` builds — but they are `CCW` macro invocations, so the macro can emit either format. Make it an assembly-time choice now rather than finding 240 sites later; [17-CARRY-FORWARD-64.md](17-CARRY-FORWARD-64.md). Corrected in all three places and re-verified. | mitigated |
| **R-22** | `AUXLCL` anchor fragility | Update decks are anchored on base sequence numbers in columns 73–80. If CE renumbers a member or issues an `HRC` update touching the same anchors, an `AUXLCL` deck can fail or apply in the wrong place. Not hypothetical: `UPSTREAM.md` records that `DMKGRF` and `DMSSTT` required correct host handling of repeated sequence anchors, and that `PSA`'s sequence-number increment needed a host fix. **97 of 201 modules already carry `HRC` lines, `DMKPSA` among them.** | M | M | **4** | Keep decks small and anchored on stable, distinctive lines; re-run the full assembly after any CE update; treat a failed `UPDATE` as a signal rather than a nuisance, since it is the mechanism telling us the base moved. | open *(superseded — see status note)* |
| **R-21** | Lab-only emulator patch leaks out | Hercules 3.13 needed `__thread` dropped from `float_exception_flags` and `float_rounding_mode` to link. Safe for a one-CPU lab with no floating point; wrong anywhere else, since those are per-CPU state. | L | M | **2** | Documented as lab-only in `../arch/31bit/README.md`. Never distribute that binary; never carry the patch into a real build. | mitigated |

## Distribution

| Weight | Count | IDs |
|---|---|---|
| 9 critical | **2** | R-01, **R-02** |
| 6 high | 9 | R-03 … R-11 |
| 3–4 moderate | 8 | R-12 … R-18 *(R-17 closed)*, R-22 |
| 1–2 low | 3 | R-19 … R-21 |

**Ten risks at weight 6 is an undifferentiated middle**, and that is honest
rather than tidy: most of them are "certain work with a silent failure mode",
which is exactly the profile of an architecture conversion. The discriminator
between them is not weight but *which milestone carries them* — see the mapping
below.

## Which milestone retires which risk

The gap this register was created to close. Previously the ranked risks and the
milestone table did not reference each other, and R-12 had no owner at all.

| Milestone | Risks it must retire |
|---|---|
| **M1** | R-02 (gates), R-03 (stub logout), R-04 (first real edits), R-13, R-19 — ~~R-17~~ **retired 27 Sep** |
| **M2** | R-01, R-05, R-07 — ~~R-14~~ **retired 27 Sep** |
| **M3a** | **R-09** — now owned, having had no milestone until the definitions were fixed |
| **M3b** | R-08 |
| **M3c** | R-06 |
| **M4** | R-12 |
| **M5** | **R-10** — likewise now owned |
| *(continuous)* | R-11, R-15, R-16, R-18, R-20, R-21, R-22 |

**Every risk now has a milestone.** R-09 (no budgeted route to a bootable
nucleus) and R-10 (CMS stage 2 unowned) were the two weight-6 rows this table
was created to expose, and both were unowned because no milestone covered them.
M3a and M5 exist for exactly that reason.

