"""Add auto-generated file revisions and applications

Revision ID: 46d84960bae3
Revises: a37b92a3e063
Create Date: 2026-10-30 12:00:00.000000

"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

from ai.backend.manager.models.base import GUID

# revision identifiers, used by Alembic.
revision = "46d84960bae3"
down_revision = "a37b92a3e063"
# Part of: NEXT_RELEASE_VERSION
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "auto_generated_file_revisions",
        sa.Column("id", GUID(), nullable=False, server_default=sa.text("uuid_generate_v7()")),
        sa.Column("file_id", GUID(), nullable=False),
        sa.Column("revision_number", sa.Integer(), nullable=False),
        sa.Column("data", sa.Text(), nullable=False),
        sa.Column("creator_id", GUID(), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_auto_generated_file_revisions")),
        sa.ForeignKeyConstraint(
            ["file_id"],
            ["dotfiles.id"],
            name=op.f("fk_auto_generated_file_revisions_file_id_dotfiles"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["creator_id"],
            ["users.uuid"],
            name=op.f("fk_auto_generated_file_revisions_creator_id_users"),
            ondelete="SET NULL",
        ),
        sa.UniqueConstraint(
            "file_id", "revision_number", name=op.f("uq_auto_generated_file_revisions_file_id")
        ),
        sa.CheckConstraint(
            "char_length(data) <= 65536", name=op.f("ck_auto_generated_file_revisions_data_length")
        ),
    )
    op.create_table(
        "auto_generated_file_applications",
        sa.Column("entity_type", sa.String(32), nullable=False),
        sa.Column("entity_id", GUID(), nullable=False),
        sa.Column("path", sa.Text(), nullable=False),
        sa.Column("perm", sa.Text(), nullable=False),
        sa.Column("file_id", GUID(), nullable=False),
        sa.PrimaryKeyConstraint(
            "entity_type", "entity_id", "path", name=op.f("pk_auto_generated_file_applications")
        ),
        sa.ForeignKeyConstraint(
            ["entity_type", "entity_id"],
            ["virtual_entities.entity_type", "virtual_entities.entity_id"],
            name=op.f("fk_auto_generated_file_applications_entity_virtual_entities"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["file_id"],
            ["dotfiles.id"],
            name=op.f("fk_auto_generated_file_applications_file_id_dotfiles"),
            ondelete="CASCADE",
        ),
        sa.CheckConstraint(
            "char_length(perm) <= 4", name=op.f("ck_auto_generated_file_applications_perm_length")
        ),
    )
    op.create_index(
        op.f("ix_auto_generated_file_applications_file_id"),
        "auto_generated_file_applications",
        ["file_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        op.f("ix_auto_generated_file_applications_file_id"),
        table_name="auto_generated_file_applications",
    )
    op.drop_table("auto_generated_file_applications")
    op.drop_table("auto_generated_file_revisions")
