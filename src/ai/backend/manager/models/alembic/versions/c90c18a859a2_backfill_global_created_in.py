"""Backfill global created_in

Create the existing domain, project, user and global-family entity nodes in the `global`
scope: a membership and a scope binding from the `global` node to each.

Revision ID: c90c18a859a2
Revises: b76f2d5191d4
Create Date: 2026-09-18

"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "c90c18a859a2"  # Part of: NEXT_RELEASE_VERSION
down_revision = "b76f2d5191d4"
branch_labels = None
depends_on = None

MEMBER_ENTITY_TYPES = (
    "domain",
    "project",
    "user",
    "runtime_variant",
    "runtime_variant_preset",
    "prometheus_query_preset",
    "prometheus_query_preset_category",
    "resource_slot_type",
    "login_client_type",
    "deployment_preset",
    "container_registry",
    "resource_preset",
    "resource_group",
    "idle_checker",
    "keypair_resource_policy",
    "user_resource_policy",
    "project_resource_policy",
    "object_storage",
    "vfs_storage",
    "storage_namespace",
    "artifact_registry",
    "artifact",
    "notification_channel",
    "notification_rule",
    "retention_policy",
    "role_preset",
    "app_config_allow_list",
    "app_config_definition",
    "service_catalog",
    "client_ip_masking_policy",
)

GLOBAL_NODE_SQL = """
    SELECT ve.id FROM virtual_entities ve
    JOIN global_entities ge ON ve.entity_type = 'global' AND ve.entity_id = ge.id
    WHERE ge.name = 'global'
"""

MEMBER_NODES_SQL = """
    SELECT ve.id FROM virtual_entities ve
    WHERE ve.entity_type = ANY(:member_entity_types)
    UNION
    SELECT ve.id FROM virtual_entities ve
    JOIN app_config_fragments f ON ve.entity_type = 'app_config_fragment' AND ve.entity_id = f.id
    WHERE f.scope_type = 'public'
"""


def upgrade() -> None:
    conn = op.get_bind()
    params = {"member_entity_types": list(MEMBER_ENTITY_TYPES)}
    conn.execute(
        sa.text(f"""
            INSERT INTO entity_memberships (virtual_entity_id, member_entity_id, capped)
            SELECT g.id, m.id, FALSE
            FROM ({GLOBAL_NODE_SQL}) g, ({MEMBER_NODES_SQL}) m
            ON CONFLICT (virtual_entity_id, member_entity_id) DO NOTHING
        """),
        params,
    )
    conn.execute(
        sa.text(f"""
            INSERT INTO scope_bindings (virtual_entity_id, scope_entity_id, permission_cap)
            SELECT m.id, g.id, NULL
            FROM ({GLOBAL_NODE_SQL}) g, ({MEMBER_NODES_SQL}) m
            ON CONFLICT DO NOTHING
        """),
        params,
    )


def downgrade() -> None:
    conn = op.get_bind()
    conn.execute(
        sa.text(f"""
            DELETE FROM entity_memberships
            WHERE virtual_entity_id IN ({GLOBAL_NODE_SQL})
              AND member_entity_id <> virtual_entity_id
        """)
    )
    conn.execute(
        sa.text(f"""
            DELETE FROM scope_bindings
            WHERE scope_entity_id IN ({GLOBAL_NODE_SQL})
              AND virtual_entity_id <> scope_entity_id
        """)
    )
