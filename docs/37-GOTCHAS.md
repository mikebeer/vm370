# Things that cost hours, so they need not cost them again

Hard-won on VM/370 CE, September 2026. Most of these produce symptoms
that look like something else entirely, which is why each one was
expensive.

## Reading decks in

**`#CP PURGE RDR ALL` before every `devinit`.** Three times a queued file
was read instead of the new deck, and the symptom was a code fault that
made no sense — an old module running against new expectations.

**Check what landed.** `LISTFILE x TEXT A (LABEL` and compare the record
count. A deck that did not arrive looks exactly like a bug in the deck
that did.

## The CMS loader

**It drops objects past roughly twenty**, whatever `SET LDRTBLS` is set
to, and reports them as undefined. Reordering helps but is not reliable.

**One TEXT file holding many object decks** is the way round it: `LOAD`
reads them all and there is a single name to lose. Concatenate the decks,
80 bytes at a time, in the order they should load.

**A TXTLIB is not available to us.** `TXTLIB GEN` rejects our objects with
`INVALID ESD RECORD FORMATS` because cc370 emits unnamed CSECTs —
deliberately, so the IBM linker cannot silently merge same-named sections.

**The entry point must come first in the `LOAD`.** Otherwise `GENMOD`
builds a module that starts somewhere arbitrary and the program returns
immediately, or faults at a fixed low address. **A crash address that does
not move across different programs means exactly this.**

**Anything replacing a library function must load before anything that
references it**, or the loader resolves to the library's copy first and
yours is reported as the duplicate. `DUPLICATE IDENTIFIER 'MALLOC'` in the
*first* `LOAD` line is the sign it worked.

**Include every libgcc helper, not the ones a scan predicts.** Generated
code calls `@@MULDI3`, `@172SU3F` and friends; nothing in the object
headers says which will be needed.

**`LOAD` and `INCLUDE` take `(NOTYPE`** to send the loader's commentary to
the listing. `SET CMSTYPE HT` does not reach it.

## CMS itself

**`@` is the character-delete symbol.** Every symbol cc370 generates
starts with `@@`, so any command naming one is silently mangled —
`GENMOD ... (FROM @@MAIN` becomes `(FROMAIN`. Issue
`CP TERMINAL CHARDEL OFF` first.

**Never name a module like its EXEC.** `MEMTEST MODULE` and
`MEMTEST EXEC` on the same disk means `MEMTEST` calls the EXEC, which
calls itself, until `MAXIMUM SVC DEPTH 20 HAS BEEN EXCEEDED`.

**A file caps at 65,535 records.** Ours reached 122,651 and we blamed
VMARC. Split decks below the limit; `vma` on the PC compresses by two
thirds and lets the package install the ordinary way.

**`COPYFILE` with a new LRECL pads each record**, it does not join them.
To reblock 80-byte records into 800, concatenate ten at a time — REXX
runs out of storage doing it in variables, so a small C program is
easier.

**PDPCLIB vintages differ.** The 2011 build on 191 defines `@@GTOUT`,
`@@GTERR` and `@@GET@ER`; the 2022 build on MAINT 19E does not. Read ours
onto A so it is found first.

## EBCDIC

**Codepoint arithmetic is wrong.** `48 + digit` gives ASCII zero; EBCDIC
zero is 240. Twenty library members did this, and the symptom was
`date()` printing only the month and `time()` printing nothing.

**Letters are not contiguous.** They come in three blocks with gaps, so
no range test works. Read codes from character literals with `strchar`
and test membership with `poschar` against a literal set.

**Whitespace is 0x40, not 0x20.** The VM recognised only Unicode
whitespace, so `words()` answered 1 for any string.

**Packing sources into card images: never split on a space.** CMS drops
trailing blanks from a variable-length record, so a chunk boundary that
lands on a space welds two words together. The compiler then reports a
missing THEN six hundred lines from the real cause.

## 24-bit code at 31-bit mode boundaries

**`BAL` and `BALR` are mode-sensitive, and that is mostly good news.** In
24-bit mode they place the instruction-length code, condition code and
program mask in bits 0-7 of R1 — `BALR 15,0` at `X'2000'` yields
`40002002`, not `00002002`. Bits 0-7 take no part in 24-bit address
generation, so it is invisible there. **In 31-bit mode the same
instructions set bit 0 to zero and put the updated address in bits 1-31**,
so they are correct with no change at all.

So a module converted wholesale to run AMODE 31 from entry needs no
attention here. CP contains 3,482 `BAL` and 118 `BALR`: **a population to
think about, not 3,600 fixes.** An earlier version of this entry claimed
every one was a latent bug. That was wrong.

**The hazard is mode boundaries** — a base or link register established in
24-bit code and then used in 31-bit code:

    BALR  15,0
    LA    15,0(0,15)      <- needed only when 24-bit code later runs AMODE 31

`LA` in 24-bit mode yields a 24-bit address with bits 0-7 zeroed. DAT
step 3 faulted at `V:400020B4` for exactly this: the `BALR` ran at entry in
24-bit mode and the register was used as a base after the `BSM`.

**The worse version of the same problem is deliberate packing, and mode
sensitivity does not rescue it.** Adrian found CP's `SAVE.COPY` overlaying
processor identity onto a fullword that holds a three-byte return address.
That is a control-block layout change with caller changes behind it. A
crude scan of CP finds 567 candidate sites — `ICM`/`STCM` with a 3-byte
mask, `AL3(` constants, `=X'00FFFFFF'` literals — which is indicative
rather than a work estimate, and the category most likely to be badly
wrong in either direction.

**A non-taken branch generates no address**, which is why the step 3 fault
surfaced several instructions after the mode switch rather than
immediately — the `BNM` in between never computed its target. Do not read
the faulting instruction as the first one affected.

## Hercules, running standalone code

**`hercules.rc` runs whether you asked or not.** Hercules 3.07 reads it
from the working directory at startup. Start in the CE directory and CE's
rc file runs: all its DASD attaches, and lowcore and the control
registers come up holding CP's leftovers. Give a standalone test its own
directory with its own `.conf` and `.rc` — and then the mechanism is
useful, because the whole test can live in the rc file.

**`stop` and `restart` do not load a new program.** They touch only the
CPU. Storage keeps whatever was poked into it, and the `.rc` file is read
at startup and never again. Edit the rc file, type `stop` then `restart`,
and the PREVIOUS program runs again — and if it passed before it will
pass again, looking for all the world like the new one passed. This cost a
full cycle on DAT step 2. Either exit Hercules and start it again, or at
the panel:

    stop
    sysclear
    script hercules.rc

`sysclear` is a clear reset: main storage and registers zeroed, so
nothing survives into the next program.

**How to tell which program actually ran**: read the disassembly and the
registers in the trace, never the result. Step 1 and step 2 both ended
`00600D`; what distinguished them was `STNSM 74(15)` versus `STNSM
118(15)` and `GR02=00000000` versus `GR02=00005000`. **A pass proves
nothing until you have confirmed which program produced it.**

**Always overwrite everything the previous test touched.** Step 2 happened
to cover step 1's whole footprint, which was luck rather than design. A
later test with a smaller footprint leaves the tail of its predecessor in
storage, and what runs is a chimera. `sysclear` removes the question.

**A rejected `ARCHMODE` still leaves you in some mode.** `EAS/390` was a
transposition; Hercules said `HHCPN128E Invalid architecture mode` and
`HHCCF008E ... Syntax error: ARCHMODE`, then defaulted to ESA/390 and the
test ran. Right answer by luck. Read the startup messages.

**CE's own config must stay `ARCHMODE S/370`.** Setting ESA/390 in it makes
CP die at IPL — observed as a disabled wait, `PSW=000A0000 00000017`, with
control registers still at Hercules reset values because CP never reached
`LCTL C0,C14,CTLREGS`. The ESA/390 lab needs its own config file.

**There is no IPL for a standalone program.** `stop`, poke storage with
`r`, plant a restart PSW at real address 0, `restart`. `restart` takes no
address of its own; it reads that PSW. Nothing is IPL'd because there is
no operating system.

**Trace the first run.** `t+` before `restart`. Hercules disassembles each
instruction, which is how hand-assembled bytes get verified rather than
trusted — a swapped `AC`/`AD` would turn DAT off instead of on and the
test would pass while proving nothing.

**Then turn tracing off.** `t+` prints a line plus a ten-line register dump
per instruction, so a poll loop floods the scrollback and pushes real
output — a console message, for instance — off the top before you see it.

**Hercules tells you whether DAT is live, and which mode.** Storage
displays are prefixed `R:` for real and `V:` for virtual; PSW byte 0
carries `04` when DAT is on; and the PSW's second word carries `80000000`
when AMODE 31 is in force. Free confirmation in every trace line. The
condition code sits in PSW bits 18-19, so byte 2 of `04081000` being `10`
said `LTR` had found a negative value, which corroborated the amode
independently.

**A marker byte left over from the previous run will fool you.** `MVI`
then `CLI` on the same byte reports success if the byte already held the
value, even when the store never executed. Clear it before every run.
Same family as the truncation artifact below.

**Give a bare-metal test a config with no DASD.** It builds its own channel
programs and has no operating system to stop it addressing the wrong
subchannel. A write command went to subchannel `0000` while a writable CE
pack was attached; only the device rejecting the command code prevented a
disk being scribbled on. A config with nothing attached cannot do that.

## ESA/390 DAT

**CR0 carries the translation format, and DAT checks it before it reads
any table.** Bits 8-12 must be `10110` — 4K pages, 1M segments. From
Hercules `esa390.h`:

    CR0_TRAN_FMT     0x00F80000    translation format bits
    CR0_TRAN_ESA390  0x00B00000    1M/4K ESA/390 format

Anything else is a translation-specification exception, code `0012`, on
the first translated reference — before a single segment or page table
entry is examined. Loading CR1 alone is not enough. The trap is assuming
ESA/390 has no format field because the page and segment sizes are fixed;
it has one, it is not defaulted, and a guest's leftover CR0 will not
satisfy it. **`LCTL 0,1,...` and load the pair.**

**Alignment the machine enforces**, from the same header: segment table
origin 4 KB aligned (`STD_STO 0x7FFFF000`), page table origin 64-byte
aligned (`SEGTAB_PTO 0x7FFFFFC0`). `STL` counts 64-byte units less one,
so 0 means sixteen entries; `PTL` counts 16-entry units less one, so 0
means sixteen pages. Reserved bits that must be zero: `SEGTAB_RESV
0x80000000`, `PAGETAB_RESV 0x80000900`.

**Reading the amode needs no above-the-line address.** `BSM R1,0` — with
R2 zero no branch is taken and the instruction only reports the current
mode in bit 0 of R1, which is the sign bit, so `LTR` then tests it. This
matters because every test that distinguishes 24-bit from 31-bit *by
truncation* necessarily uses an address above 16 MB, which would conflate
the mode switch with above-the-line translation.

**Identity mapping cannot prove translation is happening.** With every
page mapped to itself, DAT on and DAT off look the same. The first test
that distinguishes them maps one page to a *different* frame, stores
through it, turns DAT off and reads the frame directly — and checks the
ORIGINAL frame is untouched as well, because checking only the target
passes if the store were duplicated, and checking only the original
passes if nothing were stored at all.

**Segment 16 is where the 16 MB line falls.** Virtual `X'01000000'` needs
segment table entry 16, so a sixteen-entry table (`STL` 0) cannot reach
above the line at all — `STL` goes to 1 and entry 16 needs a page table of
its own.

## ESA/390 channel subsystem

**A subchannel is never enabled until `MSCH` says so.** `config.c:740`
sets only `PMCW5_V` at device creation; nothing sets `PMCW5_E` except
`MSCH` and the IPL path, and `device_reset()` clears it again. **`SSCH`
with E off returns condition code 3 silently** — no exception, no message,
nothing on the log. `STSCH` → `OI pmcw+5,X'80'` → `MSCH` first, always.
This is the `CR0` of channel I/O.

**`LPM` must be `X'80'`, not `X'00'`.** SSCH tests `orb.lpm & pmcw.pam`
and `pam` is `0x80`, so zero gives cc=3 rather than meaning "any path".
`MSCH` cannot change `pam`, which is why `STSCH`-first is safe.

**Allocate 32 bytes for the ORB, not 12.** `io.c:561` fetches
`sizeof(ORB)-1` = 31 bytes unconditionally whatever the X bit says, so a
12-byte ORB near the end of a loaded image takes an addressing exception
on a fetch the Principles of Operation says never happens.

**The alignment rules differ within one sequence.** ORB, SCHIB and IRB need
a **word**; the **CCW needs a doubleword** or it is a channel program
check.

**`SSCH` is asynchronous.** It returns cc=0 with the channel program merely
queued, so a single `TSCH` afterwards normally gives cc=1. The poll loop is
not optional — bound it so a stall is diagnosable rather than a hang.

**Subchannel numbers are sequential from `X'0000'` in config-file order**,
not by device number. Verify with `devlist` rather than arithmetic.

**`3215-C`, not `3215`.** Plain `3215` maps to the 3270 handler, an
entirely different code path.

**If you poll, CR6 is irrelevant.** Taking interrupts instead needs all
three of: PMCW E bit on, PSW bit 6 on, CR6 bit 0 on, plus a valid I/O new
PSW at `X'78'`.

## Addressing, if the S/380 route is ever revisited

**A test that writes and reads through the same address cannot detect
truncation.** In 24-bit mode `04100000` and `00100000` are the same byte,
so a write-then-read-back passes while quietly scribbling on CMS. Three
published measurements — 192 MB aliasing, a 32 MB fault, a 12 MB limit —
were all this artifact.

**The test that cannot fool itself**: write two different bytes at two
addresses that are the same storage if the mask is in force and different
if it is not, then check whether both survived. Under CE: they collide at
24-bit, they are separate after `BSM`. Reusable for any addressing change.

**A guest's `STCTL` does not read the real control registers.** CP
intercepts it and simulates against the ECBLOK, so a CMS program reading
`CR13` reads the *virtual* one. `CR0 = 000000E0` from such a program is the
giveaway — `DMKBLDEC` contains literally `MVI EXTCR0+3,X'E0'`. Read real
control registers at the Hercules panel with `stop` then `cr`.

**`GETMAIN LOC=ANY` only goes above the line for requests over 16 MB.**
Exactly 16 MB with a subpool is refused with abend `A0A`; 20 MB is
granted. Anything smaller is quietly satisfied from ordinary storage —
and then writing 6 MB into it destroys CMS.

**Only one such request at a time**, which is why PDPCLIB uses `memmgr`:
one `GETMAIN` of `REQ_CHUNK` bytes, sub-allocated thereafter.

**I/O buffers must stay below the line.** Channel programs address 24
bits. Output appearing one character at a time is the symptom.

**GCCLIB will not accept a foreign `malloc`** — its stdio is tied into
dlmalloc. PDPCLIB will.

## Debugging method that worked

**Bracket, do not read.** Probes at phase boundaries, each printing a
marker and then allocating and freeing a small block so the heap is
checked at every step. The last marker to print names the phase. Three
rounds took "somewhere in the compiler" to one line — the `snprintf`
hack in `S370/cms.h`.

The faulting instruction was a victim in every case but one. Reading code
at the crash site almost never helped.

**Arm the failure answer first.** DATTEST's second instruction plants its
own program-check PSW, so a fault lands in a wait state whose address
says "program check" instead of looping or wandering. That one
instruction is why three broken runs produced `000DED` plus a usable
interruption code rather than a hang.

**Give each test a distinct answer.** Step 2 uses `000BA1` for "the target
frame did not receive it" and `000BA2` for "the original frame was
modified", because one shared failure code would have needed a debugging
session to tell apart what a different constant says for free. Distinct
codes across successive *tests* would also have caught the wrong program
running — steps 1 and 2 both used `00600D`, and that cost a cycle.

**Compute addresses, do not count them.** Hand-assembly was fine at ten
instructions and stopped being trustworthy at thirty. `asm.py` resolves
labels in two passes and checks every displacement against the 12-bit
field and every alignment the machine enforces. It earned its keep
immediately: the one-instruction fix above shifted all 33 displacements,
which was an edit rather than a transcription — and its alignment check
caught a bug in the assembler itself before any Hercules run. Its `put()`
is bounds-checked because a bytearray slice assignment past the end
silently **appends** instead of failing, which put a page table on the tail
of an image once.

**Measure, do not infer.** Every claim retracted in this project failed the
same way: a mechanism was inferred that fit the symptom, and the inference
was never measured. The 192 MB aliasing, the VMARC limit, the CR13
argument. A fifteen-minute panel reading beats a confident explanation.

**Make iteration cheap first.** Once the build kept object decks on disk,
an experiment cost a 30 KB deck instead of 2.5 MB. Everything after that
went faster. Same with these DAT tests: twenty-odd lines in an rc file,
and usually one word changed between steps.

**Keep a known-good reference.** A big-endian 32-bit build of the same
sources answered, every time, whether a fault was in the code or in the
port.

## The first paging workload (5 October)

**Nothing before M5a made this CP page.** Every test had a 16 MB real
machine and guests too small to fill it. A 16 MB MAINT loading the CMS
nucleus from the reader — the CMS loader clears storage with `MVCL` — is
the first workload that did, and it found five defects in a row, each one
hidden behind the previous (I-236 … I-240). Treat "has it paged yet?" as a
coverage question, like "has it taken an I/O interrupt yet?".

**A flag byte riding on a pointer is invisible in AMODE 24 and an address
in AMODE 31.** Two shapes so far: a field whose byte 0 is a flag
(`CORSWPNT`/`CORFLAG`, read whole with `L`), and a flag stored into byte 0
of a *branch* address (`CPEXADD`, DMKPAG's I/O-error marker, branched
through by DMKDSP). The `(,R0)` cousin: **register 0 as a base is no
base**, so `LA R0,1(,R0)` loads 1. The assembler cannot say so;
`mkdeck.verify` now does.

**An ESA/390 PTE of `00000001` is real frame 0, valid.** The S/370 habit of
clearing a PTE's address bytes and keeping the flag byte does not carry
over: the I bit lives in byte 2 with the address nibble. A three-byte `XC`
takes it along, and a guest page silently maps to CP's own PSA — the
symptom is CP's new PSWs changing by one byte each (`X'65'` → `FE`,
`X'69'` → wait bit) while nothing in CP wrote them.

**CE's VM50-4 is a preferred PAGE volume whose TEMP cylinders are 800-byte
CMS format.** `SYSOWN (VM50-4,PAGE)`, allocation record TEMP 1–100, every
track `dl 800`. The first page write to it ends in unit check + incorrect
length (`Sense=NRF`). CE itself never pages, so it never noticed. Patched
on our pack (cylinders 1–100 → TDSK); the original is kept beside it.

**Diagnostics that worked.** Hercules's instruction-trace *range* filters
on the real address — a pageable module traced by its virtual address
shows nothing. A breakpoint fires once per run. The HTTP command channel
(`/cgi-bin/tasks/syslog?command=`) lets you answer a stuck Start prompt or
`exit` a dead CP without killing Hercules. When a module grows, every
module after it moves — reread the map before trusting an address from
yesterday's dump (8 bytes of DMKDSP moved ASYSVM and WAITPAGE, and two
hours went into a "completions never processed" theory). To see who owns
real storage at a wait, dump the top 256 KB in 15.5 KB `r` calls (the HTTP
reply truncates near 1000 lines), read CR1, and walk the segment table
offline — that is what found I-240 in one run.

## EC-mode CMS (6 October)

- **DMKVMI is guest code.** CP's IPL simulator is a pageable CP module, but
  DMKCFG pages it into the *virtual machine* at X'20000' and it runs there.
  Every PSA reference inside it is the guest's page 0, so the rule "rename
  the architected S/370 slots so nothing uses them by accident" does not
  apply to it: its `STH R13,INTTIO` is where a S/370 EC-mode IPL leaves the
  IPL device address for the guest (`G370TIO` in our PSA). I-47 got this
  wrong, I-241 undid it. The same question — whose low core is this? — is
  worth asking at every `X-PSA(,Rn)` site.
- **An undefined symbol is four zero bytes, not an error you will see.** XF
  flags IFO188 and still writes the deck. `asmchk` is the gate, and it only
  knew `EXEC VMFASM` lines until I-241: a staged slice types `vmfasm` at the
  console. Check the gate when the result is impossible.
- **A S/370 EC PSW is strict where BC was not.** Bits 24–31 and 32–39 must
  be zero: `CL4' INI'` in a wait PSW's address, a return PSW with an SVC
  code in bytes 2–3, bit 32 as a "31-bit" marker — each is a specification
  exception, and since the program new PSW points back at the loader, a
  wait becomes a restart loop with no message. Our CP's TM X'7F' on byte 4
  (bit 32 = AMODE) is the one deliberate relaxation.
- **Who builds the PSW?** Converting every `DC` PSW constant misses the PSWs
  code constructs (`MVI ITSPSW,ON` / `XC ITSPSW(8)` / `STC key`). grep for
  `MVI|OI|NI|STC|XC .*PSW` and for `LPSW` of a work area, not just `X'FF06'`.
- **A reader IPL and a disk IPL arrive in different modes.** The disk IPL
  record carries the EC PSW; the card loader branches under its own BC PSW.
  Code that must run in EC mode switches itself (`LPSW` to the next
  instruction) rather than trusting the IPL path.
- **`cmswrite`'s 300-second wait after the heading prompt** is the one place
  the build cannot poll: an abend prints `CMS` and waits for a command. When
  the dialogue fails, read `c1.log` after `DMSINI612R`; the nucleus is
  already written by then, so a following `IPL 290` tests the same code.
- **CP TRACE as a debugger.** `CP TRACE SVC` / `TRACE PROG` (RUN off) stop
  the VM at each event with the terminal in CP mode; `IPL xxx STOP` stops at
  the IPL PSW. A test json can `D G`, `D PSW`, `D 0.C0` at each stop and `B`
  on. For "what did the guest see at its first SVC" this beats Hercules
  `t+`, which filters on real addresses.
- **`build.sh reset` + `write` restore the whole pack**, MAINT's 191 (the
  staged TXTLCLs) and the 290 nucleus included. Stage CP, write, then stage
  CMS and `cmswrite`, and take the snapshot after the CMS write — or the
  next reset silently hands back the pristine CMSTEST nucleus ("VM/CMS Test
  System"), which boots in BC mode and looks like success.
