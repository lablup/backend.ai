"""Add domain container registry relations

Revision ID: ece8800e945c
Revises: b3e53701440e
Create Date: 2026-11-03 12:00:00.000000

"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

from ai.backend.manager.models.base import GUID

# revision identifiers, used by Alembic.
revision = "ece8800e945c"
down_revision = "b3e53701440e"
# Part of: NEXT_RELEASE_VERSION
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "domain_container_registry_relations",
        sa.Column("domain_id", GUID(), nullable=False),
        sa.Column("registry_id", GUID(), nullable=False),
        sa.PrimaryKeyConstraint(
            "domain_id",
            "registry_id",
            name=op.f("pk_domain_container_registry_relations"),
        ),
        sa.ForeignKeyConstraint(
            ["domain_id"],
            ["domains.id"],
            name=op.f("fk_domain_container_registry_relations_domain_id_domains"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["registry_id"],
            ["container_registries.id"],
            name="fk_domain_container_registry_relations_registry_id",
            ondelete="CASCADE",
        ),
    )
    op.create_index(
        op.f("ix_domain_container_registry_relations_registry_id"),
        "domain_container_registry_relations",
        ["registry_id"],
    )


def downgrade() -> None:
    op.drop_index(
        op.f("ix_domain_container_registry_relations_registry_id"),
        table_name="domain_container_registry_relations",
    )
    op.drop_table("domain_container_registry_relations")
