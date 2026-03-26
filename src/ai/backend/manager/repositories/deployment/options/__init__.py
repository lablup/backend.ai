"""Query conditions and orders for deployment-related entities."""

from ai.backend.manager.models.deployment_policy.conditions import DeploymentPolicyConditions
from ai.backend.manager.models.deployment_revision.conditions import RevisionConditions
from ai.backend.manager.models.deployment_revision.orders import RevisionOrders
from ai.backend.manager.models.endpoint.conditions import (
    AccessTokenConditions,
    AutoScalingRuleConditions,
    DeploymentConditions,
)
from ai.backend.manager.models.endpoint.orders import (
    AccessTokenOrders,
    AutoScalingRuleOrders,
    DeploymentOrders,
)
from ai.backend.manager.models.routing.conditions import RouteConditions
from ai.backend.manager.models.routing.orders import RouteOrders

__all__ = [
    # AccessToken
    "AccessTokenConditions",
    "AccessTokenOrders",
    # AutoScalingRule
    "AutoScalingRuleConditions",
    "AutoScalingRuleOrders",
    # Deployment
    "DeploymentConditions",
    "DeploymentOrders",
    # DeploymentPolicy
    "DeploymentPolicyConditions",
    # Revision
    "RevisionConditions",
    "RevisionOrders",
    # Route
    "RouteConditions",
    "RouteOrders",
]
