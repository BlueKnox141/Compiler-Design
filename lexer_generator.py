"""Lexical Analyzer Generator.

Reads token specifications from a specification data structure or file,
and produces a working scanner (Lexer) that adheres to standard Lex
disambiguation principles:
1. Longest match wins.
2. Earlier rule in spec breaks ties.

Approach used:
This generator uses Python's standard library `re` module. Each regular expression
rule from the specification is compiled into an individual regex pattern anchored
at the current scan position. At each scan step, candidate matches across all rules
are evaluated to find the maximum length match, preserving the first rule in case
of equal length ties.
"""

import re
from typing import List, Tuple
from lexer import Lexer, Token
from token_spec import TOKEN_SPECS


class LexerGenerator:
    """Generator that compiles token specifications into a working Lexer."""

    def __init__(self, token_specs: List[Tuple[str, str]] = None):
        """Initialize generator with an ordered list of (TOKEN_NAME, regex_pattern).

        Args:
            token_specs: Ordered list of (name, regex) pairs. Defaults to TOKEN_SPECS.
        """
        self.specs = token_specs if token_specs is not None else TOKEN_SPECS
        self.compiled_rules = self._compile_rules()

    def _compile_rules(self) -> List[Tuple[str, re.Pattern]]:
        """Compile regex patterns using Python's re module."""
        compiled = []
        for name, pattern in self.specs:
            compiled.append((name, re.compile(pattern)))
        return compiled

    def build_lexer(self) -> Lexer:
        """Produce and return a configured Lexer instance."""
        return Lexer(self.compiled_rules)


def get_default_lexer() -> Lexer:
    """Convenience factory function to create a scanner using default token specs."""
    generator = LexerGenerator()
    return generator.build_lexer()
