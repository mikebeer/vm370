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
| `guest31-tape.json` | M2 step 3: `devinit 480 io/g31.aws` (built by `../guest31/mkipl31.py`), ATTACH as 181, directory recompiled to 64M, `DEF STOR 32M`, `IPL 181`: the guest runs in AMODE 31, stores `AMODE 31` at 1FF0000 and `HI31` at 1000000, takes an SVC with a 31-bit PSW (old PSW `00080000 8000041E` at 1FF0010) and waits `000A0000 00000031`; displayed from CP | the `Online` wait; `ATTACHED` arrives on the user's terminal, not the operator's |
| `gcclib-15m.json` | the 15M GCCLIB / autolog regression: `IPL CMS`, `SEGMENT LOAD GCCLIB` ("already defined"), the key map of F00000–FFFFFF, AUTOLOG CMSUSER, `IND`, FORCE | the `Online` wait |
| `m5g-native.json` | M5g: GCCLIB31 deck (`gcclib31/gcclib31.txt`) read onto CMSUSER 195, `GCLB31 EXEC` builds GCCLIB31 TXTLIB on VM/370+; M5G2 compiled by GCC380 and run AMODE 31 (30 MB at X'01000340', 20 MB memcpy, HIGHSTOR all returned, `exit(3)` -> `Ready(00003)`); `CRXMK31 EXEC` builds cREXX 2022 natively (RXCN/RXASN/RXBVMN/RXDASN), BASIC through the chain prints `0.1`. 256 MB machine. Last clean: w266, 7 October 08:14; r4b15, 7 October 10:50, under the M4b.2 paging store (309 s) | the `Online` wait; `cp link maint 290` (already linked) |

Last run clean: 6 October 2026 23:55 UTC on the M4c nucleus (XA0052DK,
interval timer emulated, I-250) — rguest31-tape, ramode31-32m, ripl190-16m,
rgcclib-15m. Extra timeouts that are environment drift, not failures: the
live directory already says `16M 64M`/`16M 256M` (the `change` steps find
nothing to change), and `q names` lists users before `USERS =` arrives.
Previous: 5 October 2026 14:45 UTC on SNAP-I241's nucleus (w109, w111,
w112) — CP in AMODE 31 (`34-AMODE31.md`).
