"""Backfill each project's default registry from groups.container_registry

The image commit lookup now reads a project's default registry from its registry
associations. Mark the association of the registry each project's `container_registry`
names as its default registry. A project not allowed on that registry is left without
one: the backfill grants no project a registry it was not allowed on.

Revision ID: b3e53701440e
Revises: 46d84960bae3
Create Date: 2026-11-02

"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "b3e53701440e"
down_revision = "46d84960bae3"
# Part of: NEXT_RELEASE_VERSION
branch_labels = None
depends_on = None


def mark_default_registries(conn: sa.Connection) -> None:
    """Mark the association of the registry each project names as its default registry,
    unless the project already has one. A name matching no registry, or more than one,
    is skipped."""
    conn.execute(
        sa.text("""
            UPDATE association_container_registries_groups a
            SET is_default = TRUE
            FROM groups g
            JOIN container_registries r
              ON r.registry_name = g.container_registry ->> 'registry'
             AND r.project IS NOT DISTINCT FROM g.container_registry ->> 'project'
            WHERE a.project_id = g.id
              AND a.registry_id = r.id
              AND (
                SELECT count(*) FROM container_registries same
                WHERE same.registry_name = r.registry_name
                  AND same.project IS NOT DISTINCT FROM r.project
              ) = 1
              AND NOT EXISTS (
                SELECT 1 FROM association_container_registries_groups d
                WHERE d.project_id = a.project_id AND d.is_default
              )
        """)
    )


def upgrade() -> None:
    mark_default_registries(op.get_bind())


def downgrade() -> None:
    # Nothing is reverted: a default this revision marked cannot be told apart from one
    # the API marked.
    pass
