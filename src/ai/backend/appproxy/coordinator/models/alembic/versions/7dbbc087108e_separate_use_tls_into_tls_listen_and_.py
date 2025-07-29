"""separate use_tls into tls_listen and tls_advertised

Revision ID: 7dbbc087108e
Revises: 66f87e010f90
Create Date: 2025-03-31 18:00:24.074776

"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.sql.expression import bindparam

from ai.backend.appproxy.coordinator.models.base import GUID, convention

# revision identifiers, used by Alembic.
revision = "7dbbc087108e"
down_revision = "66f87e010f90"
branch_labels = None
depends_on = None


metadata = sa.MetaData(naming_convention=convention)


def upgrade():
    workers = sa.Table(
        "workers",
        metadata,
        sa.Column("id", GUID),
        sa.Column("use_tls", sa.BOOLEAN()),
        sa.Column("tls_advertised", sa.BOOLEAN()),
    )

    op.add_column(
        "workers", sa.Column("tls_listen", sa.BOOLEAN(), nullable=False, server_default="false")
    )
    op.add_column(
        "workers", sa.Column("tls_advertised", sa.BOOLEAN(), nullable=False, server_default="false")
    )
    conn = op.get_bind()
    query = sa.select(workers)
    updates = [
        {"wid": row.id, "tls_advertised": row.use_tls} for row in conn.execute(query).fetchall()
    ]
    if updates:
        query = (
            sa.update(workers)
            .values(tls_advertised=bindparam("tls_advertised"))
            .where(workers.c.id == bindparam("wid"))
        )
        conn.execute(query, updates)

    op.drop_column("workers", "use_tls")


def downgrade():
    op.add_column(
        "workers", sa.Column("use_tls", sa.BOOLEAN(), autoincrement=False, nullable=False)
    )

    op.drop_column("workers", "tls_advertised")
    op.drop_column("workers", "tls_listen")
