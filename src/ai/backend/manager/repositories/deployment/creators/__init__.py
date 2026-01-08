"""CreatorSpec implementations for deployment domain."""

from .auto_scaling import DeploymentAutoScalingPolicyCreatorSpec
from .deployment import (
    DeploymentCreatorSpec,
    DeploymentExecutionFields,
    DeploymentMetadataFields,
    DeploymentMountFields,
    DeploymentNetworkFields,
    DeploymentReplicaFields,
    DeploymentResourceFields,
    ModelRevisionFields,
)
from .policy import DeploymentPolicyCreatorSpec
from .revision import DeploymentRevisionCreatorSpec
from .route import RouteBatchUpdaterSpec, RouteCreatorSpec
from .token import EndpointTokenCreatorSpec

__all__ = [
    # Deployment (endpoint) - CreatorSpec
    "DeploymentCreatorSpec",
    # Deployment (endpoint) - Field groups
    "DeploymentMetadataFields",
    "DeploymentReplicaFields",
    "DeploymentNetworkFields",
    "DeploymentResourceFields",
    "DeploymentMountFields",
    "DeploymentExecutionFields",
    "ModelRevisionFields",
    # Revision
    "DeploymentRevisionCreatorSpec",
    # Auto-scaling
    "DeploymentAutoScalingPolicyCreatorSpec",
    # Policy
    "DeploymentPolicyCreatorSpec",
    # Route
    "RouteCreatorSpec",
    "RouteBatchUpdaterSpec",
    # Token
    "EndpointTokenCreatorSpec",
]
