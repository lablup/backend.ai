"""recompute inflated fair-share usage buckets from kernel records

The aggregator summed amounts and durations separately and multiplied them
afterwards, so both the JSONB ``resource_usage`` mirror and the normalized
entries hold a cross product.  Neither can be corrected in place, so both are
rebuilt from ``kernel_usage_records``, which was never affected.

``usage_bucket_entries.amount`` becomes ``resource_usage``, matching what the
JSONB mirror on ``kernel_usage_records`` and the three bucket tables already call
this quantity, and drops its precision limit.  It now holds the product directly
rather than a factor readers had to multiply back out: a domain-level daily mem
bucket runs past any fixed precision, and unconstrained NUMERIC has no ceiling.

``duration_seconds`` goes with it.  It only ever existed to reconstitute that
product, no reader consulted it on its own, and it counted kernel-seconds rather
than wall-clock, so leaving it would leave a column that invites the same
misreading the product form did.

Revision ID: c4a91d7e05b2
Revises: c4e1a7f9b26d
Create Date: 2026-07-20 00:00:00.000000

"""

import logging
from datetime import date, timedelta

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "c4a91d7e05b2"
down_revision = "c4e1a7f9b26d"
# Part of: NEXT_RELEASE_VERSION
branch_labels = None
depends_on = None

log = logging.getLogger("alembic.runtime.migration")


def upgrade() -> None:
    # Schema change: amount -> resource_usage (now the product, so no fixed
    # precision), and duration_seconds is no longer needed.
    op.alter_column(
        "usage_bucket_entries",
        "amount",
        new_column_name="resource_usage",
        existing_type=sa.Numeric(precision=24, scale=6),
        type_=sa.Numeric(),
        existing_nullable=False,
    )
    # Fold the old (amount, duration_seconds) pair into the product for every row.
    # In-window rows are rebuilt below, but out-of-window rows are not; without this
    # they would keep a raw amount that the new read path misreads as resource-seconds.
    # amount * duration_seconds equals the value the JSONB mirror already holds, so the
    # two representations stay consistent.  The duration_seconds <> 0 guard keeps a
    # downgrade -> upgrade rerun a no-op (downgrade restores duration_seconds to 0).
    op.execute(
        "UPDATE usage_bucket_entries SET resource_usage = resource_usage * duration_seconds "
        "WHERE duration_seconds <> 0"
    )
    op.drop_column("usage_bucket_entries", "duration_seconds")

    # Data change: rebuild the corrupted values from kernel_usage_records.
    # Delete every corrupted entry first (all levels at once), then rebuild each
    # level.  Each level writes its own entries (their join keys genuinely differ),
    # then hands the shared JSONB-mirror step to _sync_jsonb_mirror.
    conn = op.get_bind()
    window = _rebuildable_date_range(conn)
    if window is None:
        # No usage records to rebuild from (fresh install, or everything purged).
        return
    rebuild_from, rebuild_to = window
    _purge_corrupted_usage(conn, rebuild_from, rebuild_to)
    _rebuild_user_buckets(conn, rebuild_from, rebuild_to)
    _rebuild_project_buckets(conn, rebuild_from, rebuild_to)
    _rebuild_domain_buckets(conn, rebuild_from, rebuild_to)


def downgrade() -> None:
    op.add_column(
        "usage_bucket_entries",
        sa.Column("duration_seconds", sa.Integer(), nullable=False, server_default="0"),
    )
    # The rebuilt values are the correct ones and the inflated originals cannot
    # be reconstructed, so only the column definition is reverted.  Values that
    # exceed the restored precision will fail the cast, which is the honest
    # outcome: they do not fit the old column.
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


def _sync_jsonb_mirror(
    conn: sa.engine.Connection,
    bucket_table: str,
    bucket_type: str,
    rebuild_from: date,
    rebuild_to: date,
) -> None:
    """Rebuild one bucket table's JSONB mirror from its freshly rebuilt entries.

    The mirror is just the slot map of the bucket's entries, or an empty object
    when the bucket has no kernel records left to rebuild from.  This step is
    identical for every level once the entries exist, so all three call it.
    """
    conn.execute(
        sa.text(
            f"""
            UPDATE {bucket_table}
            SET resource_usage = COALESCE(
                (
                    -- ResourceSlotColumn stores JSONB values as strings, so cast to
                    -- text; a JSON number would be read back as a float and lose precision.
                    SELECT jsonb_object_agg(
                               usage_bucket_entries.slot_name,
                               usage_bucket_entries.resource_usage::text
                           )
                    FROM usage_bucket_entries
                    WHERE usage_bucket_entries.bucket_id = {bucket_table}.id
                      AND usage_bucket_entries.bucket_type = :bucket_type
                ),
                jsonb_build_object()
            )
            WHERE {bucket_table}.period_start BETWEEN :rebuild_from AND :rebuild_to
            """
        ),
        {"rebuild_from": rebuild_from, "rebuild_to": rebuild_to, "bucket_type": bucket_type},
    )


def _rebuild_user_buckets(conn: sa.engine.Connection, rebuild_from: date, rebuild_to: date) -> None:
    """Recompute user bucket entries, then rebuild their JSONB mirror."""
    # Insert one entry per (bucket, slot), summing the per-slice resource-seconds
    # that kernel_usage_records already stores correctly.  capacity is refilled by
    # the next observation tick, so 0 here is safe.
    conn.execute(
        sa.text(
            """
            INSERT INTO usage_bucket_entries
                (bucket_id, bucket_type, slot_name, resource_usage, capacity)
            SELECT user_usage_buckets.id, 'user', slot.key, SUM(slot.value::numeric), 0
            FROM user_usage_buckets
            JOIN kernel_usage_records
              ON kernel_usage_records.user_uuid = user_usage_buckets.user_uuid
             AND kernel_usage_records.project_id = user_usage_buckets.project_id
             AND kernel_usage_records.resource_group_id = user_usage_buckets.resource_group_id
             AND (kernel_usage_records.period_start AT TIME ZONE 'UTC')::date
                 = user_usage_buckets.period_start
            CROSS JOIN LATERAL jsonb_each_text(kernel_usage_records.resource_usage) AS slot
            WHERE user_usage_buckets.period_start BETWEEN :rebuild_from AND :rebuild_to
            GROUP BY user_usage_buckets.id, slot.key
            """
        ),
        {"rebuild_from": rebuild_from, "rebuild_to": rebuild_to},
    )
    _sync_jsonb_mirror(conn, "user_usage_buckets", "user", rebuild_from, rebuild_to)


def _rebuild_project_buckets(
    conn: sa.engine.Connection, rebuild_from: date, rebuild_to: date
) -> None:
    """Recompute project bucket entries, then rebuild their JSONB mirror."""
    conn.execute(
        sa.text(
            """
            INSERT INTO usage_bucket_entries
                (bucket_id, bucket_type, slot_name, resource_usage, capacity)
            SELECT project_usage_buckets.id, 'project', slot.key, SUM(slot.value::numeric), 0
            FROM project_usage_buckets
            JOIN kernel_usage_records
              ON kernel_usage_records.project_id = project_usage_buckets.project_id
             AND kernel_usage_records.resource_group_id = project_usage_buckets.resource_group_id
             AND (kernel_usage_records.period_start AT TIME ZONE 'UTC')::date
                 = project_usage_buckets.period_start
            CROSS JOIN LATERAL jsonb_each_text(kernel_usage_records.resource_usage) AS slot
            WHERE project_usage_buckets.period_start BETWEEN :rebuild_from AND :rebuild_to
            GROUP BY project_usage_buckets.id, slot.key
            """
        ),
        {"rebuild_from": rebuild_from, "rebuild_to": rebuild_to},
    )
    _sync_jsonb_mirror(conn, "project_usage_buckets", "project", rebuild_from, rebuild_to)


def _rebuild_domain_buckets(
    conn: sa.engine.Connection, rebuild_from: date, rebuild_to: date
) -> None:
    """Recompute domain bucket entries, then rebuild their JSONB mirror."""
    conn.execute(
        sa.text(
            """
            INSERT INTO usage_bucket_entries
                (bucket_id, bucket_type, slot_name, resource_usage, capacity)
            SELECT domain_usage_buckets.id, 'domain', slot.key, SUM(slot.value::numeric), 0
            FROM domain_usage_buckets
            JOIN kernel_usage_records
              ON kernel_usage_records.domain_name = domain_usage_buckets.domain_name
             AND kernel_usage_records.resource_group_id = domain_usage_buckets.resource_group_id
             AND (kernel_usage_records.period_start AT TIME ZONE 'UTC')::date
                 = domain_usage_buckets.period_start
            CROSS JOIN LATERAL jsonb_each_text(kernel_usage_records.resource_usage) AS slot
            WHERE domain_usage_buckets.period_start BETWEEN :rebuild_from AND :rebuild_to
            GROUP BY domain_usage_buckets.id, slot.key
            """
        ),
        {"rebuild_from": rebuild_from, "rebuild_to": rebuild_to},
    )
    _sync_jsonb_mirror(conn, "domain_usage_buckets", "domain", rebuild_from, rebuild_to)
