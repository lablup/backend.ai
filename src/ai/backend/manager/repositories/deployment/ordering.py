from dataclasses import dataclass, field

from ai.backend.manager.api.gql.model_deployment.model_deployment import (
    DeploymentOrderField,
)
from ai.backend.manager.api.gql.model_deployment.model_replica import ReplicaOrderField
from ai.backend.manager.api.gql.model_deployment.model_revision import ModelRevisionOrderField


@dataclass
class DeploymentOrderingOptions:
    """Options for ordering model deployments."""

    order_by: list[tuple[DeploymentOrderField, bool]] = field(
        default_factory=lambda: [(DeploymentOrderField.CREATED_AT, True)]
    )


@dataclass
class ModelRevisionOrderingOptions:
    """Options for ordering model revisions."""

    order_by: list[tuple[ModelRevisionOrderField, bool]] = field(
        default_factory=lambda: [(ModelRevisionOrderField.CREATED_AT, True)]
    )


@dataclass
class ModelReplicaOrderingOptions:
    """Options for ordering model replicas."""

    order_by: list[tuple[ReplicaOrderField, bool]] = field(
        default_factory=lambda: [(ReplicaOrderField.CREATED_AT, True)]
    )
