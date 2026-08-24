"""add entity_invitations table

Revision ID: f4b1c9d27a08
Revises: 8c41a7e5b6d2
Create Date: 2026-08-25 00:00:00.000000

"""

import sqlalchemy as sa
from alembic import op

from ai.backend.manager.models.base import GUID

# revision identifiers, used by Alembic.
revision = "f4b1c9d27a08"
down_revision = "8c41a7e5b6d2"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "entity_invitations",
        sa.Column("id", GUID, primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column(
            "inviter_user_id",
            GUID,
            sa.ForeignKey("users.uuid", onupdate="CASCADE", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("invitee_email", sa.String(length=64), nullable=False),
        sa.Column("target_entity_type", sa.String(length=32), nullable=False),
        sa.Column("target_entity_id", GUID, nullable=False),
        sa.Column("permission_cap", sa.SmallInteger(), nullable=True),
        sa.Column("status", sa.String(length=64), nullable=False, server_default="pending"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
    )
    op.create_index(
        "uq_entity_invitations_open",
        "entity_invitations",
        ["invitee_email", "target_entity_type", "target_entity_id"],
        unique=True,
        postgresql_where=sa.text("status != 'accepted'"),
    )
    op.create_index(
        "ix_entity_invitations_target",
        "entity_invitations",
        ["target_entity_type", "target_entity_id"],
    )
    op.create_index(
        "ix_entity_invitations_invitee_email",
        "entity_invitations",
        ["invitee_email"],
    )


def downgrade() -> None:
    op.drop_index("ix_entity_invitations_invitee_email", table_name="entity_invitations")
    op.drop_index("ix_entity_invitations_target", table_name="entity_invitations")
    op.drop_index("uq_entity_invitations_open", table_name="entity_invitations")
    op.drop_table("entity_invitations")
