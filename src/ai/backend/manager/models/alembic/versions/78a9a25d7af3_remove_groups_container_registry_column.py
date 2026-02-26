"""remove groups.container_registry jsonb column

Revision ID: 78a9a25d7af3
Revises: ffcf0ed13a26
Create Date: 2026-02-26 00:00:00.000000

"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "78a9a25d7af3"
down_revision = "ffcf0ed13a26"
branch_labels = None
depends_on = None


def upgrade() -> None:
    conn = op.get_bind()

    # Migrate existing container_registry JSONB data into the association table.
    # The JSONB column stores {"registry": "<hostname>", "project": "<name>"}.
    # We match against the container_registries table and insert into the
    # junction table (association_container_registries_groups) if not already present.
    conn.execute(
        sa.text("""
            INSERT INTO association_container_registries_groups (registry_id, group_id)
            SELECT cr.id, g.id
            FROM groups g
            JOIN container_registries cr
              ON cr.registry_name = g.container_registry->>'registry'
              AND cr.project = g.container_registry->>'project'
            WHERE g.container_registry IS NOT NULL
              AND g.container_registry != '{}'::jsonb
            ON CONFLICT DO NOTHING
        """)
    )

    op.drop_column("groups", "container_registry")

    # Add a new container_registry_id UUID column (no FK constraint).
    op.add_column(
        "groups",
        sa.Column("container_registry_id", postgresql.UUID(as_uuid=True), nullable=True),
    )

    # Populate container_registry_id from the association table (pick one per group).
    conn.execute(
        sa.text("""
            UPDATE groups g
            SET container_registry_id = (
                SELECT registry_id
                FROM association_container_registries_groups
                WHERE group_id = g.id
                LIMIT 1
            )
        """)
    )


def downgrade() -> None:
    op.drop_column("groups", "container_registry_id")

    op.add_column(
        "groups",
        sa.Column("container_registry", postgresql.JSONB(), nullable=True),
    )

    # Best-effort: backfill one registry per group from the association table.
    conn = op.get_bind()
    conn.execute(
        sa.text("""
            UPDATE groups g
            SET container_registry = jsonb_build_object(
                'registry', cr.registry_name,
                'project', cr.project
            )
            FROM association_container_registries_groups acr
            JOIN container_registries cr ON cr.id = acr.registry_id
            WHERE acr.group_id = g.id
        """)
    )
