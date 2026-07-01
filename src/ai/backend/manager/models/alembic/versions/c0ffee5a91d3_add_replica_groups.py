"""add replica_groups table and replica group references

Introduce the ReplicaGroup concept for deployments:

- ``replica_groups`` — one row per group within a deployment. Owns the
  revision pointers (``current_revision_id`` / ``target_revision_id``)
  and the per-revision desired replica counts, plus a ``traffic_weight``.
- ``endpoints.primary_replica_group_id`` / ``target_replica_group_id`` —
  references to the serving group and the group being rolled out
  (no FK; avoids a circular FK with ``replica_groups.deployment_id``).
- ``routings.replica_group_id`` — the group a replica belongs to
  (no FK; relationship only, mirrors ``routings.revision``).

Backfill: create one replica group per existing endpoint (reusing the
endpoint id as the group id for a deterministic 1:1 mapping), migrate the
endpoint's revision pointers and replica count into it, point the
endpoint's ``primary_replica_group_id`` at it, and attach every existing
routing to it.

Create Date: 2026-05-29
"""

import sqlalchemy as sa
from alembic import op

from ai.backend.manager.models.base import GUID

revision = "c0ffee5a91d3"
down_revision = "0113c63f3261"
# Part of: 26.6.0
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "replica_groups",
        sa.Column(
            "id",
            GUID(),
            server_default=sa.text("uuid_generate_v4()"),
            nullable=False,
        ),
        sa.Column("deployment_id", GUID(), nullable=False),
        sa.Column("current_revision_id", GUID(), nullable=True),
        sa.Column("target_revision_id", GUID(), nullable=True),
        sa.Column(
            "desired_current_replica_count",
            sa.Integer(),
            server_default=sa.text("0"),
            nullable=False,
        ),
        sa.Column(
            "desired_target_replica_count",
            sa.Integer(),
            server_default=sa.text("0"),
            nullable=False,
        ),
        sa.Column(
            "traffic_weight",
            sa.Integer(),
            server_default=sa.text("100"),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["deployment_id"],
            ["endpoints.id"],
            name=op.f("fk_replica_groups_deployment_id_endpoints"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_replica_groups")),
    )
    op.create_index(
        "ix_replica_groups_deployment_id",
        "replica_groups",
        ["deployment_id"],
    )

    op.add_column(
        "endpoints",
        sa.Column("primary_replica_group_id", GUID(), nullable=True),
    )
    op.add_column(
        "endpoints",
        sa.Column("target_replica_group_id", GUID(), nullable=True),
    )

    op.add_column(
        "routings",
        sa.Column("replica_group_id", GUID(), nullable=True),
    )
    op.create_index(
        "ix_routings_replica_group_id",
        "routings",
        ["replica_group_id"],
    )

    # Backfill: one replica group per endpoint, reusing the endpoint id as
    # the group id for a deterministic 1:1 mapping. Active endpoints get the
    # default traffic weight (100) so their lone group keeps serving traffic;
    # destroyed endpoints are left at weight 0 since they no longer route.
    op.execute("""
        INSERT INTO replica_groups (
            id, deployment_id, current_revision_id, target_revision_id,
            desired_current_replica_count, desired_target_replica_count,
            traffic_weight, created_at, updated_at
        )
        SELECT
            e.id, e.id, e.current_revision, e.deploying_revision,
            COALESCE(e.desired_replicas, e.replicas), 0,
            CASE WHEN e.lifecycle_stage = 'destroyed' THEN 0 ELSE 100 END,
            now(), now()
        FROM endpoints e
    """)
    op.execute("UPDATE endpoints SET primary_replica_group_id = id")
    op.execute("UPDATE routings SET replica_group_id = endpoint")


def downgrade() -> None:
    op.drop_index("ix_routings_replica_group_id", table_name="routings")
    op.drop_column("routings", "replica_group_id")
    op.drop_column("endpoints", "target_replica_group_id")
    op.drop_column("endpoints", "primary_replica_group_id")
    op.drop_index("ix_replica_groups_deployment_id", table_name="replica_groups")
    op.drop_table("replica_groups")
