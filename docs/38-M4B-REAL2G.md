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

## The design: user pages above the line, CP below — as VM/SP HPO did

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
| **M4b.2** | High-frame free list; user page-ins take high frames; DMKPAG IDAWs | `MAINSIZE 64`, a 128 MB guest running M5G2 (50 MB touched): `CP IND` paging falls; frames above 16 MB in use (`D` of the CORTABLE) |
| **M4b.3** | DMKCCW / DMKDGD / spool for high frames | the M5g regression (GCC380, file I/O, cREXX build) at `MAINSIZE 256` |
| **M4b.4** | 2 GB | `MAINSIZE 2048`, several 256 MB guests at once |
