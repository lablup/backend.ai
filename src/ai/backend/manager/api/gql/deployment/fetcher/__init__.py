"""Deployment fetcher package."""

from .access_token import (
    fetch_access_tokens,
    get_access_token_pagination_spec,
)
from .auto_scaling import (
    fetch_auto_scaling_rules,
    get_auto_scaling_rule_pagination_spec,
)
from .deployment import (
    fetch_deployment,
    fetch_deployments,
    get_deployment_pagination_spec,
)
from .replica import (
    fetch_replica,
    fetch_replicas,
    get_replica_pagination_spec,
)
from .revision import (
    fetch_revision,
    fetch_revisions,
    get_revision_pagination_spec,
)
from .route import (
    fetch_route,
    fetch_routes,
)

__all__ = [
    # Access Token
    "fetch_access_tokens",
    "get_access_token_pagination_spec",
    # Auto Scaling
    "fetch_auto_scaling_rules",
    "get_auto_scaling_rule_pagination_spec",
    # Deployment
    "fetch_deployment",
    "fetch_deployments",
    "get_deployment_pagination_spec",
    # Replica
    "fetch_replica",
    "fetch_replicas",
    "get_replica_pagination_spec",
    # Revision
    "fetch_revision",
    "fetch_revisions",
    "get_revision_pagination_spec",
    # Route
    "fetch_route",
    "fetch_routes",
]
