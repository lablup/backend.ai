"""Merge heads 51d33226c0a5 and c9e1b7a4d2f0

Two revisions were written against the same parent and both landed, leaving the branch
with two heads. Neither touches what the other does, so the merge carries no statements.

Revision ID: d5d3ddd91ae1
Revises: 51d33226c0a5, c9e1b7a4d2f0
Create Date: 2026-10-22

"""

from __future__ import annotations

# revision identifiers, used by Alembic.
revision = "d5d3ddd91ae1"  # Part of: NEXT_RELEASE_VERSION
down_revision = ("51d33226c0a5", "c9e1b7a4d2f0")
branch_labels = None
depends_on = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
