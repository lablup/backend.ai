"""tighten the always-populated keypairs columns

``is_admin`` and ``num_queries`` have a default, so a null there is backfilled.
The others do not: a keypair missing ``user_id``, ``secret_key`` or ``is_active``
is deleted rather than given an invented value.

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
    "is_admin": "false",
    "num_queries": "0",
}
_REQUIRED = (
    "user_id",
    "secret_key",
    "is_active",
)
_TIGHTENED = (*_REQUIRED, *_BACKFILLED)


def _delete_keypairs_missing_a_required_value(bind: Connection) -> None:
    any_missing = " OR ".join(f"k.{column} IS NULL" for column in _REQUIRED)
    which_missing = ", ".join(f"CASE WHEN k.{c} IS NULL THEN '{c}' END" for c in _REQUIRED)
    doomed = bind.execute(
        sa.text(f"""
            SELECT k.access_key, u.email, array_remove(ARRAY[{which_missing}], NULL) AS missing
            FROM keypairs k LEFT JOIN users u ON u."uuid" = k."user"
            WHERE {any_missing}
            ORDER BY k.access_key
        """)
    ).all()
    if not doomed:
        return

    log.warning(
        "Deleting %d keypair(s) with a null in a column that has no default to backfill from:",
        len(doomed),
    )
    for access_key, email, missing in doomed:
        log.warning(
            "  %s (owner: %s) missing %s", access_key, email or "<unknown>", ", ".join(missing)
        )

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
    _delete_keypairs_missing_a_required_value(bind)
    for column, default in _BACKFILLED.items():
        bind.execute(sa.text(f"UPDATE keypairs SET {column} = {default} WHERE {column} IS NULL"))

    for column in _TIGHTENED:
        op.alter_column("keypairs", column, nullable=False)


def downgrade() -> None:
    for column in _TIGHTENED:
        op.alter_column("keypairs", column, nullable=True)
