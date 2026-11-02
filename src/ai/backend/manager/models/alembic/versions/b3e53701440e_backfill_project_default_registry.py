"""Backfill each project's default registry from groups.container_registry

The image commit lookup now reads a project's default registry from its registry
associations. Write the registry each project's `container_registry` names as its
default registry, with the graph edges an association stands for.

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


def link_default_registries(conn: sa.Connection) -> None:
    """Link each project to the registry its `container_registry` names, and make that
    its default registry unless it already has one. A name matching no registry, or more
    than one, is skipped."""
    conn.execute(
        sa.text("""
            INSERT INTO association_container_registries_groups (registry_id, project_id)
            SELECT r.id, g.id
            FROM groups g
            JOIN container_registries r
              ON r.registry_name = g.container_registry ->> 'registry'
             AND r.project IS NOT DISTINCT FROM g.container_registry ->> 'project'
            WHERE (
                SELECT count(*) FROM container_registries same
                WHERE same.registry_name = r.registry_name
                  AND same.project IS NOT DISTINCT FROM r.project
            ) = 1
            ON CONFLICT (registry_id, project_id) DO NOTHING
        """)
    )
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


def add_relation_edges(conn: sa.Connection) -> None:
    """The project governs the registry under READ; the registry holds READ on the
    project. Idempotent, so an association already holding the edges is unchanged."""
    conn.execute(
        sa.text("""
            INSERT INTO scope_bindings (virtual_entity_id, scope_entity_id, permission_cap)
            SELECT registry.id, project.id, 1
            FROM association_container_registries_groups a
            JOIN virtual_entities registry
              ON registry.entity_type = 'container_registry' AND registry.entity_id = a.registry_id
            JOIN virtual_entities project
              ON project.entity_type = 'project' AND project.entity_id = a.project_id
            ON CONFLICT DO NOTHING
        """)
    )
    conn.execute(
        sa.text("""
            INSERT INTO entity_memberships (virtual_entity_id, member_entity_id, capped)
            SELECT registry.id, project.id, TRUE
            FROM association_container_registries_groups a
            JOIN virtual_entities registry
              ON registry.entity_type = 'container_registry' AND registry.entity_id = a.registry_id
            JOIN virtual_entities project
              ON project.entity_type = 'project' AND project.entity_id = a.project_id
            ON CONFLICT (virtual_entity_id, member_entity_id) DO NOTHING
        """)
    )
    conn.execute(
        sa.text("""
            INSERT INTO entity_membership_caps (membership_id, permission, all_fields)
            SELECT m.id, 1, TRUE
            FROM association_container_registries_groups a
            JOIN virtual_entities registry
              ON registry.entity_type = 'container_registry' AND registry.entity_id = a.registry_id
            JOIN virtual_entities project
              ON project.entity_type = 'project' AND project.entity_id = a.project_id
            JOIN entity_memberships m
              ON m.virtual_entity_id = registry.id AND m.member_entity_id = project.id
            WHERE m.capped
            ON CONFLICT (membership_id, permission) DO UPDATE SET all_fields = TRUE
        """)
    )


def upgrade() -> None:
    conn = op.get_bind()
    link_default_registries(conn)
    add_relation_edges(conn)


def downgrade() -> None:
    # Nothing is removed: a row this revision added cannot be told apart from one the
    # API wrote.
    pass
