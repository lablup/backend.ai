"""add ``domain_id`` UUID FK column to ``users``

Adds a ``users.domain_id`` UUID column referencing ``domains.id``,
backfills it from ``domains.name`` via the legacy ``users.domain_name``
column, and drops the old FK that pointed at ``domains.name``. The
legacy ``users.domain_name`` string column is retained without a FK
constraint; its removal is deferred to BA-6122. The ``domains`` primary
key remains ``name`` in this revision — the PK swap is BA-6046.

Revision ID: e8c4d2b96123
Revises: b8a85c96607c
Create Date: 2026-05-21

"""

# Part of: 26.5.0

import sqlalchemy as sa
from alembic import op
from sqlalchemy.engine import Connection

from ai.backend.manager.models.base import GUID

# revision identifiers, used by Alembic.
revision = "e8c4d2b96123"
down_revision = "b8a85c96607c"
branch_labels = None
depends_on = None


_LEGACY_FK_COLUMN = "domain_name"


def _find_fk_name(conn: Connection, table: str, column: str) -> str | None:
    inspector = sa.inspect(conn)
    for fk in inspector.get_foreign_keys(table):
        if fk["constrained_columns"] == [column] and fk["referred_table"] == "domains":
            return fk["name"]
    return None


def upgrade() -> None:
    conn = op.get_bind()

    op.add_column("users", sa.Column("domain_id", GUID(), nullable=True))
    conn.execute(
        sa.text(
            "UPDATE users SET domain_id = domains.id "
            "FROM domains WHERE users.domain_name = domains.name"
        )
    )

    old_fk_name = _find_fk_name(conn, "users", _LEGACY_FK_COLUMN)
    if old_fk_name is not None:
        op.drop_constraint(old_fk_name, "users", type_="foreignkey")

    op.create_foreign_key(
        "fk_users_domain_id_domains",
        "users",
        "domains",
        ["domain_id"],
        ["id"],
    )
    op.create_index("ix_users_domain_id", "users", ["domain_id"])


def downgrade() -> None:
    op.drop_index("ix_users_domain_id", table_name="users")
    op.drop_constraint("fk_users_domain_id_domains", "users", type_="foreignkey")
    op.create_foreign_key(
        "fk_users_domain_name_domains",
        "users",
        "domains",
        ["domain_name"],
        ["name"],
    )
    op.drop_column("users", "domain_id")
