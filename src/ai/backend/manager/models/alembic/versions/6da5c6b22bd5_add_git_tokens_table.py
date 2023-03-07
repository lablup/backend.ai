"""add git_tokens table

Revision ID: 6da5c6b22bd5
Revises: 10c58e701d87
Create Date: 2023-03-06 17:42:53.712150

"""
import sqlalchemy as sa
from alembic import op

from ai.backend.manager.models.base import GUID

# revision identifiers, used by Alembic.
revision = "6da5c6b22bd5"
down_revision = "10c58e701d87"
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
