"""Build the full API module tree (composition root).

Called from ``server.py`` to assemble all route registries into a single
tree rooted at the empty-prefix root registry.  All handler construction
and dependency wiring happens here — registrars are pure routing functions.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from aiohttp import web

from .routing import RouteRegistry
from .server_status import ALL_ALLOWED, READ_ALLOWED, server_status_required
from .types import RouteDeps

if TYPE_CHECKING:
    from ai.backend.common.clients.valkey_client.valkey_rate_limit.client import (
        ValkeyRateLimitClient,
    )
    from ai.backend.common.health_checker.probe import HealthProbe
    from ai.backend.common.plugin.monitor import ErrorPluginContext
    from ai.backend.manager.config.provider import ManagerConfigProvider
    from ai.backend.manager.event_dispatcher.handlers.stream_cleanup import (
        StreamCleanupEventHandler,
    )
    from ai.backend.manager.services.processors import Processors

    from .types import CORSOptions, GQLContextDeps


def build_api_routes(
    *,
    processors: Processors,
    cors_options: CORSOptions,
    config_provider: ManagerConfigProvider,
    error_monitor: ErrorPluginContext,
    gql_context_deps: GQLContextDeps,
    valkey_rate_limit: ValkeyRateLimitClient | None,
    health_probe: HealthProbe | None,
    root_app: web.Application,
    stream_cleanup_handler: StreamCleanupEventHandler,
    pidx: int = 0,
) -> list[RouteRegistry]:
    """Build the full API module tree and return all root-level registries.

    This is the composition root: all handlers are constructed here and
    passed to pure routing registrar functions.
    """
    # Lazy imports to avoid circular dependencies at module level
    from ai.backend.manager.api.gql.schema import schema as strawberry_schema
    from ai.backend.manager.api.gql_legacy.schema import graphene_schema

    from .acl.handler import AclHandler
    from .acl.registry import register_acl_routes
    from .admin.handler import AdminHandler
    from .admin.registry import register_admin_routes
    from .agent.handler import AgentHandler
    from .agent.registry import register_agent_routes
    from .artifact.handler import ArtifactHandler
    from .artifact.registry import register_artifact_routes
    from .artifact_registry.handler import ArtifactRegistryHandler
    from .artifact_registry.registry import register_artifact_registry_routes
    from .auth.handler import AuthHandler
    from .auth.registry import register_auth_routes
    from .auto_scaling_rule.handler import AutoScalingRuleHandler
    from .auto_scaling_rule.registry import register_auto_scaling_rule_routes
    from .cluster_template.handler import ClusterTemplateHandler
    from .cluster_template.registry import register_cluster_template_routes
    from .compute_sessions.handler import ComputeSessionsHandler
    from .compute_sessions.registry import register_compute_sessions_routes
    from .container_registry.handler import ContainerRegistryHandler
    from .container_registry.registry import register_container_registry_routes
    from .deployment.handler import DeploymentAPIHandler
    from .deployment.registry import register_deployment_routes
    from .domain.handler import DomainHandler
    from .domain.registry import register_domain_routes
    from .domainconfig.handler import DomainConfigHandler
    from .domainconfig.registry import register_domainconfig_routes
    from .error_log.handler import ErrorLogHandler
    from .error_log.registry import register_error_log_routes
    from .etcd.handler import EtcdHandler
    from .etcd.registry import register_etcd_routes
    from .events.handler import EventsHandler
    from .events.handler import PrivateContext as EventsPrivateContext
    from .events.registry import register_events_routes
    from .export.handler import ExportHandler
    from .export.registry import register_export_routes
    from .fair_share.handler import FairShareAPIHandler
    from .fair_share.registry import register_fair_share_routes
    from .group.handler import GroupHandler
    from .group.registry import register_group_routes
    from .groupconfig.handler import GroupConfigHandler
    from .groupconfig.registry import register_groupconfig_routes
    from .health.handler import HealthHandler
    from .health.registry import register_health_routes
    from .image.handler import ImageHandler
    from .image.registry import register_image_routes
    from .manager.handler import ManagerHandler
    from .manager.registry import register_manager_api_routes
    from .notification.handler import NotificationHandler
    from .notification.registry import register_notification_routes
    from .object_storage.handler import ObjectStorageHandler
    from .object_storage.registry import register_object_storage_routes
    from .prometheus_query_preset import PrometheusQueryPresetHandler
    from .prometheus_query_preset.registry import register_prometheus_query_preset_routes
    from .quota_scope.handler import QuotaScopeHandler
    from .quota_scope.registry import register_quota_scope_routes
    from .ratelimit.registry import register_ratelimit_routes
    from .rbac.handler import RBACHandler
    from .rbac.registry import register_rbac_routes
    from .resource.handler import ResourceHandler
    from .resource.registry import register_resource_routes
    from .resource_slot.handler import ResourceSlotHandler
    from .resource_slot.registry import register_resource_slot_routes
    from .scaling_group.handler import ScalingGroupHandler
    from .scaling_group.registry import register_scaling_group_routes
    from .scheduling_history.handler import SchedulingHistoryHandler
    from .scheduling_history.registry import register_scheduling_history_routes
    from .service.handler import ServiceHandler
    from .service.registry import register_service_routes
    from .session.handler import SessionHandler
    from .session.registry import register_session_routes
    from .session_template.handler import SessionTemplateHandler
    from .session_template.registry import register_session_template_routes
    from .spec.handler import SpecHandler
    from .spec.registry import register_spec_routes
    from .stream.handler import PrivateContext as StreamPrivateContext
    from .stream.handler import StreamHandler
    from .stream.registry import register_stream_routes
    from .template.registry import register_template_routes
    from .user.handler import UserHandler
    from .user.registry import register_user_routes
    from .userconfig.handler import UserConfigHandler
    from .userconfig.registry import register_userconfig_routes
    from .vfolder.handler import VFolderHandler
    from .vfolder.registry import register_vfolder_routes
    from .vfs_storage.handler import VFSStorageHandler
    from .vfs_storage.registry import register_vfs_storage_routes

    # 1. Build shared routing deps
    route_deps = RouteDeps(
        cors_options=cors_options,
        read_status_mw=server_status_required(READ_ALLOWED, config_provider),
        all_status_mw=server_status_required(ALL_ALLOWED, config_provider),
    )

    # 2. Build all handlers
    acl_handler = AclHandler()
    auth_handler = AuthHandler(auth=processors.auth)
    agent_handler = AgentHandler(agent=processors.agent)
    resource_slot_handler = ResourceSlotHandler(resource_slot=processors.resource_slot)
    artifact_handler = ArtifactHandler(
        artifact=processors.artifact,
        artifact_revision=processors.artifact_revision,
    )
    artifact_registry_handler = ArtifactRegistryHandler(
        artifact=processors.artifact,
        artifact_revision=processors.artifact_revision,
    )
    compute_sessions_handler = ComputeSessionsHandler(session=processors.session)
    container_registry_handler = ContainerRegistryHandler(
        container_registry=processors.container_registry
    )
    deployment_handler = DeploymentAPIHandler(deployment=processors.deployment)
    domainconfig_handler = DomainConfigHandler(dotfile=processors.dotfile)
    error_log_handler = ErrorLogHandler(error_log=processors.error_log)
    etcd_handler = EtcdHandler(
        container_registry=processors.container_registry,
        etcd_config=processors.etcd_config,
    )
    export_handler = ExportHandler(
        export=processors.export,
        export_config=config_provider.config.export,
    )
    fair_share_handler = FairShareAPIHandler(
        fair_share=processors.fair_share,
        resource_usage=processors.resource_usage,
        scaling_group=processors.scaling_group,
    )
    group_handler = GroupHandler(container_registry=processors.container_registry)
    groupconfig_handler = GroupConfigHandler(dotfile=processors.dotfile)
    manager_handler = ManagerHandler(manager_admin=processors.manager_admin)
    notification_handler = NotificationHandler(notification=processors.notification)
    object_storage_handler = ObjectStorageHandler(
        object_storage=processors.object_storage,
        storage_namespace=processors.storage_namespace,
    )
    resource_handler = ResourceHandler(
        resource_preset=processors.resource_preset,
        agent=processors.agent,
        group=processors.group,
        user=processors.user,
        container_registry=processors.container_registry,
    )
    scaling_group_handler = ScalingGroupHandler(scaling_group=processors.scaling_group)
    scheduling_history_handler = SchedulingHistoryHandler(
        scheduling_history=processors.scheduling_history
    )
    service_handler = ServiceHandler(
        auth=processors.auth,
        deployment=processors.deployment,
        model_serving=processors.model_serving,
        model_serving_auto_scaling=processors.model_serving_auto_scaling,
    )
    session_handler = SessionHandler(
        auth=processors.auth,
        session=processors.session,
        agent=processors.agent,
        vfolder=processors.vfolder,
        config_provider=config_provider,
    )
    userconfig_handler = UserConfigHandler(
        auth=processors.auth,
        dotfile=processors.dotfile,
    )
    vfolder_handler = VFolderHandler(
        auth=processors.auth,
        vfolder=processors.vfolder,
        vfolder_file=processors.vfolder_file,
        vfolder_invite=processors.vfolder_invite,
        vfolder_sharing=processors.vfolder_sharing,
    )
    vfs_storage_handler = VFSStorageHandler(vfs_storage=processors.vfs_storage)

    # Admin sub-registries
    domain_handler = DomainHandler(domain=processors.domain)
    user_handler = UserHandler(user=processors.user, config_provider=config_provider)
    image_handler = ImageHandler(image=processors.image)
    rbac_handler = RBACHandler(permission_controller=processors.permission_controller)
    quota_scope_handler = QuotaScopeHandler(vfs_storage=processors.vfs_storage)
    auto_scaling_rule_handler = AutoScalingRuleHandler(deployment=processors.deployment)

    domain_reg = register_domain_routes(domain_handler, route_deps)
    user_reg = register_user_routes(user_handler, route_deps)
    image_reg = register_image_routes(image_handler, route_deps)
    rbac_reg = register_rbac_routes(rbac_handler, route_deps)
    quota_scope_reg = register_quota_scope_routes(quota_scope_handler, route_deps)
    auto_scaling_rule_reg = register_auto_scaling_rule_routes(auto_scaling_rule_handler, route_deps)

    if gql_context_deps is None:
        raise RuntimeError("GQLContextDeps required for admin routes")
    admin_handler = AdminHandler(
        gql_schema=graphene_schema,
        gql_deps=gql_context_deps,
        strawberry_schema=strawberry_schema,
    )

    # Template sub-registries
    cluster_template_handler = ClusterTemplateHandler(template=processors.template)
    session_template_handler = SessionTemplateHandler(template=processors.template)
    cluster_template_reg = register_cluster_template_routes(cluster_template_handler, route_deps)
    session_template_reg = register_session_template_routes(session_template_handler, route_deps)

    # Health handler
    if health_probe is None:
        raise RuntimeError("health_probe is required for the health module")
    health_handler = HealthHandler(health_probe=health_probe)

    # Spec handler
    spec_handler = SpecHandler(config_provider=config_provider, root_app=root_app)

    # Events handler
    events_processors = processors.events
    event_hub = events_processors.event_hub
    event_fetcher = events_processors.event_fetcher
    events_ctx = EventsPrivateContext()
    events_handler = EventsHandler(
        private_ctx=events_ctx,
        events_processors=events_processors,
        event_hub=event_hub,
        event_fetcher=event_fetcher,
    )

    # Stream handler
    stream_processors = processors.stream
    stream_ctx = StreamPrivateContext()
    stream_handler = StreamHandler(
        private_ctx=stream_ctx,
        stream_processors=stream_processors,
        config_provider=config_provider,
        error_monitor=error_monitor,
    )

    # Prometheus query preset handler
    prometheus_processor = processors.prometheus_query_preset
    prometheus_query_preset_handler = PrometheusQueryPresetHandler(processor=prometheus_processor)

    # 3. Build all registries
    return [
        register_auth_routes(auth_handler, route_deps),
        register_acl_routes(acl_handler, route_deps),
        register_admin_routes(
            admin_handler,
            route_deps,
            sub_registries=[
                domain_reg,
                user_reg,
                image_reg,
                rbac_reg,
                quota_scope_reg,
                auto_scaling_rule_reg,
            ],
        ),
        register_template_routes(
            route_deps,
            sub_registries=[cluster_template_reg, session_template_reg],
        ),
        register_scaling_group_routes(scaling_group_handler, route_deps),
        register_error_log_routes(error_log_handler, route_deps),
        register_health_routes(health_handler, route_deps),
        register_ratelimit_routes(route_deps, valkey_rate_limit=valkey_rate_limit),
        register_container_registry_routes(container_registry_handler, route_deps),
        register_artifact_routes(artifact_handler, route_deps),
        register_artifact_registry_routes(artifact_registry_handler, route_deps),
        register_etcd_routes(
            etcd_handler,
            route_deps,
            pidx=pidx,
            config_provider=config_provider,
        ),
        register_events_routes(
            events_handler,
            route_deps,
            event_hub=event_hub,
        ),
        register_vfolder_routes(
            vfolder_handler,
            route_deps,
            vfolder_processors=processors.vfolder,
        ),
        register_spec_routes(
            spec_handler,
            route_deps,
            config_provider=config_provider,
        ),
        register_service_routes(service_handler, route_deps),
        register_session_routes(session_handler, route_deps),
        register_stream_routes(
            stream_handler,
            route_deps,
            stream_processors=stream_processors,
            stream_cleanup_handler=stream_cleanup_handler,
        ),
        register_manager_api_routes(manager_handler, route_deps),
        register_resource_routes(resource_handler, route_deps),
        register_userconfig_routes(userconfig_handler, route_deps),
        register_domainconfig_routes(domainconfig_handler, route_deps),
        register_group_routes(group_handler, route_deps),
        register_groupconfig_routes(groupconfig_handler, route_deps),
        register_object_storage_routes(object_storage_handler, route_deps),
        register_vfs_storage_routes(vfs_storage_handler, route_deps),
        register_notification_routes(notification_handler, route_deps),
        register_deployment_routes(deployment_handler, route_deps),
        register_scheduling_history_routes(scheduling_history_handler, route_deps),
        register_compute_sessions_routes(compute_sessions_handler, route_deps),
        register_fair_share_routes(fair_share_handler, route_deps),
        register_export_routes(export_handler, route_deps),
        register_agent_routes(agent_handler, route_deps),
        register_resource_slot_routes(resource_slot_handler, route_deps),
        register_prometheus_query_preset_routes(prometheus_query_preset_handler, route_deps),
    ]
