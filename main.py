"""Main compiler pipeline driver.

Orchestrates:
1. Lexical Analysis (Scanner generator based on token specs)
2. Symbol Table Generation
3. Syntax and Semantic Checking
4. Three-Address Code (TAC) Generation
5. Optimization (Temporary copy elimination and literal constant folding)
6. Target Code Generation (Single-register R1 architecture)
"""

import sys
import argparse
from typing import List, Optional

from lexer_generator import get_default_lexer
from lexer import format_token_stream, format_token_table, Token
from parser import Parser, ParserError
from semantic import SemanticAnalyzer
from tac import TACGenerator
from optimizer import Optimizer
from codegen import TargetCodeGenerator

SEPARATOR = "=" * 55


def print_section(title: str, content: Optional[str] = None):
    """Print a pipeline section with 55 '=' separator lines."""
    print(SEPARATOR)
    print(title)
    print(SEPARATOR)
    if content:
        print(content)


def compile_source(source_code: str, show_tokens_table: bool = False) -> bool:
    """Compile a source code string through the full compiler pipeline.

    Returns:
        True if compilation succeeded without errors, False otherwise.
    """
    # -------------------------------------------------------------------------
    # Phase 1: Lexical Analysis
    # -------------------------------------------------------------------------
    lexer = get_default_lexer()
    tokens, lex_errors = lexer.tokenize(source_code)

    lex_output_lines = []
    if lex_errors:
        for err in lex_errors:
            lex_output_lines.append(err)
    lex_output_lines.append("Tokens:")
    lex_output_lines.append(format_token_stream(tokens))

    if show_tokens_table:
        lex_output_lines.append("")
        lex_output_lines.append(format_token_table(tokens))

    print_section("LEXICAL ANALYSIS", "\n".join(lex_output_lines))

    # -------------------------------------------------------------------------
    # Phase 2: Parsing (Syntax Analysis)
    # -------------------------------------------------------------------------
    parser = Parser(tokens)
    syntax_error: Optional[str] = None
    ast = None
    try:
        ast = parser.parse()
    except ParserError as pe:
        syntax_error = str(pe)

    # -------------------------------------------------------------------------
    # Phase 3: Semantic Analysis & Symbol Table
    # -------------------------------------------------------------------------
    semantic_analyzer = SemanticAnalyzer()
    sem_errors: List[str] = []
    symbol_table = semantic_analyzer.symbol_table

    if ast is not None:
        symbol_table, sem_errors = semantic_analyzer.analyze(ast)

    # Output Symbol Table
    print_section("SYMBOL TABLE", symbol_table.format_table())

    # Output Syntax and Semantic Checking results
    all_errors = []
    if syntax_error:
        all_errors.append(syntax_error)
    all_errors.extend(sem_errors)

    if all_errors:
        print_section("SYNTAX AND SEMANTIC CHECKING", "\n".join(all_errors))
        return False
    else:
        print_section("SYNTAX AND SEMANTIC CHECKING", "No syntax or semantic errors found.")

    # -------------------------------------------------------------------------
    # Phase 4: Three-Address Code (TAC) Generation
    # -------------------------------------------------------------------------
    tac_gen = TACGenerator()
    tac_instructions = tac_gen.generate(ast)
    print_section("THREE ADDRESS CODE", "\n".join(tac_instructions))

    # -------------------------------------------------------------------------
    # Phase 5: Optimization
    # -------------------------------------------------------------------------
    optimizer = Optimizer()
    opt_instructions = optimizer.optimize(tac_instructions)
    print_section("OPTIMIZED CODE", "\n".join(opt_instructions))

    # -------------------------------------------------------------------------
    # Phase 6: Target Code Generation
    # -------------------------------------------------------------------------
    target_gen = TargetCodeGenerator()
    target_instructions = target_gen.generate(opt_instructions)
    print_section("TARGET CODE", "\n".join(target_instructions))

    # -------------------------------------------------------------------------
    # Completion Banner
    # -------------------------------------------------------------------------
    print(SEPARATOR)
    print("COMPILATION COMPLETED SUCCESSFULLY")
    print(SEPARATOR)
    return True


def main():
    parser = argparse.ArgumentParser(description="Mini Lexical Analyzer Generator & Compiler Pipeline")
    parser.add_argument("source_file", nargs="?", default="sample.txt", help="Path to source program (default: sample.txt)")
    parser.add_argument("--tokens-table", action="store_true", help="Display token type and lexeme table in lexical analysis")
    args = parser.parse_args()

    try:
        with open(args.source_file, "r") as f:
            source_code = f.read()
    except FileNotFoundError:
        print(f"Error: file '{args.source_file}' not found.", file=sys.stderr)
        sys.exit(1)

    success = compile_source(source_code, show_tokens_table=args.tokens_table)
    if not success:
        sys.exit(1)


if __name__ == "__main__":
    main()
