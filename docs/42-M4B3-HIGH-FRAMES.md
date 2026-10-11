# M4b.3 — guest pages in real frames above 16 MB (started 11 October 2026)

M4b.2/M4b.4 use real storage above 16 MB as a paging store (MVCL slots, doc 38).
CP still has only the 16 MB of frames below the line, and that is what makes two
Debians at once unusable (I-254): their working sets do not fit, and the
scheduler keeps one of them in the eligible list. M4b.3 lets **guest pages**
live in frames above 16 MB, as VM/SP HPO did. CP's own storage, locked and V=R
pages, SYSTEM-space pages (spool buffers) and shared-segment pages stay below.

## Inventory (11 October, read from all 201 modules with our decks applied)

The merged sources the survey read are produced by `tools/applied.py
assembled()`. About 85 sites in 25 modules; the classes:

| Class | Where | What to do |
|---|---|---|
| CP drops to AMODE 24 after an inline TRANS / DMKPTRAN's LRA | TRANS macro (34 sites), DMKPTR PTRLRA | **done** (step 1): CP stays in AMODE 31 |
| Channel programs with a guest frame in a 24-bit CCW address | DMKCCW CCWNXT9 (one-page area), DMKDGD NOTCHG1, DMKPAG SETRWCCW (paging), HDKD7C | a high frame always goes through an IDAL (IDAWs are 31-bit); the IDA paths for page-crossing areas exist in DMKCCW and DMKDGD |
| IDAW consumers that assume 24 bits | DMKUNT IDASET, DMKVCA (`CLI 0(R4),X'00'`, `TM 0(R1),X'FF'`), DMKDIB (`N =X'00FFFFF0'`), DMKISM, HDKD7C (`X2048BND`) | 31-bit masks on IDAW values |
| `XPAGNUM` (X'00FFF000') / `X2048BND` (X'00FFF800') on real frame addresses | DMKPTR (LRA result, PTRUL, PTRLK), DMKPSA key checks, DMKCCW, DMKUNT, DMKDGD, DMKCDS, DMKATS, DMKVMA, HDKD7C/8C | per site: 31-bit where the value is a frame address (an IDAW or an LRA result); unchanged where it is a 24-bit CCW word (a non-IDA CCW only ever points to a low frame) |
| Range checks against `DMKSYSRM` (16 MB since M4b.4) | DMKPTRUL (abend 2 above it), DMKUNT, DMKVCA, DMKDIB | check against the top of frames |
| Allocator | DMKPTR PAGFREE/GETFREE, DMKPTRFT/CHAINPAG, FREEQ hand-off, DMKPTRFR/FE, SELECT's scan blocks; DMKCPI CORLOOP | a second free list for high frames, taken only by a guest page-in (SETWAIT1) for a non-SYSTEM, non-V=R, non-shared page; CORTABLE entries for the high frames |

Uncertain and to be read when the work gets there: DMKTRK's set-file-mask
argument, DMKMNI's page, an IOBLOK copied for paging error recovery (DMKPAG
WTPGERR, DMKIOS) keeping its IDAL.

## Plan

| Step | Content | Observable |
|---|---|---|
| 1 | AMODE 31 after TRANS and DMKPTRAN's LRA | **done** f6f85d6: gcclib-15m, m5g-native, IPL LINUX to the login prompt |
| 2 | IDAW consumers and real-address masks 31-bit clean (no high frame in use yet) | the regression unchanged |
| 3 | DMKPAG: paging I/O through a two-IDAW list when the frame is high | the regression unchanged |
| 4 | DMKCCW / DMKDGD: a one-page data area in a high frame through an IDAL | the regression unchanged |
| 5 | CORTABLE for frames up to a frames top; the second free list; a switch (off by default) | switch on: the regression at MAINSIZE 256 with guest pages above 16 MB |
| 6 | Two Debians at once (I-254) | both reach the login prompt and answer over the network |

How the storage above 16 MB is shared between frames and the M4b.2 paging store
is decided at step 5 (simplest: frames up to a configured top, the store above it).

## Way back

If a nucleus does not IPL, `tools/nucpatch.py` and a standalone load of the
punched deck under `ARCHMODE S/370` restore a working CP without a pack
restore (doc 37, 11 October).
