from dataclasses import dataclass, field, fields, is_dataclass
from typing import List, Optional


@dataclass
class Node:
    pass


@dataclass
class Program(Node):
    decls: List["Node"]


@dataclass
class FuncDef(Node):
    return_type: str
    name: str
    params: List["Param"]
    body: "Block"
    line: int = 0


@dataclass
class Param(Node):
    type: str
    name: str
    line: int = 0


@dataclass
class Block(Node):
    statements: List["Node"] = field(default_factory=list)


@dataclass
class VarDecl(Node):
    type: str
    name: str
    init: Optional["Node"] = None
    line: int = 0


@dataclass
class ArrayDecl(Node):
    type: str
    name: str
    size: int
    line: int = 0


@dataclass
class Assign(Node):
    name: str
    value: "Node"
    line: int = 0


@dataclass
class ArrayAssign(Node):
    name: str
    index: "Node"
    value: "Node"
    line: int = 0


@dataclass
class IfStmt(Node):
    cond: "Node"
    then_block: "Block"
    else_block: Optional["Block"] = None
    line: int = 0


@dataclass
class WhileStmt(Node):
    cond: "Node"
    body: "Block"
    line: int = 0


@dataclass
class ForStmt(Node):
    init: Optional["Node"]
    cond: Optional["Node"]
    update: Optional["Node"]
    body: "Block"
    line: int = 0


@dataclass
class ReturnStmt(Node):
    value: Optional["Node"] = None
    line: int = 0


@dataclass
class ExprStmt(Node):
    expr: "Node"
    line: int = 0


@dataclass
class PrintStmt(Node):
    expr: "Node"
    line: int = 0


@dataclass
class ReadStmt(Node):
    name: str
    line: int = 0


@dataclass
class BinOp(Node):
    op: str
    left: "Node"
    right: "Node"
    line: int = 0


@dataclass
class UnaryOp(Node):
    op: str
    operand: "Node"
    line: int = 0


@dataclass
class Literal(Node):
    type: str
    value: object
    line: int = 0


@dataclass
class Identifier(Node):
    name: str
    line: int = 0


@dataclass
class ArrayAccess(Node):
    name: str
    index: "Node"
    line: int = 0


@dataclass
class FuncCall(Node):
    name: str
    args: List["Node"] = field(default_factory=list)
    line: int = 0


def dump(node, indent: int = 0) -> str:
    pad = "  " * indent
    if isinstance(node, list):
        if not node:
            return pad + "[]"
        return "\n".join(dump(item, indent) for item in node)
    if not is_dataclass(node):
        return pad + repr(node)
    out = [pad + type(node).__name__]
    for f in fields(node):
        if f.name == "line":
            continue
        val = getattr(node, f.name)
        if is_dataclass(val) or isinstance(val, list):
            out.append(pad + f"  {f.name}:")
            out.append(dump(val, indent + 2))
        else:
            out.append(pad + f"  {f.name}={val!r}")
    return "\n".join(out)
