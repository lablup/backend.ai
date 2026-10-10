"""Merge heads e4a9c2d71b58 and f55b5bb47fef

Two revisions were written against the same parent and both landed, leaving the branch
with two heads. Neither touches what the other does, so the merge carries no statements.

Revision ID: c568d88b65b5
Revises: e4a9c2d71b58, f55b5bb47fef
Create Date: 2026-10-11

"""

from __future__ import annotations

# revision identifiers, used by Alembic.
revision = "c568d88b65b5"  # Part of: NEXT_RELEASE_VERSION
down_revision = ("e4a9c2d71b58", "f55b5bb47fef")
branch_labels = None
depends_on = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
