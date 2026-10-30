"""Token specifications for the lexical analyzer generator.

Rules are defined as an ordered list of (TOKEN_NAME, regular_expression) pairs.
In accordance with Lex disambiguation principles:
- Longer matches take precedence over shorter ones.
- On equal match length, earlier rules in this specification win.
Therefore:
- KEYWORD is placed before IDENTIFIER so keywords are disambiguated on tie.
- Multi-character operators (>=, <=, ==, !=) appear before single-character operators.
- WHITESPACE is explicitly listed and flagged to be skipped.
"""

TOKEN_SPECS = [
    ("WHITESPACE", r"[ \t\r\n]+"),
    ("KEYWORD", r"\b(int|if|else|while)\b"),
    ("IDENTIFIER", r"[A-Za-z_][A-Za-z0-9_]*"),
    ("NUMBER", r"[0-9]+"),
    ("OPERATOR", r">=|<=|==|!=|\+|-|\*|/|=|>|<"),
    ("SPECIAL SYMBOL", r"[(){};]"),
]
