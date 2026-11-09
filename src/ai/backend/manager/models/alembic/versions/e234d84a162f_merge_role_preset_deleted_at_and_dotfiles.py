"""Merge heads e0f2e337ef00 and f8d19a2c760e

Two revisions were written against the same parent and both landed, leaving the branch
with two heads. Neither touches what the other does, so the merge carries no statements.

Revision ID: e234d84a162f
Revises: e0f2e337ef00, f8d19a2c760e
Create Date: 2026-10-20

"""

from __future__ import annotations

# revision identifiers, used by Alembic.
revision = "e234d84a162f"  # Part of: NEXT_RELEASE_VERSION
down_revision = ("e0f2e337ef00", "f8d19a2c760e")
branch_labels = None
depends_on = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
