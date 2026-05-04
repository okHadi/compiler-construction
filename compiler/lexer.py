from dataclasses import dataclass
from typing import List


KEYWORDS = {
    "int", "float", "char", "void",
    "if", "else", "while", "for", "return",
    "print", "read",
}


@dataclass
class Token:
    kind: str
    value: object
    line: int
    col: int

    def __repr__(self):
        return f"Token({self.kind!r}, {self.value!r}, line={self.line}, col={self.col})"


class LexerError(Exception):
    def __init__(self, message: str, line: int, col: int):
        super().__init__(f"line {line}, col {col}: {message}")
        self.line = line
        self.col = col


class Lexer:
    def __init__(self, source: str):
        self.src = source
        self.pos = 0
        self.line = 1
        self.col = 1

    def _peek(self, offset: int = 0) -> str:
        i = self.pos + offset
        return self.src[i] if i < len(self.src) else ""

    def _advance(self) -> str:
        ch = self.src[self.pos]
        self.pos += 1
        if ch == "\n":
            self.line += 1
            self.col = 1
        else:
            self.col += 1
        return ch

    def _match(self, expected: str) -> bool:
        if self._peek() == expected:
            self._advance()
            return True
        return False

    def tokenize(self) -> List[Token]:
        tokens: List[Token] = []
        while self.pos < len(self.src):
            ch = self._peek()
            if ch in " \t\r\n":
                self._advance()
                continue
            if ch == "/" and self._peek(1) == "/":
                while self.pos < len(self.src) and self._peek() != "\n":
                    self._advance()
                continue
            if ch == "/" and self._peek(1) == "*":
                start_line, start_col = self.line, self.col
                self._advance(); self._advance()
                while self.pos < len(self.src) and not (self._peek() == "*" and self._peek(1) == "/"):
                    self._advance()
                if self.pos >= len(self.src):
                    raise LexerError("unterminated block comment", start_line, start_col)
                self._advance(); self._advance()
                continue
            tokens.append(self._scan_token())
        tokens.append(Token("EOF", None, self.line, self.col))
        return tokens

    def _scan_token(self) -> Token:
        line, col = self.line, self.col
        ch = self._peek()
        if ch.isalpha() or ch == "_":
            return self._scan_identifier(line, col)
        if ch.isdigit():
            return self._scan_number(line, col)
        if ch == "'":
            return self._scan_char(line, col)
        return self._scan_operator(line, col)

    def _scan_identifier(self, line: int, col: int) -> Token:
        start = self.pos
        while self._peek().isalnum() or self._peek() == "_":
            self._advance()
        text = self.src[start:self.pos]
        if text in KEYWORDS:
            return Token(text.upper(), text, line, col)
        return Token("IDENT", text, line, col)

    def _scan_number(self, line: int, col: int) -> Token:
        start = self.pos
        while self._peek().isdigit():
            self._advance()
        if self._peek() == "." and self._peek(1).isdigit():
            self._advance()
            while self._peek().isdigit():
                self._advance()
            return Token("FLOAT_LIT", float(self.src[start:self.pos]), line, col)
        return Token("INT_LIT", int(self.src[start:self.pos]), line, col)

    def _scan_char(self, line: int, col: int) -> Token:
        self._advance()
        if self._peek() == "\\":
            self._advance()
            esc = self._advance()
            value = {"n": "\n", "t": "\t", "r": "\r", "\\": "\\", "'": "'", "0": "\0"}.get(esc)
            if value is None:
                raise LexerError(f"unknown escape '\\{esc}'", line, col)
        else:
            if self.pos >= len(self.src):
                raise LexerError("unterminated character literal", line, col)
            value = self._advance()
        if self._peek() != "'":
            raise LexerError("expected closing quote in character literal", line, col)
        self._advance()
        return Token("CHAR_LIT", value, line, col)

    def _scan_operator(self, line: int, col: int) -> Token:
        ch = self._advance()
        two = ch + self._peek()
        if two in ("==", "!=", "<=", ">=", "&&", "||"):
            self._advance()
            return Token(two, two, line, col)
        single_map = {
            "+": "PLUS", "-": "MINUS", "*": "STAR", "/": "SLASH", "%": "PERCENT",
            "=": "ASSIGN", "<": "LT", ">": "GT", "!": "BANG",
            "(": "LPAREN", ")": "RPAREN",
            "{": "LBRACE", "}": "RBRACE",
            "[": "LBRACKET", "]": "RBRACKET",
            ",": "COMMA", ";": "SEMI",
        }
        if ch in single_map:
            return Token(single_map[ch], ch, line, col)
        raise LexerError(f"unexpected character {ch!r}", line, col)
