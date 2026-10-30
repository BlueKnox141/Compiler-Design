# Mini Lexical Analyzer Generator & Mini-Compiler Pipeline

A modular, standard-library-only implementation of a **Lex-like Lexical Analyzer Generator** and a complete **Mini-Compiler Pipeline** in Python 3.

---

## 1. Project Overview & Architecture

This project implements a simplified Lex-like lexical analyzer generator as the foundational engine, accompanied by a complete multi-stage compiler pipeline built directly on top of it.

```
Source Code
    │
    ▼
[Token Specification (token_spec.py)]
    │
    ▼
[Lexer Generator (lexer_generator.py)] ──> [Lexer Scanner (lexer.py)]
                                                 │
                                                 ▼ (Tokens)
                                         [Parser (parser.py)]
                                                 │
                                                 ▼ (AST)
                                    [Semantic Analyzer (semantic.py)] ──> [Symbol Table (symbol_table.py)]
                                                 │
                                                 ▼ (Validated AST)
                                       [TAC Generator (tac.py)]
                                                 │
                                                 ▼ (Three-Address Code)
                                       [Optimizer (optimizer.py)]
                                                 │
                                                 ▼ (Optimized TAC)
                                   [Target Code Generator (codegen.py)]
                                                 │
                                                 ▼ (R1 Assembly-like Code)
```

---

## 2. File Structure

All source files are strictly self-contained and rely exclusively on the Python 3 standard library:

| File | Purpose |
|---|---|
| `token_spec.py` | Token specifications: ordered list of `(TOKEN_NAME, regex_pattern)` pairs. |
| `lexer_generator.py` | Compiles regular expression rules and builds working `Lexer` scanners. |
| `lexer.py` | Scanner engine: tracks line/column, applies Lex disambiguation, handles lexical errors, and formats token streams and tables. |
| `parser.py` | Recursive-descent parser producing an Abstract Syntax Tree (AST) for the target grammar. |
| `symbol_table.py` | Symbol table tracking variable names, types (`int`), and initial literal values. |
| `semantic.py` | Scope-aware semantic analyzer validating variable declaration and usage rules. |
| `tac.py` | Three-Address Code (TAC) generator with condition temporary allocation and inverted jump logic. |
| `optimizer.py` | Two-pass TAC optimizer: temporary copy elimination and literal constant folding. |
| `codegen.py` | Single-register (`R1`) target assembly code generator with register reuse tracking. |
| `main.py` | CLI driver running the end-to-end pipeline with exact formatted output. |
| `sample.txt` | Default sample test program. |
| `test_suite.py` | Test suite covering all 6 mandatory test scenarios with diff-style assertions. |
| `README.md` | Comprehensive documentation, execution instructions, and test report. |

---

## 3. How to Run

### Run the Default Sample
```bash
python main.py sample.txt
```
*(If no argument is passed, `main.py` defaults to `sample.txt`)*

### Run with the Token Table Displayed
```bash
python main.py --tokens-table sample.txt
```

### Run Lexer Standalone
```bash
python lexer.py sample.txt
```

### Run the Complete Automated Test Suite
```bash
python test_suite.py
```

---

## 4. Phase-by-Phase Technical Explanation

### Phase 1: Lexical Analyzer Generator (Part A)
- **Token Specification (`token_spec.py`)**: Token rules are specified externally as an ordered list of `(TOKEN_NAME, regex_pattern)` pairs without hard-coding token patterns into the scanner.
- **Approach Used**: Python standard library `re` module. Each rule pattern is pre-compiled. At each scanning position, all rules are matched to find the maximum match length.
- **Lex Disambiguation**:
  1. *Longest Match Wins*: The rule matching the greatest number of characters is selected.
  2. *Rule Order Breaks Ties*: If two rules match the exact same number of characters, the rule appearing earlier in `token_spec.py` takes precedence (e.g., `KEYWORD` is placed before `IDENTIFIER`).
- **Token Classes**:
  - `KEYWORD`: `int`, `if`, `else`, `while`
  - `IDENTIFIER`: `[A-Za-z_][A-Za-z0-9_]*`
  - `NUMBER`: `[0-9]+`
  - `OPERATOR`: `>= <= == != + - * / = > <`
  - `SPECIAL SYMBOL`: `( ) { } ;`
  - `WHITESPACE`: `[ \t\r\n]+` (skipped, never emitted into token stream)
- **Error Recovery**: On an unrecognized character at line $L$ and column $C$, reports:
  `Lexical error at line L, column C: unexpected character 'X'`
  and advances by 1 character to continue scanning remaining tokens.
- **Representations**:
  1. Flat lexeme stream: `" ".join(token.lexeme for token in tokens)`
  2. Formatted table: `TOKEN TYPE | LEXEME`

### Phase 2: Syntax Analysis (Parser)
- **Recursive-descent parser** adhering strictly to the grammar:
  ```
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
  ```
- **Operator Precedence**: `*` and `/` bind tighter than `+` and `-`; operations are strictly left-associative.
- **Error Handling**: On syntax error, prints:
  `Syntax error at line L, column C: expected X, found Y`
  and immediately halts downstream pipeline phases.

### Phase 3: Symbol Table & Semantic Checks
- **Symbol Table Structure**: `Name Type Value`
  - Variable type is always `int`.
  - Initializer value is recorded if the variable was initialized with an integer literal, otherwise `-`.
- **Semantic Rules Checked**:
  1. *Use of an undeclared variable*: references to variables not present in the current or any enclosing scope.
  2. *Redeclaration of a variable in the same scope*: declaring the same variable multiple times within the same block level.
- **Type Checking**: Trivial because `int` is the sole data type; no artificial types are added.

### Phase 4: Three-Address Code (TAC) Generation
- Temporaries are sequentially numbered `t1, t2, ...` in creation order.
- Labels are sequentially numbered `L1, L2, ...`.
- Binary expressions emit `tN = left op right`.
- Assignments `x = expr` emit expression instructions followed by `x = tN` (or plain `x = y` / `x = 5` for single operands).
- Declarations with initializers emit nothing in TAC (only recorded in the symbol table).
- Condition evaluation consumes one temporary number that is allocated but never printed (explaining the jump from `t2` to `t4`).
- Relational operators in `if` statements are inverted to jump over the body:
  `>` $\to$ `<=`, `<` $\to$ `>=`, `>=` $\to$ `<`, `<=` $\to$ `>`, `==` $\to$ `!=`, `!=` $\to$ `==`.

### Phase 5: Optimizer
- **Pass 1: Copy/Temporary Elimination**:
  For an instruction `tN = expr` immediately followed by `x = tN`, where `tN` is never referenced in subsequent instructions, both lines are collapsed into `x = expr`.
- **Pass 2: Constant Folding**:
  Folds an arithmetic operation if and only if **both** operands are numeric literals (e.g. `t1 = 2 * 3` $\to$ `t1 = 6`). Program variable values (e.g. `b = 5`) are **never** propagated into expressions.
- **Dead Temporary Cleanup**:
  Removes dead assignments to temporaries that are never used in subsequent instructions.

### Phase 6: Target Code Generation
- Single-register machine architecture utilizing register `R1`.
- **Instruction Mapping**:
  - `x = a op b` $\to$ `LOAD R1, a` / `OP R1, b` / `STORE x, R1` (with `OP` in `{ADD, SUB, MUL, DIV}`)
  - `x = y` $\to$ `LOAD R1, y` / `STORE x, R1`
  - `if a relop b goto L` $\to$ `CMP a, b` / `{JLE, JGE, JL, JG, JE, JNE} L`
  - `L:` is emitted directly.
- **Register Reuse Optimization**:
  When a temporary holds the result of a previous computation and is consumed as an operand in the next operation, the value is retained in `R1` without an unnecessary store or reload, exploiting operator commutativity for `+` and `*`.

---

## 5. Actual Outputs of the Six Test Cases

Below are the actual verbatim outputs produced by the compiler pipeline for all required tests (verified with `test_suite.py`):

### Test 1: Default Sample Program (Exact Diff Match)
**Source**:
```c
int a = 10;
int b = 5;
int c;
c = a + b * 2;
if (c > 15) {
c = c + 1;
}
```
**Actual Output**:
```
=======================================================
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
```

---

### Test 2: Undeclared Variable
**Source**:
```c
x = 5;
```
**Actual Output**:
```
=======================================================
LEXICAL ANALYSIS
=======================================================
Tokens:
x = 5 ;
=======================================================
SYMBOL TABLE
=======================================================
Name Type Value
=======================================================
SYNTAX AND SEMANTIC CHECKING
=======================================================
Semantic error at line 1: variable 'x' is undeclared
```

---

### Test 3: Redeclaration in Same Scope
**Source**:
```c
int a;
int a;
```
**Actual Output**:
```
=======================================================
LEXICAL ANALYSIS
=======================================================
Tokens:
int a ; int a ;
=======================================================
SYMBOL TABLE
=======================================================
Name Type Value
a int -
=======================================================
SYNTAX AND SEMANTIC CHECKING
=======================================================
Semantic error at line 2: redeclaration of variable 'a'
```

---

### Test 4: Syntax Error
**Source**:
```c
int a = ;
```
**Actual Output**:
```
=======================================================
LEXICAL ANALYSIS
=======================================================
Tokens:
int a = ;
=======================================================
SYMBOL TABLE
=======================================================
Name Type Value
=======================================================
SYNTAX AND SEMANTIC CHECKING
=======================================================
Syntax error at line 1, column 9: expected expression, found ';'
```

---

### Test 5: Illegal Character
**Source**:
```c
int a = 5 @ 3;
```
**Actual Output**:
```
=======================================================
LEXICAL ANALYSIS
=======================================================
Lexical error at line 1, column 11: unexpected character '@'
Tokens:
int a = 5 3 ;
=======================================================
SYMBOL TABLE
=======================================================
Name Type Value
=======================================================
SYNTAX AND SEMANTIC CHECKING
=======================================================
Syntax error at line 1, column 13: expected ';', found '3'
```

---

### Test 6: Literal-Only Expression Constant Folding
**Source**:
```c
int r;
r = 2 * 3 + 4;
```
**Actual Output**:
```
=======================================================
LEXICAL ANALYSIS
=======================================================
Tokens:
int r ; r = 2 * 3 + 4 ;
=======================================================
SYMBOL TABLE
=======================================================
Name Type Value
r int -
=======================================================
SYNTAX AND SEMANTIC CHECKING
=======================================================
No syntax or semantic errors found.
=======================================================
THREE ADDRESS CODE
=======================================================
t1 = 2 * 3
t2 = t1 + 4
r = t2
=======================================================
OPTIMIZED CODE
=======================================================
r = 10
=======================================================
TARGET CODE
=======================================================
LOAD R1, 10
STORE r, R1
=======================================================
COMPILATION COMPLETED SUCCESSFULLY
=======================================================
```

---

## 6. Assumptions and Limitations

1. **Token Table vs Flat Stream in Sample Output**:
   - Requirement A7 specifies displaying recognized tokens in two forms: (1) flat lexeme stream, and (2) a table of `TOKEN TYPE | LEXEME`.
   - The sample output layout in the prompt specifically renders `Tokens:\n<flat stream>` without the table.
   - *Design Decision*: `main.py` prints the flat stream by default to match the sample layout byte-for-byte. The `--tokens-table` command-line flag and `lexer.py` provide the table representation without altering default output compliance.
2. **Variable vs Literal Propagation in Optimizer**:
   - In accordance with prompt instructions, constant folding is strictly restricted to operations whose operands are numeric literals (or compiler temporaries folded to literals).
   - Program variables with known initial values (e.g. `int b = 5;`) are **not** propagated into expressions (preserving `b * 2` unfolded in `c = a + b * 2;`).
3. **Single Data Type**:
   - The language supports only `int`. Type checking is therefore trivial, and no other types (e.g., float, char, boolean) are invented.
4. **Single Register Architecture (`R1`)**:
   - The target code generator targets a single accumulator register `R1`.
   - Spilling or multi-register allocation (e.g., R2, R3) is intentionally omitted to adhere strictly to the target specification.
5. **No Scope Expansion**:
   - Unsupported constructs (loops like `while`, `else` branches, functions, arrays) are omitted from the grammar and compiler phases in accordance with the strict project boundaries.
