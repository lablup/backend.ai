"""Put fixture-written entities in the graph

An install writes registries, presets and policies as fixture rows, which the entity
ops never see, so none of them has a virtual entity node and every graph read of one
fails. Give each row of those tables a node owning and governing itself.

Revision ID: f7c1b930a2d5
Revises: c3f8a1d6e920
Create Date: 2026-09-16

"""

from __future__ import annotations

from typing import Final

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "f7c1b930a2d5"  # Part of: NEXT_RELEASE_VERSION
down_revision = "c3f8a1d6e920"
branch_labels = None
depends_on = None

# (table, id column, entity type) of every table a fixture writes entity rows into.
_ENTITY_TABLES: Final[tuple[tuple[str, str, str], ...]] = (
    ("container_registries", "id", "container_registry"),
    ("domains", "id", "domain"),
    ("groups", "id", "project"),
    ("huggingface_registries", "id", "artifact_registry"),
    ("keypair_resource_policies", "uuid", "keypair_resource_policy"),
    ("login_client_types", "id", "login_client_type"),
    ("object_storages", "id", "object_storage"),
    ("project_resource_policies", "uuid", "project_resource_policy"),
    ("prometheus_query_preset_categories", "id", "prometheus_query_preset_category"),
    ("prometheus_query_presets", "id", "prometheus_query_preset"),
    ("reservoir_registries", "id", "artifact_registry"),
    ("resource_presets", "id", "resource_preset"),
    ("resource_slot_types", "uuid", "resource_slot_type"),
    ("retention_policies", "id", "retention_policy"),
    ("role_presets", "id", "role_preset"),
    ("runtime_variant_presets", "id", "runtime_variant_preset"),
    ("runtime_variants", "id", "runtime_variant"),
    ("scaling_groups", "id", "resource_group"),
    ("storage_namespace", "id", "storage_namespace"),
    ("user_resource_policies", "uuid", "user_resource_policy"),
    ("users", "uuid", "user"),
)


def upgrade() -> None:
    conn = op.get_bind()
    entity_types = sorted({entity_type for _, _, entity_type in _ENTITY_TABLES})
    for table, id_column, entity_type in _ENTITY_TABLES:
        conn.execute(
            sa.text(f"""
                INSERT INTO virtual_entities (entity_type, entity_id)
                SELECT '{entity_type}', {id_column} FROM {table}
                ON CONFLICT (entity_type, entity_id) DO NOTHING
            """)
        )
    placeholders = ", ".join(f"'{entity_type}'" for entity_type in entity_types)
    conn.execute(
        sa.text(f"""
            INSERT INTO entity_memberships (virtual_entity_id, member_entity_id, capped)
            SELECT id, id, FALSE FROM virtual_entities
            WHERE entity_type IN ({placeholders})
            ON CONFLICT (virtual_entity_id, member_entity_id) DO NOTHING
        """)
    )
    conn.execute(
        sa.text(f"""
            INSERT INTO scope_bindings (virtual_entity_id, scope_entity_id, permission_cap)
            SELECT id, id, NULL FROM virtual_entities
            WHERE entity_type IN ({placeholders})
            ON CONFLICT DO NOTHING
        """)
    )


def downgrade() -> None:
    # Nothing is removed: a node this revision added cannot be told apart from one an
    # entity creation made, and these types were reachable through the ops before it.
    pass
