"""drop sessions/kernels access_key columns

Part of BA-5653. The ``access_key`` column is removed from the
``sessions`` and ``kernels`` tables. Downstream code now resolves the
owner's ``main_access_key`` from the ``users`` table when needed
(keypair-scoped concurrency tracking, resource policy lookups, agent
RPC payloads). The ``user_uuid`` column is kept on both tables as the
canonical owner reference; only the redundant ``access_key`` snapshot
is dropped.

Revision ID: 8c1d2e3f4a5b
Revises: 2a531e0c528e
Create Date: 2026-04-14

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "8c1d2e3f4a5b"
down_revision = "2a531e0c528e"
branch_labels = None
depends_on = None


def _column_names(inspector: sa.engine.reflection.Inspector, table: str) -> set[str]:
    return {c["name"] for c in inspector.get_columns(table)}


def _index_names(inspector: sa.engine.reflection.Inspector, table: str) -> set[str]:
    return {ix["name"] for ix in inspector.get_indexes(table) if ix["name"] is not None}


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    for table in ("sessions", "kernels"):
        cols = _column_names(inspector, table)
        if "access_key" not in cols:
            continue
        # Drop any index referencing access_key on this table first.
        for ix_name in _index_names(inspector, table):
            if "access_key" in ix_name:
                op.drop_index(ix_name, table_name=table)
        op.drop_column(table, "access_key")


def downgrade() -> None:
    """Recreate the ``access_key`` columns as nullable.

    NOTE: This downgrade is intentionally lossy. Previous values cannot
    be restored because the upgrade does not preserve them. Callers that
    depended on the old column must resolve ``main_access_key`` via the
    ``users`` table instead.
    """
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    for table in ("sessions", "kernels"):
        cols = _column_names(inspector, table)
        if "access_key" in cols:
            continue
        op.add_column(
            table,
            sa.Column("access_key", sa.String(length=20), nullable=True),
        )
