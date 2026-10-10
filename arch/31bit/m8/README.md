# M8: current cREXX on VM/370plus

**M8.1 (8 October 2026): current cREXX (1.0.0-beta.3, adesutherland/crexx
77ba820c3) cross-built and running on VM/370plus.** RXC8 compiles a REXX
program on CMS, RXAS8 assembles it, RXBVM8 runs it (run m8f):

    rxc8 -l a hello          HELLO CREXX A -> HELLO RXAS A
    rxas8 -l a hello         -> HELLO RXBIN A
    rxbvm8 -l a hello
    Hello from current cREXX on VM/370plus
    sum 1..10 = 55

Route: cREXX's own single-threaded CMS ELF port (`ports/single-threaded`,
`CREXX_CMS_ELF`, `CREXX_CMS_TEXT_IO`, `CREXX_CMS_DIRENT`), GCC 13 `-m31`,
newlib and the M5f CMS runtime (`../m5f/cmsrt.c`), which gained:
- `mainframe_set_text_conversion` (raw IBM-1047 records, LF between them):
  cREXX does its own code-page conversion at the file and console boundary;
- `crexx_cms_text_open`/`crexx_cms_text_encoding` (the CMS text hooks);
- `opendir`/`readdir`/`closedir` (from `LISTFILE * * m (EXEC`) for import
  discovery; `stat`/`fstat`.

Files: `build.sh vm|rxas|rxc` (TEXT decks; RXC is 2.8 MB, elf_to_cms built
with an 8 MB image limit), `mkdecks.py` (reader decks), `unhex.c` (RXBIN
modules travel as hex text: 80-byte card padding breaks the RXBIN loader).
RXC needs `LIBRARY RXBIN` and `RXCEXITS RXBIN` (built on the PC:
`make library compiler_exit_bin`) on the location disk. Source files are
`fn CREXX` (no extension given). Runs: `tests/runs/m8-install.json`,
`tests/runs/m8-current-crexx.json`, Hercules 4.x (z900 instructions).

Next (M8.2): build it natively on VM/370plus (GCC380 / GCCLIB31), as M5g did
for the 2022 tree.
