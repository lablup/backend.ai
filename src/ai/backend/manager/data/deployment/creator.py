from dataclasses import dataclass
from typing import Any, override
from uuid import UUID

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

    @override
    def fields_to_store(self) -> dict[str, Any]:
        """Return a dictionary of all fields for storage operations."""
        return {
            "name": self.metadata.name,
            "domain": self.metadata.domain,
            "project": self.metadata.project,
            "resource_group": self.metadata.resource_group,
            "created_user": self.metadata.created_user,
            "session_owner": self.metadata.session_owner,
            "tag": self.metadata.tag,
            "replicas": self.replica_spec.replica_count,
            "model_vfolder_id": self.model_revision.mounts.model_vfolder_id,
            "model_mount_destination": self.model_revision.mounts.model_mount_destination,
            "extra_mounts": self.model_revision.mounts.extra_mounts,
            "image": self.model_revision.image,
            "cluster_mode": self.model_revision.resource_spec.cluster_mode,
            "cluster_size": self.model_revision.resource_spec.cluster_size,
            "resource_slots": self.model_revision.resource_spec.resource_slots,
            "resource_opts": self.model_revision.resource_spec.resource_opts,
            "runtime_variant": self.model_revision.execution.runtime_variant,
            "startup_command": self.model_revision.execution.startup_command,
            "bootstrap_script": self.model_revision.execution.bootstrap_script,
            "environ": self.model_revision.execution.environ,
            "callback_url": self.model_revision.execution.callback_url,
            "open_to_public": self.network.open_to_public,
            "url": self.network.url,
        }
