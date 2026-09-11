"""Every model module, imported by name so the template schema is the full one.

``ensure_all_tables_registered`` imports these dynamically; Pants cannot see that, so a
sandbox built from inferred dependencies holds only part of the schema. Generated from
the package listing; regenerate when a model package is added.
"""

from __future__ import annotations

# ruff: noqa: F401
import ai.backend.manager.models.agent
import ai.backend.manager.models.agent.row
import ai.backend.manager.models.agent_installed_image
import ai.backend.manager.models.agent_installed_image.row
import ai.backend.manager.models.app_config_allow_list
import ai.backend.manager.models.app_config_allow_list.row
import ai.backend.manager.models.app_config_definition
import ai.backend.manager.models.app_config_definition.row
import ai.backend.manager.models.app_config_fragment
import ai.backend.manager.models.app_config_fragment.row
import ai.backend.manager.models.artifact
import ai.backend.manager.models.artifact.row
import ai.backend.manager.models.artifact_registries
import ai.backend.manager.models.artifact_registries.row
import ai.backend.manager.models.artifact_revision
import ai.backend.manager.models.artifact_revision.row
import ai.backend.manager.models.association_artifacts_storages
import ai.backend.manager.models.association_artifacts_storages.row
import ai.backend.manager.models.association_container_registries_groups
import ai.backend.manager.models.association_container_registries_groups.row
import ai.backend.manager.models.audit_log
import ai.backend.manager.models.audit_log.row
import ai.backend.manager.models.base
import ai.backend.manager.models.clauses
import ai.backend.manager.models.client_ip_masking
import ai.backend.manager.models.client_ip_masking.row
import ai.backend.manager.models.condition_utils
import ai.backend.manager.models.container_registry
import ai.backend.manager.models.container_registry.row
import ai.backend.manager.models.deployment_auto_scaling_policy
import ai.backend.manager.models.deployment_auto_scaling_policy.row
import ai.backend.manager.models.deployment_policy
import ai.backend.manager.models.deployment_policy.row
import ai.backend.manager.models.deployment_revision
import ai.backend.manager.models.deployment_revision.row
import ai.backend.manager.models.deployment_revision_preset
import ai.backend.manager.models.deployment_revision_preset.row
import ai.backend.manager.models.domain
import ai.backend.manager.models.domain.row
import ai.backend.manager.models.endpoint
import ai.backend.manager.models.endpoint.row
import ai.backend.manager.models.entity_label
import ai.backend.manager.models.entity_label.row
import ai.backend.manager.models.entity_share
import ai.backend.manager.models.entity_share.row
import ai.backend.manager.models.error_log
import ai.backend.manager.models.error_log.row
import ai.backend.manager.models.event_log
import ai.backend.manager.models.event_log.row
import ai.backend.manager.models.fair_share
import ai.backend.manager.models.fair_share.row
import ai.backend.manager.models.huggingface_registry
import ai.backend.manager.models.huggingface_registry.row
import ai.backend.manager.models.idle_checker
import ai.backend.manager.models.idle_checker.row
import ai.backend.manager.models.image
import ai.backend.manager.models.image.row
import ai.backend.manager.models.kernel
import ai.backend.manager.models.kernel.row
import ai.backend.manager.models.keypair
import ai.backend.manager.models.keypair.row
import ai.backend.manager.models.login_client_type
import ai.backend.manager.models.login_client_type.row
import ai.backend.manager.models.login_session
import ai.backend.manager.models.login_session.row
import ai.backend.manager.models.mixins
import ai.backend.manager.models.model_card
import ai.backend.manager.models.model_card.row
import ai.backend.manager.models.network
import ai.backend.manager.models.network.row
import ai.backend.manager.models.notification
import ai.backend.manager.models.notification.row
import ai.backend.manager.models.object_storage
import ai.backend.manager.models.object_storage.row
import ai.backend.manager.models.project
import ai.backend.manager.models.project.row
import ai.backend.manager.models.prometheus_query_preset
import ai.backend.manager.models.prometheus_query_preset.row
import ai.backend.manager.models.prometheus_query_preset_category
import ai.backend.manager.models.prometheus_query_preset_category.row
import ai.backend.manager.models.rbac_models
import ai.backend.manager.models.replica_group
import ai.backend.manager.models.replica_group.row
import ai.backend.manager.models.replica_group_history
import ai.backend.manager.models.replica_group_history.row
import ai.backend.manager.models.reservoir_registry
import ai.backend.manager.models.reservoir_registry.row
import ai.backend.manager.models.resource_group
import ai.backend.manager.models.resource_group.row
import ai.backend.manager.models.resource_policy
import ai.backend.manager.models.resource_policy.row
import ai.backend.manager.models.resource_preset
import ai.backend.manager.models.resource_preset.row
import ai.backend.manager.models.resource_slot
import ai.backend.manager.models.resource_slot.row
import ai.backend.manager.models.resource_usage
import ai.backend.manager.models.resource_usage_history
import ai.backend.manager.models.resource_usage_history.row
import ai.backend.manager.models.retention
import ai.backend.manager.models.retention.row
import ai.backend.manager.models.routing
import ai.backend.manager.models.routing.row
import ai.backend.manager.models.runtime_variant
import ai.backend.manager.models.runtime_variant.row
import ai.backend.manager.models.runtime_variant_preset
import ai.backend.manager.models.runtime_variant_preset.row
import ai.backend.manager.models.scheduling_history
import ai.backend.manager.models.scheduling_history.row
import ai.backend.manager.models.scope_source
import ai.backend.manager.models.scopes
import ai.backend.manager.models.service_catalog
import ai.backend.manager.models.service_catalog.row
import ai.backend.manager.models.session
import ai.backend.manager.models.session.row
import ai.backend.manager.models.session_group
import ai.backend.manager.models.session_group.row
import ai.backend.manager.models.session_template
import ai.backend.manager.models.specs
import ai.backend.manager.models.storage
import ai.backend.manager.models.storage_namespace
import ai.backend.manager.models.storage_namespace.row
import ai.backend.manager.models.types
import ai.backend.manager.models.user
import ai.backend.manager.models.user.row
import ai.backend.manager.models.utils
import ai.backend.manager.models.uuid7
import ai.backend.manager.models.vfolder
import ai.backend.manager.models.vfolder.row
import ai.backend.manager.models.vfs_storage
import ai.backend.manager.models.vfs_storage.row
import ai.backend.manager.models.virtual_entity


def registered() -> int:
    """How many model modules this file names; a smoke check for the generator."""
    return 131
