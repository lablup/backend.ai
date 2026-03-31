"""create model_cards table

Revision ID: ed1aa96c40d0
Revises: 4b79df76c749
Create Date: 2026-03-31

"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql as pgsql

from ai.backend.manager.models.base import GUID, IDColumn

# revision identifiers, used by Alembic.
revision = "ed1aa96c40d0"
down_revision = "4b79df76c749"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "model_cards",
        IDColumn(),
        sa.Column("name", sa.String(length=512), nullable=False),
        sa.Column(
            "vfolder",
            GUID(),
            sa.ForeignKey("vfolders.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "domain",
            sa.String(length=64),
            sa.ForeignKey("domains.name", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "project",
            GUID(),
            sa.ForeignKey("groups.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "creator",
            GUID(),
            sa.ForeignKey("users.uuid", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("author", sa.String(length=256), nullable=True),
        sa.Column("title", sa.String(length=512), nullable=True),
        sa.Column("model_version", sa.String(length=64), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("task", sa.String(length=128), nullable=True),
        sa.Column("category", sa.String(length=128), nullable=True),
        sa.Column("architecture", sa.String(length=128), nullable=True),
        sa.Column("framework", pgsql.ARRAY(sa.String), nullable=False, server_default="{}"),
        sa.Column("label", pgsql.ARRAY(sa.String), nullable=False, server_default="{}"),
        sa.Column("license", sa.String(length=128), nullable=True),
        sa.Column("min_resource", pgsql.JSONB(), nullable=True),
        sa.Column("readme", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_model_cards")),
        sa.UniqueConstraint(
            "name", "domain", "project", name=op.f("uq_model_cards_name_domain_project")
        ),
    )


def downgrade() -> None:
    op.drop_table("model_cards")
