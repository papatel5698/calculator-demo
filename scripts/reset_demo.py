#!/usr/bin/env python3
"""Reset calculator-demo to its demo starting state.

Two parts, both on by default:

* Code: make `src/` and `tests/` match the `demo-baseline` tag exactly (restoring
  the intentional bugs) and commit that on top of `main`. History is kept.
* Issues: close every open issue with a comment, then open a fresh copy of each
  issue in `demo/issues.json`.

Usage:
    python scripts/reset_demo.py --dry-run          # show what would change
    python scripts/reset_demo.py --push             # reset code and issues, push main
    python scripts/reset_demo.py --code-only        # no GitHub token needed
    python scripts/reset_demo.py --issues-only

Needs GITHUB_TOKEN (issues: write) for the issue reset.
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import urllib.error
import urllib.request
from dataclasses import dataclass
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_ISSUE_SET = REPO_ROOT / "demo" / "issues.json"
DEFAULT_REPO = "papatel5698/calculator-demo"
BASELINE_REF = "demo-baseline"
BASELINE_PATHS = ["src", "tests"]
CLOSE_COMMENT = (
    "Closed by the demo reset (`scripts/reset_demo.py`). "
    "A fresh copy of the standard issue set has been opened."
)


class ResetError(Exception):
    """The reset can't safely go ahead."""


class IssueSetError(ResetError):
    """demo/issues.json is missing or malformed."""


class GitHubError(ResetError):
    """A GitHub API call returned an error status."""

    def __init__(self, status: int, message: str):
        super().__init__(message)
        self.status = status


# --- issue set ---------------------------------------------------------------


@dataclass
class IssueSet:
    labels: dict[str, str]
    issues: list[dict]


def load_issue_set(path: Path) -> IssueSet:
    try:
        data = json.loads(Path(path).read_text())
    except (OSError, json.JSONDecodeError) as error:
        raise IssueSetError(f"Can't read issue set {path}: {error}") from None
    labels = data.get("labels", {})
    issues = data.get("issues", [])
    seen = set()
    for i, issue in enumerate(issues, 1):
        missing = [k for k in ("title", "body", "labels") if k not in issue]
        if missing:
            raise IssueSetError(f"Issue {i} is missing {', '.join(missing)}")
        if issue["title"] in seen:
            raise IssueSetError(f"Duplicate title: {issue['title']!r}")
        seen.add(issue["title"])
        undeclared = [label for label in issue["labels"] if label not in labels]
        if undeclared:
            raise IssueSetError(
                f"Issue {issue['title']!r} uses undeclared labels: {', '.join(undeclared)}"
            )
    return IssueSet(labels=labels, issues=issues)


# --- GitHub ------------------------------------------------------------------


class GitHubClient:
    """The four GitHub REST calls the reset needs. Standard library only."""

    API = "https://api.github.com"

    def __init__(self, repo: str, token: str):
        self.repo = repo
        self.token = token

    def _request(self, method: str, path: str, payload: dict | None = None):
        data = json.dumps(payload).encode() if payload is not None else None
        request = urllib.request.Request(
            f"{self.API}{path}",
            data=data,
            method=method,
            headers={
                "Authorization": f"Bearer {self.token}",
                "Accept": "application/vnd.github+json",
                "X-GitHub-Api-Version": "2022-11-28",
                "Content-Type": "application/json",
            },
        )
        try:
            with urllib.request.urlopen(request, timeout=30) as response:
                body = response.read()
        except urllib.error.HTTPError as error:
            detail = error.read()[:200].decode(errors="replace") if error.fp else error.reason
            raise GitHubError(error.code, f"GitHub {method} {path} failed: {error.code} {detail}") from None
        except urllib.error.URLError as error:
            raise ResetError(f"GitHub {method} {path} failed: {error.reason}") from None
        return json.loads(body) if body else None

    def list_open_issues(self) -> list[dict]:
        issues, page = [], 1
        while True:
            batch = self._request(
                "GET", f"/repos/{self.repo}/issues?state=open&per_page=100&page={page}"
            )
            # The issues endpoint also returns pull requests; the reset leaves those alone.
            issues.extend(i for i in batch if "pull_request" not in i)
            if len(batch) < 100:
                return issues
            page += 1

    def close_issue(self, number: int, comment: str) -> None:
        # Close first: if the comment then fails, a rerun won't see the issue and comment twice.
        self._request(
            "PATCH",
            f"/repos/{self.repo}/issues/{number}",
            {"state": "closed", "state_reason": "not_planned"},
        )
        self._request("POST", f"/repos/{self.repo}/issues/{number}/comments", {"body": comment})

    def ensure_label(self, name: str, color: str) -> None:
        try:
            self._request("POST", f"/repos/{self.repo}/labels", {"name": name, "color": color})
        except GitHubError as error:
            if error.status != 422:  # 422: label already exists
                raise

    def create_issue(self, title: str, body: str, labels: list[str]) -> int:
        issue = self._request(
            "POST", f"/repos/{self.repo}/issues", {"title": title, "body": body, "labels": labels}
        )
        return issue["number"]


def reset_issues(github, issue_set: IssueSet, dry_run: bool) -> list[str]:
    """Open the standard set, then close every issue that was open before.

    Opening first means a failure partway through leaves duplicates (fixed by
    rerunning), never a repo with no open issues.
    """
    old_issues = github.list_open_issues()
    if dry_run:
        return [f"[dry run] would open: {i['title']}" for i in issue_set.issues] + [
            f"[dry run] would close #{i['number']}: {i['title']}" for i in old_issues
        ]
    lines = []
    for name, color in issue_set.labels.items():
        github.ensure_label(name, color)
    for issue in issue_set.issues:
        number = github.create_issue(issue["title"], issue["body"], issue["labels"])
        lines.append(f"opened #{number}: {issue['title']}")
    for issue in old_issues:
        github.close_issue(issue["number"], CLOSE_COMMENT)
        lines.append(f"closed #{issue['number']}: {issue['title']}")
    return lines


# --- code --------------------------------------------------------------------


def _git(repo_dir: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", *args], cwd=repo_dir, capture_output=True, text=True
    )
    if result.returncode != 0:
        raise ResetError(f"git {' '.join(args)} failed: {result.stderr.strip()}")
    return result.stdout


def reset_code(repo_dir: Path, ref: str, paths: list[str], dry_run: bool) -> list[str]:
    """Make `paths` match `ref` exactly and commit the result on main."""
    try:
        _git(repo_dir, "rev-parse", "--verify", "--quiet", f"{ref}^{{commit}}")
    except ResetError:
        raise ResetError(f"Baseline ref {ref!r} not found. Fetch tags: git fetch --tags") from None

    _check_safe_to_commit(repo_dir)

    changes = _git(
        repo_dir, "diff", "--no-renames", "--name-status", ref, "HEAD", "--", *paths
    ).splitlines()
    if not changes:
        return [f"Code already matches {ref}."]
    lines = []
    for line in changes:
        # Diffing baseline -> HEAD: "A" means a file the baseline doesn't have.
        status, path = line.split(maxsplit=1)
        verb = ("remove", "removed") if status == "A" else ("restore", "restored")
        lines.append(f"[dry run] would {verb[0]} {path}" if dry_run else f"{verb[1]} {path}")
    if dry_run:
        return lines

    _git(repo_dir, "rm", "-r", "-q", "--ignore-unmatch", "--", *paths)
    _git(repo_dir, "checkout", ref, "--", *paths)
    _git(repo_dir, "commit", "-q", "-m", f"Reset demo code to {ref}")
    return lines


def _check_safe_to_commit(repo_dir: Path) -> None:
    """The reset commits on main, so main must be clean and up to date."""
    branch = _git(repo_dir, "rev-parse", "--abbrev-ref", "HEAD").strip()
    if branch != "main":
        raise ResetError(f"Run the code reset on main (currently on {branch!r}).")
    if _git(repo_dir, "status", "--porcelain"):
        raise ResetError("Working tree has uncommitted changes. Commit or stash them first.")
    if "origin" in _git(repo_dir, "remote").split():
        _git(repo_dir, "fetch", "-q", "origin", "main")
        if _git(repo_dir, "rev-parse", "HEAD") != _git(repo_dir, "rev-parse", "FETCH_HEAD"):
            raise ResetError("Local main doesn't match origin/main. Run `git pull` first.")


def push(repo_dir: Path) -> None:
    _git(repo_dir, "push", "origin", "main")


# --- command line ------------------------------------------------------------


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Reset calculator-demo to its demo state.")
    parser.add_argument("--repo", default=os.environ.get("GITHUB_REPO", DEFAULT_REPO))
    parser.add_argument("--ref", default=BASELINE_REF, help="git ref holding the buggy code")
    parser.add_argument("--issue-set", type=Path, default=DEFAULT_ISSUE_SET)
    parser.add_argument("--dry-run", action="store_true", help="show changes, make none")
    parser.add_argument("--push", action="store_true", help="push the reset commit to origin/main")
    scope = parser.add_mutually_exclusive_group()
    scope.add_argument("--code-only", action="store_true")
    scope.add_argument("--issues-only", action="store_true")
    args = parser.parse_args(argv)
    if args.push and args.issues_only:
        parser.error("--push only applies to the code reset; drop it or --issues-only")

    do_code, do_issues = not args.issues_only, not args.code_only
    token = os.environ.get("GITHUB_TOKEN")
    if do_issues and not token:
        print("Error: GITHUB_TOKEN is required to reset issues.", file=sys.stderr)
        return 1

    try:
        # Validate everything before changing anything.
        issue_set = load_issue_set(args.issue_set) if do_issues else None
        if do_code:
            lines = reset_code(REPO_ROOT, ref=args.ref, paths=BASELINE_PATHS, dry_run=args.dry_run)
            print("\n".join(lines))
            if args.push and not args.dry_run:
                push(REPO_ROOT)
                print("Pushed main.")
        if do_issues:
            github = GitHubClient(args.repo, token)
            print("\n".join(reset_issues(github, issue_set, dry_run=args.dry_run)))
    except ResetError as error:
        print(f"Error: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":  # pragma: no cover - entry point; main() is tested directly
    sys.exit(main())
