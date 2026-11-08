"""Check `new-changelog.py` and `rename-changelog-fragments.py` against temporary git repositories.

Run it directly: `python scripts/test_changelog_fragments.py`.
`/scripts/` is outside the pants source tree, so this cannot be a pants test.
"""

import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent
COPIED = ["changelog_fragments.py", "new-changelog.py", "rename-changelog-fragments.py"]
PYPROJECT = """\
[tool.towncrier]
directory = "changes/"

[[tool.towncrier.type]]
directory = "feature"
name = "Features"

[[tool.towncrier.type]]
directory = "fix"
name = "Fixes"
"""
UNNUMBERED = "20261108-153012-k3f9qa"


def git(repo: Path, *args: str) -> str:
    return subprocess.run(
        ["git", *args], cwd=repo, check=True, capture_output=True, text=True
    ).stdout


def make_repo(root: Path) -> Path:
    repo = root / "repo"
    (repo / "scripts").mkdir(parents=True)
    (repo / "changes").mkdir()
    for name in COPIED:
        shutil.copy(SCRIPTS / name, repo / "scripts" / name)
    (repo / "pyproject.toml").write_text(PYPROJECT)
    for name in ["README.md", "KNOWLEDGE.md", "KNOWLEDGE.ko.md", "template.md"]:
        (repo / "changes" / name).write_text("x\n")
    git(repo, "init", "-q", "-b", "main")
    git(repo, "config", "user.email", "test@example.com")
    git(repo, "config", "user.name", "test")
    commit(repo, "chore: initial")
    return repo


def commit(repo: Path, subject: str, files: dict[str, str] | None = None) -> None:
    for rel, content in (files or {}).items():
        (repo / rel).write_text(content)
    git(repo, "add", "-A")
    git(repo, "commit", "-q", "-m", subject)


def merge_branch(repo: Path, branch: str, subject: str, files: dict[str, str]) -> None:
    """Add `files` on `branch` with a subject without a PR number, then merge it with `subject`."""
    git(repo, "checkout", "-q", "-b", branch)
    commit(repo, "wip", files)
    git(repo, "checkout", "-q", "main")
    git(repo, "merge", "-q", "--no-ff", "-m", subject, branch)


def rename(repo: Path) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, "scripts/rename-changelog-fragments.py"],
        cwd=repo,
        capture_output=True,
        text=True,
    )


def fragment_names(repo: Path) -> set[str]:
    return {p.name for p in (repo / "changes").iterdir()} - {
        "README.md",
        "KNOWLEDGE.md",
        "KNOWLEDGE.ko.md",
        "template.md",
    }


def test_new_changelog(root: Path) -> None:
    repo = make_repo(root)
    result = subprocess.run(
        [sys.executable, "scripts/new-changelog.py", "fix", "Fix a bug"],
        cwd=repo,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr
    path = result.stdout.strip()
    assert re.fullmatch(r"changes/\d{8}-\d{6}-[a-z0-9]{6}\.fix\.md", path), path
    assert (repo / path).read_text() == "Fix a bug\n"

    for args in [["unknown", "Fix a bug"], ["fix", " "], ["fix", "two\nlines"]]:
        result = subprocess.run(
            [sys.executable, "scripts/new-changelog.py", *args],
            cwd=repo,
            capture_output=True,
            text=True,
        )
        assert result.returncode == 1, args


def test_renames(root: Path) -> None:
    repo = make_repo(root)
    commit(repo, "feat: numbered (#100)", {"changes/100.feature.md": "a\n"})
    commit(repo, "fix(BA-1): squash merged (#200)", {f"changes/{UNNUMBERED}.fix.md": "b\n"})
    commit(
        repo,
        "fix(BA-2): backported (#300) (#301)",
        {"changes/20261108-153013-aaaaaa.fix.md": "c\n"},
    )
    # Same PR number as an existing fragment of the same type: towncrier counter names.
    commit(
        repo,
        "feat: two fragments (#100)",
        {
            "changes/20261108-153014-bbbbbb.feature.md": "d\n",
            "changes/20261108-153015-cccccc.feature.md": "e\n",
        },
    )
    merge_branch(
        repo,
        "topic",
        "feat: merge commit (#400)",
        {"changes/20261108-153016-dddddd.feature.md": "f\n"},
    )

    result = rename(repo)
    assert result.returncode == 0, result.stderr
    assert fragment_names(repo) == {
        "100.feature.md",
        "200.fix.md",
        "300.fix.md",
        "100.feature.1.md",
        "100.feature.2.md",
        "400.feature.md",
    }, fragment_names(repo)
    status = git(repo, "status", "--porcelain")
    assert f"R  changes/{UNNUMBERED}.fix.md -> changes/200.fix.md" in status, status
    assert (repo / "changes/300.fix.md").read_text() == "c\n"

    # A second run has nothing left to rename.
    result = rename(repo)
    assert result.returncode == 0, result.stderr


def test_rejects(root: Path) -> None:
    cases: list[tuple[str, str, str]] = [
        ("unconventional name", "fix: x (#1)", "BA-123.fix.md"),
        ("uppercase suffix", "fix: x (#1)", "20261108-153012-K3F9QA.fix.md"),
        ("no PR number in subject", "fix: x", f"{UNNUMBERED}.fix.md"),
    ]
    for label, subject, name in cases:
        repo = make_repo(root / label.replace(" ", "-"))
        commit(repo, "fix: fine (#9)", {"changes/20261108-000000-zzzzzz.fix.md": "ok\n"})
        commit(repo, subject, {f"changes/{name}": "x\n"})
        result = rename(repo)
        assert result.returncode == 1, label
        assert name in result.stderr, (label, result.stderr)
        # Nothing is renamed when any fragment fails.
        assert "20261108-000000-zzzzzz.fix.md" in fragment_names(repo), label

    repo = make_repo(root / "uncommitted")
    (repo / "changes" / f"{UNNUMBERED}.fix.md").write_text("x\n")
    result = rename(repo)
    assert result.returncode == 1
    assert UNNUMBERED in result.stderr, result.stderr


def main() -> None:
    tests = [test_new_changelog, test_renames, test_rejects]
    for test in tests:
        with tempfile.TemporaryDirectory() as tmp:
            test(Path(tmp))
    print(f"OK: {len(tests)} tests")


if __name__ == "__main__":
    main()
