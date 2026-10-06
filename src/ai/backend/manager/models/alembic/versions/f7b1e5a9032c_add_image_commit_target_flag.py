"""Add an optional image commit target flag to registry access associations."""

import sqlalchemy as sa
from alembic import op

revision = "f7b1e5a9032c"
down_revision = "c7d2fb1e5a90"
# Part of: NEXT_RELEASE_VERSION
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "association_container_registries_groups",
        sa.Column("is_default", sa.Boolean(), nullable=False, server_default=sa.false()),
    )
    op.create_index(
        "uq_project_default_registry",
        "association_container_registries_groups",
        ["group_id"],
        unique=True,
        postgresql_where=sa.text("is_default"),
    )


def downgrade() -> None:
    op.drop_index(
        "uq_project_default_registry", table_name="association_container_registries_groups"
    )
    op.drop_column("association_container_registries_groups", "is_default")
