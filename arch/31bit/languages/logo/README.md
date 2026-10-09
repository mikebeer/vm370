# LOGO in CREXX

A LOGO (turtle graphics) interpreter written in CREXX Level B. The whole
interpreter is one file, `logo.crexx`: tokenizer, recursive-descent expression
parser, user procedures with dynamic scoping, and an SVG turtle.

## Run

```sh
crexx logo.crexx --args examples/tree.logo tree.svg
crexx logo.crexx                      # built-in demo, writes logo.svg
```

The first argument is the LOGO program, the second the SVG output file
(default `logo.svg`). `PRINT` and `SHOW` write to standard output. CREXX
program arguments go after `--args`. Tested with CREXX 1.0.0 beta 3 built
from source.

## Manual

`docs/LOGO-User-Guide.docx` is the full Introduction and User's Guide: installation,
the language, turtle graphics, examples, messages, and how the interpreter works.

## Language

| Area    | Words |
|---------|-------|
| Turtle  | `FD BK RT LT PU PD HOME CS CLEAN SETXY SETX SETY SETH SETHEADING SETPC SETPENSIZE SETBG LABEL HEADING XCOR YCOR PENDOWNP` |
| Control | `REPEAT IF IFELSE FOR WHILE RUN STOP OUTPUT` (`IF` takes an optional else list) |
| Procs   | `TO name :a :b ... END`, recursion, `REPCOUNT` |
| Data    | `MAKE LOCAL THING :var "word [list] 12.5` |
| Math    | `+ - * / = < > <= >= <>` `SUM DIFFERENCE PRODUCT QUOTIENT REMAINDER MODULO INT ROUND ABS SQRT POWER SIN COS PI RANDOM` |
| Lists   | `FIRST LAST BF BL COUNT ITEM FPUT LPUT WORD LIST SENTENCE EMPTYP MEMBERP NUMBERP LISTP WORDP` |
| Logic   | `NOT AND OR EQUALP LESSP GREATERP` |

Colours accept 0-15 or a CSS colour name. Comments start with `;`.

## Limits and notes

- Arguments of prefix words are full expressions: `SQRT 16 + 9` is `SQRT 25`.
- Write negative literals after a first argument in brackets or use `SETY -150`;
  `SETXY 0 -150` reads as `0 - 150`.
- `RUN` takes a list value; `IF`, `REPEAT`, `FOR`, `WHILE` take literal lists.
- Recursion depth is capped at 300 calls.
- Not implemented: `TYPE`, `READ`, property lists, `ARC`/`CIRCLE`, variadic
  `(WORD a b c)` forms, screen wrap modes.

## Examples

`examples/` holds `star`, `spiral`, `tree` (recursion) and `fact`
(functions and lists, no graphics).
