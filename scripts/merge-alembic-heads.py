"""Linearize diverged alembic heads by re-pointing ``down_revision`` (file-only).

The project keeps a single linear migration chain and forbids alembic merge
migrations (see ``src/ai/backend/manager/models/alembic/README.md``). When two
heads appear, this script resolves them by rebasing one head's diverged chain
onto the other -- editing only the ``down_revision`` of migration files, with no
database access.

Given heads that share a common ancestor::

    ... --> X --> base                (base chain)
              \\-> top                 (top chain)

the diverged portion of the *top* chain is re-pointed so that the result is a
single linear history::

    ... --> X --> base --> top

Usage::

    python scripts/merge-alembic-heads.py                 # auto-detect 2 heads
    python scripts/merge-alembic-heads.py BASE TOP        # TOP rebased onto BASE
    python scripts/merge-alembic-heads.py --dry-run
    python scripts/merge-alembic-heads.py --versions-dir <path>
"""

import argparse
import ast
import graphlib
import re
import sys
from pathlib import Path

DEFAULT_VERSIONS_DIR = Path("src/ai/backend/manager/models/alembic/versions")


def build_revision_map(versions_dir: Path) -> tuple[dict[str, set[str]], dict[str, Path]]:
    """Return ``{revision: {down_revisions}}`` and ``{revision: file_path}``."""
    rev_map: dict[str, set[str]] = {}
    rev_files: dict[str, Path] = {}
    current_rev = None
    for p in versions_dir.glob("*.py"):
        src = p.read_text()
        tree = ast.parse(src, filename=str(p))
        for node in ast.walk(tree):
            if isinstance(node, ast.Assign):
                target = node.targets[0]
                if isinstance(target, ast.Name) and target.id in ("revision", "down_revision"):
                    values = []
                    assigned_value = node.value
                    match assigned_value:
                        case ast.Constant():
                            if assigned_value.value is not None:
                                values.append(assigned_value.value)
                        case ast.Tuple():
                            for el in assigned_value.elts:
                                if isinstance(el, ast.Constant) and el.value is not None:
                                    values.append(el.value)
                    match target.id:
                        case "revision":
                            current_rev = values[0]
                            rev_map[current_rev] = set()
                            rev_files[current_rev] = p
                        case "down_revision":
                            rev_map[current_rev] = {*values}
    return rev_map, rev_files


def find_heads(rev_map: dict[str, set[str]]) -> set[str]:
    sorter = graphlib.TopologicalSorter(rev_map)
    heads = {*rev_map.keys()}
    for rev in reversed([*sorter.static_order()]):
        for down_rev in rev_map.get(rev, []):
            heads.discard(down_rev)
    return heads


def get_chain(rev: str, rev_map: dict[str, set[str]]) -> list[str]:
    """Return the chain from root to ``rev`` (first parent only), root-first."""
    chain = []
    cur: str | None = rev
    while cur is not None:
        chain.append(cur)
        downs = rev_map.get(cur, set())
        cur = sorted(downs)[0] if downs else None
    return list(reversed(chain))


def find_common_ancestor(
    base: str, top: str, rev_map: dict[str, set[str]]
) -> str | None:
    base_chain = set(get_chain(base, rev_map))
    for rev in reversed(get_chain(top, rev_map)):
        if rev in base_chain:
            return rev
    return None


def rewrite_down_revision(file_path: Path, new_down_revision: str) -> None:
    """Replace the ``down_revision`` assignment in a migration file."""
    content = file_path.read_text()
    new_content, n = re.subn(
        r"^down_revision\s*=\s*(['\"][^'\"]*['\"]|None)",
        f'down_revision = "{new_down_revision}"',
        content,
        flags=re.MULTILINE,
    )
    if n != 1:
        raise SystemExit(f"Could not rewrite down_revision in {file_path}")
    file_path.write_text(new_content)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Linearize diverged alembic heads by re-pointing down_revision.",
    )
    parser.add_argument("base", nargs="?", help="Head that stays in place (becomes ancestor)")
    parser.add_argument("top", nargs="?", help="Head whose chain is rebased onto base")
    parser.add_argument(
        "--versions-dir",
        type=Path,
        default=DEFAULT_VERSIONS_DIR,
        help=f"Alembic versions directory (default: {DEFAULT_VERSIONS_DIR})",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show the planned change without editing any file",
    )
    args = parser.parse_args()

    if not args.versions_dir.is_dir():
        raise SystemExit(f"Versions directory not found: {args.versions_dir}")

    rev_map, rev_files = build_revision_map(args.versions_dir)

    if args.base and args.top:
        base, top = args.base, args.top
    elif args.base or args.top:
        raise SystemExit("Provide both BASE and TOP, or neither (to auto-detect).")
    else:
        heads = find_heads(rev_map)
        if len(heads) == 1:
            print(f"Single head detected ({next(iter(heads))}); nothing to merge.")
            return
        if len(heads) != 2:
            raise SystemExit(
                f"Expected exactly 2 heads to auto-merge, found {len(heads)}: "
                f"{', '.join(sorted(heads))}\nPass BASE and TOP explicitly."
            )
        base, top = sorted(heads)
        print(f"Auto-detected heads: base={base}, top={top}")

    for rev in (base, top):
        if rev not in rev_map:
            raise SystemExit(f"Revision not found in {args.versions_dir}: {rev}")
    if base == top:
        raise SystemExit("BASE and TOP must differ.")

    ancestor = find_common_ancestor(base, top, rev_map)
    if ancestor is None:
        raise SystemExit(f"No common ancestor between {base} and {top}.")

    # The migration to re-point is the first one on the top chain after the
    # common ancestor; it currently descends (transitively) from the ancestor
    # and must instead descend from base.
    top_chain = get_chain(top, rev_map)
    ancestor_idx = top_chain.index(ancestor)
    diverged = top_chain[ancestor_idx + 1 :]
    if not diverged:
        raise SystemExit(f"{top} is an ancestor of {base}; nothing to rebase.")
    pivot = diverged[0]
    pivot_file = rev_files[pivot]
    old_down = sorted(rev_map[pivot])[0]

    print(f"Common ancestor: {ancestor}")
    print(f"Rebasing {top}'s chain onto {base}:")
    print(f"  {pivot_file.name}")
    print(f"    down_revision: {old_down} -> {base}")
    print(f"Resulting linear head: {top}")

    if args.dry_run:
        print("\nDry run: no files modified.")
        return

    rewrite_down_revision(pivot_file, base)
    print("\nDone. Verify with: python scripts/check-multiple-alembic-heads.py")


if __name__ == "__main__":
    main()
