"""Reference users from sessions and kernels with ON DELETE SET NULL."""

import sqlalchemy as sa
from alembic import op

revision = "c7e2a91f4d36"
down_revision = "b2e7c8a94610"
# Part of: NEXT_RELEASE_VERSION
branch_labels = None
depends_on = None


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
    op.drop_constraint(op.f("fk_sessions_user_uuid_users"), "sessions", type_="foreignkey")

    # Purged owners cannot be recovered. Each session gets its own id as the owner,
    # so namesakes do not collide on the per-user name index; kernels follow their session.
    op.execute(sa.text("UPDATE sessions SET user_uuid = id WHERE user_uuid IS NULL"))
    op.execute(
        sa.text("""
        UPDATE kernels AS k SET user_uuid = s.user_uuid
        FROM sessions AS s
        WHERE k.session_id = s.id AND k.user_uuid IS NULL
    """)
    )
    op.alter_column("kernels", "user_uuid", nullable=False)
    op.alter_column("sessions", "user_uuid", nullable=False)
