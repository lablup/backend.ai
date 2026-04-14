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


def upgrade() -> None:
    # The (access_key, sess_id) partial unique index on ``kernels`` references the
    # column being dropped — remove it first.
    op.drop_index("ix_kernels_unique_sess_token", table_name="kernels")
    op.drop_column("kernels", "access_key")
    op.drop_column("sessions", "access_key")


def downgrade() -> None:
    """Recreate the ``access_key`` columns as nullable.

    NOTE: This downgrade is intentionally lossy. Previous values cannot
    be restored because the upgrade does not preserve them. Callers that
    depended on the old column must resolve ``main_access_key`` via the
    ``users`` table instead.
    """
    op.add_column(
        "sessions",
        sa.Column("access_key", sa.String(length=20), nullable=True),
    )
    op.add_column(
        "kernels",
        sa.Column("access_key", sa.String(length=20), nullable=True),
    )
    op.create_index(
        op.f("ix_kernels_unique_sess_token"),
        "kernels",
        ["access_key", "sess_id"],
        unique=True,
        postgresql_where=sa.text("kernels.status != 'TERMINATED' and kernels.role = 'master'"),
    )
