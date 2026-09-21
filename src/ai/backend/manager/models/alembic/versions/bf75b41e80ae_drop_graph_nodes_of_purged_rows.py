"""Drop the graph nodes of purged rows

A row purged before its purge removed its node leaves a node in the graph, and the
edges and bindings of that node. The next revision reads the project rosters from the
graph and grants roles to the users on them, which fails for a user the users table no
longer holds. Drop every node whose row is gone; its edges, bindings, scoped roles and
shares go with it by cascade.

Revision ID: bf75b41e80ae
Revises: f345b344d526
Create Date: 2026-09-21

"""

from __future__ import annotations

from typing import Final

import sqlalchemy as sa
from alembic import op

revision = "bf75b41e80ae"  # Part of: NEXT_RELEASE_VERSION
down_revision = "f345b344d526"
branch_labels = None
depends_on = None

NODE_SOURCES: Final[tuple[tuple[str, tuple[tuple[str, str], ...]], ...]] = (
    ("agent", (("agents", "uuid"),)),
    ("app_config_allow_list", (("app_config_allow_list", "id"),)),
    ("app_config_definition", (("app_config_definitions", "id"),)),
    ("app_config_fragment", (("app_config_fragments", "id"),)),
    ("artifact", (("artifacts", "id"),)),
    ("artifact_registry", (("huggingface_registries", "id"), ("reservoir_registries", "id"))),
    ("client_ip_masking_policy", (("client_ip_masking_policies", "id"),)),
    ("container_registry", (("container_registries", "id"),)),
    ("deployment", (("endpoints", "id"),)),
    ("deployment_preset", (("deployment_revision_presets", "id"),)),
    ("domain", (("domains", "id"),)),
    ("entity_share", (("entity_shares", "id"),)),
    ("idle_checker", (("idle_checkers", "id"),)),
    ("image", (("images", "id"),)),
    ("keypair_resource_policy", (("keypair_resource_policies", "uuid"),)),
    ("login_client_type", (("login_client_types", "id"),)),
    ("model_card", (("model_cards", "id"),)),
    ("network", (("networks", "id"),)),
    ("notification_channel", (("notification_channels", "id"),)),
    ("notification_rule", (("notification_rules", "id"),)),
    ("object_storage", (("object_storages", "id"),)),
    ("project", (("groups", "id"),)),
    ("project_resource_policy", (("project_resource_policies", "uuid"),)),
    ("prometheus_query_preset", (("prometheus_query_presets", "id"),)),
    ("prometheus_query_preset_category", (("prometheus_query_preset_categories", "id"),)),
    ("resource_group", (("scaling_groups", "id"),)),
    ("resource_preset", (("resource_presets", "id"),)),
    ("resource_slot_type", (("resource_slot_types", "uuid"),)),
    ("retention_policy", (("retention_policies", "id"),)),
    ("role", (("roles", "id"),)),
    ("role_preset", (("role_presets", "id"),)),
    ("runtime_variant", (("runtime_variants", "id"),)),
    ("runtime_variant_preset", (("runtime_variant_presets", "id"),)),
    ("service_catalog", (("service_catalog", "id"),)),
    ("session", (("sessions", "id"),)),
    ("session_group", (("session_groups", "id"),)),
    ("session_template", (("session_templates", "id"),)),
    ("storage_namespace", (("storage_namespace", "id"),)),
    ("user", (("users", "uuid"),)),
    ("user_resource_policy", (("user_resource_policies", "uuid"),)),
    ("vfolder", (("vfolders", "id"),)),
    ("vfs_storage", (("vfs_storages", "id"),)),
)


def _drop_nodes_of_purged_rows(conn: sa.Connection) -> None:
    for entity_type, tables in NODE_SOURCES:
        absent = " AND ".join(
            f"NOT EXISTS (SELECT 1 FROM {table} WHERE {id_column} = v.entity_id)"
            for table, id_column in tables
        )
        conn.execute(
            sa.text(f"""
                DELETE FROM virtual_entities v
                WHERE v.entity_type = :entity_type AND {absent}
            """),
            {"entity_type": entity_type},
        )


def upgrade() -> None:
    _drop_nodes_of_purged_rows(op.get_bind())


def downgrade() -> None:
    # A dropped node cannot be restored: the row it stood for is gone.
    pass
