"""Optimizer for Three-Address Code (TAC).

Implements exactly two optimization passes:
(1) Copy/temporary elimination: for `tN = expr` immediately followed by `x = tN`,
    with tN unused afterwards, replace both with `x = expr`.
(2) Constant folding: fold an operation only when BOTH operands are numeric literals,
    e.g. `t1 = 2 * 3` -> `t1 = 6`. Do NOT propagate variable values (the sample keeps
    `b * 2` unfolded even though b = 5).

Removes temporaries and lines that become unused.
"""

import re
from typing import List, Dict, Optional, Tuple


def _is_int_literal(token: str) -> bool:
    """Check if token is an integer literal."""
    return bool(re.match(r"^-?\d+$", token))


def _is_temp(name: str) -> bool:
    """Check if name is a compiler temporary (e.g., t1, t2)."""
    return bool(re.match(r"^t\d+$", name))


def _eval_binary(op1: int, op: str, op2: int) -> int:
    """Evaluate binary arithmetic operator."""
    if op == "+":
        return op1 + op2
    elif op == "-":
        return op1 - op2
    elif op == "*":
        return op1 * op2
    elif op == "/":
        return op1 // op2
    raise ValueError(f"Unsupported operator: {op}")


class Optimizer:
    """Performs copy/temporary elimination and literal constant folding on TAC."""

    def optimize(self, instructions: List[str]) -> List[str]:
        """Run optimization passes and return optimized instructions."""
        code = list(instructions)

        # Pass 1: Constant folding
        code = self._constant_folding_pass(code)

        # Pass 2: Copy / temporary elimination
        code = self._copy_elimination_pass(code)

        # Clean up any unused temporaries
        code = self._remove_unused_temporaries(code)

        return code

    def _constant_folding_pass(self, instructions: List[str]) -> List[str]:
        """Fold operations when both operands are numeric literals.

        Temporaries holding literal values may be folded, but program variable
        values are strictly never propagated.
        """
        result: List[str] = []
        temp_consts: Dict[str, str] = {}

        binop_pattern = re.compile(r"^(\w+)\s*=\s*(\w+)\s*([+\-*/])\s*(\w+)$")
        copy_pattern = re.compile(r"^(\w+)\s*=\s*(\w+)$")

        for line in instructions:
            line_str = line.strip()

            m_bin = binop_pattern.match(line_str)
            if m_bin:
                target, op1, op, op2 = m_bin.groups()

                # If operand is a temporary holding a constant literal, resolve it
                val1 = temp_consts[op1] if op1 in temp_consts else op1
                val2 = temp_consts[op2] if op2 in temp_consts else op2

                # Fold if and only if BOTH operands are numeric literals
                if _is_int_literal(val1) and _is_int_literal(val2):
                    folded_val = str(_eval_binary(int(val1), op, int(val2)))
                    if _is_temp(target):
                        temp_consts[target] = folded_val
                    result.append(f"{target} = {folded_val}")
                else:
                    # Keep as is (or with resolved temp constants if applicable)
                    result.append(f"{target} = {val1} {op} {val2}")
                continue

            m_copy = copy_pattern.match(line_str)
            if m_copy:
                target, src = m_copy.groups()
                val = temp_consts[src] if src in temp_consts else src
                if _is_temp(target) and _is_int_literal(val):
                    temp_consts[target] = val
                result.append(f"{target} = {val}")
                continue

            # Other instructions (labels, conditional jumps)
            result.append(line_str)

        return result

    def _copy_elimination_pass(self, instructions: List[str]) -> List[str]:
        """Replace `tN = expr` immediately followed by `x = tN` with `x = expr`

        provided tN is unused afterwards.
        """
        code = list(instructions)
        changed = True

        while changed:
            changed = False
            new_code: List[str] = []
            i = 0
            n = len(code)

            while i < n:
                if i + 1 < n:
                    line1 = code[i].strip()
                    line2 = code[i + 1].strip()

                    # Match line1: tN = expr
                    m1 = re.match(r"^(t\d+)\s*=\s*(.+)$", line1)
                    # Match line2: x = tN
                    m2 = re.match(r"^(\w+)\s*=\s*(t\d+)$", line2)

                    if m1 and m2:
                        temp1, expr1 = m1.groups()
                        target2, temp2 = m2.groups()

                        if temp1 == temp2:
                            # Check if temp1 is used anywhere in remaining instructions
                            remaining_text = " \n ".join(code[i + 2:])
                            pattern = rf"\b{temp1}\b"
                            if not re.search(pattern, remaining_text):
                                # Replace both lines with target2 = expr1
                                new_code.append(f"{target2} = {expr1}")
                                i += 2
                                changed = True
                                continue

                new_code.append(code[i])
                i += 1

            code = new_code

        return code

    def _remove_unused_temporaries(self, instructions: List[str]) -> List[str]:
        """Remove dead assignments to temporaries that are never referenced afterwards."""
        code = list(instructions)
        changed = True

        while changed:
            changed = False
            # Count usages of all identifiers across the code
            # An identifier is used if it appears on the RHS or in conditions
            usage_counts: Dict[str, int] = {}
            for line in code:
                line_str = line.strip()
                if line_str.endswith(":"):
                    continue
                if "=" in line_str:
                    _, rhs = line_str.split("=", 1)
                    words = re.findall(r"\b\w+\b", rhs)
                    for w in words:
                        usage_counts[w] = usage_counts.get(w, 0) + 1
                elif line_str.startswith("if "):
                    words = re.findall(r"\b\w+\b", line_str[3:])
                    for w in words:
                        usage_counts[w] = usage_counts.get(w, 0) + 1

            new_code: List[str] = []
            for line in code:
                line_str = line.strip()
                m = re.match(r"^(t\d+)\s*=", line_str)
                if m:
                    temp_name = m.group(1)
                    if usage_counts.get(temp_name, 0) == 0:
                        # Dead temporary assignment
                        changed = True
                        continue
                new_code.append(line_str)

            code = new_code

        return code
