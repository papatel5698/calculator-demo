"""Tests for scripts/reset_demo.py. No network: GitHub is faked, git runs in temp repos."""

import io
import json
import subprocess
from pathlib import Path
from unittest.mock import patch

import pytest

from scripts import reset_demo
from scripts.reset_demo import (
    GitHubClient,
    IssueSetError,
    ResetError,
    load_issue_set,
    reset_code,
    reset_issues,
)

REPO_ROOT = Path(__file__).resolve().parents[2]


# --- issue set ---------------------------------------------------------------


def write_issue_set(tmp_path, data):
    path = tmp_path / "issues.json"
    path.write_text(json.dumps(data))
    return path


def test_load_issue_set_reads_labels_and_issues(tmp_path):
    path = write_issue_set(tmp_path, {
        "labels": {"bug": "d73a4a"},
        "issues": [{"title": "A", "body": "a", "labels": ["bug"]}],
    })
    issue_set = load_issue_set(path)
    assert issue_set.labels == {"bug": "d73a4a"}
    assert issue_set.issues == [{"title": "A", "body": "a", "labels": ["bug"]}]


def test_load_issue_set_rejects_duplicate_titles(tmp_path):
    # The answer key matches issues by title, so titles must be unique.
    path = write_issue_set(tmp_path, {
        "labels": {},
        "issues": [
            {"title": "Same", "body": "a", "labels": []},
            {"title": "Same", "body": "b", "labels": []},
        ],
    })
    with pytest.raises(IssueSetError, match="Duplicate title"):
        load_issue_set(path)


def test_load_issue_set_rejects_missing_fields(tmp_path):
    path = write_issue_set(tmp_path, {"labels": {}, "issues": [{"title": "No body"}]})
    with pytest.raises(IssueSetError, match="missing"):
        load_issue_set(path)


def test_load_issue_set_rejects_undeclared_labels(tmp_path):
    path = write_issue_set(tmp_path, {
        "labels": {"bug": "d73a4a"},
        "issues": [{"title": "A", "body": "a", "labels": ["question"]}],
    })
    with pytest.raises(IssueSetError, match="question"):
        load_issue_set(path)


def test_repo_issue_set_is_valid():
    issue_set = load_issue_set(REPO_ROOT / "demo" / "issues.json")
    assert len(issue_set.issues) >= 7


# --- issue reset -------------------------------------------------------------


class FakeGitHub:
    def __init__(self, open_issues):
        self.open_issues = list(open_issues)
        self.closed = []
        self.created = []
        self.labels = []

    def list_open_issues(self):
        return list(self.open_issues)

    def close_issue(self, number, comment):
        self.closed.append((number, comment))

    def ensure_label(self, name, color):
        self.labels.append((name, color))

    def create_issue(self, title, body, labels):
        number = 100 + len(self.created)
        self.created.append({"title": title, "body": body, "labels": labels})
        return number


def make_issue_set(*titles):
    return reset_demo.IssueSet(
        labels={"bug": "d73a4a"},
        issues=[{"title": t, "body": f"body of {t}", "labels": ["bug"]} for t in titles],
    )


def test_reset_issues_closes_every_open_issue_then_recreates_the_set():
    github = FakeGitHub([{"number": 5, "title": "Old"}, {"number": 9, "title": "A"}])
    reset_issues(github, make_issue_set("A", "B"), dry_run=False)

    assert [n for n, _ in github.closed] == [5, 9]
    assert [i["title"] for i in github.created] == ["A", "B"]
    assert github.created[0] == {"title": "A", "body": "body of A", "labels": ["bug"]}
    assert github.labels == [("bug", "d73a4a")]


def test_reset_issues_comments_when_closing():
    github = FakeGitHub([{"number": 5, "title": "Old"}])
    reset_issues(github, make_issue_set("A"), dry_run=False)
    assert "demo reset" in github.closed[0][1].lower()


def test_reset_issues_dry_run_changes_nothing():
    github = FakeGitHub([{"number": 5, "title": "Old"}])
    lines = reset_issues(github, make_issue_set("A"), dry_run=True)

    assert github.closed == [] and github.created == [] and github.labels == []
    text = "\n".join(lines)
    assert "#5" in text and "A" in text


# --- GitHub client -----------------------------------------------------------


class FakeResponse(io.BytesIO):
    def __init__(self, payload):
        super().__init__(json.dumps(payload).encode())

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False


def test_client_lists_open_issues_across_pages_and_skips_pull_requests():
    page1 = [{"number": i, "title": f"t{i}"} for i in range(1, 101)]
    page1[0]["pull_request"] = {"url": "x"}
    page2 = [{"number": 101, "title": "t101"}]
    responses = [FakeResponse(page1), FakeResponse(page2)]

    with patch("scripts.reset_demo.urllib.request.urlopen", side_effect=responses) as urlopen:
        issues = GitHubClient("owner/repo", "tok").list_open_issues()

    numbers = [i["number"] for i in issues]
    assert numbers == list(range(2, 102))
    first_request = urlopen.call_args_list[0].args[0]
    assert "state=open" in first_request.full_url and "page=1" in first_request.full_url
    assert first_request.get_header("Authorization") == "Bearer tok"


def test_client_close_issue_comments_then_closes_as_not_planned():
    with patch("scripts.reset_demo.urllib.request.urlopen",
               side_effect=[FakeResponse({}), FakeResponse({})]) as urlopen:
        GitHubClient("owner/repo", "tok").close_issue(7, "bye")

    comment, close = [c.args[0] for c in urlopen.call_args_list]
    assert comment.full_url.endswith("/repos/owner/repo/issues/7/comments")
    assert json.loads(comment.data) == {"body": "bye"}
    assert close.get_method() == "PATCH"
    assert json.loads(close.data) == {"state": "closed", "state_reason": "not_planned"}


def test_client_create_issue_returns_number():
    with patch("scripts.reset_demo.urllib.request.urlopen",
               return_value=FakeResponse({"number": 42})) as urlopen:
        number = GitHubClient("owner/repo", "tok").create_issue("T", "B", ["bug"])

    assert number == 42
    request = urlopen.call_args.args[0]
    assert json.loads(request.data) == {"title": "T", "body": "B", "labels": ["bug"]}


def test_client_ensure_label_ignores_already_exists():
    error = reset_demo.urllib.error.HTTPError("u", 422, "exists", {}, None)
    with patch("scripts.reset_demo.urllib.request.urlopen", side_effect=error):
        GitHubClient("owner/repo", "tok").ensure_label("bug", "d73a4a")  # no raise


def test_client_ensure_label_raises_other_errors():
    error = reset_demo.urllib.error.HTTPError("u", 403, "forbidden", {}, None)
    with patch("scripts.reset_demo.urllib.request.urlopen", side_effect=error):
        with pytest.raises(reset_demo.urllib.error.HTTPError):
            GitHubClient("owner/repo", "tok").ensure_label("bug", "d73a4a")


# --- code reset --------------------------------------------------------------


def git(repo, *args):
    return subprocess.run(
        ["git", "-c", "user.name=t", "-c", "user.email=t@example.com", *args],
        cwd=repo, check=True, capture_output=True, text=True,
    ).stdout


@pytest.fixture
def demo_repo(tmp_path):
    """A repo whose `demo-baseline` tag has the bug, and whose main has since fixed it."""
    repo = tmp_path / "repo"
    repo.mkdir()
    git(repo, "init", "-q", "-b", "main")
    (repo / "src").mkdir()
    (repo / "tests").mkdir()
    (repo / "src" / "calc.py").write_text("result = a // b\n")
    (repo / "tests" / "test_calc.py").write_text("# baseline tests\n")
    (repo / "README.md").write_text("readme v1\n")
    git(repo, "add", ".")
    git(repo, "commit", "-q", "-m", "baseline")
    git(repo, "tag", "demo-baseline")

    (repo / "src" / "calc.py").write_text("result = a / b\n")
    (repo / "src" / "helper.py").write_text("added by a fix\n")
    (repo / "tests" / "test_calc.py").write_text("# tests for the fix\n")
    (repo / "README.md").write_text("readme v2\n")
    git(repo, "add", ".")
    git(repo, "commit", "-q", "-m", "fix the bug")
    return repo


def test_reset_code_restores_baseline_paths_and_commits(demo_repo):
    with patch.dict("os.environ", {"GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t@e.com",
                                   "GIT_COMMITTER_NAME": "t", "GIT_COMMITTER_EMAIL": "t@e.com"}):
        lines = reset_code(demo_repo, ref="demo-baseline", paths=["src", "tests"], dry_run=False)

    assert (demo_repo / "src" / "calc.py").read_text() == "result = a // b\n"
    assert not (demo_repo / "src" / "helper.py").exists()
    assert (demo_repo / "tests" / "test_calc.py").read_text() == "# baseline tests\n"
    # Paths outside the baseline set are left alone.
    assert (demo_repo / "README.md").read_text() == "readme v2\n"
    # History is kept: a new commit on top, not a rewrite.
    log = git(demo_repo, "log", "--format=%s").splitlines()
    assert log[1:] == ["fix the bug", "baseline"]
    assert "demo-baseline" in log[0]
    assert git(demo_repo, "status", "--porcelain") == ""
    assert any("src/helper.py" in line for line in lines)


def test_reset_code_does_nothing_when_already_at_baseline(demo_repo):
    git(demo_repo, "checkout", "-q", "demo-baseline", "--", "src", "tests")
    git(demo_repo, "rm", "-q", "src/helper.py")
    git(demo_repo, "commit", "-q", "-m", "manual reset")

    lines = reset_code(demo_repo, ref="demo-baseline", paths=["src", "tests"], dry_run=False)

    assert git(demo_repo, "log", "-1", "--format=%s").strip() == "manual reset"
    assert any("already" in line.lower() for line in lines)


def test_reset_code_dry_run_lists_changes_without_touching_files(demo_repo):
    lines = reset_code(demo_repo, ref="demo-baseline", paths=["src", "tests"], dry_run=True)

    assert (demo_repo / "src" / "calc.py").read_text() == "result = a / b\n"
    assert git(demo_repo, "status", "--porcelain") == ""
    assert "[dry run] would restore src/calc.py" in lines
    assert "[dry run] would remove src/helper.py" in lines


def test_reset_code_refuses_a_dirty_tree(demo_repo):
    (demo_repo / "src" / "calc.py").write_text("uncommitted\n")
    with pytest.raises(ResetError, match="uncommitted"):
        reset_code(demo_repo, ref="demo-baseline", paths=["src", "tests"], dry_run=False)


def test_reset_code_refuses_a_branch_other_than_main(demo_repo):
    git(demo_repo, "checkout", "-q", "-b", "feature")
    with pytest.raises(ResetError, match="main"):
        reset_code(demo_repo, ref="demo-baseline", paths=["src", "tests"], dry_run=False)


def test_reset_code_reports_a_missing_baseline_ref(demo_repo):
    with pytest.raises(ResetError, match="no-such-tag"):
        reset_code(demo_repo, ref="no-such-tag", paths=["src", "tests"], dry_run=True)


# --- command line ------------------------------------------------------------


def test_main_requires_a_token_for_issue_reset(monkeypatch, capsys):
    monkeypatch.delenv("GITHUB_TOKEN", raising=False)
    assert reset_demo.main(["--issues-only", "--repo", "o/r"]) == 1
    assert "GITHUB_TOKEN" in capsys.readouterr().err


def test_main_runs_code_then_issues_and_pushes(monkeypatch):
    calls = []
    monkeypatch.setenv("GITHUB_TOKEN", "tok")
    monkeypatch.setattr(reset_demo, "reset_code", lambda *a, **k: calls.append(("code", k)) or [])
    monkeypatch.setattr(reset_demo, "push", lambda repo_dir: calls.append(("push", None)))
    monkeypatch.setattr(reset_demo, "reset_issues", lambda *a, **k: calls.append(("issues", k)) or [])

    assert reset_demo.main(["--repo", "o/r", "--push"]) == 0
    assert [c[0] for c in calls] == ["code", "push", "issues"]
    assert calls[0][1]["dry_run"] is False


def test_main_dry_run_never_pushes(monkeypatch):
    calls = []
    monkeypatch.setenv("GITHUB_TOKEN", "tok")
    monkeypatch.setattr(reset_demo, "reset_code", lambda *a, **k: calls.append("code") or [])
    monkeypatch.setattr(reset_demo, "push", lambda repo_dir: calls.append("push"))
    monkeypatch.setattr(reset_demo, "reset_issues", lambda *a, **k: calls.append("issues") or [])

    assert reset_demo.main(["--repo", "o/r", "--push", "--dry-run"]) == 0
    assert calls == ["code", "issues"]


def test_main_code_only_skips_issues_and_needs_no_token(monkeypatch):
    calls = []
    monkeypatch.delenv("GITHUB_TOKEN", raising=False)
    monkeypatch.setattr(reset_demo, "reset_code", lambda *a, **k: calls.append("code") or [])
    monkeypatch.setattr(reset_demo, "reset_issues", lambda *a, **k: calls.append("issues") or [])

    assert reset_demo.main(["--code-only"]) == 0
    assert calls == ["code"]


def test_main_reports_reset_errors(monkeypatch, capsys):
    def boom(*a, **k):
        raise ResetError("tree has uncommitted changes")
    monkeypatch.setattr(reset_demo, "reset_code", boom)

    assert reset_demo.main(["--code-only"]) == 1
    assert "uncommitted" in capsys.readouterr().err


def test_push_sends_main_to_origin(demo_repo, tmp_path):
    remote = tmp_path / "remote.git"
    git(tmp_path, "init", "-q", "--bare", str(remote))
    git(demo_repo, "remote", "add", "origin", str(remote))

    reset_demo.push(demo_repo)

    assert git(remote, "log", "-1", "--format=%s", "main").strip() == "fix the bug"
