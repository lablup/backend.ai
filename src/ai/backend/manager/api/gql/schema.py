import strawberry
from strawberry.federation import Schema
from strawberry.schema.config import StrawberryConfig

from .agent import (
    agent_stats,
    agents_v2,
)
from .app_config import (
    delete_domain_app_config,
    delete_user_app_config,
    domain_app_config,
    merged_app_config,
    upsert_domain_app_config,
    upsert_user_app_config,
    user_app_config,
)
from .artifact import (
    approve_artifact_revision,
    artifact,
    artifact_import_progress_updated,
    artifact_revision,
    artifact_revisions,
    artifact_status_changed,
    artifacts,
    cancel_import_artifact,
    cleanup_artifact_revisions,
    delegate_import_artifacts,
    delegate_scan_artifacts,
    delete_artifacts,
    import_artifacts,
    reject_artifact_revision,
    restore_artifacts,
    scan_artifact_models,
    scan_artifacts,
    update_artifact,
)
from .artifact_registry import default_artifact_registry
from .background_task import background_task_events
from .deployment import (
    # Revision
    activate_deployment_revision,
    add_model_revision,
    # Access Token
    create_access_token,
    # Auto Scaling
    create_auto_scaling_rule,
    # Deployment
    create_model_deployment,
    create_model_revision,
    delete_auto_scaling_rule,
    delete_model_deployment,
    deployment,
    deployment_status_changed,
    deployments,
    inference_runtime_config,
    inference_runtime_configs,
    # Replica
    replica,
    replica_status_changed,
    replicas,
    revision,
    revisions,
    # Route
    route,
    routes,
    sync_replicas,
    update_auto_scaling_rule,
    update_model_deployment,
    update_route_traffic_status,
)
from .fair_share import (
    domain_fair_share,
    domain_fair_shares,
    project_fair_share,
    project_fair_shares,
    upsert_domain_fair_share_weight,
    upsert_project_fair_share_weight,
    upsert_user_fair_share_weight,
    user_fair_share,
    user_fair_shares,
)
from .huggingface_registry import (
    create_huggingface_registry,
    delete_huggingface_registry,
    huggingface_registries,
    huggingface_registry,
    update_huggingface_registry,
)
from .notification import (
    create_notification_channel,
    create_notification_rule,
    delete_notification_channel,
    delete_notification_rule,
    notification_channel,
    notification_channels,
    notification_rule,
    notification_rule_types,
    notification_rules,
    update_notification_channel,
    update_notification_rule,
    validate_notification_channel,
    validate_notification_rule,
)
from .object_storage import (
    create_object_storage,
    delete_object_storage,
    get_presigned_download_url,
    get_presigned_upload_url,
    object_storage,
    object_storages,
    update_object_storage,
)
from .reservoir_registry import (
    create_reservoir_registry,
    delete_reservoir_registry,
    reservoir_registries,
    reservoir_registry,
    update_reservoir_registry,
)
from .resource_group import (
    resource_groups,
    update_resource_group_fair_share_spec,
)
from .resource_usage import (
    domain_usage_buckets,
    project_usage_buckets,
    user_usage_buckets,
)
from .scheduler import (
    scheduling_events_by_session,
)
from .scheduling_history import (
    deployment_histories,
    route_histories,
    session_scheduling_histories,
)
from .storage_namespace import (
    register_storage_namespace,
    unregister_storage_namespace,
)
from .vfs_storage import (
    create_vfs_storage,
    delete_vfs_storage,
    update_vfs_storage,
    vfs_storage,
    vfs_storages,
)


@strawberry.type
class Query:
    agent_stats = agent_stats
    agents_v2 = agents_v2
    artifact = artifact
    artifacts = artifacts
    artifact_revision = artifact_revision
    artifact_revisions = artifact_revisions
    domain_app_config = domain_app_config
    user_app_config = user_app_config
    merged_app_config = merged_app_config
    deployments = deployments
    deployment = deployment
    domain_fair_share = domain_fair_share
    domain_fair_shares = domain_fair_shares
    domain_usage_buckets = domain_usage_buckets
    project_fair_share = project_fair_share
    project_fair_shares = project_fair_shares
    project_usage_buckets = project_usage_buckets
    user_fair_share = user_fair_share
    user_fair_shares = user_fair_shares
    user_usage_buckets = user_usage_buckets
    revisions = revisions
    revision = revision
    replicas = replicas
    replica = replica
    notification_channel = notification_channel
    notification_channels = notification_channels
    notification_rule = notification_rule
    notification_rules = notification_rules
    notification_rule_types = notification_rule_types
    object_storage = object_storage
    object_storages = object_storages
    vfs_storage = vfs_storage
    vfs_storages = vfs_storages
    huggingface_registry = huggingface_registry
    huggingface_registries = huggingface_registries
    reservoir_registry = reservoir_registry
    reservoir_registries = reservoir_registries
    resource_groups = resource_groups
    default_artifact_registry = default_artifact_registry
    inference_runtime_configs = inference_runtime_configs
    inference_runtime_config = inference_runtime_config
    route = route
    routes = routes
    session_scheduling_histories = session_scheduling_histories
    deployment_histories = deployment_histories
    route_histories = route_histories


@strawberry.type
class Mutation:
    scan_artifacts = scan_artifacts
    scan_artifact_models = scan_artifact_models
    import_artifacts = import_artifacts
    upsert_domain_app_config = upsert_domain_app_config
    upsert_user_app_config = upsert_user_app_config
    delete_domain_app_config = delete_domain_app_config
    delete_user_app_config = delete_user_app_config
    delegate_scan_artifacts = delegate_scan_artifacts
    delegate_import_artifacts = delegate_import_artifacts
    update_artifact = update_artifact
    delete_artifacts = delete_artifacts
    restore_artifacts = restore_artifacts
    cleanup_artifact_revisions = cleanup_artifact_revisions
    cancel_import_artifact = cancel_import_artifact
    create_model_deployment = create_model_deployment
    update_model_deployment = update_model_deployment
    delete_model_deployment = delete_model_deployment
    sync_replicas = sync_replicas
    add_model_revision = add_model_revision
    create_model_revision = create_model_revision
    create_notification_channel = create_notification_channel
    update_notification_channel = update_notification_channel
    delete_notification_channel = delete_notification_channel
    validate_notification_channel = validate_notification_channel
    create_notification_rule = create_notification_rule
    update_notification_rule = update_notification_rule
    delete_notification_rule = delete_notification_rule
    validate_notification_rule = validate_notification_rule
    create_object_storage = create_object_storage
    update_object_storage = update_object_storage
    create_auto_scaling_rule = create_auto_scaling_rule
    update_auto_scaling_rule = update_auto_scaling_rule
    delete_auto_scaling_rule = delete_auto_scaling_rule
    delete_object_storage = delete_object_storage
    create_vfs_storage = create_vfs_storage
    update_vfs_storage = update_vfs_storage
    delete_vfs_storage = delete_vfs_storage
    register_storage_namespace = register_storage_namespace
    unregister_storage_namespace = unregister_storage_namespace
    create_huggingface_registry = create_huggingface_registry
    update_huggingface_registry = update_huggingface_registry
    delete_huggingface_registry = delete_huggingface_registry
    create_reservoir_registry = create_reservoir_registry
    update_reservoir_registry = update_reservoir_registry
    delete_reservoir_registry = delete_reservoir_registry
    get_presigned_download_url = get_presigned_download_url
    get_presigned_upload_url = get_presigned_upload_url
    approve_artifact_revision = approve_artifact_revision
    reject_artifact_revision = reject_artifact_revision
    create_access_token = create_access_token
    activate_deployment_revision = activate_deployment_revision
    update_route_traffic_status = update_route_traffic_status
    # Fair Share
    upsert_domain_fair_share_weight = upsert_domain_fair_share_weight
    upsert_project_fair_share_weight = upsert_project_fair_share_weight
    upsert_user_fair_share_weight = upsert_user_fair_share_weight
    # Resource Group
    update_resource_group_fair_share_spec = update_resource_group_fair_share_spec


@strawberry.type
class Subscription:
    artifact_status_changed = artifact_status_changed
    artifact_import_progress_updated = artifact_import_progress_updated
    deployment_status_changed = deployment_status_changed
    replica_status_changed = replica_status_changed
    scheduling_events_by_session = scheduling_events_by_session
    background_task_events = background_task_events


class CustomizedSchema(Schema):
    def as_str(self) -> str:
        sdl = super().as_str()
        sdl = sdl.replace("type PageInfo", "type PageInfo @shareable").replace(
            'import: ["@external", "@key"]', 'import: ["@external", "@key", "@shareable"]'
        )
        # Convert escaped newlines to actual newlines for better description formatting
        return sdl.replace("\\n", "\n")


schema = CustomizedSchema(
    query=Query,
    mutation=Mutation,
    subscription=Subscription,
    config=StrawberryConfig(auto_camel_case=True),
    enable_federation_2=True,
)
