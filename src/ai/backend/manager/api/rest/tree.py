"""Build the full API module tree.

Called from ``server.py`` to assemble all route registries into a single
tree rooted at the empty-prefix root registry.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from .routing import RouteRegistry

if TYPE_CHECKING:
    from .types import ModuleDeps


def build_api_routes(deps: ModuleDeps) -> list[RouteRegistry]:
    """Build the full API module tree and return all root-level registries."""
    from .acl.registry import register_acl_routes
    from .admin.registry import register_admin_routes
    from .agent.registry import register_agent_routes
    from .artifact.registry import register_artifact_routes
    from .artifact_registry.registry import register_artifact_registry_routes
    from .auth.registry import register_auth_routes
    from .compute_sessions.registry import register_compute_sessions_routes
    from .container_registry.registry import register_container_registry_routes
    from .deployment.registry import register_deployment_routes
    from .domainconfig.registry import register_domainconfig_routes
    from .error_log.registry import register_error_log_routes
    from .etcd.registry import register_etcd_routes
    from .events.registry import register_events_routes
    from .export.registry import register_export_routes
    from .fair_share.registry import register_fair_share_routes
    from .group.registry import register_group_routes
    from .groupconfig.registry import register_groupconfig_routes
    from .manager.registry import register_manager_api_routes
    from .notification.registry import register_notification_routes
    from .object_storage.registry import register_object_storage_routes
    from .ratelimit.registry import register_ratelimit_routes
    from .resource.registry import register_resource_routes
    from .scaling_group.registry import register_scaling_group_routes
    from .scheduling_history.registry import register_scheduling_history_routes
    from .service.registry import register_service_routes
    from .session.registry import register_session_routes
    from .spec.registry import register_spec_routes
    from .stream.registry import register_stream_routes
    from .template.registry import register_template_routes
    from .userconfig.registry import register_userconfig_routes
    from .vfolder.registry import register_vfolder_routes
    from .vfs_storage.registry import register_vfs_storage_routes

    return [
        register_auth_routes(deps),
        register_acl_routes(deps),
        register_admin_routes(deps),
        register_template_routes(deps),
        register_scaling_group_routes(deps),
        register_error_log_routes(deps),
        register_ratelimit_routes(deps),
        register_container_registry_routes(deps),
        register_artifact_routes(deps),
        register_artifact_registry_routes(deps),
        register_etcd_routes(deps),
        register_events_routes(deps),
        register_vfolder_routes(deps),
        register_spec_routes(deps),
        register_service_routes(deps),
        register_session_routes(deps),
        register_stream_routes(deps),
        register_manager_api_routes(deps),
        register_resource_routes(deps),
        register_userconfig_routes(deps),
        register_domainconfig_routes(deps),
        register_group_routes(deps),
        register_groupconfig_routes(deps),
        register_object_storage_routes(deps),
        register_vfs_storage_routes(deps),
        register_notification_routes(deps),
        register_deployment_routes(deps),
        register_scheduling_history_routes(deps),
        register_compute_sessions_routes(deps),
        register_fair_share_routes(deps),
        register_export_routes(deps),
        register_agent_routes(deps),
    ]
