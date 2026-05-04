from dataclasses import dataclass
from typing import List, Optional

from compiler.ast_nodes import (
    Program, FuncDef, Block, VarDecl, ArrayDecl, Assign, ArrayAssign,
    IfStmt, WhileStmt, ForStmt, ReturnStmt, ExprStmt, PrintStmt, ReadStmt,
    BinOp, UnaryOp, Literal, Identifier, ArrayAccess, FuncCall,
)


@dataclass
class TAC:
    op: str
    arg1: Optional[str] = None
    arg2: Optional[str] = None
    result: Optional[str] = None

    def __str__(self):
        op = self.op
        a, b, r = self.arg1, self.arg2, self.result
        if op == "label":
            return f"{r}:"
        if op == "func_begin":
            return f"func_begin {r}"
        if op == "func_end":
            return f"func_end {r}"
        if op == "param":
            return f"param {a}"
        if op == "call":
            return f"{r} = call {a}, {b}"
        if op == "call_void":
            return f"call {a}, {b}"
        if op == "return":
            return f"return {a}" if a is not None else "return"
        if op == "goto":
            return f"goto {r}"
        if op == "if_goto":
            return f"if {a} goto {r}"
        if op == "if_false_goto":
            return f"if_false {a} goto {r}"
        if op == "assign":
            return f"{r} = {a}"
        if op == "unary":
            return f"{r} = {a}{b}"
        if op == "array_load":
            return f"{r} = {a}[{b}]"
        if op == "array_store":
            return f"{r}[{a}] = {b}"
        if op == "print":
            return f"print {a}"
        if op == "read":
            return f"read {r}"
        return f"{r} = {a} {op} {b}"


class TACGenerator:
    def __init__(self):
        self.code: List[TAC] = []
        self.temp_counter = 0
        self.label_counter = 0

    def _new_temp(self) -> str:
        self.temp_counter += 1
        return f"t{self.temp_counter}"

    def _new_label(self) -> str:
        self.label_counter += 1
        return f"L{self.label_counter}"

    def _emit(self, op, arg1=None, arg2=None, result=None):
        self.code.append(TAC(op, arg1, arg2, result))

    def generate(self, program: Program) -> List[TAC]:
        for decl in program.decls:
            if isinstance(decl, VarDecl):
                if decl.init is not None:
                    val = self._gen_expr(decl.init)
                    self._emit("assign", val, result=decl.name)
            elif isinstance(decl, ArrayDecl):
                pass
        for decl in program.decls:
            if isinstance(decl, FuncDef):
                self._gen_function(decl)
        return self.code

    def _gen_function(self, func: FuncDef):
        self._emit("func_begin", result=func.name)
        for p in func.params:
            self._emit("param", arg1=p.name)
        for stmt in func.body.statements:
            self._gen_stmt(stmt)
        self._emit("func_end", result=func.name)

    def _gen_stmt(self, node):
        if isinstance(node, VarDecl):
            if node.init is not None:
                val = self._gen_expr(node.init)
                self._emit("assign", val, result=node.name)
        elif isinstance(node, ArrayDecl):
            pass
        elif isinstance(node, Assign):
            val = self._gen_expr(node.value)
            self._emit("assign", val, result=node.name)
        elif isinstance(node, ArrayAssign):
            idx = self._gen_expr(node.index)
            val = self._gen_expr(node.value)
            self._emit("array_store", arg1=idx, arg2=val, result=node.name)
        elif isinstance(node, IfStmt):
            cond = self._gen_expr(node.cond)
            else_label = self._new_label()
            end_label = self._new_label() if node.else_block is not None else else_label
            self._emit("if_false_goto", arg1=cond, result=else_label)
            for s in node.then_block.statements:
                self._gen_stmt(s)
            if node.else_block is not None:
                self._emit("goto", result=end_label)
                self._emit("label", result=else_label)
                for s in node.else_block.statements:
                    self._gen_stmt(s)
                self._emit("label", result=end_label)
            else:
                self._emit("label", result=else_label)
        elif isinstance(node, WhileStmt):
            top = self._new_label()
            end = self._new_label()
            self._emit("label", result=top)
            cond = self._gen_expr(node.cond)
            self._emit("if_false_goto", arg1=cond, result=end)
            for s in node.body.statements:
                self._gen_stmt(s)
            self._emit("goto", result=top)
            self._emit("label", result=end)
        elif isinstance(node, ForStmt):
            if node.init is not None:
                self._gen_stmt_or_expr(node.init)
            top = self._new_label()
            end = self._new_label()
            self._emit("label", result=top)
            if node.cond is not None:
                cond = self._gen_expr(node.cond)
                self._emit("if_false_goto", arg1=cond, result=end)
            for s in node.body.statements:
                self._gen_stmt(s)
            if node.update is not None:
                self._gen_stmt_or_expr(node.update)
            self._emit("goto", result=top)
            self._emit("label", result=end)
        elif isinstance(node, ReturnStmt):
            if node.value is None:
                self._emit("return")
            else:
                v = self._gen_expr(node.value)
                self._emit("return", arg1=v)
        elif isinstance(node, ExprStmt):
            self._gen_expr(node.expr)
        elif isinstance(node, PrintStmt):
            v = self._gen_expr(node.expr)
            self._emit("print", arg1=v)
        elif isinstance(node, ReadStmt):
            self._emit("read", result=node.name)
        elif isinstance(node, Block):
            for s in node.statements:
                self._gen_stmt(s)

    def _gen_stmt_or_expr(self, node):
        if isinstance(node, (VarDecl, Assign, ArrayAssign, ExprStmt, Block)):
            self._gen_stmt(node)
        else:
            self._gen_expr(node)

    def _gen_expr(self, node) -> str:
        if isinstance(node, Literal):
            if node.type == "char":
                return repr(node.value)
            return str(node.value)
        if isinstance(node, Identifier):
            return node.name
        if isinstance(node, ArrayAccess):
            idx = self._gen_expr(node.index)
            t = self._new_temp()
            self._emit("array_load", arg1=node.name, arg2=idx, result=t)
            return t
        if isinstance(node, UnaryOp):
            v = self._gen_expr(node.operand)
            t = self._new_temp()
            self._emit("unary", arg1=node.op, arg2=v, result=t)
            return t
        if isinstance(node, BinOp):
            l = self._gen_expr(node.left)
            r = self._gen_expr(node.right)
            t = self._new_temp()
            self._emit(node.op, arg1=l, arg2=r, result=t)
            return t
        if isinstance(node, FuncCall):
            arg_vals = [self._gen_expr(a) for a in node.args]
            for v in arg_vals:
                self._emit("param", arg1=v)
            t = self._new_temp()
            self._emit("call", arg1=node.name, arg2=str(len(arg_vals)), result=t)
            return t
        return "?"
