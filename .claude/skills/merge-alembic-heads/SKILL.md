---
name: merge-alembic-heads
description: Resolve two or more alembic heads already on main by adding an empty merge migration — detect the heads, check the branches do not conflict, generate the merge revision, verify a single head, and open the PR. Use when `alembic upgrade head` fails with "Multiple head revisions", CI `check-multiple-alembic-heads` fails on main, or the user asks to merge diverged heads on main.
tags:
  - database
  - alembic
  - migration
---

# Merge alembic heads on main

Rules this follows: `src/ai/backend/manager/models/alembic/AGENTS.md` (Diverged heads).
Only for heads that are **already on main**. If one head is your own unmerged migration, repoint its
`down_revision` instead (`scripts/alembic-rebase.py`) — no merge migration.

## 1. Detect

```bash
git switch main && git pull --ff-only
python scripts/check-multiple-alembic-heads.py   # manager; exit 0 → one head, stop here
./py -m alembic -c <config> heads                # any component (alembic.ini / alembic-appproxy.ini / alembic-accountmgr.ini)
```

## 2. Check the heads

For each head, find its file, the PR that added it, and the common parent:

```bash
grep -l '^revision = "<head>"' src/ai/backend/manager/models/alembic/versions/*.py
git log --diff-filter=A --format='%h %s' -- <file>
./py -m alembic -c <config> history -r <parent>:heads
```

Read every revision between the common parent and each head. If both sides touch the same
table, column, constraint, or enum, **stop and report** — the merge needs real statements or an
order, and the user decides it. Otherwise the merge is empty.

## 3. Generate

```bash
git switch -c chore/merge-alembic-heads-<short-topic>
./py -m alembic -c <config> merge -m "Merge heads <head_a> and <head_b>" <head_a> <head_b>
```

Rewrite the generated file to match the existing merge revisions (e.g. `e234d84a162f_*.py`):

```python
"""Merge heads <head_a> and <head_b>

Two revisions were written against the same parent and both landed, leaving the branch
with two heads. Neither touches what the other does, so the merge carries no statements.

Revision ID: <new>
Revises: <head_a>, <head_b>
Create Date: <YYYY-MM-DD>

"""

from __future__ import annotations

# revision identifiers, used by Alembic.
revision = "<new>"  # Part of: NEXT_RELEASE_VERSION
down_revision = ("<head_a>", "<head_b>")
branch_labels = None
depends_on = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
```

- Drop the template's unused `sa` / `op` imports.
- Keep `NEXT_RELEASE_VERSION` as is; the release freezes it.

## 4. Verify

```bash
python scripts/check-multiple-alembic-heads.py   # one head
./py -m alembic -c <config> heads
./py -m alembic -c <config> upgrade head         # needs the local DB (/halfstack); keep the output for the PR
pants lint check <new file>
```

If `current` fails with `Can't locate revision` (the local DB sits on another branch's revision), do not
touch the DB. Check the path offline instead — both heads, then the merge, must appear:

```bash
./py -m alembic -c <config> upgrade <parent>:head --sql 2>&1 | grep "Running upgrade"
```

## 5. Submit

Only after the user asks to commit:

- Commit: `chore: merge diverged alembic heads`
- News fragment `changes/<PR>.misc.md`:
  `Merge the two alembic heads left by two revisions written against the same parent, so `alembic upgrade head` resolves again.`
- PR body: the `upgrade head` error, a table of the heads (`| Head | From |` with revision, title, PR),
  why the merge is empty, and the `heads` / `upgrade head` output. Example: #15896.
