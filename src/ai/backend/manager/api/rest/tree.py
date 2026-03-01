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
    from .acl.registry import register_acl_module
    from .admin.registry import register_admin_module
    from .agent.registry import register_agent_module
    from .artifact.registry import register_artifact_module
    from .artifact_registry.registry import register_artifact_registry_module
    from .auth.registry import register_auth_module
    from .compute_sessions.registry import register_compute_sessions_module
    from .container_registry.registry import register_container_registry_module
    from .deployment.registry import register_deployment_module
    from .domainconfig.registry import register_domainconfig_module
    from .error_log.registry import register_error_log_module
    from .etcd.registry import register_etcd_module
    from .events.registry import register_events_module
    from .export.registry import register_export_module
    from .fair_share.registry import register_fair_share_module
    from .group.registry import register_group_module
    from .groupconfig.registry import register_groupconfig_module
    from .manager.registry import register_manager_api_module
    from .notification.registry import register_notification_module
    from .object_storage.registry import register_object_storage_module
    from .ratelimit.registry import register_ratelimit_module
    from .resource.registry import register_resource_module
    from .scaling_group.registry import register_scaling_group_module
    from .scheduling_history.registry import register_scheduling_history_module
    from .service.registry import register_service_module
    from .session.registry import register_session_module
    from .spec.registry import register_spec_module
    from .stream.registry import register_stream_module
    from .template.registry import register_template_module
    from .userconfig.registry import register_userconfig_module
    from .vfolder.registry import register_vfolder_module
    from .vfs_storage.registry import register_vfs_storage_module

    return [
        register_auth_module(deps),
        register_acl_module(deps),
        register_admin_module(deps),
        register_template_module(deps),
        register_scaling_group_module(deps),
        register_error_log_module(deps),
        register_ratelimit_module(deps),
        register_container_registry_module(deps),
        register_artifact_module(deps),
        register_artifact_registry_module(deps),
        register_etcd_module(deps),
        register_events_module(deps),
        register_vfolder_module(deps),
        register_spec_module(deps),
        register_service_module(deps),
        register_session_module(deps),
        register_stream_module(deps),
        register_manager_api_module(deps),
        register_resource_module(deps),
        register_userconfig_module(deps),
        register_domainconfig_module(deps),
        register_group_module(deps),
        register_groupconfig_module(deps),
        register_object_storage_module(deps),
        register_vfs_storage_module(deps),
        register_notification_module(deps),
        register_deployment_module(deps),
        register_scheduling_history_module(deps),
        register_compute_sessions_module(deps),
        register_fair_share_module(deps),
        register_export_module(deps),
        register_agent_module(deps),
    ]
