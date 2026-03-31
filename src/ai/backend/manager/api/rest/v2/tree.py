"""Build the v2 API sub-tree (composition root for REST v2).

Called from the main ``tree.py`` to assemble all v2 route registries
into a single v2 parent registry.  All v2 handlers call Adapters
directly — never Processors or Services.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from ai.backend.manager.api.rest.routing import RouteRegistry

if TYPE_CHECKING:
    from ai.backend.manager.api.adapters.registry import Adapters
    from ai.backend.manager.api.rest.export.handler import ExportHandler
    from ai.backend.manager.api.rest.types import RouteDeps


def build_v2_routes(
    *,
    adapters: Adapters,
    route_deps: RouteDeps,
    export_handler: ExportHandler | None = None,
) -> RouteRegistry:
    """Build the v2 parent registry with all domain sub-registries."""

    # Lazy imports to avoid circular dependencies at module level
    from .agent.handler import V2AgentHandler
    from .agent.registry import register_v2_agent_routes
    from .app_config.handler import V2AppConfigHandler
    from .app_config.registry import register_v2_app_config_routes
    from .artifact.handler import V2ArtifactHandler
    from .artifact.registry import register_v2_artifact_routes
    from .artifact_registry.handler import V2ArtifactRegistryHandler
    from .artifact_registry.registry import register_v2_artifact_registry_routes
    from .audit_log.handler import V2AuditLogHandler
    from .audit_log.registry import register_v2_audit_log_routes
    from .container_registry.handler import V2ContainerRegistryHandler
    from .container_registry.registry import register_v2_container_registry_routes
    from .deployment.handler import V2DeploymentHandler
    from .deployment.registry import register_v2_deployment_routes
    from .domain.handler import V2DomainHandler
    from .domain.registry import register_v2_domain_routes
    from .fair_share.handler import V2FairShareHandler
    from .fair_share.registry import register_v2_fair_share_routes
    from .huggingface_registry.handler import V2HuggingFaceRegistryHandler
    from .huggingface_registry.registry import register_v2_huggingface_registry_routes
    from .image.handler import V2ImageHandler
    from .image.registry import register_v2_image_routes
    from .keypair.handler import V2KeypairHandler
    from .keypair.registry import register_v2_keypair_routes
    from .login_history.handler import V2LoginHistoryHandler
    from .login_history.registry import register_v2_login_history_routes
    from .login_session.handler import V2LoginSessionHandler
    from .login_session.registry import register_v2_login_session_routes
    from .notification.handler import V2NotificationHandler
    from .notification.registry import register_v2_notification_routes
    from .object_storage.handler import V2ObjectStorageHandler
    from .object_storage.registry import register_v2_object_storage_routes
    from .project.handler import V2ProjectHandler
    from .project.registry import register_v2_project_routes
    from .prometheus_query_preset.handler import V2PrometheusQueryPresetHandler
    from .prometheus_query_preset.registry import register_v2_prometheus_query_preset_routes
    from .rbac.handler import V2RBACHandler
    from .rbac.registry import register_v2_rbac_routes
    from .reservoir_registry.handler import V2ReservoirRegistryHandler
    from .reservoir_registry.registry import register_v2_reservoir_registry_routes
    from .resource_allocation.handler import V2ResourceAllocationHandler
    from .resource_allocation.registry import register_v2_resource_allocation_routes
    from .resource_group.handler import V2ResourceGroupHandler
    from .resource_group.registry import register_v2_resource_group_routes
    from .resource_policy.handler import V2ResourcePolicyHandler
    from .resource_policy.registry import register_v2_resource_policy_routes
    from .resource_preset.handler import V2ResourcePresetHandler
    from .resource_preset.registry import register_v2_resource_preset_routes
    from .resource_slot.handler import V2ResourceSlotHandler
    from .resource_slot.registry import register_v2_resource_slot_routes
    from .resource_usage.handler import V2ResourceUsageHandler
    from .resource_usage.registry import register_v2_resource_usage_routes
    from .scheduling_history.handler import V2SchedulingHistoryHandler
    from .scheduling_history.registry import register_v2_scheduling_history_routes
    from .service_catalog.handler import V2ServiceCatalogHandler
    from .service_catalog.registry import register_v2_service_catalog_routes
    from .session.handler import V2SessionHandler
    from .session.registry import register_v2_session_routes
    from .storage_namespace.handler import V2StorageNamespaceHandler
    from .storage_namespace.registry import register_v2_storage_namespace_routes
    from .user.handler import V2UserHandler
    from .user.registry import register_v2_user_routes
    from .vfolder.handler import V2VFolderHandler
    from .vfolder.registry import register_v2_vfolder_routes
    from .vfs_storage.handler import V2VFSStorageHandler
    from .vfs_storage.registry import register_v2_vfs_storage_routes

    # Build all handlers (each takes its individual adapter)
    agent_handler = V2AgentHandler(adapter=adapters.agent)
    app_config_handler = V2AppConfigHandler(adapter=adapters.app_config)
    artifact_handler = V2ArtifactHandler(adapter=adapters.artifact)
    artifact_registry_handler = V2ArtifactRegistryHandler(adapter=adapters.artifact_registry)
    audit_log_handler = V2AuditLogHandler(adapter=adapters.audit_log)
    container_registry_handler = V2ContainerRegistryHandler(adapter=adapters.container_registry)
    deployment_handler = V2DeploymentHandler(adapter=adapters.deployment)
    domain_handler = V2DomainHandler(adapter=adapters.domain)
    fair_share_handler = V2FairShareHandler(adapter=adapters.fair_share)
    huggingface_registry_handler = V2HuggingFaceRegistryHandler(
        adapter=adapters.huggingface_registry
    )
    image_handler = V2ImageHandler(adapter=adapters.image)
    keypair_handler = V2KeypairHandler(adapter=adapters.user)
    login_history_handler = V2LoginHistoryHandler(adapter=adapters.login_history)
    login_session_handler = V2LoginSessionHandler(adapter=adapters.login_session)
    notification_handler = V2NotificationHandler(adapter=adapters.notification)
    object_storage_handler = V2ObjectStorageHandler(adapter=adapters.object_storage)
    project_handler = V2ProjectHandler(adapter=adapters.project)
    prometheus_query_preset_handler = V2PrometheusQueryPresetHandler(
        adapter=adapters.prometheus_query_preset
    )
    rbac_handler = V2RBACHandler(adapter=adapters.rbac)
    reservoir_registry_handler = V2ReservoirRegistryHandler(adapter=adapters.reservoir_registry)
    resource_allocation_handler = V2ResourceAllocationHandler(adapter=adapters.resource_allocation)
    resource_group_handler = V2ResourceGroupHandler(adapter=adapters.resource_group)
    resource_policy_handler = V2ResourcePolicyHandler(adapter=adapters.resource_policy)
    resource_preset_handler = V2ResourcePresetHandler(adapter=adapters.resource_preset)
    resource_slot_handler = V2ResourceSlotHandler(adapter=adapters.resource_slot)
    resource_usage_handler = V2ResourceUsageHandler(adapter=adapters.resource_usage)
    scheduling_history_handler = V2SchedulingHistoryHandler(adapter=adapters.scheduling_history)
    service_catalog_handler = V2ServiceCatalogHandler(adapter=adapters.service_catalog)
    session_handler = V2SessionHandler(adapter=adapters.session)
    storage_namespace_handler = V2StorageNamespaceHandler(adapter=adapters.storage_namespace)
    user_handler = V2UserHandler(adapter=adapters.user)
    vfolder_handler = V2VFolderHandler(adapter=adapters.vfolder)
    vfs_storage_handler = V2VFSStorageHandler(adapter=adapters.vfs_storage)

    # Build the v2 parent registry
    v2_reg = RouteRegistry.create("v2", route_deps.cors_options)

    # Add all domain sub-registries
    v2_reg.add_subregistry(register_v2_agent_routes(agent_handler, route_deps))
    v2_reg.add_subregistry(register_v2_app_config_routes(app_config_handler, route_deps))
    v2_reg.add_subregistry(register_v2_artifact_routes(artifact_handler, route_deps))
    v2_reg.add_subregistry(
        register_v2_artifact_registry_routes(artifact_registry_handler, route_deps)
    )
    v2_reg.add_subregistry(register_v2_audit_log_routes(audit_log_handler, route_deps))
    v2_reg.add_subregistry(
        register_v2_container_registry_routes(container_registry_handler, route_deps)
    )
    v2_reg.add_subregistry(register_v2_deployment_routes(deployment_handler, route_deps))
    v2_reg.add_subregistry(register_v2_domain_routes(domain_handler, route_deps))
    v2_reg.add_subregistry(register_v2_fair_share_routes(fair_share_handler, route_deps))
    v2_reg.add_subregistry(
        register_v2_huggingface_registry_routes(huggingface_registry_handler, route_deps)
    )
    v2_reg.add_subregistry(register_v2_image_routes(image_handler, route_deps))
    v2_reg.add_subregistry(register_v2_keypair_routes(keypair_handler, route_deps))
    v2_reg.add_subregistry(register_v2_login_history_routes(login_history_handler, route_deps))
    v2_reg.add_subregistry(register_v2_login_session_routes(login_session_handler, route_deps))
    v2_reg.add_subregistry(register_v2_notification_routes(notification_handler, route_deps))
    v2_reg.add_subregistry(register_v2_object_storage_routes(object_storage_handler, route_deps))
    v2_reg.add_subregistry(register_v2_project_routes(project_handler, route_deps))
    v2_reg.add_subregistry(
        register_v2_prometheus_query_preset_routes(prometheus_query_preset_handler, route_deps)
    )
    v2_reg.add_subregistry(register_v2_rbac_routes(rbac_handler, route_deps))
    v2_reg.add_subregistry(
        register_v2_reservoir_registry_routes(reservoir_registry_handler, route_deps)
    )
    v2_reg.add_subregistry(
        register_v2_resource_allocation_routes(resource_allocation_handler, route_deps)
    )
    v2_reg.add_subregistry(register_v2_resource_group_routes(resource_group_handler, route_deps))
    v2_reg.add_subregistry(register_v2_resource_policy_routes(resource_policy_handler, route_deps))
    v2_reg.add_subregistry(register_v2_resource_preset_routes(resource_preset_handler, route_deps))
    v2_reg.add_subregistry(register_v2_resource_slot_routes(resource_slot_handler, route_deps))
    v2_reg.add_subregistry(register_v2_resource_usage_routes(resource_usage_handler, route_deps))
    v2_reg.add_subregistry(
        register_v2_scheduling_history_routes(scheduling_history_handler, route_deps)
    )
    v2_reg.add_subregistry(register_v2_service_catalog_routes(service_catalog_handler, route_deps))
    v2_reg.add_subregistry(register_v2_session_routes(session_handler, route_deps))
    v2_reg.add_subregistry(
        register_v2_storage_namespace_routes(storage_namespace_handler, route_deps)
    )
    v2_reg.add_subregistry(register_v2_user_routes(user_handler, route_deps))
    v2_reg.add_subregistry(register_v2_vfolder_routes(vfolder_handler, route_deps))
    v2_reg.add_subregistry(register_v2_vfs_storage_routes(vfs_storage_handler, route_deps))

    # Export (reuses v1 handler directly, no adapter)
    if export_handler is not None:
        from .export.registry import register_v2_export_routes

        v2_reg.add_subregistry(register_v2_export_routes(export_handler, route_deps))

    return v2_reg
