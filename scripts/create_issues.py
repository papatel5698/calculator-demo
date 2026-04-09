#!/usr/bin/env python3
"""Script to create 20 GitHub Issues on the calculator-demo repository."""

import os
import requests
import time

GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN")
REPO = os.environ.get("GITHUB_REPO", "papatel5698/calculator-demo")
API_BASE = "https://api.github.com"

ISSUES = [
    # 1 - Automatable bug
    {
        "title": "Division by zero crashes the program",
        "body": (
            "When I enter `10/0`, the program crashes with an unhandled exception "
            "instead of showing an error message.\n\n"
            "Steps to reproduce:\n"
            "1. Run the calculator\n"
            "2. Type `10/0`\n"
            "3. Program crashes with ZeroDivisionError traceback."
        ),
        "labels": ["bug"],
    },
    # 2 - Automatable bug
    {
        "title": "Empty input crashes the program",
        "body": (
            "Pressing Enter without typing anything crashes the program with an "
            "IndexError. Expected: show an error message or re-prompt."
        ),
        "labels": ["bug"],
    },
    # 3 - Automatable bug
    {
        "title": "Division returns integer instead of decimal \u2014 7/2 gives 3",
        "body": (
            "The division operation truncates decimal results. `7/2` returns `3` "
            "instead of `3.5`. `10/3` returns `3` instead of `3.333...`. It seems "
            "to be using integer division."
        ),
        "labels": ["bug"],
    },
    # 4 - Automatable bug
    {
        "title": "Whitespace in expressions causes parse error",
        "body": (
            "Entering `2 + 3` (with spaces around the operator) causes a parse "
            "error. Only `2+3` (no spaces) works. Users naturally type spaces "
            "around operators."
        ),
        "labels": ["bug"],
    },
    # 5 - Engineer review bug
    {
        "title": "Operator precedence is wrong \u2014 2+3*4 returns 20 instead of 14",
        "body": (
            "The calculator doesn't respect standard math operator precedence. "
            "Multiplication and division should be evaluated before addition and "
            "subtraction.\n\n"
            "Example: `2+3*4` should return `14` but returns `20`. It seems to "
            "evaluate left to right."
        ),
        "labels": ["bug"],
    },
    # 6 - Engineer review bug
    {
        "title": "Negative number input causes parse error",
        "body": (
            "Entering an expression starting with a negative number like `-5+3` "
            "causes a crash. The parser doesn't handle the leading minus sign. "
            "Expected result: `-2`. Actual: ParseError."
        ),
        "labels": ["bug"],
    },
    # 7 - Engineer review bug
    {
        "title": "Repeated calculations show previous result",
        "body": (
            "After calculating `5+3=8`, if I then calculate `2+2`, sometimes the "
            "result includes the previous answer. The calculator seems to carry "
            "state between calculations."
        ),
        "labels": ["bug"],
    },
    # 8 - Needs more info bug
    {
        "title": "Calculator gives wrong answer for large numbers",
        "body": (
            "Sometimes when I use really big numbers the answer is wrong. "
            "I don't remember exactly what I typed but it was something like a "
            "million times a million."
        ),
        "labels": ["bug"],
    },
    # 9 - Needs more info bug
    {
        "title": "It crashed yesterday",
        "body": (
            "The calculator crashed when I was using it yesterday. Not sure what "
            "I typed. Can someone look into this?"
        ),
        "labels": ["bug"],
    },
    # 10 - Feature request
    {
        "title": "Add support for parentheses in expressions",
        "body": (
            "It would be great if the calculator could handle expressions with "
            "parentheses like `(2+3)*4`. Currently this causes a parse error."
        ),
        "labels": ["enhancement"],
    },
    # 11 - Feature request
    {
        "title": "Add calculation history feature",
        "body": (
            "I'd like to be able to see my previous calculations. Maybe an "
            "'history' command that shows the last 10 calculations and their "
            "results."
        ),
        "labels": ["enhancement"],
    },
    # 12 - Feature request
    {
        "title": "Support for mathematical functions (sqrt, pow, etc.)",
        "body": (
            "The calculator should support common math functions like:\n"
            "- `sqrt(16)` = 4\n"
            "- `pow(2, 8)` = 256\n"
            "- `abs(-5)` = 5\n"
            "- `round(3.7)` = 4"
        ),
        "labels": ["enhancement"],
    },
    # 13 - Feature request
    {
        "title": "Add variable storage (let x = 5)",
        "body": (
            "It would be useful to store values in variables and use them in "
            "calculations. For example:\n"
            "```\n"
            "> let x = 5\n"
            "> x + 3\n"
            "8\n"
            "```"
        ),
        "labels": ["enhancement"],
    },
    # 14 - Cleanup
    {
        "title": "Refactor duplicated operation handler functions",
        "body": (
            "The `add()`, `subtract()`, `multiply()`, and `divide()` functions "
            "all follow the same pattern. They could be consolidated into a "
            "single function that takes an operator parameter, or use a "
            "dictionary mapping operators to Python's built-in operations."
        ),
        "labels": ["cleanup"],
    },
    # 15 - Cleanup
    {
        "title": "Add type hints throughout the codebase",
        "body": (
            "The codebase has no type hints. Adding proper type annotations would "
            "improve readability, enable better IDE support, and allow for static "
            "type checking with mypy."
        ),
        "labels": ["cleanup"],
    },
    # 16 - Cleanup
    {
        "title": "Add docstrings to all functions",
        "body": (
            "None of the functions have docstrings. Adding docstrings would help "
            "developers understand what each function does, what parameters it "
            "expects, and what it returns."
        ),
        "labels": ["cleanup"],
    },
    # 17 - Cleanup
    {
        "title": "Improve error messages to be more helpful",
        "body": (
            "Currently the calculator just shows 'Invalid input' for any error. "
            "The error messages should be more specific:\n"
            "- 'Division by zero is not allowed'\n"
            "- 'Could not parse expression: unexpected character at position X'\n"
            "- 'Empty input: please enter an expression'"
        ),
        "labels": ["cleanup"],
    },
    # 18 - Needs more info
    {
        "title": "Does the calculator support decimal input?",
        "body": (
            "I haven't tried it yet, but can I enter decimal numbers like `3.14 * 2`? "
            "If not, this should be added."
        ),
        "labels": ["question"],
    },
    # 19 - Needs more info
    {
        "title": "What Python versions are supported?",
        "body": (
            "The README doesn't mention which Python versions are supported. "
            "I'm using Python 3.8 \u2014 will this work? Also, are there any "
            "plans to add a pyproject.toml?"
        ),
        "labels": ["question"],
    },
    # 20 - Feature request
    {
        "title": "Fix typo in welcome message",
        "body": (
            "When starting the calculator, the welcome message might have a typo. "
            "Can someone verify the welcome message is spelled correctly? "
            "It should say 'Welcome to Calculator'."
        ),
        "labels": ["bug"],
    },
]


def create_label(session, repo, label_name):
    colors = {
        "bug": "d73a4a",
        "enhancement": "a2eeef",
        "cleanup": "0e8a16",
        "question": "d876e3",
    }
    url = f"{API_BASE}/repos/{repo}/labels"
    data = {
        "name": label_name,
        "color": colors.get(label_name, "ededed"),
    }
    resp = session.post(url, json=data)
    if resp.status_code == 201:
        print(f"  Created label: {label_name}")
    elif resp.status_code == 422:
        print(f"  Label already exists: {label_name}")
    else:
        print(f"  Failed to create label {label_name}: {resp.status_code}")


def create_issue(session, repo, issue):
    url = f"{API_BASE}/repos/{repo}/issues"
    data = {
        "title": issue["title"],
        "body": issue["body"],
        "labels": issue["labels"],
    }
    resp = session.post(url, json=data)
    if resp.status_code == 201:
        number = resp.json()["number"]
        print(f"  Created issue #{number}: {issue['title']}")
        return number
    else:
        print(f"  Failed to create issue: {resp.status_code} - {resp.text}")
        return None


def main():
    if not GITHUB_TOKEN:
        print("Error: GITHUB_TOKEN environment variable is required.")
        print("Export your GitHub personal access token:")
        print("  export GITHUB_TOKEN=ghp_your_token_here")
        return

    session = requests.Session()
    session.headers.update({
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json",
    })

    print(f"Creating labels on {REPO}...")
    for label in ["bug", "enhancement", "cleanup", "question"]:
        create_label(session, REPO, label)

    print(f"\nCreating {len(ISSUES)} issues on {REPO}...")
    for i, issue in enumerate(ISSUES, 1):
        print(f"\n[{i}/{len(ISSUES)}]")
        create_issue(session, REPO, issue)
        time.sleep(1)  # Rate limiting

    print("\nDone! All issues created.")


if __name__ == "__main__":
    main()
