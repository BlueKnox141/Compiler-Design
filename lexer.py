"""Lexical analyzer (Scanner) implementation.

Scans input source text into a stream of tokens using rules compiled by LexerGenerator.
Tracks line and column positions, logs lexical errors on unexpected characters without
aborting the scan, and provides both stream and tabular formatting.
"""

import sys
import re
from typing import List, Tuple, NamedTuple, Optional


class Token(NamedTuple):
    """Represents a lexical token."""
    type: str
    lexeme: str
    line: int
    col: int

    def __repr__(self) -> str:
        return f"Token({self.type}, {self.lexeme!r}, line={self.line}, col={self.col})"


class Lexer:
    """Scanner driven by compiled token specification rules."""

    def __init__(self, compiled_rules: List[Tuple[str, re.Pattern]]):
        self.rules = compiled_rules

    def tokenize(self, source: str) -> Tuple[List[Token], List[str]]:
        """Tokenize source string into tokens and lexical error messages.

        Returns:
            Tuple of (tokens_list, lexical_errors_list)
        """
        tokens: List[Token] = []
        errors: List[str] = []

        line = 1
        col = 1
        pos = 0
        n = len(source)

        while pos < n:
            best_rule: Optional[str] = None
            best_match: Optional[re.Match] = None
            max_len = 0

            # Lex disambiguation:
            # 1. Longest match wins.
            # 2. On tie, the earlier rule in the specification wins.
            for rule_name, regex in self.rules:
                m = regex.match(source, pos)
                if m:
                    match_len = m.end() - m.start()
                    # Strictly greater ensures earlier rule wins ties
                    if match_len > max_len:
                        max_len = match_len
                        best_match = m
                        best_rule = rule_name

            if best_match is not None and best_rule is not None and max_len > 0:
                lexeme = best_match.group(0)
                start_line = line
                start_col = col

                # Advance line and column counters across the matched lexeme
                for ch in lexeme:
                    if ch == '\n':
                        line += 1
                        col = 1
                    else:
                        col += 1

                pos += max_len

                # Whitespace tokens are skipped from the emitted token stream
                if best_rule != "WHITESPACE":
                    tokens.append(Token(best_rule, lexeme, start_line, start_col))
            else:
                # Unrecognized character error
                ch = source[pos]
                errors.append(f"Lexical error at line {line}, column {col}: unexpected character '{ch}'")
                if ch == '\n':
                    line += 1
                    col = 1
                else:
                    col += 1
                pos += 1

        return tokens, errors


def format_token_stream(tokens: List[Token]) -> str:
    """Format tokens as a flat lexeme stream separated by spaces."""
    return " ".join(t.lexeme for t in tokens)


def format_token_table(tokens: List[Token]) -> str:
    """Format tokens as a table of TOKEN TYPE | LEXEME."""
    lines = ["TOKEN TYPE      | LEXEME", "----------------|-------"]
    for t in tokens:
        lines.append(f"{t.type:<15} | {t.lexeme}")
    return "\n".join(lines)


if __name__ == "__main__":
    from token_spec import TOKEN_SPECS
    rules = [(name, re.compile(pat)) for name, pat in TOKEN_SPECS]
    lexer = Lexer(rules)

    filename = sys.argv[1] if len(sys.argv) > 1 else "sample.txt"
    with open(filename, "r") as f:
        src = f.read()

    tokens, errors = lexer.tokenize(src)

    print("=== LEXICAL ANALYSIS ===")
    print("Tokens:")
    print(format_token_stream(tokens))
    print()
    print("Token Table:")
    print(format_token_table(tokens))

    if errors:
        print()
        print("Errors:")
        for err in errors:
            print(err)
