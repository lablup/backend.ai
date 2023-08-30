"""add git_token table

Revision ID: 3d31a989dd0a
Revises: 02535458c0b3
Create Date: 2023-08-31 01:04:48.109184

"""
import sqlalchemy as sa
from alembic import op

from ai.backend.manager.models.base import GUID

# revision identifiers, used by Alembic.
revision = "3d31a989dd0a"
down_revision = "02535458c0b3"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "git_tokens",
        sa.Column("user_id", GUID(), nullable=False, index=True),
        sa.Column("domain", sa.String(length=200), nullable=False, index=True),
        sa.Column("token", sa.String(length=200)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column(
            "modified_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=True,
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.uuid"],
            name=op.f("fk_git_tokens_user_id_users"),
            onupdate="CASCADE",
            ondelete="CASCADE",
        ),
        sa.UniqueConstraint("user_id", "domain", name="uq_git_tokens_user_id_domain"),
    )
    # Create a default github and gitlab tokens


def downgrade():
    op.drop_table("git_tokens")
