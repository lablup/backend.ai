"""add unique constraint to storage_volumes.name

Revision ID: 3b8e1d6c9a47
Revises: fa2dfd48c169
Create Date: 2026-10-21

"""

from alembic import op

revision = "3b8e1d6c9a47"  # Part of: NEXT_RELEASE_VERSION
down_revision = "fa2dfd48c169"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_unique_constraint(op.f("uq_storage_volumes_name"), "storage_volumes", ["name"])


def downgrade() -> None:
    op.drop_constraint(op.f("uq_storage_volumes_name"), "storage_volumes", type_="unique")
