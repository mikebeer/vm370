# Traceability: issues → risks → milestones

27 September 2026. Three registers exist —
[`12-RISKS.md`](12-RISKS.md) (what may go wrong),
[`13-ISSUES.md`](13-ISSUES.md) (what did), and the milestone table in
[`../arch/31bit/README.md`](../arch/31bit/README.md) (what we are doing about
it). Each was useful alone and none of them said how they connect.

This is the connection, and it is not bookkeeping: **linking issues to risks
turns an estimated probability into a measured one.** A risk with realised
instances is not a guess any more, and two of them were scored too low.

## The finding first

| Risk | Scored P | Realised instances | Should be |
|---|---|---|---|
| **R-02** silent-gate omissions | M | **4** — CR0 format, `PMCW5_E`, CR6, and `I-06` | **H → weight 9** |
| **R-04** column/encoding-sensitive source corrupted by tooling | H | 2 — `I-17`, `I-02` | H, confirmed |
| **R-13** z390 dialect unreliability | M | **4** — `I-01`, `I-03`, `I-17`, `I-18` | M, but see below |
| R-16 corrupting the CE distribution | M | 1 near-miss — subchannel 0000 write | M, confirmed |
| R-22 `AUXLCL` anchor fragility | M | 2 in CE's own history — `DMKGRF`, `DMSSTT` | M, confirmed |

**R-02 was underscored and is now the joint top risk.** Three silent gates were
already known — CR0's translation format, `PMCW5_E`, and CR6 — and `I-06` is a
fourth of exactly the same shape: a wrong bit, no diagnostic, and a failure that
presents as success. `X'20'` in a page-table entry leaves the invalid bit clear,
so every unmapped page in the segment was a *valid* entry aliased to real page 0.
Four realised instances is not "Medium probability of another one".

**R-13 is the interesting opposite case.** It has four realised instances, which
normally argues for raising it — but `16-NATIVE-BASELINE.md` demoted z390 from
authority to convenience, so the *impact* of a z390 misbehaviour collapsed. The
probability is high and the consequence is now nearly nil. Left at 4, with the
reasoning recorded so nobody re-raises it on instance count alone.

## Issues → risks → milestones

Not every issue maps to a risk. Forcing one would be worse than leaving it
blank, so `—` means "a defect with no standing risk behind it", and those are
mostly environment facts and one-off authoring slips.

| Issue | | Risk | Milestone | Status |
|---|---|---|---|---|
| **I-01** | CP's `MSG` macro under z390 | R-13 | continuous | z390 only |
| **I-02** | `DMKCPI` U+E000 encoding | **R-04** | M1 / M2 | fix known |
| **I-03** | `DMKDSP` duplicate `USING` | R-13 | continuous | z390 only |
| **I-04** | `XATEST` listing never checked | R-17 | M0 | fixed |
| **I-05** | 59 macro names vs z390 directives | R-13 | continuous | **open** |
| **I-06** | PTE invalid bit `X'20'` vs `X'400'` | **R-02** | M2 | fixed |
| **I-07** | `herc.conf` codepage name | — | continuous | fixed |
| **I-08** | M1 criterion passes a hung CP | **R-02** | M1 | fixed |
| **I-09** | M2 names no observable | — | M2 | fixed |
| **I-10** | M3 bundles three risks | R-06, R-08 | M3a/b/c | fixed |
| **I-11** | IPL-from-DASD unowned | **R-09** | M3a | fixed |
| **I-12** | CMS stage 2 unnumbered | **R-10** | M5 | fixed |
| **I-13** | Hercules softfloat TLS link | R-21 | continuous | worked around |
| **I-14** | `--disable-shared` module clash | — | continuous | documented |
| **I-15** | device modules need `make install` | — | continuous | documented |
| **I-16** | OPERATOR cannot IPL CMS at 2 MB | — | continuous | documented |
| **I-17** | `TRACE`/z390 collision, and the column trap | **R-04**, R-13 | continuous | fixed |
| **I-18** | first `XAOPS` validation proved nothing | R-13 | M0 | fixed |
| **I-19** | `snt-collisions.py` `SYSHRSG` assumption | — | M3c | fixed |
| **I-20** | storage-key control broke the guard | — | M4 | fixed |
| **I-21** | `RSCH` opcode "dispute" | R-17 | M0 | closed |
| **I-22** | "Hercules cannot prototype `SIO`" | R-03 | M1 | closed |
| **I-23** | "segment 15 is the false alarm" | **R-06** | M3c | closed |
| **I-24** | `CODE70` not `CODEB0` | R-07 | M2 | closed |
| **I-25** | `CPCREG0` called a constant | R-15 | M2 | closed |
| **I-26** | duplicate spool file from `START`+`devinit` | R-16 | continuous | fixed |
| **I-27** | "g4ugm verifies CE against IBM" | — | continuous | closed |
| **I-28** | `SAM24`/`SAM31` called z/Architecture | — | 64-bit | **open** |
| **I-29** | CE already has a 4 KB storage-key change | **R-12** | M4 | **open** |

## Risks → issues, the reverse view

The column that matters is the middle one: a risk with nothing in it is scored on
judgement alone.

| Risk | W | Realised as | Milestone |
|---|---|---|---|
| **R-01** geometry in bare shift literals | 9 | — *(enumerated, not yet realised)* | M2 |
| **R-02** silent-gate omissions | 9 ↑ | CR0, `PMCW5_E`, CR6, **I-06**, **I-08** | M1 |
| R-03 channel logout has no equivalent | 6 | I-22 | M1 |
| **R-04** column-sensitive source | 6 | **I-17**, I-02 | M1/M2 |
| R-05 `DMKBLDRT` ABI | 6 | — | M2 |
| R-06 frame sharing needs bookkeeping | 6 | I-10, **I-23** | M3c |
| R-07 STE flag invariant unenforced | 6 | I-24 | M2 |
| R-08 S/370 guest regression | 6 | I-10 | M3b |
| R-09 no route to a bootable nucleus | 6 | **I-11** | M3a |
| R-10 CMS stage 2 unowned | 6 | **I-12** | M5 |
| R-11 analysis outruns implementation | 6 | — | continuous |
| R-12 guest-visible storage keys | 4 | **I-29** | M4 |
| R-13 z390 dialect unreliability | 4 | I-01, I-03, I-17, I-18, I-05 | continuous |
| R-15 constant sites needing judgement | 4 | I-25 | M2 |
| R-16 corrupting the CE distribution | 4 | I-26, near-miss | continuous |
| R-18 `wide/` supersedes 31-bit | 3 | — | continuous |
| R-19 counts are floors | 2 | — | M1 |
| R-20 multiple-device interrupts | 2 | — | continuous |
| R-21 lab patch leaks out | 2 | I-13 | continuous |
| R-22 `AUXLCL` anchor fragility | 4 | CE's own `DMKGRF`, `DMSSTT` | M1 onward |
| ~~R-14~~ OSMACRO/DOSMACRO | — | closed 27 Sep | — |
| ~~R-17~~ CE assembler rejects `XAOPS` | — | closed 27 Sep, I-04/I-21 | M0 |

**Five risks have no realised instance and no milestone evidence yet**: R-01,
R-05, R-11, R-18, R-20. R-01 at weight 9 is the one to watch — it is scored
highest and rests entirely on reading, which is precisely the profile of the two
conclusions this project has had to retract (`I-23`, `I-27`). Its enumeration
([`R01-SHIFT-SITES.md`](R01-SHIFT-SITES.md)) is evidence that the sites exist,
not that converting them is as mechanical as claimed.

## Milestones → modules, risks and issues (maintained table, 4 October 2026)

This is the one table that links the three registers. Rows are milestones;
each names the modules it changed (as update decks), the risks it retires and
the issues it opened and closed. `13-ISSUES.md` holds the issue text,
`28-IPL-WALLS.md` the traces, `30-STATE.md` the current position.

| Milestone | Status | Modules / decks | Risks | Issues |
|---|---|---|---|---|
| M0 macros | done | `MACLIB GEN`, 24 members | — | I-08…I-12 closed |
| M1 IPL + console | done 3 Oct | `XAIO` macro set; DMKIOS XA0004DK, DMKCNS XA0021DK, DMKCKP XA0015DK, DMKCPI XA0013DK, DMKCCH XA0010DK, DMKSAV XA0017DK, DMKRIO/RBLOKS XA0002DK, PSA XA0001DK… | R-02, R-03, R-04, R-19, R-22 retired | walls 1–22; I-83, I-86, I-87, I-97, I-102, I-107, I-115 closed; **I-211** (device without subchannel → CC3) |
| M2 DAT tables | tables done | CORE XA0033DK, EQU XA0037DK, DMKBLD XA0034DK, DMKPTR/DMKPGS/DMKCFG/DMKVMA/DMKATS/DMKCDB/DMKCDM/DMKCDS/DMKDRD XA0036DK (the DAT sweep), DMKPRV XA0041DK keys | R-01, R-05, R-07 retired for the tables | I-185 (16-bit page numbers in DMKBLDRT), I-196, I-200, I-202 closed |
| M2 AMODE 31 | **step 1 done** (5 Oct, SNAP-I231): the `TRANS`/DMKPTRAN LRA runs in AMODE 31 via a PSA stub (XA0046DK, PSA XA0001DK, EQU XA0037DK); `OPT=AMODE31` for CP-computed 31-bit addresses (DMKCDB, DMKCDS, DMKPGS); DMKBLDRT builds segment tables past 16 MB (XA0034DK). **Step 2 done** (5 Oct, i241/SNAP-I241): the sweep (XA0047DK, 209 strips in 74 modules, I-126) and the PSW flip (XA0048DK), plus the six idioms the sweep cannot see (I-225–I-233: LA sums at 16 MB, CCW words as bases, BALR/BAL condition-code saves, packed FRET words, ICM-3 register history, guest-resident CP code). **Step 3 done** (5 Oct, i244/SNAP-I244): the G31 tape guest runs in AMODE 31 — `VMAM31` kept by the PSW gatekeepers, GADR31 for guest addresses (I-234). Open for M5: a 31-bit guest's own DAT (DMKVAT), IDAWs/format-1 CCWs | R-01, R-15 | **I-208, I-224, I-126 closed**; I-216 – I-234 (34-AMODE31) |
| M3a DASD IPL | done 3 Oct | DMKSAV, DMKCKP, DMKCPI | R-09 retired | I-119 (snapshot purpose) |
| M3b CMS by `IPL 190` | done 4 Oct | HDK modules reassembled (I-194); DMKPTR XA0036DK (I-196); DMKPRV XA0041DK (I-199, I-200, I-202); DMKDEH/DMKDIR XA0042DK (I-203); DMKPGS (I-206); DMKCDB/DMKCDS XA0044DK (I-207, I-209) | R-08 retired | walls 23, 25–29 closed; I-201 (dump) open |
| M3c shared by frame | done 4 Oct | DMKCFG, DMKPGS, DMKVMA, DMKBLD XA0045DK | R-06 retired | I-195, I-210, I-211, I-212 closed; increment 2 open (`33-FRAME-SHARING.md`) |
| M4 two guests, keys | largely done | DMKPRV (ISKE/SSKE), DMKCDB (DISPLAY K) | R-12 measured (CMS sets both halves alike) | I-29 superseded |
| M4b real storage up to 2 GB | **done** 7 Oct: M4b.1 probe + CORTABLE at IPL; M4b.2 storage above 16 MB is CP's paging store (XA0053DK, docs/38); M4b.4 CP's machine ends at 16 MB, the rest up to 2 GB is paging store. M5g regression clean at 256 MB (r4b15) and 2048 MB (r4b17). M4b.3 (high frames as frames, HPO route) deferred, not needed for M7/M8 | DMKCPI (storage sizing, CORTABLE), the flag-in-byte-0 fields (CORSWPNT/CPEXADD family, I-236/I-238 patterns), I-185 (16-bit page numbers), DMKCDB/DMKCDS DISPLAY/STORE (I-207); test: Hercules mainsize 64M → 256M → 2G, paging workload at each step | R-01, R-05 | I-185, I-207; storage above 2 GB belongs to M9 (64-bit) |
| M5 31-bit CMS, real > 16 MB | **in progress** as XA-CMS-light (`36-M5-CMS31.md`): M5a build route ✔ 5 Oct; M5b EC-mode nucleus ✔ 6 Oct; M5c HIGHSTOR (storage above 16 MB) ✔; M5d SVC 120 GETMAIN/FREEMAIN RU, GCC380 runs AMODE 31 ✔ (LOC=BELOW stays low, I-248); M5e cREXX: 24-bit build with GCC370 running (w235); 31-bit blocked — GCC380's S/380 PDPCLIB passes high addresses to CMS OS services (BLDL), see M5f | DMSINI, DMSITS, DMSITE, DMSITP, DMSIOW, DMSFRE, DMSINS, DMSSVT, DMSEXC; HIGHSTOR; DMSLCL control file | R-10 | I-203, I-204, I-235, I-241, I-242–I-248 |
| M5f 31-bit C toolchain (cross) | **done** 7 Oct: GCC 13 `-m31` on the PC + newlib 4.4 + `cmsrt` (HIGHSTOR heap, CMS file/console bridge, IBM-1047) + soft-fp; cREXX 2022 RXC/RXAS/RXBVM/RXDAS cross-built, full chain runs on VM/370+ in AMODE 31, 2022 tests identical to a Linux build (w258–w260). Needs Hercules 4.x (z900-level N3 instructions) | `arch/31bit/m5f/` | R-10 | — |
| M5g native 31-bit C | **done** 7 Oct: GCCLIB31 (cms-370-gcclib 1.0.0 + `mk31.py`: AMODE 31 C, AMODE 24 CMS stubs with BSM returns, dlmalloc on HIGHSTOR, low DMSFREE storage for everything CMS sees, MVCL loops) built on VM/370+ by `GCLB31 EXEC`; M5G2 (30 MB heap above 16 MB) runs; cREXX 2022 built natively by `CRXMK31 EXEC` (GCC380) as RXCN/RXASN/RXBVMN/RXDASN, output equal to the cross build (w265). Fixed on the way: I-252 (SVC 10 from AMODE 31), cREXX's snprintf hack (the DLMALLOC PANIC), GCCLIB's stack-bin size and %g. `36-M5-CMS31.md` M5g | GCCLIB, DMSSMN, cREXX `cms.h` | R-10 | I-252 |
| M7 ESA/390 guests | **done** 8 Oct (lx78): Linux/390 4.0 31-bit, IPLed from MAINT's reader, boots with its 3215 console and runs `/init` ("HELLO FROM LINUX/390 ON VM/370+ (M7)"). M7.1 SET ESA; M7.2 channel subsystem DMKVCS; M7.3 guest DAT DMKVAX; M7.4 timers and missing instructions; M7.5 cio (MSCH PMCW bits, SENSE ID and lone NOP answered by DMKVCS, immediate status as interruption, CSCH status, DSP001), real TEID for protection exceptions, home-space instruction fetch and quick LRA (docs/39 M7.5, docs/40 §5). **Deviations from ESA/390: register D-1…D-19 in `docs/40-M7.3-GUEST-DAT.md`** | guest channel-subsystem I/O simulation (SSCH/TSCH/STSCH/MSCH/TPI, subchannels, ISC) in DMKPRV/DMKVIO/DMKVSI/DMKCCW; ESA/390-format guest DAT shadowing (DMKVAT); ESA/390 virtual control registers, lowcore and interruption codes; guest machine mode per directory (cf. VM/XA S/370 vs XA guests) | new | — |
| M8 current cREXX natively | **planned**: current cREXX (needs ~18.5 MB heap with exits; C99+). Gap: GCC380 is GCC 3.2.3; measure the C-language gap, then patch sources (cf. Adrian's CMS patches) or bring a newer native compiler (cc370 / GCC 3.4.6 hosted on CMS). Cross build (M5f) meanwhile | — | R-10 | — |
| M6 31-bit CMS proper | **deferred** — not required for cREXX | the CMS nucleus itself at AMODE 31: FSCBs, PLISTs and DIAG plists above the line, the 156 `LA` strips and 34 ICM-3 sites in nucleus code, DMKPRV's ISKE/SSKE/RRBE simulation (I-46) | R-10 | — |
| continuous | — | build tools: `mkrun`, `snapshot`, `replchk`, `mkdeck`, `drive` | R-11, R-13, R-16, R-18, R-20, R-21 | I-197, I-198, I-205, I-210 closed |
| M9 64-bit (z/Architecture) | **planned** — after M8; restored to the list 7 Oct (user) | what `17-CARRY-FORWARD-64.md` says must be redone: PSW and lowcore (8 → 16 bytes, `LPSWE`), DAT (region tables, CR1, 8-byte table entries -- the parameterised entry width and shift symbols), AMODE 64 switching (`SAM64`, I-28), the 912 self-relative branch sites; the channel subsystem, 4 KB keys, frame sharing, page/segment geometry, `XAOPS` and the build harness carry over unchanged; then 64-bit guests and CMS storage above 2 GB | R-01, R-05 | I-28 |

## I-29, and why a new issue is good news here

`PSA.AUXHRC` reads:

    HRC019DK V01 IMPLEMENT EXTENDED HRC QUERY FUNCTIONS
    HRC004DK V01 ENABLE SUPPORT FOR 4K STORAGE KEYS
    HRC002DK V01 SHUTDOWN POWEROFF SUPPORT

**CE has already made a 4 KB storage-key change**, as update level `HRC004DK`,
across six members: `DMKAPI`, `DMKCLK`, `DMKCPI`, `DMKPSA`, `EQU` and `PSA`. In
`PSA` it replaces one line:

    CPCREG0  DC    X'81800CC0' CP ARCH CONTROL AND EXTERNAL MASK   HRC004DK

`X'81800CC0'` has CR0 bit 8 set and bit 9 clear — page size 4 K — with bits
11–12 clear, segment size 64 K. Which is exactly what `06-LEDGER.md` recorded
from `CTLREGS`: `PAGE4K` without `SEG1M`.

Two things follow. **`R-12` has prior art inside the tree**, so the 4 KB key
transition should start by reading those six decks rather than re-deriving it.
And it is a second sighting of the same pattern as `ARCHTECT`: the groundwork for
this conversion keeps turning out to be partly done, by IBM in 1979 or by CE
later, and **the update levels are where CE's half of it is recorded.** Nothing
in `docs/` had looked there before `15-UPDATE-LEVELS.md`.

It also vindicates `I-25`. `CPCREG0` was first classified as a constant and
corrected to "a live CR0 save area"; it is in fact *both* — a `DC` carrying CP's
architecture control value, which `STCTL C0,C0,CPCREG0` then overwrites. A
constant that is also a save area is worth flagging to anyone about to treat it
as one or the other.
