from dataclasses import dataclass
from uuid import UUID

from ai.backend.manager.data.deployment.types import (
    DeploymentMetadata,
    DeploymentNetworkSpec,
    ModelRevisionSpec,
    ReplicaSpec,
)


@dataclass
class DeploymentCreator:
    metadata: DeploymentMetadata
    replica_spec: ReplicaSpec
    network: DeploymentNetworkSpec
    model_revision: ModelRevisionSpec

    # Accessor properties for backward compatibility
    @property
    def model_id(self) -> UUID:
        """Get the model vfolder ID from model revision."""
        return self.model_revision.mounts.model_vfolder_id

    @property
    def domain(self) -> str:
        """Get the domain name from metadata."""
        return self.metadata.domain

    @property
    def project(self) -> UUID:
        """Get the project ID from metadata."""
        return self.metadata.project

    @property
    def name(self) -> str:
        """Get the deployment name from metadata."""
        return self.metadata.name
