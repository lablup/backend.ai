"""Reference users from sessions and kernels with ON DELETE SET NULL."""

import sqlalchemy as sa
from alembic import op

revision = "c7e2a91f4d36"
down_revision = "a31e8d4c9b72"
# Part of: NEXT_RELEASE_VERSION
branch_labels = None
depends_on = None

# Downgrade cannot recover purged owners, so null owners become this placeholder uuid.
_NULL_OWNER = "00000000-0000-0000-0000-000000000000"


def upgrade() -> None:
    op.alter_column("sessions", "user_uuid", nullable=True)
    op.execute(
        sa.text("""
        UPDATE sessions AS s SET user_uuid = NULL
        WHERE s.user_uuid IS NOT NULL
          AND NOT EXISTS (SELECT 1 FROM users AS u WHERE u.uuid = s.user_uuid)
    """)
    )
    op.create_foreign_key(
        op.f("fk_sessions_user_uuid_users"),
        "sessions",
        "users",
        ["user_uuid"],
        ["uuid"],
        ondelete="SET NULL",
    )

    op.alter_column("kernels", "user_uuid", nullable=True)
    op.execute(
        sa.text("""
        UPDATE kernels AS k SET user_uuid = NULL
        WHERE k.user_uuid IS NOT NULL
          AND NOT EXISTS (SELECT 1 FROM users AS u WHERE u.uuid = k.user_uuid)
    """)
    )
    op.create_foreign_key(
        op.f("fk_kernels_user_uuid_users"),
        "kernels",
        "users",
        ["user_uuid"],
        ["uuid"],
        ondelete="SET NULL",
    )


def downgrade() -> None:
    op.drop_constraint(op.f("fk_kernels_user_uuid_users"), "kernels", type_="foreignkey")
    op.execute(sa.text(f"UPDATE kernels SET user_uuid = '{_NULL_OWNER}' WHERE user_uuid IS NULL"))
    op.alter_column("kernels", "user_uuid", nullable=False)

    op.drop_constraint(op.f("fk_sessions_user_uuid_users"), "sessions", type_="foreignkey")
    op.execute(sa.text(f"UPDATE sessions SET user_uuid = '{_NULL_OWNER}' WHERE user_uuid IS NULL"))
    op.alter_column("sessions", "user_uuid", nullable=False)
