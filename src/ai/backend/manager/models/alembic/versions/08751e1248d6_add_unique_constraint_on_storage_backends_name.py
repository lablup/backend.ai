"""Add a unique constraint on storage_backends.name

A status report inserts a backend under its name when absent, which needs the name
as the conflict key.

Revision ID: 08751e1248d6
Revises: a37b92a3e063
Create Date: 2026-10-29

"""

from __future__ import annotations

from alembic import op

# revision identifiers, used by Alembic.
revision = "08751e1248d6"
down_revision = "a37b92a3e063"
# Part of: NEXT_RELEASE_VERSION
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_unique_constraint(op.f("uq_storage_backends_name"), "storage_backends", ["name"])


def downgrade() -> None:
    op.drop_constraint(op.f("uq_storage_backends_name"), "storage_backends", type_="unique")
