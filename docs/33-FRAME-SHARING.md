# Named systems shared at frame granularity — M3c, built and measured

4 October 2026. `IPL CMS` by saved-system name works on the converted CP, for
two users at once, with the shared pages in one set of frames and each user's
private pages private. This is CP-67's mechanism (`05-CP67-PRIOR-ART.md` §3)
in VM/370's modules, and it closes wall 24 (`I-195`). Deck `XA0045DK`:
DMKCFG, DMKPGS, DMKVMA, DMKBLD.

## What VM/370 did, and why it could not survive 1 MB segments

At the first `IPL CMS`, DMKCFG's `PAGLOOP` writes the saved system's DASD
slots and keys into the user's own swap entries, then `SHRTBLD` **adopts the
user's page table** for each shared 64 KB segment as *the* shared table,
hooks it to a `SHRTABLE`, and every later user (`SHRTFND`) swaps their own
table for it and frees theirs. The segment table entry is the unit of
sharing. With ESA/390's 1 MB segments the whole megabyte F00000–FFFFFF would
become common — and CMS keeps private nucleus pages in F00000–F7FFFF beside
the shared F80000–FAFFFF. That is `FRE013` at `SHRSLOOP` (`I-195`), and the
reason stage A (an unshared CMS) was retracted.

## What CP does now

**The SHRTABLE's page tables are models, never placed in a user's STE.**

1. *First IPL (`SHRTBLD` → `MODLOOP`)*: for each shared 64 KB group,
   `DMKBLDRT PARM=PAGTONLY+NEWPAGES` makes a fresh 256-entry table; its
   header gets `PAGSHR` → the SHRTABLE and `SWPVM` = SYSTEM; the group's 16
   swap entries are copied from the user's table (slots and keys from
   `PAGLOOP`) and flagged `SWPSHR`. The model is then put in the user's STE
   for sixteen `TRANS 2,1,OPT=(BRING,DEFER,LOCK)`, one per page, so the
   frames come in through the first user's address space, locked
   (`CORIOLCK`); `CORFPNT` is moved to SYSTEM and `VMPAGES` corrected. The
   user's own STE is restored and `PTLB` issued. One model per group keeps
   `SHRPAGE` one-to-one with `SHRSEGNM`, as before.
2. *Every IPL (`SHRCOPY`)*: the model's 16 PTEs (frame | valid) and 16 swap
   entries are copied into the user's **private** 256-entry table for the
   megabyte: group *g* of 64 KB segment number *s* is STE `s>>4`, pages
   `(s&15)*16 … +15`. Private pages in the same megabyte are untouched.
3. *Release (DMKPGS `SHRDROP`)*: a user's copy is dropped — PTE invalidated,
   swap entry rewritten as a fresh zero-page entry (`SWPRECMP` + page
   number) — never freed, since the frame is SYSTEM's and the slot the saved
   system's. `PARTIAL` keeps them. An all-zero entry is not allowed: DMKPGSPO
   rescans and DMKPGTPR abends on a zero slot (`I-212`).
4. *Change detection (DMKVMASH)*: scans the group's 16 PTEs (not the
   megabyte); a `CORIOLCK`'d frame is unlocked before it is freed; the
   model's PTE is invalidated with the user's copy.
5. *DMKBLD*: a segment that already has a full table is left alone by
   `DMKBLDRT` (LOADSYS of GCCLIB, in the same megabyte, used to rebuild it
   — `BLD002`), and `DMKBLDRL`'s `CHKPAGE` lets an `SWPSHR` copy go.
6. *DMKCFG `PAGBLDTB`* rounds a small machine's table extension to the
   megabyte (a 2 MB AUTOLOG1 used to get a 48-entry table for segment 15).

The ESA/390 common-segment bit is not used anywhere.

## Measured

Storage image at the hang of the second attempt, then w41 on `SNAP-I217`:

```
model 0 pto FF0080 hdr act/tot 00000001 shr 00F05608 swp 00FF0488  swaphdr 00042700 00FF0080
   page 128 pte 00E7E000 swp 5c80060600071300 frame[0:16]=00f9080800f8004400f8004800f92158
MAINT seg15 pto FF0D00: page 128 pte 00E7E000 swp 5c80060600071300   (the same frame)
                       page   0 pte 00000400 swp 4000000000000000   (private, untouched)
```
```
14:31:23 LINE 00A LOGON  AS MAINT    USERS = 004
VM Community Edition V1 R1.2 … Ready;
00F80000  00F90808  00F80044  00F80048  00F92158
AUTO LOGON   ***   CMSUSER  USERS = 005
CPWATCH  - DSC, AUTOLOG1 - DSC, OPERATOR - 009, CMSUSER  - DSC, MAINT - 00A
14:31:45 USER DSC LOGOFF AS CMSUSER  USERS = 004  FORCED
LOGOFF AT 14:31:49 GMT SUNDAY 10/04/26
```

CP initialisation now completes with AUTOLOG1's directory `IPL CMS` (which
autologs CPWATCH), which it never had before on this CP.

## Found on the way

- `I-210` `build.sh stage` ran without `asmchk`; a deck that failed to
  assemble was reported staged and tested.
- `I-211` a device DMKRIO names but the Hercules configuration lacks has
  `RDEVSSID` 0; `TSCH` with SID 0 is an operand exception (PoP: *bits 0-15 of
  the SID must contain 0001 hex*). DMKIOS answers CC3 as SIO did.
- XA0036DK's DMKVMASH kept S/370's `SLL R2,8` on the fullword PTE, so ISKE
  read another frame's key — never exercised until a named system IPLed.

## Not yet done (M3, increment 2)

- `SHRUSECT`/`VMABLOK`/`VMSHRSYS` bookkeeping when a user leaves a named
  system, and freeing the models (unlock, `DMKPTRFT`, `DMKFRET`) when the
  last one leaves. Today the models stay resident until CP is re-IPLed.
- When DMKVMASH finds an altered shared page, other sharers' copies are not
  yet invalidated (only the model's PTE and the finder's copy).
- ~~LOADSYS (`DIAG 64`, DCSS such as GCCLIB)~~ — done 19:15: a shared group may
  end short (GCCLIB is 13 of 16 pages in its second group); unsaved pages are
  private zero pages (`I-214`), and DMKBLDRL lets copies go (`I-215`, the
  base-register-0 trap). PURGESYS by name still uses VM/370's path.
- A small machine whose VMSIZE is extended to reach a shared segment can
  address the rest of that megabyte as zero pages (VM/370 exposed only the
  64 KB segments).
