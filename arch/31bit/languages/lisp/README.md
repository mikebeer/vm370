# Lisp for cREXX

A Common Lisp interpreter written in [cREXX](https://github.com/adesutherland/CREXX)
Level B. It reads Lisp source, evaluates it directly, and runs on the cREXX
virtual machine. The whole interpreter is one source file, `lisp.crexx`.

It implements a practical subset of Common Lisp: lexical scope, closures,
macros with backquote, `loop`, `format`, condition handling with
`handler-case`, hash tables, vectors, structures, and about 220 built-in
functions.

## Building

You need the cREXX tools `rxc`, `rxas` and `rxvm` (cREXX 1.0.0 beta 3 or later).

```
export CREXX_BIN=/path/to/crexx/bin     # the directory holding rxc, rxas, rxvm
make                                    # builds build/lisp.rxbin
make test                               # runs the test programs in tests/
```

## Running

```
./lisp program.lisp            # load and run a file
./lisp a.lisp b.lisp           # load several files in order
./lisp                         # read-eval-print loop on standard input
```

In the loop every form is evaluated and its value is printed after the
prompt `* `. An error prints `Error: ...` and the loop carries on. When a
file is loaded, the first error stops the load, prints `Error: ...` and the
exit code is 1.

```
$ cat hello.lisp
(defun greet (name) (format t "Hello, ~A!~%" name))
(greet "world")
(print (loop for i from 1 to 5 collect (* i i)))

$ ./lisp hello.lisp
Hello, world!

(1 4 9 16 25)
```

## What is supported

* **Data:** fixnums, floats, strings, characters, symbols, conses, vectors
  (including adjustable vectors with fill pointers), hash tables, structures
  (`defstruct`), property lists.
* **Special forms and macros:** `quote function if cond case ecase typecase
  and or when unless progn prog1 prog2 let let* setq setf incf decf push
  pushnew pop rotatef psetq defun defmacro defvar defparameter defconstant
  defstruct lambda flet labels block return-from return catch throw
  unwind-protect handler-case ignore-errors do do* dolist dotimes loop
  multiple-value-bind multiple-value-list nth-value destructuring-bind
  with-output-to-string assert the declare`.
* **Functions:** `&optional`, `&rest`, `&key`, `&aux`, closures, `apply`,
  `funcall`, `mapcar mapc mapcan maplist map reduce remove remove-if find
  position count some every sort` and many more.
* **Backquote:** `` ` ``, `,` and `,@`.
* **Extended `loop`:** `for ... in/on/across/from/to/below/downto/by/=/then`,
  `being the hash-keys`, `repeat`, `with`, `while`, `until`, `always`,
  `never`, `thereis`, `collect`, `append`, `nconc`, `sum`, `count`,
  `maximize`, `minimize` (with `into`), `when/if/unless ... else`, `do`,
  `initially`, `finally`, `return`.
* **`format`:** `~A ~S ~D ~B ~O ~X ~F ~$ ~C ~% ~& ~~ ~* ~^ ~{...~} ~[...~]
  ~(...~)` with column widths, pad characters, `:` and `@` modifiers.
* **Errors:** `error`, `warn`, `assert`, `handler-case` with `error`,
  `division-by-zero`, `type-error` and so on; `ignore-errors`.

## Differences from Common Lisp

* No bignums and no ratios. Integers are 62-bit. `(/ 7 2)` gives `3.5`,
  and `(/ 6 3)` gives `2`.
* One float type; floats print like single floats (`1.5`, `1.0e10`).
* No packages, no `tagbody`/`go`, no CLOS, no streams or file I/O other than
  standard input and output, no `declare` processing, no nested backquote.
* `values` returns its first value; `multiple-value-bind`,
  `multiple-value-list` and `nth-value` see all values when the value
  producer is `values`, `floor`, `ceiling`, `round`, `truncate` or `gethash`.
* There is no garbage collector. Every cons stays allocated until the
  program ends, so very long-running allocation-heavy programs run out of
  memory.
* Evaluation nests at most 24000 levels (about 12000 Lisp calls). Deeper
  recursion signals an error. Tail calls in `if`, `cond`, `progn`, `let`,
  `when`, `unless`, `case`, `and`, `or` and function calls do not use stack.

## Documentation

`docs/Lisp-User-Guide.docx` is the user manual.

## Layout

```
lisp.crexx       the interpreter
lisp             shell wrapper that runs a program
Makefile         build and test
examples/        example programs (primes, account, wordcount, deriv, hello)
tests/           test programs with expected output
docs/            user manual
```
