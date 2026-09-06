"""add permission field scopes

Revision ID: b44c240c7680
Revises: a4c1d9b5e207
Create Date: 2026-09-03

"""

import sqlalchemy as sa
from alembic import op

from ai.backend.manager.models.base import GUID

# Part of: NEXT_RELEASE_VERSION

# revision identifiers, used by Alembic.
revision = "b44c240c7680"
down_revision = "a4c1d9b5e207"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(sa.text("ALTER TABLE permissions ALTER COLUMN id SET DEFAULT uuid_generate_v7()"))
    op.add_column(
        "permissions",
        sa.Column("all_fields", sa.Boolean(), server_default=sa.true(), nullable=False),
    )
    op.create_check_constraint(
        op.f("ck_permissions_field_scope"),
        "permissions",
        "all_fields OR permission IN (1, 2)",
    )
    op.create_table(
        "permission_fields",
        sa.Column("permission_id", GUID(), nullable=False),
        sa.Column("path", sa.Text(), nullable=False),
        sa.CheckConstraint("path <> ''", name="ck_permission_fields_path"),
        sa.ForeignKeyConstraint(
            ["permission_id"],
            ["permissions.id"],
            name=op.f("fk_permission_fields_permission_id_permissions"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("permission_id", "path", name=op.f("pk_permission_fields")),
    )


def downgrade() -> None:
    op.drop_table("permission_fields")
    op.drop_constraint(op.f("ck_permissions_field_scope"), "permissions", type_="check")
    op.drop_column("permissions", "all_fields")
    op.execute(sa.text("ALTER TABLE permissions ALTER COLUMN id SET DEFAULT uuid_generate_v4()"))
