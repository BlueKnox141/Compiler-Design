"""Automated test suite verifying the compiler pipeline.

Tests required:
1. Sample program: Output must match prompt sample exactly (diff-style assertion).
2. Undeclared variable: `x = 5;`
3. Redeclaration: `int a; int a;`
4. Syntax error: `int a = ;`
5. Illegal character: `int a = 5 @ 3;`
6. Literal-only expression: `int r; r = 2 * 3 + 4;`
"""

import sys
import io
import difflib
from main import compile_source

EXPECTED_SAMPLE_OUTPUT = """=======================================================
LEXICAL ANALYSIS
=======================================================
Tokens:
int a = 10 ; int b = 5 ; int c ; c = a + b * 2 ; if ( c > 15 ) { c = c + 1 ; }
=======================================================
SYMBOL TABLE
=======================================================
Name Type Value
a int 10
b int 5
c int -
=======================================================
SYNTAX AND SEMANTIC CHECKING
=======================================================
No syntax or semantic errors found.
=======================================================
THREE ADDRESS CODE
=======================================================
t1 = b * 2
t2 = a + t1
c = t2
if c <= 15 goto L1
t4 = c + 1
c = t4
L1:
=======================================================
OPTIMIZED CODE
=======================================================
t1 = b * 2
c = a + t1
if c <= 15 goto L1
c = c + 1
L1:
=======================================================
TARGET CODE
=======================================================
LOAD R1, b
MUL R1, 2
ADD R1, a
STORE c, R1
CMP c, 15
JLE L1
LOAD R1, c
ADD R1, 1
STORE c, R1
L1:
=======================================================
COMPILATION COMPLETED SUCCESSFULLY
=======================================================
"""


def capture_compilation(source: str, show_tokens_table: bool = False) -> str:
    """Run compile_source and capture its stdout string."""
    old_stdout = sys.stdout
    captured = io.StringIO()
    try:
        sys.stdout = captured
        compile_source(source, show_tokens_table=show_tokens_table)
    finally:
        sys.stdout = old_stdout
    return captured.getvalue()


def run_tests():
    print("=" * 70)
    print("RUNNING COMPILER PIPELINE TEST SUITE")
    print("=" * 70)

    # -------------------------------------------------------------------------
    # Test 1: Default sample program with diff-style assertion
    # -------------------------------------------------------------------------
    print("\n--- TEST 1: Default Sample Program (Exact Diff Assertion) ---")
    sample_src = """int a = 10;
int b = 5;
int c;
c = a + b * 2;
if (c > 15) {
c = c + 1;
}
"""
    actual_1 = capture_compilation(sample_src)
    print("ACTUAL OUTPUT:")
    print(actual_1)

    diff = list(difflib.unified_diff(
        EXPECTED_SAMPLE_OUTPUT.splitlines(keepends=True),
        actual_1.splitlines(keepends=True),
        fromfile="EXPECTED",
        tofile="ACTUAL"
    ))

    if diff:
        print("DIFF DETECTED:")
        print("".join(diff))
        raise AssertionError("Test 1 failed: Actual output does not match expected output!")
    else:
        print("DIFF CHECK: PASSED (Exact byte-for-byte match)\n")

    # -------------------------------------------------------------------------
    # Test 2: Undeclared variable (x = 5;)
    # -------------------------------------------------------------------------
    print("--- TEST 2: Undeclared Variable (`x = 5;`) ---")
    src_2 = "x = 5;\n"
    actual_2 = capture_compilation(src_2)
    print("ACTUAL OUTPUT:")
    print(actual_2)
    assert "variable 'x' is undeclared" in actual_2, "Test 2 failed: undeclared variable error missing!"
    print("ASSERTION CHECK: PASSED (Detected undeclared variable 'x')\n")

    # -------------------------------------------------------------------------
    # Test 3: Redeclaration in same scope (int a; int a;)
    # -------------------------------------------------------------------------
    print("--- TEST 3: Redeclaration in Same Scope (`int a; int a;`) ---")
    src_3 = "int a;\nint a;\n"
    actual_3 = capture_compilation(src_3)
    print("ACTUAL OUTPUT:")
    print(actual_3)
    assert "redeclaration of variable 'a'" in actual_3, "Test 3 failed: redeclaration error missing!"
    print("ASSERTION CHECK: PASSED (Detected redeclaration of variable 'a')\n")

    # -------------------------------------------------------------------------
    # Test 4: Syntax error (int a = ;)
    # -------------------------------------------------------------------------
    print("--- TEST 4: Syntax Error (`int a = ;`) ---")
    src_4 = "int a = ;\n"
    actual_4 = capture_compilation(src_4)
    print("ACTUAL OUTPUT:")
    print(actual_4)
    assert "Syntax error at line 1, column 9: expected expression, found ';'" in actual_4, "Test 4 failed: syntax error missing!"
    print("ASSERTION CHECK: PASSED (Detected syntax error at line 1, col 9)\n")

    # -------------------------------------------------------------------------
    # Test 5: Illegal character (int a = 5 @ 3;)
    # -------------------------------------------------------------------------
    print("--- TEST 5: Illegal Character (`int a = 5 @ 3;`) ---")
    src_5 = "int a = 5 @ 3;\n"
    actual_5 = capture_compilation(src_5)
    print("ACTUAL OUTPUT:")
    print(actual_5)
    assert "unexpected character '@'" in actual_5, "Test 5 failed: lexical error for '@' missing!"
    assert "Syntax error" in actual_5, "Test 5 failed: downstream syntax error missing!"
    print("ASSERTION CHECK: PASSED (Lexical error reported and scan continued)\n")

    # -------------------------------------------------------------------------
    # Test 6: Literal-only expression (int r; r = 2 * 3 + 4;)
    # -------------------------------------------------------------------------
    print("--- TEST 6: Literal-only Expression Constant Folding (`int r; r = 2 * 3 + 4;`) ---")
    src_6 = "int r;\nr = 2 * 3 + 4;\n"
    actual_6 = capture_compilation(src_6)
    print("ACTUAL OUTPUT:")
    print(actual_6)
    assert "r = 10" in actual_6, "Test 6 failed: constant folding to 'r = 10' missing!"
    assert "LOAD R1, 10" in actual_6, "Test 6 failed: target code LOAD R1, 10 missing!"
    print("ASSERTION CHECK: PASSED (Constant folded to 10 and target code emitted)\n")

    print("=" * 70)
    print("ALL 6 TESTS COMPLETED AND VERIFIED SUCCESSFULLY!")
    print("=" * 70)


if __name__ == "__main__":
    run_tests()
