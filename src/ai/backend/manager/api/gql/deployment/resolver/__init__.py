"""Deployment resolver package.

Contains GraphQL query, mutation, and subscription resolver functions
for the deployment module.
"""

from .access_token import (
    create_access_token,
    delete_access_token,
)
from .auto_scaling import (
    create_auto_scaling_rule,
    delete_auto_scaling_rule,
    update_auto_scaling_rule,
)
from .deployment import (
    admin_deployments,
    create_model_deployment,
    delete_model_deployment,
    deployment,
    deployment_status_changed,
    my_deployments,
    project_deployments,
    sync_replicas,
    update_model_deployment,
)
from .policy import (
    update_deployment_policy,
)
from .replica import (
    replica,
    replica_status_changed,
    replicas,
)
from .revision import (
    activate_deployment_revision,
    add_model_revision,
    inference_runtime_config,
    inference_runtime_configs,
    revision,
    revisions,
)
from .revision_preset import (
    admin_create_deployment_revision_preset,
    admin_delete_deployment_revision_preset,
    admin_update_deployment_revision_preset,
    deployment_revision_preset,
    deployment_revision_presets,
)
from .route import (
    route,
    routes,
    update_route_traffic_status,
)

__all__ = [
    # Access Token
    "create_access_token",
    "delete_access_token",
    # Auto Scaling
    "create_auto_scaling_rule",
    "update_auto_scaling_rule",
    "delete_auto_scaling_rule",
    # Deployment
    "admin_deployments",
    "my_deployments",
    "project_deployments",
    "deployment",
    "create_model_deployment",
    "update_model_deployment",
    "delete_model_deployment",
    "sync_replicas",
    "deployment_status_changed",
    # Policy
    "update_deployment_policy",
    # Replica
    "replicas",
    "replica",
    "replica_status_changed",
    # Revision
    "revisions",
    "revision",
    "inference_runtime_config",
    "inference_runtime_configs",
    "add_model_revision",
    "activate_deployment_revision",
    # Route
    "routes",
    "route",
    "update_route_traffic_status",
    # Revision Preset
    "admin_create_deployment_revision_preset",
    "admin_delete_deployment_revision_preset",
    "admin_update_deployment_revision_preset",
    "deployment_revision_preset",
    "deployment_revision_presets",
]
