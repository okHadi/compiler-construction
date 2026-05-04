# C-Subset Compiler

A compiler for a defined subset of C, implemented in Python. Built for the
Spring 2026 Compiler Construction project. It runs the four standard phases
(lexical analysis, parsing, semantic analysis, three-address code generation)
and includes constant folding and dead code elimination.

## Requirements

- Python 3.10 or newer
- No third-party packages

## Run a program

```
python main.py tests/programs/recursion_factorial.c
```

By default this prints the optimized three-address code (TAC). To inspect a
specific phase, pass `--phase`:

```
python main.py tests/programs/arithmetic.c --phase tokens
python main.py tests/programs/recursion_factorial.c --phase ast
python main.py tests/programs/scoping.c --phase semantic
python main.py tests/programs/constant_folding.c --phase tac
```

To disable optimizations and see raw TAC:

```
python main.py tests/programs/constant_folding.c --phase tac --no-opt
```

If the program has lexical, syntax, or semantic errors, the compiler prints
them and exits with a non-zero status.

## Run the test suite

```
python tests/run_tests.py
```

This compiles every program under `tests/programs/`, diffs the TAC output
against the expected files in `tests/expected/`, and verifies that the
intentionally broken `errors_semantic.c` produces semantic errors. Exits with
a non-zero status if anything fails.

## Project layout

```
main.py              CLI entry point
compiler/
  lexer.py           tokenizer
  parser.py          recursive descent + Pratt parser
  ast_nodes.py       AST node definitions
  symbol_table.py    scoped symbol table
  semantic.py        type and scope checking
  tac.py             three-address code generator
  optimizer.py       constant folding and dead code elimination
tests/
  programs/          sample .c programs
  expected/          expected TAC output for each program
  run_tests.py       test harness
```

## Defined C subset

- Types: `int`, `float`, `char`, `void`
- Variables (global and local), assignment, initialization
- Fixed-size arrays with index read and write
- Operators: arithmetic `+ - * / %`, relational `< > <= >= == !=`,
  logical `&& || !`, unary `- !`
- Control flow: `if`/`else`, `while`, `for`
- Functions with parameters, return values, and recursion
- Built-ins: `print(expr)` and `read(name)` for I/O
- Comments: `//` and `/* */`

See `REPORT.md` for the full grammar and design notes.
