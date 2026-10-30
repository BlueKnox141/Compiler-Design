"""Recursive-descent parser for the mini compiler pipeline.

Grammar:
    program     -> stmt*
    stmt        -> decl | assign | if_stmt | block
    decl        -> 'int' IDENTIFIER ('=' expr)? ';'
    assign      -> IDENTIFIER '=' expr ';'
    if_stmt     -> 'if' '(' cond ')' stmt
    block       -> '{' stmt* '}'
    cond        -> expr RELOP expr          (RELOP: > < >= <= == !=)
    expr        -> term (('+'|'-') term)*
    term        -> factor (('*'|'/') factor)*
    factor      -> NUMBER | IDENTIFIER | '(' expr ')'

Operator precedence: * and / bind tighter than + and -; left-associative.
"""

from typing import List, Optional, Any
from lexer import Token


class ParserError(Exception):
    """Exception raised on syntax errors."""
    pass


# ---------------------------------------------------------------------------
# AST Node Classes
# ---------------------------------------------------------------------------

class ASTNode:
    """Base class for all Abstract Syntax Tree nodes."""
    def __init__(self, line: int, col: int):
        self.line = line
        self.col = col


class ProgramNode(ASTNode):
    def __init__(self, stmts: List[ASTNode], line: int = 1, col: int = 1):
        super().__init__(line, col)
        self.stmts = stmts


class VarDeclNode(ASTNode):
    def __init__(self, var_type: str, name: str, init_expr: Optional[ASTNode], line: int, col: int):
        super().__init__(line, col)
        self.var_type = var_type
        self.name = name
        self.init_expr = init_expr


class AssignNode(ASTNode):
    def __init__(self, name: str, expr: ASTNode, line: int, col: int):
        super().__init__(line, col)
        self.name = name
        self.expr = expr


class IfNode(ASTNode):
    def __init__(self, cond: "CondNode", body: ASTNode, line: int, col: int):
        super().__init__(line, col)
        self.cond = cond
        self.body = body


class BlockNode(ASTNode):
    def __init__(self, stmts: List[ASTNode], line: int, col: int):
        super().__init__(line, col)
        self.stmts = stmts


class CondNode(ASTNode):
    def __init__(self, left: ASTNode, relop: str, right: ASTNode, line: int, col: int):
        super().__init__(line, col)
        self.left = left
        self.relop = relop
        self.right = right


class BinaryOpNode(ASTNode):
    def __init__(self, op: str, left: ASTNode, right: ASTNode, line: int, col: int):
        super().__init__(line, col)
        self.op = op
        self.left = left
        self.right = right


class NumberNode(ASTNode):
    def __init__(self, value: int, line: int, col: int):
        super().__init__(line, col)
        self.value = value


class VarNode(ASTNode):
    def __init__(self, name: str, line: int, col: int):
        super().__init__(line, col)
        self.name = name


# ---------------------------------------------------------------------------
# Parser
# ---------------------------------------------------------------------------

class Parser:
    """Recursive-descent parser."""

    def __init__(self, tokens: List[Token]):
        self.tokens = tokens
        self.pos = 0

    def is_at_end(self) -> bool:
        return self.pos >= len(self.tokens)

    def peek(self) -> Token:
        if self.is_at_end():
            last = self.tokens[-1] if self.tokens else Token("EOF", "EOF", 1, 1)
            return Token("EOF", "EOF", last.line, last.col)
        return self.tokens[self.pos]

    def consume(self) -> Token:
        tok = self.peek()
        self.pos += 1
        return tok

    def match_exact(self, lexeme: str, expected_desc: Optional[str] = None) -> Token:
        tok = self.peek()
        if tok.lexeme == lexeme:
            return self.consume()
        expected = expected_desc if expected_desc is not None else f"'{lexeme}'"
        raise ParserError(f"Syntax error at line {tok.line}, column {tok.col}: expected {expected}, found '{tok.lexeme}'")

    def match_type(self, token_type: str, expected_desc: str) -> Token:
        tok = self.peek()
        if tok.type == token_type:
            return self.consume()
        raise ParserError(f"Syntax error at line {tok.line}, column {tok.col}: expected {expected_desc}, found '{tok.lexeme}'")

    def parse(self) -> ProgramNode:
        """Parse the full program."""
        stmts: List[ASTNode] = []
        while not self.is_at_end():
            stmts.append(self.parse_stmt())
        return ProgramNode(stmts)

    def parse_stmt(self) -> ASTNode:
        tok = self.peek()
        if tok.lexeme == "int" and tok.type == "KEYWORD":
            return self.parse_decl()
        elif tok.type == "IDENTIFIER":
            return self.parse_assign()
        elif tok.lexeme == "if" and tok.type == "KEYWORD":
            return self.parse_if()
        elif tok.lexeme == "{" and tok.type == "SPECIAL SYMBOL":
            return self.parse_block()
        else:
            raise ParserError(f"Syntax error at line {tok.line}, column {tok.col}: expected statement, found '{tok.lexeme}'")

    def parse_decl(self) -> VarDeclNode:
        int_tok = self.match_exact("int")
        id_tok = self.match_type("IDENTIFIER", "IDENTIFIER")
        init_expr = None
        if self.peek().lexeme == "=":
            self.consume()
            init_expr = self.parse_expr()
        self.match_exact(";", "';'")
        return VarDeclNode("int", id_tok.lexeme, init_expr, int_tok.line, int_tok.col)

    def parse_assign(self) -> AssignNode:
        id_tok = self.match_type("IDENTIFIER", "IDENTIFIER")
        self.match_exact("=", "'='")
        expr = self.parse_expr()
        self.match_exact(";", "';'")
        return AssignNode(id_tok.lexeme, expr, id_tok.line, id_tok.col)

    def parse_if(self) -> IfNode:
        if_tok = self.match_exact("if")
        self.match_exact("(", "'('")
        cond = self.parse_cond()
        self.match_exact(")", "')'")
        body = self.parse_stmt()
        return IfNode(cond, body, if_tok.line, if_tok.col)

    def parse_block(self) -> BlockNode:
        brace_tok = self.match_exact("{")
        stmts: List[ASTNode] = []
        while self.peek().lexeme != "}" and not self.is_at_end():
            stmts.append(self.parse_stmt())
        self.match_exact("}", "'}'")
        return BlockNode(stmts, brace_tok.line, brace_tok.col)

    def parse_cond(self) -> CondNode:
        left = self.parse_expr()
        relops = {">", "<", ">=", "<=", "==", "!="}
        tok = self.peek()
        if tok.lexeme in relops and tok.type == "OPERATOR":
            op_tok = self.consume()
            right = self.parse_expr()
            return CondNode(left, op_tok.lexeme, right, op_tok.line, op_tok.col)
        else:
            raise ParserError(f"Syntax error at line {tok.line}, column {tok.col}: expected relational operator, found '{tok.lexeme}'")

    def parse_expr(self) -> ASTNode:
        node = self.parse_term()
        while self.peek().lexeme in ("+", "-") and self.peek().type == "OPERATOR":
            op_tok = self.consume()
            right = self.parse_term()
            node = BinaryOpNode(op_tok.lexeme, node, right, op_tok.line, op_tok.col)
        return node

    def parse_term(self) -> ASTNode:
        node = self.parse_factor()
        while self.peek().lexeme in ("*", "/") and self.peek().type == "OPERATOR":
            op_tok = self.consume()
            right = self.parse_factor()
            node = BinaryOpNode(op_tok.lexeme, node, right, op_tok.line, op_tok.col)
        return node

    def parse_factor(self) -> ASTNode:
        tok = self.peek()
        if tok.type == "NUMBER":
            self.consume()
            return NumberNode(int(tok.lexeme), tok.line, tok.col)
        elif tok.type == "IDENTIFIER":
            self.consume()
            return VarNode(tok.lexeme, tok.line, tok.col)
        elif tok.lexeme == "(" and tok.type == "SPECIAL SYMBOL":
            self.consume()
            node = self.parse_expr()
            self.match_exact(")", "')'")
            return node
        else:
            raise ParserError(f"Syntax error at line {tok.line}, column {tok.col}: expected expression, found '{tok.lexeme}'")
