"""make the always-populated users columns NOT NULL

A missing domain or role is reported, not guessed. ``totp_activated`` is
already NOT NULL in migrated databases; the column is here for the ones built
from the model metadata.

Revision ID: f2c47d81a9b3
Revises: c8d51e7a3b62
Create Date: 2026-08-12 11:20:00.000000

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "f2c47d81a9b3"
down_revision = "c8d51e7a3b62"
# Part of: NEXT_RELEASE_VERSION
branch_labels = None
depends_on = None

_COLUMNS = (
    ("domain_name", sa.String(length=64)),
    ("domain_id", sa.dialects.postgresql.UUID(as_uuid=True)),
    ("role", sa.String(length=64)),
    ("need_password_change", sa.Boolean()),
    ("totp_activated", sa.Boolean()),
)


def upgrade() -> None:
    conn = op.get_bind()
    conn.execute(
        sa.text("UPDATE users SET need_password_change = false WHERE need_password_change IS NULL")
    )
    conn.execute(sa.text("UPDATE users SET totp_activated = false WHERE totp_activated IS NULL"))
    conn.execute(
        sa.text("""
            UPDATE users u
            SET domain_id = d.id
            FROM domains d
            WHERE u.domain_id IS NULL AND u.domain_name = d.name
        """)
    )

    stranded = conn.execute(
        sa.text("""
            SELECT count(*) FROM users
            WHERE domain_name IS NULL OR domain_id IS NULL OR role IS NULL
        """)
    ).scalar_one()
    if stranded:
        raise RuntimeError(
            f"{stranded} user(s) have no domain or no role, and this migration cannot pick either "
            "for them. Fill both in (or delete the account) and run the migration again: "
            "SELECT uuid, email, domain_name, role FROM users "
            "WHERE domain_name IS NULL OR domain_id IS NULL OR role IS NULL;"
        )

    for name, type_ in _COLUMNS:
        op.alter_column("users", name, existing_type=type_, nullable=False)
    op.alter_column(
        "users", "need_password_change", existing_type=sa.Boolean(), server_default=sa.false()
    )


def downgrade() -> None:
    op.alter_column(
        "users", "need_password_change", existing_type=sa.Boolean(), server_default=None
    )
    for name, type_ in _COLUMNS:
        op.alter_column("users", name, existing_type=type_, nullable=True)
