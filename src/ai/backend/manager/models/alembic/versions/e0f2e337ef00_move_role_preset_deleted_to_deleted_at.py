"""Move role_presets.deleted to deleted_at."""

import sqlalchemy as sa
from alembic import op

revision = "e0f2e337ef00"
down_revision = "c7e2a91f4d36"
# Part of: NEXT_RELEASE_VERSION
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "role_presets",
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.execute(sa.text("UPDATE role_presets SET deleted_at = now() WHERE deleted"))
    op.drop_index("ix_role_presets_scope_type_deleted", table_name="role_presets")
    op.drop_column("role_presets", "deleted")
    op.create_index(
        "ix_role_presets_scope_type_deleted_at",
        "role_presets",
        ["scope_type", "deleted_at"],
    )


def downgrade() -> None:
    op.add_column(
        "role_presets",
        sa.Column("deleted", sa.Boolean(), nullable=False, server_default=sa.false()),
    )
    op.execute(sa.text("UPDATE role_presets SET deleted = true WHERE deleted_at IS NOT NULL"))
    op.drop_index("ix_role_presets_scope_type_deleted_at", table_name="role_presets")
    op.drop_column("role_presets", "deleted_at")
    op.create_index(
        "ix_role_presets_scope_type_deleted",
        "role_presets",
        ["scope_type", "deleted"],
    )
