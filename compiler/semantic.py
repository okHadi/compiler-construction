from typing import List, Optional

from compiler.ast_nodes import (
    Program, FuncDef, Block, VarDecl, ArrayDecl, Assign, ArrayAssign,
    IfStmt, WhileStmt, ForStmt, ReturnStmt, ExprStmt, PrintStmt, ReadStmt,
    BinOp, UnaryOp, Literal, Identifier, ArrayAccess, FuncCall,
)
from compiler.symbol_table import ScopedSymbolTable, Symbol


NUMERIC = {"int", "float", "char"}


class SemanticError(Exception):
    pass


class SemanticAnalyzer:
    def __init__(self):
        self.table = ScopedSymbolTable()
        self.errors: List[str] = []
        self.current_func: Optional[FuncDef] = None

    def _err(self, line: int, msg: str):
        self.errors.append(f"line {line}: {msg}")

    def analyze(self, program: Program) -> List[str]:
        for decl in program.decls:
            if isinstance(decl, FuncDef):
                if not self.table.declare(Symbol(
                    name=decl.name, type=decl.return_type, kind="func",
                    param_types=[p.type for p in decl.params],
                    return_type=decl.return_type,
                )):
                    self._err(decl.line, f"function '{decl.name}' redeclared")
            elif isinstance(decl, VarDecl):
                if not self.table.declare(Symbol(decl.name, decl.type, "var")):
                    self._err(decl.line, f"global '{decl.name}' redeclared")
            elif isinstance(decl, ArrayDecl):
                if not self.table.declare(Symbol(decl.name, decl.type, "array", array_size=decl.size)):
                    self._err(decl.line, f"global array '{decl.name}' redeclared")

        for decl in program.decls:
            if isinstance(decl, FuncDef):
                self._check_function(decl)
            elif isinstance(decl, VarDecl) and decl.init is not None:
                init_t = self._check_expr(decl.init)
                if init_t and not self._assignable(decl.type, init_t):
                    self._err(decl.line, f"cannot initialize {decl.type} from {init_t}")

        return self.errors

    def _check_function(self, func: FuncDef):
        self.current_func = func
        self.table.enter_scope()
        for p in func.params:
            if not self.table.declare(Symbol(p.name, p.type, "var")):
                self._err(p.line, f"parameter '{p.name}' redeclared")
        for stmt in func.body.statements:
            self._check_stmt(stmt)
        self.table.exit_scope()
        self.current_func = None

    def _check_block(self, block: Block):
        self.table.enter_scope()
        for stmt in block.statements:
            self._check_stmt(stmt)
        self.table.exit_scope()

    def _check_stmt(self, node):
        if isinstance(node, VarDecl):
            if not self.table.declare(Symbol(node.name, node.type, "var")):
                self._err(node.line, f"'{node.name}' already declared in this scope")
            if node.init is not None:
                t = self._check_expr(node.init)
                if t and not self._assignable(node.type, t):
                    self._err(node.line, f"cannot initialize {node.type} from {t}")
        elif isinstance(node, ArrayDecl):
            if not self.table.declare(Symbol(node.name, node.type, "array", array_size=node.size)):
                self._err(node.line, f"'{node.name}' already declared in this scope")
        elif isinstance(node, Assign):
            sym = self.table.lookup(node.name)
            if sym is None:
                self._err(node.line, f"'{node.name}' not declared")
                self._check_expr(node.value)
            elif sym.kind != "var":
                self._err(node.line, f"'{node.name}' is not a variable")
            else:
                t = self._check_expr(node.value)
                if t and not self._assignable(sym.type, t):
                    self._err(node.line, f"cannot assign {t} to {sym.type}")
        elif isinstance(node, ArrayAssign):
            sym = self.table.lookup(node.name)
            if sym is None:
                self._err(node.line, f"'{node.name}' not declared")
            elif sym.kind != "array":
                self._err(node.line, f"'{node.name}' is not an array")
            idx_t = self._check_expr(node.index)
            if idx_t and idx_t != "int":
                self._err(node.line, f"array index must be int, got {idx_t}")
            val_t = self._check_expr(node.value)
            if sym is not None and sym.kind == "array" and val_t and not self._assignable(sym.type, val_t):
                self._err(node.line, f"cannot store {val_t} into array of {sym.type}")
        elif isinstance(node, IfStmt):
            self._check_expr(node.cond)
            self._check_block(node.then_block)
            if node.else_block is not None:
                self._check_block(node.else_block)
        elif isinstance(node, WhileStmt):
            self._check_expr(node.cond)
            self._check_block(node.body)
        elif isinstance(node, ForStmt):
            self.table.enter_scope()
            if node.init is not None:
                self._check_stmt_or_expr(node.init)
            if node.cond is not None:
                self._check_expr(node.cond)
            if node.update is not None:
                self._check_stmt_or_expr(node.update)
            for s in node.body.statements:
                self._check_stmt(s)
            self.table.exit_scope()
        elif isinstance(node, ReturnStmt):
            if self.current_func is None:
                self._err(node.line, "return outside function")
                return
            expected = self.current_func.return_type
            if node.value is None:
                if expected != "void":
                    self._err(node.line, f"function '{self.current_func.name}' must return {expected}")
            else:
                t = self._check_expr(node.value)
                if expected == "void":
                    self._err(node.line, f"void function '{self.current_func.name}' cannot return a value")
                elif t and not self._assignable(expected, t):
                    self._err(node.line, f"cannot return {t} from function returning {expected}")
        elif isinstance(node, ExprStmt):
            self._check_expr(node.expr)
        elif isinstance(node, PrintStmt):
            self._check_expr(node.expr)
        elif isinstance(node, ReadStmt):
            sym = self.table.lookup(node.name)
            if sym is None:
                self._err(node.line, f"'{node.name}' not declared")
            elif sym.kind != "var":
                self._err(node.line, f"'{node.name}' is not a variable")
        elif isinstance(node, Block):
            self._check_block(node)
        else:
            self._err(getattr(node, "line", 0), f"unsupported statement {type(node).__name__}")

    def _check_stmt_or_expr(self, node):
        if isinstance(node, (VarDecl, Assign, ArrayAssign, ExprStmt)):
            self._check_stmt(node)
        else:
            self._check_expr(node)

    def _check_expr(self, node) -> Optional[str]:
        if isinstance(node, Literal):
            return node.type
        if isinstance(node, Identifier):
            sym = self.table.lookup(node.name)
            if sym is None:
                self._err(node.line, f"'{node.name}' not declared")
                return None
            if sym.kind != "var":
                self._err(node.line, f"'{node.name}' is not a value")
                return None
            return sym.type
        if isinstance(node, ArrayAccess):
            sym = self.table.lookup(node.name)
            if sym is None:
                self._err(node.line, f"'{node.name}' not declared")
                return None
            if sym.kind != "array":
                self._err(node.line, f"'{node.name}' is not an array")
                return None
            idx_t = self._check_expr(node.index)
            if idx_t and idx_t != "int":
                self._err(node.line, f"array index must be int, got {idx_t}")
            return sym.type
        if isinstance(node, FuncCall):
            sym = self.table.lookup(node.name)
            if sym is None:
                self._err(node.line, f"'{node.name}' not declared")
                for a in node.args:
                    self._check_expr(a)
                return None
            if sym.kind != "func":
                self._err(node.line, f"'{node.name}' is not a function")
                return None
            if len(node.args) != len(sym.param_types or []):
                self._err(node.line, f"'{node.name}' expects {len(sym.param_types or [])} arg(s), got {len(node.args)}")
            for arg, expected in zip(node.args, sym.param_types or []):
                t = self._check_expr(arg)
                if t and not self._assignable(expected, t):
                    self._err(node.line, f"argument to '{node.name}' has type {t}, expected {expected}")
            return sym.return_type
        if isinstance(node, UnaryOp):
            t = self._check_expr(node.operand)
            if node.op == "!":
                return "int"
            return t
        if isinstance(node, BinOp):
            lt = self._check_expr(node.left)
            rt = self._check_expr(node.right)
            if node.op in ("<", ">", "<=", ">=", "==", "!=", "&&", "||"):
                return "int"
            if lt is None or rt is None:
                return None
            if lt == "float" or rt == "float":
                return "float"
            return "int"
        return None

    def _assignable(self, target: str, source: str) -> bool:
        if target == source:
            return True
        if target == "float" and source in ("int", "char"):
            return True
        if target == "int" and source == "char":
            return True
        return False
