#!/usr/bin/env python3
import argparse
import sys


def main():
    ap = argparse.ArgumentParser(description="Compiler for a subset of C")
    ap.add_argument("source", help="path to a .c source file")
    ap.add_argument(
        "--phase",
        choices=["tokens", "ast", "semantic", "tac"],
        default="tac",
        help="stop after this phase and print its output",
    )
    ap.add_argument(
        "--no-opt",
        action="store_true",
        help="disable constant folding and dead code elimination",
    )
    args = ap.parse_args()

    with open(args.source, "r") as f:
        source = f.read()

    from compiler.lexer import Lexer, LexerError
    from compiler.parser import Parser, ParseError
    from compiler.semantic import SemanticAnalyzer, SemanticError
    from compiler.tac import TACGenerator
    from compiler.optimizer import fold_constants, eliminate_dead_code

    try:
        tokens = Lexer(source).tokenize()
    except LexerError as e:
        print(f"Lexical error: {e}", file=sys.stderr)
        sys.exit(1)

    if args.phase == "tokens":
        for t in tokens:
            print(t)
        return

    try:
        ast = Parser(tokens).parse()
    except ParseError as e:
        print(f"Syntax error: {e}", file=sys.stderr)
        sys.exit(1)

    if not args.no_opt:
        ast = fold_constants(ast)

    if args.phase == "ast":
        from compiler.ast_nodes import dump
        print(dump(ast))
        return

    errors = SemanticAnalyzer().analyze(ast)
    if errors:
        for err in errors:
            print(f"Semantic error: {err}", file=sys.stderr)
        sys.exit(1)

    if args.phase == "semantic":
        print("Semantic analysis OK")
        return

    instructions = TACGenerator().generate(ast)
    if not args.no_opt:
        instructions = eliminate_dead_code(instructions)

    for ins in instructions:
        print(ins)


if __name__ == "__main__":
    main()
