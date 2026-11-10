"""drop role_invitations table

Role invitations are removed: no client consumed them, and a ``roles`` row
carries no scope column, so an invitation cannot name the organization it
grants. Accepted invitations already wrote their ``user_roles`` rows, and the
remaining states never granted anything, so no data is migrated.

The ``role:assignment`` permission grants made by ad7acfe8aa1c are kept — the
assign/revoke role operations still use that entity type.

Revision ID: 3f7a2c1e9b04
Revises: f4b1c9d27a08
Create Date: 2026-08-25

"""

import sqlalchemy as sa
from alembic import op

from ai.backend.manager.models.base import GUID

# revision identifiers, used by Alembic.
revision = "3f7a2c1e9b04"
down_revision = "f4b1c9d27a08"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("DROP TABLE IF EXISTS role_invitations")


def downgrade() -> None:
    op.create_table(
        "role_invitations",
        sa.Column("id", GUID, primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column(
            "inviter_user_id",
            GUID,
            sa.ForeignKey("users.uuid", onupdate="CASCADE", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "invitee_user_id",
            GUID,
            sa.ForeignKey("users.uuid", onupdate="CASCADE", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "role_id",
            GUID,
            sa.ForeignKey("roles.id", onupdate="CASCADE", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("state", sa.VARCHAR(64), nullable=False, server_default="pending"),
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
        "ix_role_invitations_invitee_user_id",
        "role_invitations",
        ["invitee_user_id"],
    )
    op.create_index(
        "uq_role_invitations_active",
        "role_invitations",
        ["invitee_user_id", "role_id"],
        unique=True,
        postgresql_where=sa.text("state != 'accepted'"),
    )
