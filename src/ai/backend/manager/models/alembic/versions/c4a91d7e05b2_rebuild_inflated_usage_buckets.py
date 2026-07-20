"""rebuild inflated usage buckets

The aggregator summed amounts and durations separately and multiplied them
afterwards, so both the JSONB ``resource_usage`` mirror and the normalized
entries hold a cross product.  Neither can be corrected in place, so both are
rebuilt from ``kernel_usage_records``, which was never affected.

``usage_bucket_entries.amount`` also widens, because a domain-level daily mem
bucket can exceed the previous 24-digit ceiling.

Revision ID: c4a91d7e05b2
Revises: 3f9a1c7b2e04
Create Date: 2026-07-20 00:00:00.000000

"""

from datetime import date, timedelta

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "c4a91d7e05b2"
down_revision = "3f9a1c7b2e04"
# Part of: NEXT_RELEASE_VERSION
branch_labels = None
depends_on = None


# Bucket tables keyed by the columns that identify the owning entity.  Every key
# column has the same name in kernel_usage_records, so the join is by name.
_BUCKET_LEVELS: list[tuple[str, str, list[str]]] = [
    ("user_usage_buckets", "user", ["user_uuid", "project_id", "resource_group"]),
    ("project_usage_buckets", "project", ["project_id", "resource_group"]),
    ("domain_usage_buckets", "domain", ["domain_name", "resource_group"]),
]


def upgrade() -> None:
    op.alter_column(
        "usage_bucket_entries",
        "amount",
        existing_type=sa.Numeric(precision=24, scale=6),
        type_=sa.Numeric(precision=32, scale=6),
        existing_nullable=False,
    )

    conn = op.get_bind()
    covered = _covered_date_range(conn)
    if covered is None:
        # No usage records to rebuild from (fresh install, or everything purged).
        return
    rebuild_from, rebuild_to = covered
    for table_name, bucket_type, key_columns in _BUCKET_LEVELS:
        _rebuild_buckets(conn, table_name, bucket_type, key_columns, rebuild_from, rebuild_to)


def downgrade() -> None:
    # Keeps the rebuilt values; only the widened precision is reverted.
    op.alter_column(
        "usage_bucket_entries",
        "amount",
        existing_type=sa.Numeric(precision=32, scale=6),
        type_=sa.Numeric(precision=24, scale=6),
        existing_nullable=False,
    )


def _covered_date_range(conn: sa.engine.Connection) -> tuple[date, date] | None:
    """Return the date range that kernel_usage_records can faithfully rebuild.

    The oldest retained day is excluded because retention purges by ``period_end``
    and may have truncated it.  Buckets outside the range keep their inflated
    values rather than being zeroed: they are unrecoverable, and zeroing them
    would destroy the only usage history left.
    """
    row = conn.execute(
        sa.text(
            "SELECT min((period_start AT TIME ZONE 'UTC')::date) AS min_date, "
            "       max((period_start AT TIME ZONE 'UTC')::date) AS max_date "
            "FROM kernel_usage_records"
        )
    ).one()
    if row.min_date is None or row.max_date is None:
        return None
    rebuild_from = row.min_date + timedelta(days=1)
    if rebuild_from > row.max_date:
        return None
    return rebuild_from, row.max_date


def _rebuild_buckets(
    conn: sa.engine.Connection,
    table_name: str,
    bucket_type: str,
    key_columns: list[str],
    rebuild_from: date,
    rebuild_to: date,
) -> None:
    """Recompute one bucket level's entries and JSONB from kernel_usage_records."""
    key_list = ", ".join(key_columns)
    join_on = " AND ".join(f"b.{col} = agg.{col}" for col in key_columns)
    params = {"rebuild_from": rebuild_from, "rebuild_to": rebuild_to}

    # Per-slot resource-seconds, summed over every kernel slice of the day.
    agg_cte = f"""
        WITH agg AS (
            SELECT {key_list},
                   (period_start AT TIME ZONE 'UTC')::date AS period_date,
                   kv.key AS slot_name,
                   SUM(kv.value::numeric) AS resource_seconds
            FROM kernel_usage_records,
                 LATERAL jsonb_each_text(resource_usage) AS kv
            WHERE (period_start AT TIME ZONE 'UTC')::date
                  BETWEEN :rebuild_from AND :rebuild_to
            GROUP BY {key_list}, period_date, kv.key
        )
    """

    # capacity is refilled by the next observation tick, so dropping it is safe.
    conn.execute(
        sa.text(
            f"""
            DELETE FROM usage_bucket_entries e
            USING {table_name} b
            WHERE e.bucket_id = b.id
              AND e.bucket_type = :bucket_type
              AND b.period_start BETWEEN :rebuild_from AND :rebuild_to
            """
        ),
        {**params, "bucket_type": bucket_type},
    )
    conn.execute(
        sa.text(
            f"""
            {agg_cte}
            INSERT INTO usage_bucket_entries
                (bucket_id, bucket_type, slot_name, amount, duration_seconds, capacity)
            SELECT b.id, :bucket_type, agg.slot_name, agg.resource_seconds, 0, 0
            FROM agg
            JOIN {table_name} b
              ON {join_on}
             AND b.period_start = agg.period_date
            ON CONFLICT (bucket_id, slot_name) DO UPDATE
                SET amount = EXCLUDED.amount
            """
        ),
        {**params, "bucket_type": bucket_type},
    )

    # Buckets with no matching kernel records collapse to an empty slot map.
    conn.execute(
        sa.text(
            f"""
            {agg_cte},
            per_bucket AS (
                SELECT {key_list}, period_date,
                       jsonb_object_agg(slot_name, resource_seconds) AS usage
                FROM agg
                GROUP BY {key_list}, period_date
            )
            UPDATE {table_name} b
            SET resource_usage = COALESCE(agg.usage, '{{}}'::jsonb)
            FROM per_bucket agg
            WHERE {join_on}
              AND b.period_start = agg.period_date
              AND b.period_start BETWEEN :rebuild_from AND :rebuild_to
            """
        ),
        params,
    )
    conn.execute(
        sa.text(
            f"""
            UPDATE {table_name} b
            SET resource_usage = '{{}}'::jsonb
            WHERE b.period_start BETWEEN :rebuild_from AND :rebuild_to
              AND NOT EXISTS (
                  SELECT 1 FROM usage_bucket_entries e
                  WHERE e.bucket_id = b.id AND e.bucket_type = :bucket_type
              )
            """
        ),
        {**params, "bucket_type": bucket_type},
    )
