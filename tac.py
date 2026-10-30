"""Three-Address Code (TAC) generator.

Generates TAC instructions adhering to:
- Temporaries t1, t2, ... created in order.
- Labels L1, L2, ... created in order.
- Binary expression: tN = left op right.
- Assignment x = expr: emits expr, then x = tN (or direct x = y / x = 5 for single var/number).
- Declaration with initializer emits nothing in TAC.
- if (cond) body: condition evaluation consumes one temporary number (not printed),
  inverts the relational operator, emits 'if <left> <inv_relop> <right> goto Ln',
  generates body code, then emits 'Ln:'.
"""

from typing import List
from parser import (
    ProgramNode, VarDeclNode, AssignNode, IfNode, BlockNode,
    CondNode, BinaryOpNode, NumberNode, VarNode, ASTNode
)


INVERSION_MAP = {
    ">": "<=",
    "<": ">=",
    ">=": "<",
    "<=": ">",
    "==": "!=",
    "!=": "==",
}


class TACGenerator:
    """Generates Three-Address Code from an AST."""

    def __init__(self):
        self.temp_count = 0
        self.label_count = 0
        self.instructions: List[str] = []

    def new_temp(self) -> str:
        """Allocate a new temporary variable t1, t2, ..."""
        self.temp_count += 1
        return f"t{self.temp_count}"

    def new_label(self) -> str:
        """Allocate a new jump label L1, L2, ..."""
        self.label_count += 1
        return f"L{self.label_count}"

    def emit(self, instruction: str):
        """Append an instruction to the TAC list."""
        self.instructions.append(instruction)

    def generate(self, program: ProgramNode) -> List[str]:
        """Generate TAC for the full program."""
        for stmt in program.stmts:
            self._gen_stmt(stmt)
        return self.instructions

    def _gen_stmt(self, node: ASTNode):
        if isinstance(node, VarDeclNode):
            # Declarations with or without initializers emit nothing in TAC
            pass
        elif isinstance(node, AssignNode):
            if isinstance(node.expr, (NumberNode, VarNode)):
                rhs = self._gen_expr(node.expr)
                self.emit(f"{node.name} = {rhs}")
            else:
                res = self._gen_expr(node.expr)
                self.emit(f"{node.name} = {res}")
        elif isinstance(node, IfNode):
            cond = node.cond
            left = self._gen_expr(cond.left)
            right = self._gen_expr(cond.right)

            # Consumes one temporary number that is never printed
            _ = self.new_temp()

            label = self.new_label()
            inv_op = INVERSION_MAP[cond.relop]
            self.emit(f"if {left} {inv_op} {right} goto {label}")

            self._gen_stmt(node.body)
            self.emit(f"{label}:")
        elif isinstance(node, BlockNode):
            for s in node.stmts:
                self._gen_stmt(s)

    def _gen_expr(self, node: ASTNode) -> str:
        if isinstance(node, NumberNode):
            return str(node.value)
        elif isinstance(node, VarNode):
            return node.name
        elif isinstance(node, BinaryOpNode):
            left = self._gen_expr(node.left)
            right = self._gen_expr(node.right)
            t = self.new_temp()
            self.emit(f"{t} = {left} {node.op} {right}")
            return t
        raise ValueError(f"Unknown expression node: {node}")
