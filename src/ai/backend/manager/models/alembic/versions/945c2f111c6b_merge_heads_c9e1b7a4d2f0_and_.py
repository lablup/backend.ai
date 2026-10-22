"""Merge heads c9e1b7a4d2f0 and 51d33226c0a5

Two revisions were written against the same parent and both landed, leaving the branch
with two heads. Neither touches what the other does, so the merge carries no statements.

Revision ID: 945c2f111c6b
Revises: c9e1b7a4d2f0, 51d33226c0a5
Create Date: 2026-10-22

"""

from __future__ import annotations

# revision identifiers, used by Alembic.
revision = "945c2f111c6b"  # Part of: NEXT_RELEASE_VERSION
down_revision = ("c9e1b7a4d2f0", "51d33226c0a5")
branch_labels = None
depends_on = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
