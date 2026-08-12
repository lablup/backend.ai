"""make the always-populated users columns NOT NULL

``bae1a7326e8a`` filled ``domain_name`` for every account except
``admin@lablup.com``, so that one can still be empty. It joins the default
domain here, and is deleted only when there is no default domain to join.
``totp_activated`` is already NOT NULL in migrated databases; the column is
here for the ones built from the model metadata.

Revision ID: f2c47d81a9b3
Revises: c8d51e7a3b62
Create Date: 2026-08-12 11:20:00.000000

"""

import logging

import sqlalchemy as sa
from alembic import op
from sqlalchemy.engine import Connection

# revision identifiers, used by Alembic.
revision = "f2c47d81a9b3"
down_revision = "c8d51e7a3b62"
# Part of: NEXT_RELEASE_VERSION
branch_labels = None
depends_on = None

log = logging.getLogger("alembic.runtime.migration")

_COLUMNS = (
    ("domain_name", sa.String(length=64)),
    ("role", sa.String(length=64)),
    ("need_password_change", sa.Boolean()),
    ("totp_activated", sa.Boolean()),
)


def _delete_users(bind: Connection, user_ids: list[str]) -> None:
    """Delete users along with the rows a user delete normally takes with it."""
    bind.execute(
        sa.text("DELETE FROM permissions WHERE scope_type = 'user' AND scope_id = ANY(:ids)"),
        {"ids": user_ids},
    )
    bind.execute(
        sa.text("""
            DELETE FROM association_scopes_entities
            WHERE (entity_type = 'user' AND entity_id = ANY(:ids))
               OR (scope_type = 'user' AND scope_id = ANY(:ids))
        """),
        {"ids": user_ids},
    )
    bind.execute(
        sa.text("DELETE FROM user_roles WHERE user_id::text = ANY(:ids)"),
        {"ids": user_ids},
    )
    bind.execute(
        sa.text('DELETE FROM keypairs WHERE "user"::text = ANY(:ids)'),
        {"ids": user_ids},
    )
    bind.execute(
        sa.text("DELETE FROM users WHERE uuid::text = ANY(:ids)"),
        {"ids": user_ids},
    )


def upgrade() -> None:
    bind = op.get_bind()
    bind.execute(
        sa.text("UPDATE users SET need_password_change = false WHERE need_password_change IS NULL")
    )
    bind.execute(sa.text("UPDATE users SET totp_activated = false WHERE totp_activated IS NULL"))
    bind.execute(
        sa.text("""
            UPDATE users SET domain_name = 'default'
            WHERE domain_name IS NULL
              AND EXISTS (SELECT 1 FROM domains WHERE name = 'default')
        """)
    )

    doomed = bind.execute(
        sa.text("SELECT uuid::text AS uuid, email FROM users WHERE domain_name IS NULL")
    ).all()
    if doomed:
        log.warning(
            "Deleting %d user(s) with no domain — there is no default domain to move them to:",
            len(doomed),
        )
        for user_id, email in doomed:
            log.warning("  %s (%s)", user_id, email or "<unknown>")
        _delete_users(bind, [row.uuid for row in doomed])

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
