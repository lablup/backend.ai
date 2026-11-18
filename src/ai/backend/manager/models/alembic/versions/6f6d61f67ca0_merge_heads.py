"""Merge heads a4160b12bb53 d1d6985d1c3b

Revisions written against the same parent landed independently, leaving the
graph with more than one head. The merge carries no statements.

Revision ID: 6f6d61f67ca0
Revises: a4160b12bb53, d1d6985d1c3b
Create Date: 2026-11-18

"""

from __future__ import annotations

revision = "6f6d61f67ca0"  # Part of: NEXT_RELEASE_VERSION
down_revision = ("a4160b12bb53", "d1d6985d1c3b")
branch_labels = None
depends_on = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
