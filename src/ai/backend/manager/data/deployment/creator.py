from dataclasses import dataclass

from ai.backend.manager.data.deployment.types import (
    DeploymentMetadata,
    DeploymentNetworkSpec,
    ModelRevisionSpec,
    ReplicaSpec,
)
from ai.backend.manager.types import Creator


@dataclass
class DeploymentCreator(Creator):
    metadata: DeploymentMetadata
    replica_spec: ReplicaSpec
    network: DeploymentNetworkSpec
    model_revision: ModelRevisionSpec
