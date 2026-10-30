"""Semantic analyzer for the mini compiler pipeline.

Performs semantic checks:
1. Use of undeclared variables.
2. Redeclaration of variables in the same scope.

Note on type checking:
Type mismatch checking is trivial because 'int' is the only supported data type
in this language. No extra types are invented.
"""

from typing import List, Dict, Set, Tuple, Optional
from parser import (
    ProgramNode, VarDeclNode, AssignNode, IfNode, BlockNode,
    CondNode, BinaryOpNode, NumberNode, VarNode, ASTNode
)
from symbol_table import SymbolTable


class SemanticAnalyzer:
    """Walks the AST, checks variable declaration rules, and builds the Symbol Table."""

    def __init__(self):
        self.symbol_table = SymbolTable()
        self.errors: List[str] = []
        # Scope stack: list of sets containing variable names declared in that scope level
        self.scopes: List[Set[str]] = [set()]

    def analyze(self, program: ProgramNode) -> Tuple[SymbolTable, List[str]]:
        """Run semantic analysis on the AST.

        Returns:
            Tuple of (symbol_table, errors_list)
        """
        for stmt in program.stmts:
            self._visit(stmt)
        return self.symbol_table, self.errors

    def _is_declared(self, name: str) -> bool:
        """Check if variable is declared in current scope or any enclosing scope."""
        for scope in reversed(self.scopes):
            if name in scope:
                return True
        return False

    def _visit(self, node: ASTNode):
        if isinstance(node, VarDeclNode):
            self._visit_var_decl(node)
        elif isinstance(node, AssignNode):
            self._visit_assign(node)
        elif isinstance(node, IfNode):
            self._visit_if(node)
        elif isinstance(node, BlockNode):
            self._visit_block(node)
        elif isinstance(node, BinaryOpNode):
            self._visit_binary_op(node)
        elif isinstance(node, CondNode):
            self._visit_cond(node)
        elif isinstance(node, VarNode):
            self._visit_var(node)
        elif isinstance(node, NumberNode):
            pass

    def _visit_var_decl(self, node: VarDeclNode):
        current_scope = self.scopes[-1]
        if node.name in current_scope:
            self.errors.append(
                f"Semantic error at line {node.line}: redeclaration of variable '{node.name}'"
            )
            return

        current_scope.add(node.name)

        # Value in symbol table is initializer if it is a literal constant, otherwise "-"
        if node.init_expr is not None and isinstance(node.init_expr, NumberNode):
            init_val = str(node.init_expr.value)
        else:
            init_val = "-"

        self.symbol_table.insert(node.name, "int", init_val)

        if node.init_expr is not None:
            self._visit(node.init_expr)

    def _visit_assign(self, node: AssignNode):
        if not self._is_declared(node.name):
            self.errors.append(
                f"Semantic error at line {node.line}: variable '{node.name}' is undeclared"
            )
        self._visit(node.expr)

    def _visit_if(self, node: IfNode):
        self._visit(node.cond)
        self._visit(node.body)

    def _visit_block(self, node: BlockNode):
        self.scopes.append(set())
        for stmt in node.stmts:
            self._visit(stmt)
        self.scopes.pop()

    def _visit_cond(self, node: CondNode):
        self._visit(node.left)
        self._visit(node.right)

    def _visit_binary_op(self, node: BinaryOpNode):
        self._visit(node.left)
        self._visit(node.right)

    def _visit_var(self, node: VarNode):
        if not self._is_declared(node.name):
            self.errors.append(
                f"Semantic error at line {node.line}: variable '{node.name}' is undeclared"
            )
