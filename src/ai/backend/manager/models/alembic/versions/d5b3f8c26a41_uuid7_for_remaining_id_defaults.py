"""use uuid_generate_v7 for the remaining id defaults

Revision ID: d5b3f8c26a41
Revises: c4a7e2f10b93
Create Date: 2026-09-05

"""

import sqlalchemy as sa
from alembic import op

# Part of: NEXT_RELEASE_VERSION

# revision identifiers, used by Alembic.
revision = "d5b3f8c26a41"
down_revision = "c4a7e2f10b93"
branch_labels = None
depends_on = None

# Existing rows keep their v4 ids; the two versions share the uuid type.
_TARGET_COLUMNS = (
    ("agent_resources", "id"),
    ("agents", "uuid"),
    ("app_config_allow_list", "id"),
    ("app_config_definitions", "id"),
    ("app_config_fragments", "id"),
    ("artifact_registries", "id"),
    ("artifact_revisions", "id"),
    ("artifacts", "id"),
    ("association_artifacts_storages", "id"),
    ("association_container_registries_groups", "id"),
    ("association_groups_users", "id"),
    ("association_scopes_entities", "id"),
    ("client_ip_masking_policies", "id"),
    ("container_registries", "id"),
    ("deployment_auto_scaling_policies", "id"),
    ("deployment_policies", "id"),
    ("deployment_revision_presets", "id"),
    ("deployment_revision_resource_slots", "id"),
    ("domain_fair_shares", "id"),
    ("domains", "id"),
    ("endpoint_auto_scaling_rules", "id"),
    ("endpoint_tokens", "id"),
    ("entity_fields", "id"),
    ("entity_invitations", "id"),
    ("entity_labels", "id"),
    ("groups", "id"),
    ("huggingface_registries", "id"),
    ("idle_checker_bindings", "id"),
    ("idle_checkers", "id"),
    ("image_aliases", "id"),
    ("images", "id"),
    ("keypair_resource_policies", "uuid"),
    ("keypairs", "id"),
    ("login_client_types", "id"),
    ("login_sessions", "id"),
    ("model_card_resource_requirements", "id"),
    ("model_cards", "id"),
    ("networks", "id"),
    ("notification_channels", "id"),
    ("notification_rules", "id"),
    ("object_permissions", "id"),
    ("object_storages", "id"),
    ("permissions", "id"),
    ("preset_resource_slots", "id"),
    ("project_fair_shares", "id"),
    ("project_resource_policies", "uuid"),
    ("prometheus_query_preset_categories", "id"),
    ("prometheus_query_presets", "id"),
    ("reservoir_registries", "id"),
    ("resource_allocations", "id"),
    ("resource_presets", "id"),
    ("resource_slot_types", "uuid"),
    ("retention_policies", "id"),
    ("role_permission_presets", "id"),
    ("role_presets", "id"),
    ("roles", "id"),
    ("runtime_variant_presets", "id"),
    ("runtime_variants", "id"),
    ("scaling_groups", "id"),
    ("service_catalog", "id"),
    ("service_catalog_endpoint", "id"),
    ("session_dependencies", "id"),
    ("session_groups", "id"),
    ("session_templates", "id"),
    ("sgroups_for_domains", "id"),
    ("sgroups_for_groups", "id"),
    ("sgroups_for_keypairs", "id"),
    ("storage_namespace", "id"),
    ("user_fair_shares", "id"),
    ("user_resource_policies", "uuid"),
    ("user_roles", "id"),
    ("users", "uuid"),
    ("vfolder_invitations", "id"),
    ("vfolder_permissions", "id"),
    ("vfolders", "id"),
    ("vfs_storages", "id"),
    ("virtual_entities", "id"),
)


def upgrade() -> None:
    for table, column in _TARGET_COLUMNS:
        op.execute(
            sa.text(f"ALTER TABLE {table} ALTER COLUMN {column} SET DEFAULT uuid_generate_v7()")
        )


def downgrade() -> None:
    for table, column in _TARGET_COLUMNS:
        op.execute(
            sa.text(f"ALTER TABLE {table} ALTER COLUMN {column} SET DEFAULT uuid_generate_v4()")
        )
