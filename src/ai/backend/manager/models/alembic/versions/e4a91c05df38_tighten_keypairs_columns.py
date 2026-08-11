"""tighten the always-populated keypairs columns

``is_active``, ``is_admin`` and ``num_queries`` are backfilled with the value a
null already behaved as — for ``is_active`` that is false, since every query
filtering on it uses ``IS TRUE`` and so already skips those rows. ``user_id`` is
recovered from the owner, which ``keypairs."user"`` always identifies. Only
``secret_key`` cannot be reconstructed, and a keypair without one cannot sign a
request, so those rows are deleted.

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

_BACKFILLED = {
    "is_active": "false",
    "is_admin": "false",
    "num_queries": "0",
}
_TIGHTENED = ("user_id", "secret_key", *_BACKFILLED)


def _delete_keypairs(bind: Connection, keys: list[str]) -> None:
    """Delete keypairs along with the RBAC rows a keypair delete normally takes with it."""
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
    doomed = bind.execute(
        sa.text("""
            SELECT keypairs.access_key, users.email
            FROM keypairs LEFT JOIN users ON users."uuid" = keypairs."user"
            WHERE keypairs.secret_key IS NULL
            ORDER BY keypairs.access_key
        """)
    ).all()
    if doomed:
        log.warning(
            "Deleting %d keypair(s) with no secret key — they cannot sign a request:", len(doomed)
        )
        for access_key, email in doomed:
            log.warning("  %s (owner: %s)", access_key, email or "<unknown>")
        _delete_keypairs(bind, [row.access_key for row in doomed])

    bind.execute(
        sa.text("""
            UPDATE keypairs SET user_id = users.email
            FROM users
            WHERE users."uuid" = keypairs."user" AND keypairs.user_id IS NULL
        """)
    )
    for column, default in _BACKFILLED.items():
        bind.execute(sa.text(f"UPDATE keypairs SET {column} = {default} WHERE {column} IS NULL"))

    for column in _TIGHTENED:
        op.alter_column("keypairs", column, nullable=False)


def downgrade() -> None:
    for column in _TIGHTENED:
        op.alter_column("keypairs", column, nullable=True)
