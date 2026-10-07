# M4b — CP real storage above 16 MB (scoped 7 October 2026)

M2 made CP run AMODE 31 and give its guests up to 256 MB of *virtual*
storage. The *real* machine is still 16 MB: Hercules runs with `MAINSIZE 16`
(R-25, I-157), and with `MAINSIZE 64` CP still says
`DMKCPI957I Storage size = 16384 K` and uses none of the rest (r4b1,
7 October). This note says why, and how CP will use real storage up to 2 GB.

## Why CP stops at 16 MB today (measured from source and r4b1)

| | Where | What |
|---|---|---|
| 1 | DMKCPI `KEYLOOP` (00590000–00596000) | The size probe walks SSKE up by 2 KB until an addressing exception. DMKCPI's own initialisation runs AMODE 24 until its first interrupt (I-224), so `LA R5,2048(,R5)` wraps at 16 MB and `L R5,=X'01000000'` stores 16 MB. |
| 2 | SYSCOR macro, DMKSYS | `RMSIZE` must be 240K–16392K. The CORTABLE (16 bytes per 4 KB frame) is a static `DC` in DMKSYS sized from RMSIZE, and DMKCPI uses min(real, RMSIZE). At 2 GB the table would be 8 MB of nucleus. |
| 3 | Everything that holds a real address in 24 bits | Format-0 CCWs carry 24-bit data addresses: paging I/O (DMKPAG's IOBLOK CCWs), guest I/O (DMKCCW's translated CCWs for one-page data areas), DIAGNOSE I/O (DMKDGD), spooling. Control-block fields with a flag in byte 0 (the I-236/I-238 family). |

Rows 1 and 2 are local. Row 3 is the work.

## The design: storage above 16 MB as CP's paging store

The first plan (kept below as *Rejected*) was VM/SP HPO's: user pages in
frames above the line. Reading the paging and I/O paths showed about fifty
modules that put a frame's real address into a format-0 CCW or a 24-bit
control-block field, so every one of them would need an IDAW path first.

M4b.2 instead uses the storage above 16 MB the way VM/XA uses *expanded
storage*: as a paging device that no channel ever addresses. CP keeps
running in the low 16 MB exactly as today; a page-out copies a frame to a
4 KB slot above the line and a page-in copies it back, with MVCL in AMODE 31.

| | Where | What |
|---|---|---|
| Slot address | — | slot *n* is real storage at 16 MB + *n* × 4096 |
| Slot as a DASD address | SWPTABLE | `SWPCYL` = *n*/128, `SWPDPAGE` = *n*%128 + 1 (0 still means "never written"), `SWPCODE` = X'FF' (no OWNDLIST index is that high) |
| Allocation | DMKPGT `DMKPGTPX` | a new entry used only by DMKPTR's user page-out: takes a slot from `XSTFREE` (released slots, chained through the slots themselves) or the high-water mark `XSTHWM` below `XSTTOP`; else falls through to DMKPGTPG (DASD). DMKCPI, DMKSST and DMKCDS still call DMKPGTPG, because DMKRPA writes their pages with its own channel programs |
| Release | DMKPGT `SPOOLDEL` | `SWPCODE` X'FF' goes to `XSTREL`, which pushes the slot and keeps the `VMPDRUM` accounting |
| I/O | DMKPAG | a request whose SWPTABLE entry has `SWPCODE` X'FF' is done by MVCL at once and the CPEXBLOK is stacked, as a completed I/O would be |
| Queueing | DMKPTR | an X'FF' page-out is queued as a write without looking for an RDEVBLOK |
| Counting | DMKPGS, DMKATS, DMKCPP | X'FF' is counted as drum (`VMPDRUM`) instead of indexing the device table |
| Size | DMKCPIB | `DMKPGTXT` (`XSTTOP`) = detected real size |

What this gives: a guest whose working set exceeds the low frames pages at
memory speed instead of 3350 speed. What it does not give: more *frames* —
that remains M4b.3 (HPO-style), now optional.

## Rejected: user pages above the line, CP below — as VM/SP HPO did

VM/SP High Performance Option ran real storage above 16 MB the same way:
frames above the line hold **user virtual pages only**; CP's own storage, and
anything a channel program addresses directly, stays below.

1. **Size and table.** DMKCPI probes in AMODE 31 (BSM around `KEYLOOP`).
   The CORTABLE is built by DMKCPI at IPL, sized from the detected storage,
   in frames below 16 MB, and its address is stored in `ACORETBL` (the PSA
   field every module already loads it from); the few `V(DMKSYSCS)` users
   switch to `ACORETBL`. SYSCOR's static table and its 16392K limit go away.
2. **Two free lists.** DMKPTR keeps frames below 16 MB on the existing list
   and frames above on a second one. Requests for CP (free storage via
   DMKPTRFR, locked and V=R pages, CP's pageable nucleus, shared-segment
   frames) take only low frames; a user page-in (DMKPTRAN for a guest) takes
   a high frame first. A frame goes back to the list its address belongs to.
3. **I/O to a high frame through IDAWs.** ESA/390 IDAWs carry 31-bit
   addresses. DMKPAG sets the IDA flag and points the read/write CCW at a
   two-IDAW list in the IOBLOK when the frame is above 16 MB. DMKCCW already
   builds IDALs for data areas that cross pages; a one-page area in a high
   frame takes the same path. DMKDGD and the spool paths likewise.
4. **Diagnostics.** `DISPLAY`/`STORE` of real addresses above 16 MB in
   DMKCDB/DMKCDS (I-207), and `QUERY STORAGE`.

## Increments and their observables

| | Increment | Observable |
|---|---|---|
| **M4b.1** | Probe in AMODE 31; CORTABLE built at IPL from the detected size; frames above 16 MB flagged and kept off every free list | `MAINSIZE 64`: `Storage size = 65536 K`; the regression runs unchanged (nothing uses a high frame yet) |
| **M4b.2** | Paging store above 16 MB (above) | `MAINSIZE 64`, a 128 MB guest running M5G2 (50 MB touched): `CP IND USER` shows the pages on "drum" and the run is faster than at `MAINSIZE 16` |
| **M4b.3** | (optional) HPO-style frames: DMKCCW / DMKDGD / spool for high frames | the M5g regression (GCC380, file I/O, cREXX build) at `MAINSIZE 256` |
| **M4b.4** | 2 GB | `MAINSIZE 2048`, several 256 MB guests at once |

## M4b.2 results (7 October)

| Run | MAINSIZE | Slots | Result |
|---|---|---|---|
| r4b14 | 16 | none (`XSTTOP` = 16 MB) | M5G2 OK: every page-out takes DMKPGTPX's fall-through to DMKPGTPG |
| r4b13 | 64 | 12 288, all used (`XSTHWM` = `XSTTOP` = X'04000000') | M5G2 OK: the store fills during the 20 MB memcpy and the rest goes to DASD |
| r4b12 | 128 | 12 901 of 28 672 used | M5G2 OK, no DASD paging |

Two bugs on the way, both in the new code:

- **DMKPGTPX fall-through** (r4b7–r4b11). `LM R0,R15,BALRSAVE` restored the
  caller's R12 and *then* `L R15,=A(DMKPGTPG)` fetched the literal through
  it -- through DMKPTR's base. The branch went to X'D7E3D90A' (r4b7) or, at
  64 MB, CP sat in an idle wait with a page read never started (r4b10/r4b11:
  `DMKPTRRQ` non-empty, `DMKPAGQ` empty, `XTNDLOCK` 0). The fix loads the
  address first and stores it into the saved R15. It hid at 128 MB because
  the store never filled.
- **Process**: the first "fixed" nucleus was built without re-running
  `build.py`, so it carried the old `DMKPGT XA0053DK`. Check the generated
  deck, not only `build.py`, before a CP build.

`ESA390_MB=<mb>` (mkrun.archmode) runs one `build.sh` command at another
MAINSIZE; it was needed here because the broken nucleus could not page at
16 MB, so its replacement was built at 128.
