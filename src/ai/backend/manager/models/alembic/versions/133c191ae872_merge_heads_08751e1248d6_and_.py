"""Merge heads 08751e1248d6 and 995eabef0eac

Two revisions were written against the same parent and both landed, leaving the branch
with two heads. Neither touches what the other does, so the merge carries no statements.

Revision ID: 133c191ae872
Revises: 08751e1248d6, 995eabef0eac
Create Date: 2026-10-30

"""

from __future__ import annotations

# revision identifiers, used by Alembic.
revision = "133c191ae872"  # Part of: NEXT_RELEASE_VERSION
down_revision = ("08751e1248d6", "995eabef0eac")
branch_labels = None
depends_on = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
