# Calculator Demo

A simple command-line calculator with **intentional bugs**, designed as a demo and test target for the [ticket-automation-tool](https://github.com/papatel5698/ticket-automation-tool).

This repo includes 20 pre-created GitHub Issues that map to real bugs, feature requests, and cleanup tasks in the code — making it a realistic playground for automated ticket triage.

---

## Prerequisites

- **Python 3.11+** — check with `python3 --version`
- **pip** — comes with Python

---

## Setup

```bash
# 1. Clone the repository
git clone https://github.com/papatel5698/calculator-demo.git
cd calculator-demo

# 2. Install test dependencies
pip install -r requirements.txt
```

That's it — no build step needed. The calculator runs directly from source.

---

## Running the Calculator

```bash
python -m src.main
```

You'll see:

```
Welcome to Calculator
>
```

Type a math expression and press Enter. Type `quit` or `exit` to close.

---

## Sample Equations to Try

### These work correctly

| Input | Output | Notes |
|-------|--------|-------|
| `2+3` | `5` | Basic addition |
| `10-4` | `6` | Subtraction |
| `3*4` | `12` | Multiplication |
| `10/2` | `5` | Division (even result) |
| `1+2+3` | `6` | Chained addition |
| `100*2` | `200` | Larger numbers |

### These expose bugs — try them and see what happens

| Input | Expected | Actual | Bug |
|-------|----------|--------|-----|
| `10/0` | Error message | **Crashes** with ZeroDivisionError | No division-by-zero handling |
| *(press Enter with no input)* | Error message or re-prompt | **"Invalid input" error** | Empty input not gracefully handled |
| `7/2` | `3.5` | **`3`** | Uses integer division (`//` instead of `/`) |
| `2 + 3` | `5` | **"Invalid input" error** | Spaces around operators not handled |
| `2+3*4` | `14` | **`20`** | Evaluates left-to-right, ignores precedence |
| `-5+3` | `-2` | **"Invalid input" error** | Can't parse negative numbers |

### State bleed — try this sequence

```
> 5+3
8
> 2+2
4
```

The results here look correct, but internally the calculator stores the previous result in a global variable that isn't reset. This can cause unexpected behavior in more complex scenarios where the global `result` variable leaks across operations.

---

## What to Look For

This calculator has **7 intentional bugs** and **3 code smells**:

### Bugs

| # | Bug | Where in Code | Impact |
|---|-----|---------------|--------|
| 1 | No division-by-zero handling | `divide()` in `calculator.py` | Unhandled `ZeroDivisionError` crash |
| 2 | Empty input crashes | `evaluate()` in `calculator.py` | `ValueError` on empty string |
| 3 | Integer division truncation | `divide()` uses `//` instead of `/` | Decimal results lost |
| 4 | Whitespace not handled | `evaluate()` uses `.isdigit()` check | Spaces in expressions rejected |
| 5 | Wrong operator precedence | `evaluate()` processes left-to-right | `2+3*4` = 20 instead of 14 |
| 6 | Negative numbers unsupported | `evaluate()` treats `-` as operator | Leading minus causes parse error |
| 7 | State bleed | Global `result` variable in `calculator.py` | Previous result leaks between calculations |

### Code Smells

- **Duplicated operation handlers** — `add()`, `subtract()`, `multiply()`, `divide()` all follow the same pattern and could be consolidated
- **No type hints or docstrings** — none of the functions have annotations or documentation
- **Unhelpful error messages** — every error just shows "Invalid input" with no explanation of what went wrong

---

## Running Tests

```bash
pytest tests/ -v
```

**Expected result: 4 tests fail, 7 pass.** The failing tests demonstrate the intentional bugs:

```
FAILED tests/test_calculator.py::test_divide_integer       — 7/2 returns 3 instead of 3.5
FAILED tests/test_calculator.py::test_operator_precedence   — 2+3*4 returns 20 instead of 14
FAILED tests/test_calculator.py::test_evaluate_with_spaces  — "2 + 3" raises ValueError
FAILED tests/test_calculator.py::test_negative_number       — "-5+3" raises ValueError
```

---

## GitHub Issues

This repo has **20 GitHub Issues** that cover the bugs, feature requests, and cleanup tasks. They are categorized as:

| Category | Count | Examples |
|----------|-------|---------|
| Automatable bugs | 4 | Division by zero, empty input, integer division, whitespace |
| Engineer-review bugs | 3 | Operator precedence, negative numbers, state bleed |
| Needs-more-info bugs | 2 | Vague reports with missing reproduction steps |
| Feature requests | 4 | Parentheses, history, math functions, variables |
| Cleanup tasks | 4 | Refactoring, type hints, docstrings, error messages |
| Questions | 2 | Decimal support, Python version compatibility |

To recreate the issues (if starting from scratch):

```bash
export GITHUB_TOKEN=your_token_here
python scripts/create_issues.py
```

---

## Project Structure

```
calculator-demo/
├── src/
│   ├── __init__.py
│   ├── main.py             # CLI entry point — REPL loop
│   └── calculator.py       # Calculation logic (contains the intentional bugs)
├── tests/
│   └── test_calculator.py  # Unit tests (4 intentionally failing)
├── scripts/
│   └── create_issues.py    # Script to create 20 GitHub Issues
├── .gitignore
├── requirements.txt        # pytest
└── README.md
```

---

## Using with the Ticket Automation Tool

This repo is the default target for the [ticket-automation-tool](https://github.com/papatel5698/ticket-automation-tool). To analyze the issues in this repo:

```bash
# From the ticket-automation-tool directory
export GITHUB_REPO=papatel5698/calculator-demo
ticket-analyzer analyze --stale-days 0
```

The `--stale-days 0` flag treats all issues as stale so they are included in the analysis, even if they were just created.
