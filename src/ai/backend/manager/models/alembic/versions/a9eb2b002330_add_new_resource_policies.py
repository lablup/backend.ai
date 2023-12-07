"""add new resource policies

Revision ID: a9eb2b002330
Revises: 5fbd368d12a2
Create Date: 2023-06-28 20:51:13.352391

"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.sql import text

from ai.backend.manager.models.base import convention

# revision identifiers, used by Alembic.
revision = "a9eb2b002330"
down_revision = "5fbd368d12a2"
branch_labels = None
depends_on = None


def upgrade():
    metadata = sa.MetaData(naming_convention=convention)
    conn = op.get_bind()
    op.create_table(
        "user_resource_policies",
        metadata,
        sa.Column("name", sa.String(length=256), primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("max_vfolder_size", sa.BigInteger(), nullable=False),
    )
    op.create_table(
        "project_resource_policies",
        metadata,
        sa.Column("name", sa.String(length=256), primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("max_vfolder_size", sa.BigInteger(), nullable=False),
    )
    op.execute(
        text("INSERT INTO user_resource_policies (name, max_vfolder_size) VALUES ('default', -1)")
    )
    op.execute(
        text(
            "INSERT INTO project_resource_policies (name, max_vfolder_size) VALUES ('default', -1)"
        )
    )
    op.add_column(
        "users",
        sa.Column(
            "resource_policy",
            sa.String(length=256),
            sa.ForeignKey("user_resource_policies.name"),
            nullable=True,
        ),
    )
    op.add_column(
        "groups",
        sa.Column(
            "resource_policy",
            sa.String(length=256),
            sa.ForeignKey("project_resource_policies.name"),
            nullable=True,
        ),
    )
    op.execute(text("UPDATE users SET resource_policy = 'default'"))
    op.execute(text("UPDATE groups SET resource_policy = 'default'"))
    op.alter_column("users", "resource_policy", nullable=False)
    op.alter_column("groups", "resource_policy", nullable=False)
    conn.execute(
        text(
            "UPDATE vfolders SET quota_scope_id = CONCAT(REPLACE(ownership_type::text, 'group',"
            " 'project'), ':', CONCAT(UUID(quota_scope_id), ''));"
        )
    )


def downgrade():
    op.execute(text("UPDATE vfolders SET quota_scope_id = SPLIT_PART(quota_scope_id, ':', 2);"))
    op.drop_column("users", "resource_policy")
    op.drop_column("groups", "resource_policy")
    op.drop_table("user_resource_policies")
    op.drop_table("project_resource_policies")
