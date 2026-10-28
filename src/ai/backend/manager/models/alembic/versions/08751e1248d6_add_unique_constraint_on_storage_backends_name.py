"""Add a unique constraint on storage_backends.name

A status report inserts a backend under its name when absent, which needs the name
as the conflict key. storage_volume_service_holdings.status becomes nullable, as it now
holds the health judged from a service's reports, which no holding has yet.

Revision ID: 08751e1248d6
Revises: 8bb02f0415eb
Create Date: 2026-10-28

"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "08751e1248d6"  # Part of: NEXT_RELEASE_VERSION
down_revision = "8bb02f0415eb"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_unique_constraint(op.f("uq_storage_backends_name"), "storage_backends", ["name"])
    op.alter_column(
        "storage_volume_service_holdings",
        "status",
        existing_type=sa.String(length=64),
        nullable=True,
    )
    op.execute(
        "UPDATE storage_volume_service_holdings SET status = NULL"
        " WHERE status NOT IN ('healthy', 'unhealthy')"
    )


def downgrade() -> None:
    op.execute(
        "UPDATE storage_volume_service_holdings SET status = 'not_checked' WHERE status IS NULL"
    )
    op.alter_column(
        "storage_volume_service_holdings",
        "status",
        existing_type=sa.String(length=64),
        nullable=False,
    )
    op.drop_constraint(op.f("uq_storage_backends_name"), "storage_backends", type_="unique")
