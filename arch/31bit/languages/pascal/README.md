# Pascal for cREXX

A Pascal compiler written in cREXX Level B. It translates Pascal programs into
cREXX assembly (`.rxas`), which `rxas` assembles and `rxvm` runs, together with
a small runtime library (`pasrt`).

    make                  # build build/pascal.rxbin and build/pasrt.rxbin
    ./pasc hello.pas      # compile and run
    ./pasc -c hello.pas   # compile only
    make test             # run the programs in tests/

`CREXX_BIN` names the directory with `rxc`, `rxas` and `rxvm` if they are not on `PATH`.

## Turbo-Pascal-style environment

    ./tp [file.pas]       # full-screen editor, menus, compile and run in one key

`tp` opens a blue-screen editor in the manner of Turbo Pascal 7: menu bar (File, Edit, Search,
Run, Compile, Options, Help), Pascal syntax colouring, auto indent, undo, WordStar block commands
(`Ctrl-K B/K/C/V/Y`, `Ctrl-K R/W`), find / replace / go to line, an error Messages window that
puts the cursor on the offending line, and a help window (`F1`).

| Key | Action | Key | Action |
|---|---|---|---|
| F2 / F3 | save / open | F9 | compile (make) |
| Ctrl-R | compile and run | F10 | menu (or Alt-F, Alt-E, ...) |
| Ctrl-Z | undo | Alt-X | exit |

The editor is a Python 3 curses program (`ide/tpide.py`); it drives the cREXX Pascal compiler,
`rxas` and `rxvm`. `CREXX_BIN` names their directory. A program runs on the normal terminal screen
and returns to the editor when you press Enter. `make ide-test` runs the editor-core tests.

## Language

integer, real, boolean, char, string; subranges, enumerations, arrays (multi-dimensional),
records (nested), pointers with `new`/`dispose`; const/type/var; procedures and functions
(nested, recursive, `var` parameters, `forward`); `if while repeat for case with`;
`write/writeln/read/readln` with field widths; the usual standard functions.

Not yet: sets, files, variant records, `goto`, procedural parameters, typed constants.

## Manual

See [docs/Pascal-User-Guide.docx](docs/Pascal-User-Guide.docx) (23 pages: language,
standard routines, examples, how the compiler works, messages, restrictions).
