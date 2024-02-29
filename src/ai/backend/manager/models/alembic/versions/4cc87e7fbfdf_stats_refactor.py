"""stats-refactor

Revision ID: 4cc87e7fbfdf
Revises: e18ed5fcfedf
Create Date: 2019-05-30 18:40:17.669756

"""

import math
from datetime import timedelta
from decimal import Decimal

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql
from sqlalchemy.sql.expression import bindparam

from ai.backend.manager.models.base import IDColumn, ResourceSlotColumn, convention

# revision identifiers, used by Alembic.
revision = "4cc87e7fbfdf"
down_revision = "e18ed5fcfedf"
branch_labels = None
depends_on = None


def upgrade():
    metadata = sa.MetaData(naming_convention=convention)

    # previous table def used for migration
    kernels = sa.Table(
        "kernels",
        metadata,
        # preserved and referred columns
        IDColumn(),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), index=True
        ),
        sa.Column(
            "terminated_at",
            sa.DateTime(timezone=True),
            nullable=True,
            default=sa.null(),
            index=True,
        ),
        sa.Column("occupied_slots", ResourceSlotColumn(), nullable=False),
        sa.Column("occupied_shares", postgresql.JSONB(), nullable=False, default={}),
        # old column(s) to be migrated and removed
        sa.Column("cpu_used", sa.BigInteger(), default=0),  # msec
        sa.Column("mem_max_bytes", sa.BigInteger(), default=0),
        sa.Column("net_rx_bytes", sa.BigInteger(), default=0),
        sa.Column("net_tx_bytes", sa.BigInteger(), default=0),
        sa.Column("io_read_bytes", sa.BigInteger(), default=0),
        sa.Column("io_write_bytes", sa.BigInteger(), default=0),
        sa.Column("io_max_scratch_size", sa.BigInteger(), default=0),
        # new column(s) to be added
        sa.Column("last_stat", postgresql.JSONB(), nullable=True, default=sa.null()),
    )

    op.add_column(
        "kernels", sa.Column("last_stat", postgresql.JSONB(astext_type=sa.Text()), nullable=True)
    )

    connection = op.get_bind()
    query = (
        sa.select([
            kernels.c.id,
            kernels.c.created_at,
            kernels.c.terminated_at,
            kernels.c.occupied_slots,
            kernels.c.occupied_shares,
            kernels.c.cpu_used,
            kernels.c.mem_max_bytes,
            kernels.c.net_rx_bytes,
            kernels.c.net_tx_bytes,
            kernels.c.io_read_bytes,
            kernels.c.io_write_bytes,
            kernels.c.io_max_scratch_size,
        ])
        .select_from(kernels)
        .order_by(kernels.c.created_at)
    )
    results = connection.execute(query).fetchall()

    updates = []
    q_pct = Decimal("0.00")
    for row in results:
        if row["terminated_at"] is None:
            cpu_avg_pct = 0
        else:
            cpu_avg_pct = (
                (
                    Decimal(100)
                    * Decimal(
                        timedelta(microseconds=1e3 * row["cpu_used"])
                        / (row["terminated_at"] - row["created_at"])
                    )
                )
                .quantize(q_pct)
                .normalize()
            )
        mem_capacity = 0
        _oslots = row["occupied_slots"]
        if _oslots:
            mem_capacity = _oslots.get("mem")
        if mem_capacity is None or mem_capacity == 0:
            # fallback: try legacy field
            _oshares = row["occupied_shares"]
            mem_capacity = _oshares.get("mem")
        if mem_capacity is None or mem_capacity == 0:
            # fallback: round-up to nearest GiB
            mem_capacity = math.ceil(row["mem_max_bytes"] / (2**30)) * (2**30)
        if mem_capacity is None or mem_capacity == 0:
            # fallback: assume 1 GiB
            mem_capacity = 2**30
        last_stat = {
            "cpu_used": {
                "current": str(row["cpu_used"]),
                "capacity": None,
            },
            "cpu_util": {
                "current": str(cpu_avg_pct),
                "capacity": None,
                "stats.avg": str(cpu_avg_pct),
            },
            "mem": {
                "current": str(row["mem_max_bytes"]),
                "capacity": str(mem_capacity),
                "stats.max": str(row["mem_max_bytes"]),
            },
            "io_read": {
                "current": str(row["io_read_bytes"]),
                "capacity": None,
                "stats.rate": "0",
            },
            "io_write": {
                "current": str(row["io_write_bytes"]),
                "capacity": None,
                "stats.rate": "0",
            },
            "io_scratch_size": {
                "current": str(row["io_max_scratch_size"]),
                "capacity": str(10 * (2**30)),  # 10 GiB
                "stats.max": str(row["io_max_scratch_size"]),
            },
        }
        updates.append({"row_id": row["id"], "last_stat": last_stat})

    if updates:
        query = (
            sa.update(kernels)
            .values(last_stat=bindparam("last_stat"))
            .where(kernels.c.id == bindparam("row_id"))
        )
        connection.execute(query, updates)

    op.drop_column("kernels", "io_max_scratch_size")
    op.drop_column("kernels", "net_rx_bytes")
    op.drop_column("kernels", "net_tx_bytes")
    op.drop_column("kernels", "mem_max_bytes")
    op.drop_column("kernels", "io_write_bytes")
    op.drop_column("kernels", "io_read_bytes")
    op.drop_column("kernels", "cpu_used")


def downgrade():
    metadata = sa.MetaData(naming_convention=convention)

    kernels = sa.Table(
        "kernels",
        metadata,
        # preserved and referred columns
        IDColumn(),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), index=True
        ),
        sa.Column(
            "terminated_at",
            sa.DateTime(timezone=True),
            nullable=True,
            default=sa.null(),
            index=True,
        ),
        sa.Column("occupied_slots", ResourceSlotColumn(), nullable=False),
        sa.Column("occupied_shares", postgresql.JSONB(), nullable=False, default={}),
        # old column(s) to be migrated
        sa.Column("last_stat", postgresql.JSONB(), nullable=True, default=sa.null()),
        # new column(s) to be added
        sa.Column("cpu_used", sa.BigInteger(), default=0),  # msec
        sa.Column("mem_max_bytes", sa.BigInteger(), default=0),
        sa.Column("net_rx_bytes", sa.BigInteger(), default=0),
        sa.Column("net_tx_bytes", sa.BigInteger(), default=0),
        sa.Column("io_read_bytes", sa.BigInteger(), default=0),
        sa.Column("io_write_bytes", sa.BigInteger(), default=0),
        sa.Column("io_max_scratch_size", sa.BigInteger(), default=0),
    )

    op.add_column("kernels", sa.Column("cpu_used", sa.BIGINT(), autoincrement=False, nullable=True))
    op.add_column(
        "kernels", sa.Column("io_read_bytes", sa.BIGINT(), autoincrement=False, nullable=True)
    )
    op.add_column(
        "kernels", sa.Column("io_write_bytes", sa.BIGINT(), autoincrement=False, nullable=True)
    )
    op.add_column(
        "kernels", sa.Column("mem_max_bytes", sa.BIGINT(), autoincrement=False, nullable=True)
    )
    op.add_column(
        "kernels", sa.Column("net_tx_bytes", sa.BIGINT(), autoincrement=False, nullable=True)
    )
    op.add_column(
        "kernels", sa.Column("net_rx_bytes", sa.BIGINT(), autoincrement=False, nullable=True)
    )
    op.add_column(
        "kernels", sa.Column("io_max_scratch_size", sa.BIGINT(), autoincrement=False, nullable=True)
    )

    # Restore old stats
    connection = op.get_bind()
    query = sa.select([kernels.c.id, kernels.c.last_stat]).select_from(kernels)
    results = connection.execute(query).fetchall()
    updates = []
    for row in results:
        last_stat = row["last_stat"]
        updates.append({
            "row_id": row["id"],
            "cpu_used": Decimal(last_stat["cpu_used"]["current"]),
            "io_read_bytes": int(last_stat["io_read"]["current"]),
            "io_write_bytes": int(last_stat["io_write"]["current"]),
            "mem_max_bytes": int(last_stat["mem"]["stats.max"]),
            "io_max_scratch_size": int(last_stat["io_scratch_size"]["stats.max"]),
        })
    if updates:
        query = (
            sa.update(kernels)
            .values({
                "cpu_used": bindparam("cpu_used"),
                "io_read_bytes": bindparam("io_read_bytes"),
                "io_write_bytes": bindparam("io_write_bytes"),
                "mem_max_bytes": bindparam("mem_max_bytes"),
                "net_tx_bytes": 0,
                "net_rx_bytes": 0,
                "io_max_scratch_size": bindparam("io_max_scratch_size"),
            })
            .where(kernels.c.id == bindparam("row_id"))
        )
        connection.execute(query, updates)

    op.drop_column("kernels", "last_stat")
