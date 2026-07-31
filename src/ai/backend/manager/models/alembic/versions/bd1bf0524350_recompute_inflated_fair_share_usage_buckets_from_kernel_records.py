"""recompute inflated fair-share usage buckets from kernel records

Backport of main's ``c4a91d7e05b2`` to the 26.4 line.  The aggregator summed
amounts and durations separately and multiplied them afterwards, so both the
JSONB ``resource_usage`` mirror and the normalized entries hold a cross
product.  Neither can be corrected in place, so both are rebuilt from
``kernel_usage_records``, which was never affected.

``usage_bucket_entries.amount`` becomes ``resource_usage`` (the name the JSONB
mirror and the three bucket tables already use) and drops its precision limit,
now holding the product directly instead of a factor to multiply back out.
``duration_seconds`` is dropped: nothing read it on its own once the product is
stored directly.

This branch predates the ``resource_group_id`` columns, so the rebuild joins on
the ``resource_group`` name, which is the bucket uniqueness key here.

Revision ID: bd1bf0524350
Revises: daf20413acda
Create Date: 2026-07-28 00:00:00.000000

"""

import logging
from datetime import date, timedelta

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "bd1bf0524350"
down_revision = "daf20413acda"
# Part of: 26.8.0
branch_labels = None
depends_on = None

log = logging.getLogger("alembic.runtime.migration")


def upgrade() -> None:
    # Schema change: amount -> resource_usage (now the product, so no fixed
    # precision), and duration_seconds is no longer needed.  Guarded with existence
    # checks so the migration stays idempotent (safe to re-apply).
    conn = op.get_bind()
    columns = {c["name"] for c in sa.inspect(conn).get_columns("usage_bucket_entries")}
    if "amount" in columns and "resource_usage" not in columns:
        op.alter_column(
            "usage_bucket_entries",
            "amount",
            new_column_name="resource_usage",
            existing_type=sa.Numeric(precision=24, scale=6),
            type_=sa.Numeric(),
            existing_nullable=False,
        )
    if "duration_seconds" in columns:
        op.drop_column("usage_bucket_entries", "duration_seconds")

    # Data change: rebuild the corrupted values from kernel_usage_records.
    # kernel_usage_records is by far the largest table, so it is scanned once into a
    # per-entity-per-day temp table; the three bucket levels then roll up from that
    # small intermediate instead of each re-scanning the raw records.
    window = _rebuildable_date_range(conn)
    if window is None:
        # No usage records to rebuild from (fresh install, or everything purged).
        return
    rebuild_from, rebuild_to = window
    _purge_corrupted_usage(conn, rebuild_from, rebuild_to)
    _aggregate_kernel_records(conn, rebuild_from, rebuild_to)
    _rebuild_user_buckets(conn, rebuild_from, rebuild_to)
    _rebuild_project_buckets(conn, rebuild_from, rebuild_to)
    _rebuild_domain_buckets(conn, rebuild_from, rebuild_to)


def downgrade() -> None:
    # Guarded for idempotency (both directions must be safe to re-apply).
    conn = op.get_bind()
    columns = {c["name"] for c in sa.inspect(conn).get_columns("usage_bucket_entries")}
    if "duration_seconds" not in columns:
        op.add_column(
            "usage_bucket_entries",
            sa.Column("duration_seconds", sa.Integer(), nullable=False, server_default="0"),
        )
    # The rebuilt values are the correct ones and the inflated originals cannot
    # be reconstructed, so only the column definition is reverted.  Values that
    # exceed the restored precision will fail the cast, which is the honest
    # outcome: they do not fit the old column.
    if "resource_usage" in columns:
        op.alter_column(
            "usage_bucket_entries",
            "resource_usage",
            new_column_name="amount",
            existing_type=sa.Numeric(),
            type_=sa.Numeric(precision=24, scale=6),
            existing_nullable=False,
        )
        log.warning(
            "usage_bucket_entries is left corrupt by this downgrade: the column restored to "
            "'amount' now holds resource-seconds products, not raw amounts, and "
            "duration_seconds is reset to 0. Re-apply revision %s to rebuild the correct "
            "values from kernel_usage_records.",
            revision,
        )


def _rebuildable_date_range(conn: sa.engine.Connection) -> tuple[date, date] | None:
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


def _purge_corrupted_usage(
    conn: sa.engine.Connection, rebuild_from: date, rebuild_to: date
) -> None:
    """Delete every corrupted entry the rebuild will replace, across all levels.

    Each entry belongs to exactly one bucket via ``bucket_id``, so listing the
    in-window buckets of the three tables and deleting entries that point at them
    clears user, project and domain in a single statement.  The rebuild then starts
    from a clean slate and only needs to insert.
    """
    conn.execute(
        sa.text(
            """
            DELETE FROM usage_bucket_entries
            WHERE (bucket_id, bucket_type) IN (
                SELECT id, 'user' FROM user_usage_buckets
                 WHERE period_start BETWEEN :rebuild_from AND :rebuild_to
                UNION ALL
                SELECT id, 'project' FROM project_usage_buckets
                 WHERE period_start BETWEEN :rebuild_from AND :rebuild_to
                UNION ALL
                SELECT id, 'domain' FROM domain_usage_buckets
                 WHERE period_start BETWEEN :rebuild_from AND :rebuild_to
            )
            """
        ),
        {"rebuild_from": rebuild_from, "rebuild_to": rebuild_to},
    )


def _aggregate_kernel_records(
    conn: sa.engine.Connection, rebuild_from: date, rebuild_to: date
) -> None:
    """Scan kernel_usage_records once into a per-(entity, day, slot) temp table.

    kernel_usage_records is the largest table and cannot be indexed for the
    per-day rebuild (the day is a functional expression on ``period_start``), so it
    is scanned a single time here.  The three bucket levels roll up from
    ``_daily_kernel_usage`` (roughly entities * days * slots rows) instead of
    re-scanning the raw records.  ``_daily_kernel_usage`` holds the finest grain
    that carries every level's key columns.
    """
    conn.execute(
        sa.text(
            """
            CREATE TEMP TABLE _daily_kernel_usage ON COMMIT DROP AS
            SELECT user_uuid, project_id, domain_name, resource_group,
                   (period_start AT TIME ZONE 'UTC')::date AS period_date,
                   kv.key AS slot_name,
                   SUM(kv.value::numeric) AS resource_usage
            FROM kernel_usage_records, LATERAL jsonb_each_text(resource_usage) AS kv
            WHERE (period_start AT TIME ZONE 'UTC')::date BETWEEN :rebuild_from AND :rebuild_to
            GROUP BY user_uuid, project_id, domain_name, resource_group, period_date, kv.key
            """
        ),
        {"rebuild_from": rebuild_from, "rebuild_to": rebuild_to},
    )
    conn.execute(sa.text("ANALYZE _daily_kernel_usage"))


def _sync_jsonb_mirror(
    conn: sa.engine.Connection,
    bucket_table: str,
    bucket_type: str,
    rebuild_from: date,
    rebuild_to: date,
) -> None:
    """Rebuild one bucket table's JSONB mirror from its freshly rebuilt entries.

    Set-based (one aggregation of the entries, not a per-bucket correlated subquery):
    buckets with entries get their slot map; in-window buckets left without entries
    are reset to an empty object so no stale inflated value survives.
    """
    params = {"rebuild_from": rebuild_from, "rebuild_to": rebuild_to, "bucket_type": bucket_type}
    # Buckets that have rebuilt entries: set the slot map.  ResourceSlotColumn stores
    # JSONB values as strings, so cast to text; a JSON number would be read back as a
    # float and lose precision.
    conn.execute(
        sa.text(
            f"""
            UPDATE {bucket_table} AS b
            SET resource_usage = agg.usage
            FROM (
                SELECT bucket_id,
                       jsonb_object_agg(slot_name, resource_usage::text) AS usage
                FROM usage_bucket_entries
                WHERE bucket_type = :bucket_type
                GROUP BY bucket_id
            ) AS agg
            WHERE b.id = agg.bucket_id
              AND b.period_start BETWEEN :rebuild_from AND :rebuild_to
            """
        ),
        params,
    )
    # In-window buckets left without entries: clear the stale (inflated) mirror.
    conn.execute(
        sa.text(
            f"""
            UPDATE {bucket_table} AS b
            SET resource_usage = '{{}}'::jsonb
            WHERE b.period_start BETWEEN :rebuild_from AND :rebuild_to
              AND NOT EXISTS (
                  SELECT 1 FROM usage_bucket_entries e
                  WHERE e.bucket_id = b.id AND e.bucket_type = :bucket_type
              )
            """
        ),
        params,
    )


def _rebuild_user_buckets(conn: sa.engine.Connection, rebuild_from: date, rebuild_to: date) -> None:
    """Roll _daily_kernel_usage up to user buckets, then sync the JSONB mirror."""
    conn.execute(
        sa.text(
            """
            INSERT INTO usage_bucket_entries
                (bucket_id, bucket_type, slot_name, resource_usage, capacity)
            SELECT user_usage_buckets.id, 'user', _daily_kernel_usage.slot_name,
                   SUM(_daily_kernel_usage.resource_usage), 0
            FROM user_usage_buckets
            JOIN _daily_kernel_usage
              ON _daily_kernel_usage.user_uuid = user_usage_buckets.user_uuid
             AND _daily_kernel_usage.project_id = user_usage_buckets.project_id
             AND _daily_kernel_usage.resource_group = user_usage_buckets.resource_group
             AND _daily_kernel_usage.period_date = user_usage_buckets.period_start
            GROUP BY user_usage_buckets.id, _daily_kernel_usage.slot_name
            """
        )
    )
    _sync_jsonb_mirror(conn, "user_usage_buckets", "user", rebuild_from, rebuild_to)


def _rebuild_project_buckets(
    conn: sa.engine.Connection, rebuild_from: date, rebuild_to: date
) -> None:
    """Roll _daily_kernel_usage up to project buckets, then sync the JSONB mirror."""
    conn.execute(
        sa.text(
            """
            INSERT INTO usage_bucket_entries
                (bucket_id, bucket_type, slot_name, resource_usage, capacity)
            SELECT project_usage_buckets.id, 'project', _daily_kernel_usage.slot_name,
                   SUM(_daily_kernel_usage.resource_usage), 0
            FROM project_usage_buckets
            JOIN _daily_kernel_usage
              ON _daily_kernel_usage.project_id = project_usage_buckets.project_id
             AND _daily_kernel_usage.resource_group = project_usage_buckets.resource_group
             AND _daily_kernel_usage.period_date = project_usage_buckets.period_start
            GROUP BY project_usage_buckets.id, _daily_kernel_usage.slot_name
            """
        )
    )
    _sync_jsonb_mirror(conn, "project_usage_buckets", "project", rebuild_from, rebuild_to)


def _rebuild_domain_buckets(
    conn: sa.engine.Connection, rebuild_from: date, rebuild_to: date
) -> None:
    """Roll _daily_kernel_usage up to domain buckets, then sync the JSONB mirror."""
    conn.execute(
        sa.text(
            """
            INSERT INTO usage_bucket_entries
                (bucket_id, bucket_type, slot_name, resource_usage, capacity)
            SELECT domain_usage_buckets.id, 'domain', _daily_kernel_usage.slot_name,
                   SUM(_daily_kernel_usage.resource_usage), 0
            FROM domain_usage_buckets
            JOIN _daily_kernel_usage
              ON _daily_kernel_usage.domain_name = domain_usage_buckets.domain_name
             AND _daily_kernel_usage.resource_group = domain_usage_buckets.resource_group
             AND _daily_kernel_usage.period_date = domain_usage_buckets.period_start
            GROUP BY domain_usage_buckets.id, _daily_kernel_usage.slot_name
            """
        )
    )
    _sync_jsonb_mirror(conn, "domain_usage_buckets", "domain", rebuild_from, rebuild_to)
