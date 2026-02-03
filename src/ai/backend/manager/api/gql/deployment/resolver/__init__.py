"""Deployment resolver package.

Contains GraphQL query, mutation, and subscription resolver functions
for the deployment module.
"""

from .access_token import (
    create_access_token,
)
from .auto_scaling import (
    create_auto_scaling_rule,
    delete_auto_scaling_rule,
    update_auto_scaling_rule,
)
from .deployment import (
    create_model_deployment,
    delete_model_deployment,
    deployment,
    deployment_status_changed,
    deployments,
    sync_replicas,
    update_model_deployment,
)
from .replica import (
    replica,
    replica_status_changed,
    replicas,
)
from .revision import (
    activate_deployment_revision,
    add_model_revision,
    create_model_revision,
    inference_runtime_config,
    inference_runtime_configs,
    revision,
    revisions,
)
from .route import (
    route,
    routes,
    update_route_traffic_status,
)

__all__ = [
    # Access Token
    "create_access_token",
    # Auto Scaling
    "create_auto_scaling_rule",
    "update_auto_scaling_rule",
    "delete_auto_scaling_rule",
    # Deployment
    "deployments",
    "deployment",
    "create_model_deployment",
    "update_model_deployment",
    "delete_model_deployment",
    "sync_replicas",
    "deployment_status_changed",
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
    "create_model_revision",
    "activate_deployment_revision",
    # Route
    "routes",
    "route",
    "update_route_traffic_status",
]
