"""Target code generator.

Translates Three-Address Code into assembly-like target code using single register R1.
Rules:
- `x = a op b` -> LOAD R1, a / OP R1, b / STORE x, R1 (OP in {ADD, SUB, MUL, DIV})
- `x = y` -> LOAD R1, y / STORE x, R1
- `if a relop b goto L` -> CMP a, b / jump (JLE, JGE, JL, JG, JE, JNE) L
- `L:` is emitted as is.
- When a temporary holds a previous result and is used as the next operand,
  keep the value in R1 instead of reloading it.
"""

import re
from typing import List, Optional


OP_MAP = {
    "+": "ADD",
    "-": "SUB",
    "*": "MUL",
    "/": "DIV",
}

JUMP_MAP = {
    "<=": "JLE",
    ">=": "JGE",
    "<": "JL",
    ">": "JG",
    "==": "JE",
    "!=": "JNE",
}


def _is_temp(name: str) -> bool:
    """Check if name is a temporary variable."""
    return bool(re.match(r"^t\d+$", name))


class TargetCodeGenerator:
    """Generates single-register R1 assembly-like code from optimized TAC."""

    def __init__(self):
        self.r1_content: Optional[str] = None
        self.target_instructions: List[str] = []

    def emit(self, instruction: str):
        self.target_instructions.append(instruction)

    def generate(self, tac_instructions: List[str]) -> List[str]:
        """Generate assembly-like target instructions."""
        self.r1_content = None
        self.target_instructions = []

        binop_pattern = re.compile(r"^(\w+)\s*=\s*(\w+)\s*([+\-*/])\s*(\w+)$")
        copy_pattern = re.compile(r"^(\w+)\s*=\s*(\w+)$")
        branch_pattern = re.compile(r"^if\s+(\w+)\s*(<=|>=|<|>|==|!=)\s*(\w+)\s+goto\s+(\w+)$")
        label_pattern = re.compile(r"^(\w+):$")

        for line in tac_instructions:
            line_str = line.strip()
            if not line_str:
                continue

            # Case 1: Label (e.g., L1:)
            m_label = label_pattern.match(line_str)
            if m_label:
                self.emit(line_str)
                self.r1_content = None
                continue

            # Case 2: Conditional branch (if a relop b goto L)
            m_branch = branch_pattern.match(line_str)
            if m_branch:
                a, relop, b, label = m_branch.groups()
                self.emit(f"CMP {a}, {b}")
                jump_inst = JUMP_MAP.get(relop, "JMP")
                self.emit(f"{jump_inst} {label}")
                self.r1_content = None
                continue

            # Case 3: Binary operation (x = a op b)
            m_binop = binop_pattern.match(line_str)
            if m_binop:
                target, a, op, b = m_binop.groups()
                op_inst = OP_MAP[op]

                # R1 reuse optimization:
                # If R1 already holds operand b and operator is commutative (+ or *)
                if self.r1_content == b and op in ("+", "*"):
                    self.emit(f"{op_inst} R1, {a}")
                elif self.r1_content == a:
                    self.emit(f"{op_inst} R1, {b}")
                else:
                    self.emit(f"LOAD R1, {a}")
                    self.emit(f"{op_inst} R1, {b}")

                if _is_temp(target):
                    # Value remains in R1 for next instruction without store
                    self.r1_content = target
                else:
                    self.emit(f"STORE {target}, R1")
                    self.r1_content = target
                continue

            # Case 4: Copy assignment (x = y)
            m_copy = copy_pattern.match(line_str)
            if m_copy:
                target, src = m_copy.groups()
                if self.r1_content != src:
                    self.emit(f"LOAD R1, {src}")

                if _is_temp(target):
                    self.r1_content = target
                else:
                    self.emit(f"STORE {target}, R1")
                    self.r1_content = target
                continue

        return self.target_instructions
