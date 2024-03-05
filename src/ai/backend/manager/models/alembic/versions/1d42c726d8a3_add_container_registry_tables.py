"""Migrate container registry schema from `etcd` to `postgreSQL`

Revision ID: 1d42c726d8a3
Revises: 75ea2b136830
Create Date: 2024-03-05 10:36:24.197922

"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.sql import text

from ai.backend.manager.models.base import IDColumn, convention

# revision identifiers, used by Alembic.
revision = "1d42c726d8a3"
down_revision = "75ea2b136830"
branch_labels = None
depends_on = None


def upgrade():
    metadata = sa.MetaData(naming_convention=convention)
    op.create_table(
        "container_registries",
        metadata,
        IDColumn("id"),
        sa.Column("url", sa.String(length=255), nullable=True, index=True),
        sa.Column("registry_name", sa.String(length=50), nullable=True, index=True),
        sa.Column(
            "type",
            sa.Enum("docker", "harbor", "harbor2", name="container_registry_type"),
            default="docker",
            index=True,
            nullable=False,
        ),
        sa.Column("project", sa.String(length=255), nullable=True),
        sa.Column("username", sa.String(length=255), nullable=True),
        sa.Column("password", sa.String(length=255), nullable=True),
        sa.Column(
            "ssl_verify", sa.Boolean(), server_default=sa.text("true"), nullable=True, index=True
        ),
        sa.Column(
            "is_global", sa.Boolean(), server_default=sa.text("true"), nullable=True, index=True
        ),
    )


def downgrade():
    op.drop_table("container_registries")
    op.execute(text("DROP TYPE container_registry_type"))
