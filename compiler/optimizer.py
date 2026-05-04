from typing import List

from compiler.ast_nodes import (
    Program, FuncDef, Block, VarDecl, ArrayDecl, Assign, ArrayAssign,
    IfStmt, WhileStmt, ForStmt, ReturnStmt, ExprStmt, PrintStmt,
    BinOp, UnaryOp, Literal,
)
from compiler.tac import TAC


def fold_constants(program: Program) -> Program:
    program.decls = [_fold_decl(d) for d in program.decls]
    return program


def _fold_decl(d):
    if isinstance(d, FuncDef):
        d.body = _fold_block(d.body)
    elif isinstance(d, VarDecl) and d.init is not None:
        d.init = _fold_expr(d.init)
    return d


def _fold_block(b: Block) -> Block:
    b.statements = [_fold_stmt(s) for s in b.statements]
    return b


def _fold_stmt(s):
    if isinstance(s, VarDecl):
        if s.init is not None:
            s.init = _fold_expr(s.init)
    elif isinstance(s, Assign):
        s.value = _fold_expr(s.value)
    elif isinstance(s, ArrayAssign):
        s.index = _fold_expr(s.index)
        s.value = _fold_expr(s.value)
    elif isinstance(s, IfStmt):
        s.cond = _fold_expr(s.cond)
        s.then_block = _fold_block(s.then_block)
        if s.else_block is not None:
            s.else_block = _fold_block(s.else_block)
    elif isinstance(s, WhileStmt):
        s.cond = _fold_expr(s.cond)
        s.body = _fold_block(s.body)
    elif isinstance(s, ForStmt):
        if s.init is not None:
            s.init = _fold_stmt(s.init) if isinstance(s.init, (VarDecl, Assign, ArrayAssign)) else _fold_expr(s.init)
        if s.cond is not None:
            s.cond = _fold_expr(s.cond)
        if s.update is not None:
            s.update = _fold_stmt(s.update) if isinstance(s.update, (VarDecl, Assign, ArrayAssign)) else _fold_expr(s.update)
        s.body = _fold_block(s.body)
    elif isinstance(s, ReturnStmt):
        if s.value is not None:
            s.value = _fold_expr(s.value)
    elif isinstance(s, ExprStmt):
        s.expr = _fold_expr(s.expr)
    elif isinstance(s, PrintStmt):
        s.expr = _fold_expr(s.expr)
    elif isinstance(s, Block):
        return _fold_block(s)
    return s


def _fold_expr(e):
    if isinstance(e, BinOp):
        e.left = _fold_expr(e.left)
        e.right = _fold_expr(e.right)
        if isinstance(e.left, Literal) and isinstance(e.right, Literal):
            if e.left.type in ("int", "float") and e.right.type in ("int", "float"):
                v = _eval_binop(e.op, e.left.value, e.right.value)
                if v is not None:
                    out_type = "float" if (e.left.type == "float" or e.right.type == "float") else "int"
                    if e.op in ("<", ">", "<=", ">=", "==", "!=", "&&", "||"):
                        out_type = "int"
                        v = int(v)
                    return Literal(out_type, v, e.line)
        return e
    if isinstance(e, UnaryOp):
        e.operand = _fold_expr(e.operand)
        if isinstance(e.operand, Literal) and e.operand.type in ("int", "float"):
            if e.op == "-":
                return Literal(e.operand.type, -e.operand.value, e.line)
            if e.op == "!":
                return Literal("int", int(not e.operand.value), e.line)
        return e
    return e


def _eval_binop(op, a, b):
    try:
        if op == "+": return a + b
        if op == "-": return a - b
        if op == "*": return a * b
        if op == "/":
            if isinstance(a, int) and isinstance(b, int):
                if b == 0: return None
                return a // b if (a >= 0) == (b >= 0) else -(-a // b) if a < 0 else a // b
            if b == 0: return None
            return a / b
        if op == "%":
            if b == 0: return None
            return a % b
        if op == "<": return a < b
        if op == ">": return a > b
        if op == "<=": return a <= b
        if op == ">=": return a >= b
        if op == "==": return a == b
        if op == "!=": return a != b
        if op == "&&": return bool(a) and bool(b)
        if op == "||": return bool(a) or bool(b)
    except Exception:
        return None
    return None


def eliminate_dead_code(code: List[TAC]) -> List[TAC]:
    used_labels = set()
    for ins in code:
        if ins.op in ("goto", "if_goto", "if_false_goto") and ins.result:
            used_labels.add(ins.result)

    reachable: List[TAC] = []
    skip = False
    for ins in code:
        if ins.op in ("label", "func_begin", "func_end"):
            skip = False
            reachable.append(ins)
            continue
        if skip:
            continue
        reachable.append(ins)
        if ins.op in ("goto", "return"):
            skip = True

    return [ins for ins in reachable if not (ins.op == "label" and ins.result not in used_labels)]
