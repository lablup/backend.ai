"""tighten the always-populated keypairs columns

Backfills ``user_id``, ``is_active``, ``is_admin`` and ``num_queries``, then sets
those and ``secret_key`` NOT NULL. A keypair with no ``secret_key`` cannot sign a
request, so it is deleted rather than given a fabricated one.

Revision ID: e4a91c05df38
Revises: 37d711158a8c
Create Date: 2026-08-06 13:10:00.000000

"""

import logging

import sqlalchemy as sa
from alembic import op
from sqlalchemy.engine import Connection

log = logging.getLogger("alembic.runtime.migration")

# revision identifiers, used by Alembic.
revision = "e4a91c05df38"
down_revision = "37d711158a8c"
# Part of: NEXT_RELEASE_VERSION
branch_labels = None
depends_on = None

_TIGHTENED = (
    "user_id",
    "secret_key",
    "is_active",
    "is_admin",
    "num_queries",
)


def _delete_keypairs_without_secret_key(bind: Connection) -> None:
    doomed = bind.execute(
        sa.text("""
            SELECT k.access_key, k.user_id, u.email
            FROM keypairs k LEFT JOIN users u ON u."uuid" = k."user"
            WHERE k.secret_key IS NULL
            ORDER BY k.access_key
        """)
    ).all()
    if not doomed:
        return

    log.warning(
        "Deleting %d keypair(s) with no secret key — they cannot sign a request, so nothing"
        " can be authenticated or running under them:",
        len(doomed),
    )
    for access_key, user_id, email in doomed:
        log.warning("  %s (owner: %s)", access_key, email or user_id or "<unknown>")

    keys = [row.access_key for row in doomed]
    bind.execute(
        sa.text("DELETE FROM permissions WHERE scope_type = 'keypair' AND scope_id = ANY(:keys)"),
        {"keys": keys},
    )
    bind.execute(
        sa.text("""
            DELETE FROM association_scopes_entities
            WHERE (entity_type = 'keypair' AND entity_id = ANY(:keys))
               OR (scope_type = 'keypair' AND scope_id = ANY(:keys))
        """),
        {"keys": keys},
    )
    bind.execute(
        sa.text("DELETE FROM keypairs WHERE access_key = ANY(:keys)"),
        {"keys": keys},
    )


def upgrade() -> None:
    bind = op.get_bind()
    _delete_keypairs_without_secret_key(bind)
    bind.execute(
        sa.text("""
            UPDATE keypairs
            SET user_id = users.email
            FROM users
            WHERE users.uuid = keypairs."user" AND keypairs.user_id IS NULL
        """)
    )
    bind.execute(sa.text("UPDATE keypairs SET is_active = true WHERE is_active IS NULL"))
    bind.execute(sa.text("UPDATE keypairs SET is_admin = false WHERE is_admin IS NULL"))
    bind.execute(sa.text("UPDATE keypairs SET num_queries = 0 WHERE num_queries IS NULL"))

    for column in _TIGHTENED:
        op.alter_column("keypairs", column, nullable=False)


def downgrade() -> None:
    for column in _TIGHTENED:
        op.alter_column("keypairs", column, nullable=True)
