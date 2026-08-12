"""make the always-populated users columns NOT NULL

Creation fills all five: the domain is resolved before the insert and the
creation fails when it does not exist, and the three remaining columns fall
back to a value when the spec leaves them out. No update path can write NULL —
they all travel as ``OptionalState``.

Rows that predate those guarantees are repaired first: the three columns with
an obvious value are backfilled, and ``domain_id`` is re-derived from
``domain_name`` the way ``c1a7d3f05e28`` did, which is what a row missing it
after that migration needs. A row with no ``domain_name`` cannot be repaired —
there is nothing to derive the domain from — so the migration stops and names
the count instead of guessing or deleting.

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
    conn.execute(sa.text("UPDATE users SET role = 'user' WHERE role IS NULL"))
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
        sa.text("SELECT count(*) FROM users WHERE domain_name IS NULL OR domain_id IS NULL")
    ).scalar_one()
    if stranded:
        raise RuntimeError(
            f"{stranded} user(s) have no domain, and this migration cannot pick one for them. "
            "Assign each a domain (or delete the account) and run the migration again: "
            "SELECT uuid, email FROM users WHERE domain_name IS NULL OR domain_id IS NULL;"
        )

    for name, type_ in _COLUMNS:
        op.alter_column("users", name, existing_type=type_, nullable=False)


def downgrade() -> None:
    for name, type_ in _COLUMNS:
        op.alter_column("users", name, existing_type=type_, nullable=True)
