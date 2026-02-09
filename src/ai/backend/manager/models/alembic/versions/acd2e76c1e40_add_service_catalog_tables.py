"""add_service_catalog_tables

Revision ID: acd2e76c1e40
Revises: 4b7b4b040a70
Create Date: 2026-02-09 12:00:00.000000

"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB

from ai.backend.manager.models.base import GUID

# revision identifiers, used by Alembic.
revision = "acd2e76c1e40"
down_revision = "4b7b4b040a70"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 1. service_catalog table
    op.create_table(
        "service_catalog",
        sa.Column("id", GUID(), nullable=False, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("service_group", sa.String(length=64), nullable=False),
        sa.Column("instance_id", sa.String(length=128), nullable=False),
        sa.Column("display_name", sa.String(length=256), nullable=False),
        sa.Column("version", sa.String(length=64), nullable=False),
        sa.Column("labels", JSONB, nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("status", sa.String(length=64), nullable=False),
        sa.Column("startup_time", sa.DateTime(timezone=True), nullable=False),
        sa.Column(
            "registered_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column(
            "last_heartbeat",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column(
            "config_hash", sa.String(length=128), nullable=False, server_default=sa.text("''")
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_service_catalog")),
        sa.UniqueConstraint(
            "service_group",
            "instance_id",
            name="uq_service_catalog_service_group_instance_id",
        ),
    )
    op.create_index(
        "ix_service_catalog_service_group",
        "service_catalog",
        ["service_group"],
        unique=False,
    )
    op.create_index(
        "ix_service_catalog_status",
        "service_catalog",
        ["status"],
        unique=False,
    )

    # 2. service_catalog_endpoint table
    op.create_table(
        "service_catalog_endpoint",
        sa.Column("id", GUID(), nullable=False, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("service_id", GUID(), nullable=False),
        sa.Column("role", sa.String(length=32), nullable=False),
        sa.Column("scope", sa.String(length=32), nullable=False),
        sa.Column("address", sa.String(length=256), nullable=False),
        sa.Column("port", sa.Integer, nullable=False),
        sa.Column("protocol", sa.String(length=16), nullable=False),
        sa.Column("metadata", JSONB, nullable=True, server_default=sa.text("'{}'::jsonb")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_service_catalog_endpoint")),
        sa.ForeignKeyConstraint(
            ["service_id"],
            ["service_catalog.id"],
            name=op.f("fk_service_catalog_endpoint_service_id_service_catalog"),
            ondelete="CASCADE",
        ),
        sa.UniqueConstraint(
            "service_id",
            "role",
            "scope",
            name="uq_service_catalog_endpoint_service_id_role_scope",
        ),
    )


def downgrade() -> None:
    op.drop_table("service_catalog_endpoint")
    op.drop_index("ix_service_catalog_status", table_name="service_catalog")
    op.drop_index("ix_service_catalog_service_group", table_name="service_catalog")
    op.drop_table("service_catalog")
