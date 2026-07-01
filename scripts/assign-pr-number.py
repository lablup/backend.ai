#!/usr/bin/env python
import json
import os
import re
import subprocess
import sys
from pathlib import Path

import tomlkit

exempted_files = ["README.md", "template.md"]


def read_news_types() -> set[str]:
    with open("./pyproject.toml", "r") as f:
        data = tomlkit.load(f)
        news_types = {section["directory"] for section in data["tool"]["towncrier"]["type"]}
    return news_types


def get_pr_added_fragments(base_ref: str, base_path: Path) -> set[str]:
    """Return fragment filenames *newly added* by this PR vs ``origin/<base_ref>``.

    Only ``A``-status entries are returned: a fragment that already existed on
    the base branch and was merely modified in place (e.g., a typo fix on a
    historical fragment) must keep its original PR-number prefix.

    Requires ``origin/<base_ref>`` to have been fetched (e.g., via
    ``actions/checkout`` with ``fetch-depth: 0``).
    """
    result = subprocess.run(
        [
            "git",
            "diff",
            "--name-only",
            "--diff-filter=A",
            f"origin/{base_ref}...HEAD",
            "--",
            str(base_path),
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    return {Path(line).name for line in result.stdout.splitlines() if line.strip()}


def main(pr_number: str) -> None:
    news_types = read_news_types()
    base_path = Path("./changes")
    rx_unnumbered_fragment = re.compile(
        r"^(\.)?(?P<type>" + "|".join(map(re.escape, news_types)) + r")(\.)?(md)?$"
    )
    rx_numbered_fragment = re.compile(
        r"^\d+\.(?P<type>" + "|".join(map(re.escape, news_types)) + r")(\.)?(md)?$"
    )

    base_ref = os.getenv("GITHUB_BASE_REF") or ""
    pr_added_fragments: set[str] | None = (
        get_pr_added_fragments(base_ref, base_path) if base_ref else None
    )
    # Backport PRs (targeting release branches) carry fragments already
    # numbered for the original ``main`` PR; rewriting those prefixes would
    # erase the link back to the original change in release notes. Restrict
    # mismatched-prefix rewrites to PRs targeting ``main``.
    rewrite_mismatched = base_ref == "main"

    all_fragments = [
        f.name for f in base_path.iterdir() if f.is_file() and f.name not in exempted_files
    ]
    if pr_added_fragments is not None:
        files = [f for f in all_fragments if f in pr_added_fragments]
    else:
        files = all_fragments

    existing_fragments: list[str] = []
    unnumbered_fragments: list[tuple[str, str]] = []
    mismatched_fragments: list[tuple[str, str]] = []
    for file in files:
        if match := rx_numbered_fragment.search(file):
            if file[0 : file.find(".")] == pr_number:
                existing_fragments.append(file)
            elif rewrite_mismatched:
                mismatched_fragments.append((file, match.group("type")))
        elif match := rx_unnumbered_fragment.search(file):
            unnumbered_fragments.append((file, match.group("type")))
        else:
            print(f"{file} is an invalid news fragment filename.")
            sys.exit(1)

    # Plan all renames before touching disk so that collisions — both with
    # existing files and between two fragments of the same type in one PR —
    # are detected atomically, not mid-way through a partial rename.
    planned_renames: list[tuple[str, str, str]] = []
    for filename, news_type in unnumbered_fragments:
        target = f"{pr_number}.{news_type}.md"
        planned_renames.append((filename, target, f"{filename} is renamed to {target}"))
    for filename, news_type in mismatched_fragments:
        target = f"{pr_number}.{news_type}.md"
        planned_renames.append((
            filename,
            target,
            f"{filename} has a PR number mismatch and is renamed to {target}",
        ))

    seen_targets: set[str] = set()
    for original, target, _ in planned_renames:
        if target in seen_targets:
            print(
                f"Cannot rename {original} to {target}: another fragment in this PR "
                f"also targets {target}. Remove or rename one of the conflicting "
                f"fragments and retry."
            )
            sys.exit(1)
        if (base_path / target).exists():
            print(
                f"Cannot rename {original} to {target}: another fragment already "
                f"occupies {target}. Remove or rename one of the conflicting "
                f"fragments and retry."
            )
            sys.exit(1)
        seen_targets.add(target)

    renamed_pairs: list[tuple[str, str]] = []
    for original, target, log_message in planned_renames:
        (base_path / original).rename(base_path / target)
        print(log_message)
        renamed_pairs.append((original, target))

    if renamed_pairs:
        subprocess.run(
            ["git", "rm", *(base_path / pair[0] for pair in renamed_pairs)],
            check=False,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.STDOUT,
        )
        subprocess.run(
            ["git", "add", *(base_path / pair[1] for pair in renamed_pairs)],
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=None,
        )
        with open(os.getenv("GITHUB_OUTPUT", os.devnull), "a") as ghoutput:
            rename_results = [f"{pair[0]} -> {pair[1]}" for pair in renamed_pairs]
            print(f"rename_results={json.dumps(rename_results)}", file=ghoutput)
            print("has_renamed_pairs=true", file=ghoutput)
    elif existing_fragments:
        print(f"The news fragment(s) for the PR #{pr_number} already exists:")
        for file in existing_fragments:
            print(file)
        with open(os.getenv("GITHUB_OUTPUT", os.devnull), "a") as ghoutput:
            print("has_renamed_pairs=false", file=ghoutput)
    else:
        print("There are no unnumbered news fragments.")
        with open(os.getenv("GITHUB_OUTPUT", os.devnull), "a") as ghoutput:
            print("has_renamed_pairs=false", file=ghoutput)
    sys.exit(0)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(f"Usage: python {sys.argv[0]} <PR Number>")
        sys.exit(1)
    pr_number = sys.argv[1]
    main(pr_number)
