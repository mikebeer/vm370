# Driven runs — the regression set for the converted CP

Each file is a `drive.py` step list (see `tools/drive.py` for the format) and
is run with `tools/esa390.sh <name> <file>` against the current nucleus on
the scratch pack; `esa390.sh` sets `ARCHMODE ESA/390` and verifies it from
the log. `send` lines go to the Hercules console (operator, 0009; a leading
`/` is CP's own prefix), `term` lines to the second terminal (000A, where the
test user logs on). Only the operator issues `shutdown`.

| File | What it proves | Expected timeouts (not failures) |
|---|---|---|
| `amode31-32m.json` | the M2 run: IPL, `enable all`, LOGON with every LINK (`q v dasd`), `IPL 190` (15M: CMS's own `DMSINI260T`, it loads high), `IPL CMS`, EDIT + `DIRECT` recompile to 16M/64M, `DEF STOR 32M`, stores and displays above 16 MB, `IPL CMS` in the 32M machine, `QUERY DISK`, LOGOFF, SHUTDOWN | the `Online` wait (the message arrives before the step), the `Ready` after `IPL 190` at 15M, `d 1ffffff.10` (DMKCDB prints its range in 6 hex digits — cosmetic) |
| `ipl190-16m.json` | `DEF STOR 16M` then `IPL 190`: CMS from the system disk, `QUERY DISK`; `DEF STOR 32M` on an unrecompiled directory answers `EXCEEDS ALLOWED MAXIMUM` | the `Online` wait; `STORAGE =` after the 32M attempt |
| `gcclib-15m.json` | the 15M GCCLIB / autolog regression: `IPL CMS`, `SEGMENT LOAD GCCLIB` ("already defined"), the key map of F00000–FFFFFF, AUTOLOG CMSUSER, `IND`, FORCE | the `Online` wait |

Last run clean: 5 October 2026 14:45 UTC on SNAP-I241's nucleus (w109, w111,
w112) — CP in AMODE 31 (`34-AMODE31.md`).
