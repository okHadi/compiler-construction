from typing import List, Optional

from compiler.lexer import Token
from compiler.ast_nodes import (
    Program, FuncDef, Param, Block, VarDecl, ArrayDecl, Assign, ArrayAssign,
    IfStmt, WhileStmt, ForStmt, ReturnStmt, ExprStmt, PrintStmt, ReadStmt,
    BinOp, UnaryOp, Literal, Identifier, ArrayAccess, FuncCall,
)


class ParseError(Exception):
    def __init__(self, message: str, token: Token):
        super().__init__(f"line {token.line}, col {token.col}: {message} (at {token.kind} {token.value!r})")
        self.token = token


TYPE_KEYWORDS = {"INT", "FLOAT", "CHAR", "VOID"}

INFIX_BP = {
    "||": (1, 2),
    "&&": (3, 4),
    "==": (5, 6), "!=": (5, 6),
    "LT": (7, 8), "GT": (7, 8), "<=": (7, 8), ">=": (7, 8),
    "PLUS": (9, 10), "MINUS": (9, 10),
    "STAR": (11, 12), "SLASH": (11, 12), "PERCENT": (11, 12),
}

OP_DISPLAY = {
    "PLUS": "+", "MINUS": "-", "STAR": "*", "SLASH": "/", "PERCENT": "%",
    "LT": "<", "GT": ">", "<=": "<=", ">=": ">=",
    "==": "==", "!=": "!=", "&&": "&&", "||": "||", "BANG": "!",
}


class Parser:
    def __init__(self, tokens: List[Token]):
        self.tokens = tokens
        self.pos = 0

    def _peek(self, offset: int = 0) -> Token:
        return self.tokens[self.pos + offset]

    def _advance(self) -> Token:
        t = self.tokens[self.pos]
        self.pos += 1
        return t

    def _check(self, kind: str) -> bool:
        return self._peek().kind == kind

    def _match(self, *kinds: str) -> Optional[Token]:
        if self._peek().kind in kinds:
            return self._advance()
        return None

    def _expect(self, kind: str, what: str = "") -> Token:
        if self._peek().kind != kind:
            raise ParseError(f"expected {what or kind}", self._peek())
        return self._advance()

    def parse(self) -> Program:
        decls = []
        while not self._check("EOF"):
            decls.append(self._parse_top_level())
        return Program(decls)

    def _parse_top_level(self):
        type_tok = self._peek()
        if type_tok.kind not in TYPE_KEYWORDS:
            raise ParseError("expected type at top level", type_tok)
        self._advance()
        name_tok = self._expect("IDENT", "identifier")
        if self._check("LPAREN"):
            return self._parse_function_def(type_tok.value, name_tok.value, type_tok.line)
        return self._parse_var_or_array_tail(type_tok.value, name_tok.value, type_tok.line, top_level=True)

    def _parse_function_def(self, return_type: str, name: str, line: int) -> FuncDef:
        self._expect("LPAREN")
        params: List[Param] = []
        if not self._check("RPAREN"):
            params.append(self._parse_param())
            while self._match("COMMA"):
                params.append(self._parse_param())
        self._expect("RPAREN")
        body = self._parse_block()
        return FuncDef(return_type, name, params, body, line)

    def _parse_param(self) -> Param:
        type_tok = self._peek()
        if type_tok.kind not in TYPE_KEYWORDS:
            raise ParseError("expected parameter type", type_tok)
        self._advance()
        name_tok = self._expect("IDENT", "parameter name")
        return Param(type_tok.value, name_tok.value, type_tok.line)

    def _parse_block(self) -> Block:
        self._expect("LBRACE")
        stmts = []
        while not self._check("RBRACE") and not self._check("EOF"):
            stmts.append(self._parse_statement())
        self._expect("RBRACE")
        return Block(stmts)

    def _parse_statement(self):
        tok = self._peek()
        if tok.kind in TYPE_KEYWORDS:
            self._advance()
            name_tok = self._expect("IDENT", "identifier")
            return self._parse_var_or_array_tail(tok.value, name_tok.value, tok.line, top_level=False)
        if tok.kind == "IF":
            return self._parse_if()
        if tok.kind == "WHILE":
            return self._parse_while()
        if tok.kind == "FOR":
            return self._parse_for()
        if tok.kind == "RETURN":
            return self._parse_return()
        if tok.kind == "PRINT":
            return self._parse_print()
        if tok.kind == "READ":
            return self._parse_read()
        if tok.kind == "LBRACE":
            return self._parse_block()
        return self._parse_expr_or_assign_stmt()

    def _parse_var_or_array_tail(self, type_name: str, name: str, line: int, top_level: bool):
        if self._match("LBRACKET"):
            size_tok = self._expect("INT_LIT", "array size")
            self._expect("RBRACKET")
            self._expect("SEMI")
            return ArrayDecl(type_name, name, int(size_tok.value), line)
        init = None
        if self._match("ASSIGN"):
            init = self._parse_expression(0)
        self._expect("SEMI")
        return VarDecl(type_name, name, init, line)

    def _parse_if(self) -> IfStmt:
        tok = self._advance()
        self._expect("LPAREN")
        cond = self._parse_expression(0)
        self._expect("RPAREN")
        then_block = self._parse_block_or_single()
        else_block = None
        if self._match("ELSE"):
            else_block = self._parse_block_or_single()
        return IfStmt(cond, then_block, else_block, tok.line)

    def _parse_block_or_single(self) -> Block:
        if self._check("LBRACE"):
            return self._parse_block()
        return Block([self._parse_statement()])

    def _parse_while(self) -> WhileStmt:
        tok = self._advance()
        self._expect("LPAREN")
        cond = self._parse_expression(0)
        self._expect("RPAREN")
        body = self._parse_block_or_single()
        return WhileStmt(cond, body, tok.line)

    def _parse_for(self) -> ForStmt:
        tok = self._advance()
        self._expect("LPAREN")
        init = None
        if not self._check("SEMI"):
            if self._peek().kind in TYPE_KEYWORDS:
                t = self._advance()
                name_tok = self._expect("IDENT", "identifier")
                init_expr = None
                if self._match("ASSIGN"):
                    init_expr = self._parse_expression(0)
                init = VarDecl(t.value, name_tok.value, init_expr, t.line)
            else:
                init = self._parse_assign_or_expr_no_semi()
        self._expect("SEMI")
        cond = None
        if not self._check("SEMI"):
            cond = self._parse_expression(0)
        self._expect("SEMI")
        update = None
        if not self._check("RPAREN"):
            update = self._parse_assign_or_expr_no_semi()
        self._expect("RPAREN")
        body = self._parse_block_or_single()
        return ForStmt(init, cond, update, body, tok.line)

    def _parse_return(self) -> ReturnStmt:
        tok = self._advance()
        value = None
        if not self._check("SEMI"):
            value = self._parse_expression(0)
        self._expect("SEMI")
        return ReturnStmt(value, tok.line)

    def _parse_print(self) -> PrintStmt:
        tok = self._advance()
        self._expect("LPAREN")
        expr = self._parse_expression(0)
        self._expect("RPAREN")
        self._expect("SEMI")
        return PrintStmt(expr, tok.line)

    def _parse_read(self) -> ReadStmt:
        tok = self._advance()
        self._expect("LPAREN")
        name_tok = self._expect("IDENT", "identifier")
        self._expect("RPAREN")
        self._expect("SEMI")
        return ReadStmt(name_tok.value, tok.line)

    def _parse_expr_or_assign_stmt(self):
        node = self._parse_assign_or_expr_no_semi()
        self._expect("SEMI")
        if isinstance(node, (Assign, ArrayAssign)):
            return node
        return ExprStmt(node, getattr(node, "line", 0))

    def _parse_assign_or_expr_no_semi(self):
        if self._check("IDENT") and self._peek(1).kind == "ASSIGN":
            name_tok = self._advance()
            self._advance()
            value = self._parse_expression(0)
            return Assign(name_tok.value, value, name_tok.line)
        if self._check("IDENT") and self._peek(1).kind == "LBRACKET":
            saved = self.pos
            name_tok = self._advance()
            self._advance()
            index = self._parse_expression(0)
            self._expect("RBRACKET")
            if self._match("ASSIGN"):
                value = self._parse_expression(0)
                return ArrayAssign(name_tok.value, index, value, name_tok.line)
            self.pos = saved
        return self._parse_expression(0)

    def _parse_expression(self, min_bp: int):
        left = self._parse_prefix()
        while True:
            tok = self._peek()
            op = tok.kind
            if op not in INFIX_BP:
                break
            l_bp, r_bp = INFIX_BP[op]
            if l_bp < min_bp:
                break
            self._advance()
            right = self._parse_expression(r_bp)
            left = BinOp(OP_DISPLAY.get(op, op), left, right, tok.line)
        return left

    def _parse_prefix(self):
        tok = self._peek()
        if tok.kind == "INT_LIT":
            self._advance()
            return Literal("int", tok.value, tok.line)
        if tok.kind == "FLOAT_LIT":
            self._advance()
            return Literal("float", tok.value, tok.line)
        if tok.kind == "CHAR_LIT":
            self._advance()
            return Literal("char", tok.value, tok.line)
        if tok.kind == "MINUS":
            self._advance()
            operand = self._parse_expression(13)
            return UnaryOp("-", operand, tok.line)
        if tok.kind == "BANG":
            self._advance()
            operand = self._parse_expression(13)
            return UnaryOp("!", operand, tok.line)
        if tok.kind == "LPAREN":
            self._advance()
            expr = self._parse_expression(0)
            self._expect("RPAREN")
            return expr
        if tok.kind == "IDENT":
            self._advance()
            if self._match("LPAREN"):
                args = []
                if not self._check("RPAREN"):
                    args.append(self._parse_expression(0))
                    while self._match("COMMA"):
                        args.append(self._parse_expression(0))
                self._expect("RPAREN")
                return FuncCall(tok.value, args, tok.line)
            if self._match("LBRACKET"):
                index = self._parse_expression(0)
                self._expect("RBRACKET")
                return ArrayAccess(tok.value, index, tok.line)
            return Identifier(tok.value, tok.line)
        raise ParseError("expected expression", tok)
