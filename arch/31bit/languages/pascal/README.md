# Pascal for cREXX

A Pascal compiler written in cREXX Level B. It translates Pascal programs into
cREXX assembly (`.rxas`), which `rxas` assembles and `rxvm` runs, together with
a small runtime library (`pasrt`).

    make                  # build build/pascal.rxbin and build/pasrt.rxbin
    ./pasc hello.pas      # compile and run
    ./pasc -c hello.pas   # compile only
    make test             # run the programs in tests/

`CREXX_BIN` names the directory with `rxc`, `rxas` and `rxvm` if they are not on `PATH`.

## Language

integer, real, boolean, char, string; subranges, enumerations, arrays (multi-dimensional),
records (nested), pointers with `new`/`dispose`; const/type/var; procedures and functions
(nested, recursive, `var` parameters, `forward`); `if while repeat for case with`;
`write/writeln/read/readln` with field widths; the usual standard functions.

Not yet: sets, files, variant records, `goto`, procedural parameters, typed constants.

## Manual

See [docs/Pascal-User-Guide.docx](docs/Pascal-User-Guide.docx) (23 pages: language,
standard routines, examples, how the compiler works, messages, restrictions).
