# Compiler Construction Project Report

## 1. Introduction and Objectives

This project is a working compiler for a defined subset of the C programming
language. It demonstrates the four core phases of compilation: lexical
analysis, parsing, semantic analysis, and intermediate representation (IR)
generation. The compiler also implements two basic optimizations on top of
the IR for the innovation marks: constant folding on the AST and dead code
elimination on the generated three-address code.

The objective is to understand and exercise each compiler phase end to end,
on a language small enough to keep the design clear but rich enough to
include functions, recursion, scoped variables, control flow, and arrays.

## 2. Defined Subset of C

### Types

`int`, `float`, `char`, `void`. Implicit widening is allowed (`int` to
`float`, `char` to `int`/`float`). Implicit narrowing (`float` to `int`) is
rejected by the semantic analyzer.

### Declarations

- Global and local scalar variables with optional initializer:
  `int x = 5;`
- Fixed-size arrays: `int a[10];`
- Function definitions with typed parameters and return type, including
  forward references and recursion.

### Statements

- Variable and array declarations
- Scalar assignment: `x = expr;`
- Array element assignment: `a[i] = expr;`
- `if (cond) { ... } else { ... }`
- `while (cond) { ... }`
- `for (init; cond; update) { ... }` with optional parts and a per-loop scope
- `return [expr];`
- Expression statement: `expr;`
- Block: `{ stmt* }`
- Built-in I/O: `print(expr);` and `read(name);`

### Expressions

- Integer, float, and character literals
- Identifier reference, array index access, function call
- Unary `-` and `!`
- Binary arithmetic `+ - * / %`, relational `< > <= >= == !=`,
  logical `&& ||`
- Parenthesized subexpressions

### Comments

`//` line comments and `/* ... */` block comments.

## 3. Grammar (EBNF)

```
program        ::= top_decl*
top_decl       ::= func_def | var_decl | array_decl
func_def       ::= type IDENT "(" param_list? ")" block
param_list     ::= param ("," param)*
param          ::= type IDENT

var_decl       ::= type IDENT ("=" expression)? ";"
array_decl     ::= type IDENT "[" INT_LIT "]" ";"
type           ::= "int" | "float" | "char" | "void"

block          ::= "{" statement* "}"
statement      ::= var_decl
                 | array_decl
                 | assign_stmt
                 | array_assign_stmt
                 | if_stmt
                 | while_stmt
                 | for_stmt
                 | return_stmt
                 | print_stmt
                 | read_stmt
                 | block
                 | expr_stmt

assign_stmt        ::= IDENT "=" expression ";"
array_assign_stmt  ::= IDENT "[" expression "]" "=" expression ";"
if_stmt        ::= "if" "(" expression ")" block_or_stmt ("else" block_or_stmt)?
while_stmt     ::= "while" "(" expression ")" block_or_stmt
for_stmt       ::= "for" "(" for_init? ";" expression? ";" for_update? ")" block_or_stmt
for_init       ::= var_decl_inner | assign_no_semi | expression
for_update     ::= assign_no_semi | expression
return_stmt    ::= "return" expression? ";"
print_stmt     ::= "print" "(" expression ")" ";"
read_stmt      ::= "read" "(" IDENT ")" ";"
expr_stmt      ::= expression ";"
block_or_stmt  ::= block | statement

expression     ::= or_expr
or_expr        ::= and_expr ("||" and_expr)*
and_expr       ::= eq_expr  ("&&" eq_expr)*
eq_expr        ::= rel_expr (("==" | "!=") rel_expr)*
rel_expr       ::= add_expr (("<" | ">" | "<=" | ">=") add_expr)*
add_expr       ::= mul_expr (("+" | "-") mul_expr)*
mul_expr       ::= unary    (("*" | "/" | "%") unary)*
unary          ::= ("-" | "!") unary | primary
primary        ::= INT_LIT | FLOAT_LIT | CHAR_LIT
                 | IDENT
                 | IDENT "(" arg_list? ")"
                 | IDENT "[" expression "]"
                 | "(" expression ")"
arg_list       ::= expression ("," expression)*
```

The parser implements precedence using a Pratt binding-power table rather
than one function per level, which keeps `parser.py` small and easy to
extend.

## 4. Design of Compiler Phases

### 4.1 Lexer (`compiler/lexer.py`)

A hand-written character-by-character scanner. Tracks `(line, col)` per
token for usable error messages. Skips whitespace and both comment styles.
Recognizes keywords, identifiers, integer/float/char literals, and the full
operator set including the multi-character operators `==`, `!=`, `<=`,
`>=`, `&&`, `||`. Errors raise `LexerError` with line and column.

### 4.2 Parser (`compiler/parser.py`)

Recursive descent for declarations, statements, and the overall program.
Expression parsing uses Pratt precedence climbing keyed off a binding-power
table. The parser produces an AST defined in `compiler/ast_nodes.py`
(Python dataclasses, one node per language construct). Errors raise
`ParseError` with the offending token.

### 4.3 Symbol Table (`compiler/symbol_table.py`)

A stack of dictionaries. `enter_scope` and `exit_scope` push and pop, and
`lookup` walks from innermost to outermost. Each `Symbol` carries `kind`
(`var`, `array`, `func`), the type, and for functions the parameter and
return types.

### 4.4 Semantic Analyzer (`compiler/semantic.py`)

Two-pass:

1. Walk top-level declarations and register every function signature plus
   every global variable and array. This lets functions call each other in
   any order, including recursion.
2. Type-check each function body. The analyzer enforces:
   - Variable, array, and function are declared before use
   - No redeclaration in the same scope
   - Argument count and types match the function signature
   - `return` expressions match the function's return type
   - Array indices are `int`
   - Assignment target types are compatible with the value type (with safe
     widening only)

Errors are accumulated and printed together at the end so the user sees
the full picture in one run.

### 4.5 IR Generator (`compiler/tac.py`)

Lowers the AST to three-address code. Each `TAC` instruction has an op,
optional `arg1`/`arg2`, and an optional `result`. Temporaries are named
`t1, t2, ...` and labels are `L1, L2, ...`. Examples of the lowering:

| Construct       | TAC pattern                                       |
| --------------- | -------------------------------------------------- |
| `a = b + c`     | `t1 = b + c; a = t1`                               |
| `if (c) S1 else S2` | `if_false c goto Lelse; S1; goto Lend; Lelse: S2; Lend:` |
| `while (c) S`   | `Ltop: if_false c goto Lend; S; goto Ltop; Lend:`  |
| `f(x, y)`       | `param x; param y; t = call f, 2`                  |
| `a[i] = v`      | `a[i] = v` (with `i` and `v` already in temps)     |

Function bodies are bracketed by `func_begin name` / `func_end name`.
Parameters are listed with `param name` immediately after `func_begin`.

### 4.6 Optimizer (`compiler/optimizer.py`)

Two passes, both toggleable with `--no-opt`:

- **Constant folding** runs over the AST. Any `BinOp` or `UnaryOp` whose
  operand(s) are literal numeric values is replaced with the evaluated
  literal. Relational and logical results are coerced to `int`.
- **Dead code elimination** runs over the generated TAC. Any instruction
  after a `return` or `goto` and before the next reachable label is
  dropped. Labels never targeted by any branch are removed.

## 5. Sample Inputs and Outputs

### 5.1 Recursive factorial

Source (`tests/programs/recursion_factorial.c`):

```c
int fact(int n) {
    if (n <= 1) {
        return 1;
    }
    return n * fact(n - 1);
}

int main() {
    print(fact(6));
    return 0;
}
```

TAC:

```
func_begin fact
param n
t1 = n <= 1
if_false t1 goto L1
return 1
L1:
t2 = n - 1
param t2
t3 = call fact, 1
t4 = n * t3
return t4
func_end fact
func_begin main
param 6
t5 = call fact, 1
print t5
return 0
func_end main
```

### 5.2 Constant folding

Source (`tests/programs/constant_folding.c`):

```c
int main() {
    int a = 2 + 3 * 4;
    int b = (10 - 4) / 2;
    int c = a + b;
    if (1 < 2) {
        print(c);
    }
    return 0;
}
```

With `--no-opt`, every subexpression produces temporaries. With
optimizations on, `a` is initialized to `14` and `b` to `3` directly, with
no temporaries for the constant arithmetic.

### 5.3 Bubble sort with arrays

`tests/programs/arrays_bubblesort.c` exercises array declaration, indexed
read/write, nested `while` loops, and a swap. The generated TAC contains
`array_load` and `array_store` instructions.

### 5.4 Semantic errors

`tests/programs/errors_semantic.c` is intentionally broken. The compiler
reports:

```
Semantic error: line 6: 'x' not declared
Semantic error: line 8: 'y' already declared in this scope
Semantic error: line 9: 'add' expects 2 arg(s), got 1
Semantic error: line 10: 'undeclared' not declared
```

## 6. Test Programs

| Program                  | Features exercised                                    |
| ------------------------ | ----------------------------------------------------- |
| `arithmetic.c`           | Arithmetic operators, precedence, mixed int/float     |
| `if_else.c`              | `if`/`else`, relational operators                     |
| `while_loop.c`           | `while` loop, accumulation                            |
| `for_loop.c`             | `for` loop with declaration in init                   |
| `functions.c`            | Function definition and call                          |
| `recursion_factorial.c`  | Recursion, `if`, return value                         |
| `scoping.c`              | Global variable, block scope, shadowing               |
| `arrays_bubblesort.c`    | Arrays, nested loops, swap                            |
| `constant_folding.c`     | Constant folding optimization                         |
| `dead_code.c`            | Dead code elimination after `return`                  |
| `errors_semantic.c`      | Negative test for semantic errors                     |

The harness in `tests/run_tests.py` compiles each program, diffs TAC
output against the expected file in `tests/expected/`, and asserts that
`errors_semantic.c` produces semantic errors. All eleven tests pass.

## 7. Limitations and Future Work

The subset is intentionally narrow. The following are not supported:

- Pointers, references, and the `&` and `*` operators
- Strings beyond single-character literals
- Structs, unions, enums, typedef
- `switch`/`case`, `break`, `continue`, `goto`
- The C preprocessor and standard library headers
- Floating-point arithmetic for relational corner cases
  (NaN handling, etc.)

Possible extensions:

- Generate LLVM IR or x86-64 assembly to produce a runnable executable
- Add `break`/`continue` for loop control
- Add a register-allocator-style pass and more optimizations
  (common subexpression elimination, copy propagation)
- Pretty-print the symbol table per scope as a debugging aid

## 8. How to Build and Run

See `README.md` for full instructions. In short:

```
python main.py path/to/program.c            # print TAC
python main.py path/to/program.c --phase ast # print AST
python tests/run_tests.py                    # run the test suite
```
