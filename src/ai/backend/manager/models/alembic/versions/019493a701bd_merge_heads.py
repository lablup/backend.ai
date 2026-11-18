"""Merge heads afcdb49cc729 b7d2a91c4e58

Revisions written against the same parent landed independently, leaving the
graph with more than one head. The merge carries no statements.

Revision ID: 019493a701bd
Revises: afcdb49cc729, b7d2a91c4e58
Create Date: 2026-11-05

"""

from __future__ import annotations

revision = "019493a701bd"  # Part of: NEXT_RELEASE_VERSION
down_revision = ("afcdb49cc729", "b7d2a91c4e58")
branch_labels = None
depends_on = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
