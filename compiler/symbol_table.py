from dataclasses import dataclass
from typing import Dict, List, Optional


@dataclass
class Symbol:
    name: str
    type: str
    kind: str
    array_size: Optional[int] = None
    param_types: Optional[List[str]] = None
    return_type: Optional[str] = None


class ScopedSymbolTable:
    def __init__(self):
        self.scopes: List[Dict[str, Symbol]] = [{}]

    def enter_scope(self):
        self.scopes.append({})

    def exit_scope(self):
        self.scopes.pop()

    def declare(self, sym: Symbol) -> bool:
        if sym.name in self.scopes[-1]:
            return False
        self.scopes[-1][sym.name] = sym
        return True

    def lookup(self, name: str) -> Optional[Symbol]:
        for scope in reversed(self.scopes):
            if name in scope:
                return scope[name]
        return None
