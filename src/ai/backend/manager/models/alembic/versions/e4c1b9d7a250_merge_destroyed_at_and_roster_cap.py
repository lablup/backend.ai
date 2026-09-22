"""Merge heads d3a7c1e5b904 and d3f9a2c81b47

Two revisions were written against the same parent and both landed, leaving the branch
with two heads. Neither touches what the other does, so the merge carries no statements.

Revision ID: e4c1b9d7a250
Revises: d3a7c1e5b904, d3f9a2c81b47
Create Date: 2026-09-22

"""

from __future__ import annotations

# revision identifiers, used by Alembic.
revision = "e4c1b9d7a250"  # Part of: NEXT_RELEASE_VERSION
down_revision = ("d3a7c1e5b904", "d3f9a2c81b47")
branch_labels = None
depends_on = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
