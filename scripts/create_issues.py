#!/usr/bin/env python3
"""Script to create 7 GitHub Issues on the calculator-demo repository."""

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
            "**Steps to reproduce:**\n"
            "1. Run the calculator\n"
            "2. Type `10/0`\n"
            "3. Program crashes with ZeroDivisionError traceback\n\n"
            "**Expected behavior:** Show a user-friendly error message like "
            "\"Error: Division by zero\" and re-prompt."
        ),
        "labels": ["bug"],
    },
    # 2 - Automatable bug
    {
        "title": "Empty input crashes the program",
        "body": (
            "Pressing Enter without typing anything crashes the program with an "
            "IndexError.\n\n"
            "**Steps to reproduce:**\n"
            "1. Run the calculator\n"
            "2. Press Enter without typing anything\n"
            "3. Program crashes\n\n"
            "**Expected behavior:** Show an error message or re-prompt the user."
        ),
        "labels": ["bug"],
    },
    # 3 - Automatable bug
    {
        "title": "Division returns integer instead of decimal \u2014 7/2 gives 3",
        "body": (
            "The division operation truncates decimal results. `7/2` returns `3` "
            "instead of `3.5`. `10/3` returns `3` instead of `3.333...`.\n\n"
            "It seems to be using integer division (`//`) instead of true division (`/`)."
        ),
        "labels": ["bug"],
    },
    # 4 - Automatable bug
    {
        "title": "Whitespace in expressions causes parse error",
        "body": (
            "Entering `2 + 3` (with spaces around the operator) causes a parse "
            "error. Only `2+3` (no spaces) works.\n\n"
            "Users naturally type spaces around operators, so this should be handled."
        ),
        "labels": ["bug"],
    },
    # 5 - Engineer review bug (complex fix)
    {
        "title": "Operator precedence is wrong \u2014 2+3*4 returns 20 instead of 14",
        "body": (
            "The calculator does not respect standard math operator precedence. "
            "Multiplication and division should be evaluated before addition and "
            "subtraction.\n\n"
            "**Example:**\n"
            "- `2+3*4` should return `14` but returns `20`\n"
            "- `10-2*3` should return `4` but returns `24`\n\n"
            "It seems to evaluate strictly left to right. Fixing this requires "
            "reworking the expression parser to handle precedence correctly."
        ),
        "labels": ["bug"],
    },
    # 6 - Engineer review feature (complex new functionality)
    {
        "title": "Add support for parentheses in expressions",
        "body": (
            "The calculator should support parentheses to let users control "
            "evaluation order.\n\n"
            "**Examples:**\n"
            "- `(2+3)*4` should return `20`\n"
            "- `10/(2+3)` should return `2`\n\n"
            "This would require updating the expression parser to handle nested "
            "groupings and recursive evaluation."
        ),
        "labels": ["enhancement"],
    },
    # 7 - Needs more info feature (vague request)
    {
        "title": "Add history feature",
        "body": (
            "It would be nice to have some kind of history feature. Maybe like "
            "pressing the up arrow or something?"
        ),
        "labels": ["enhancement"],
    },
]


def create_label(session, repo, label_name):
    colors = {
        "bug": "d73a4a",
        "enhancement": "a2eeef",
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
    for label in ["bug", "enhancement"]:
        create_label(session, REPO, label)

    print(f"\nCreating {len(ISSUES)} issues on {REPO}...")
    for i, issue in enumerate(ISSUES, 1):
        print(f"\n[{i}/{len(ISSUES)}]")
        create_issue(session, REPO, issue)
        time.sleep(1)  # Rate limiting

    print("\nDone! All issues created.")


if __name__ == "__main__":
    main()
