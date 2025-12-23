"""CreatorSpec for deployment (endpoint) creation."""

from __future__ import annotations

import uuid
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Optional

import yarl
from typing_extensions import override

from ai.backend.common.types import (
    ClusterMode,
    ResourceSlot,
    RuntimeVariant,
    VFolderMount,
)
from ai.backend.manager.models.endpoint import EndpointLifecycle, EndpointRow
from ai.backend.manager.repositories.base import CreatorSpec

# ========== Field groups for DeploymentCreatorSpec ==========


@dataclass
class DeploymentMetadataFields:
    """Metadata fields for deployment creation.

    Corresponds to DeploymentMetadata in data layer.
    """

    name: str
    domain: str
    project_id: uuid.UUID
    resource_group: str
    created_user_id: uuid.UUID
    session_owner_id: uuid.UUID
    revision_history_limit: int = 10
    tag: Optional[str] = None
    created_at: Optional[datetime] = None


@dataclass
class DeploymentReplicaFields:
    """Replica fields for deployment creation.

    Corresponds to ReplicaSpec in data layer.
    """

    replica_count: int
    desired_replica_count: Optional[int] = None


@dataclass
class DeploymentNetworkFields:
    """Network fields for deployment creation.

    Corresponds to DeploymentNetworkSpec in data layer.
    """

    open_to_public: bool = False
    url: Optional[str] = None


@dataclass
class DeploymentResourceFields:
    """Resource fields for deployment model revision.

    Corresponds to ResourceSpec in data layer.
    """

    cluster_mode: ClusterMode
    cluster_size: int
    resource_slots: ResourceSlot
    resource_opts: Optional[Mapping[str, Any]] = None


@dataclass
class DeploymentMountFields:
    """Mount fields for deployment model revision.

    Corresponds to VFolderMountsCreator in data layer.
    """

    model_vfolder_id: Optional[uuid.UUID]
    model_mount_destination: str = "/models"
    model_definition_path: Optional[str] = None
    extra_mounts: Sequence[VFolderMount] = ()


@dataclass
class DeploymentExecutionFields:
    """Execution fields for deployment model revision.

    Corresponds to ExecutionSpec in data layer.
    """

    runtime_variant: RuntimeVariant = RuntimeVariant.CUSTOM
    startup_command: Optional[str] = None
    bootstrap_script: Optional[str] = None
    environ: Optional[Mapping[str, str]] = None
    callback_url: Optional[yarl.URL] = None


@dataclass
class ModelRevisionFields:
    """Model revision fields for deployment creation.

    Corresponds to ModelRevisionCreator in data layer.
    Note: image_id is a resolved UUID, not ImageIdentifier.
    """

    image_id: uuid.UUID
    resource: DeploymentResourceFields
    mounts: DeploymentMountFields
    execution: DeploymentExecutionFields


@dataclass
class DeploymentCreatorSpec(CreatorSpec[EndpointRow]):
    """CreatorSpec for deployment creation with nested field groups.

    Corresponds to NewDeploymentCreator in data layer.
    All external references (like image) should be already resolved to UUIDs.
    """

    metadata: DeploymentMetadataFields
    replica: DeploymentReplicaFields
    network: DeploymentNetworkFields
    revision: ModelRevisionFields

    @override
    def build_row(self) -> EndpointRow:
        return EndpointRow(
            # Metadata fields
            name=self.metadata.name,
            domain=self.metadata.domain,
            project=self.metadata.project_id,
            resource_group=self.metadata.resource_group,
            created_user=self.metadata.created_user_id,
            session_owner=self.metadata.session_owner_id,
            revision_history_limit=self.metadata.revision_history_limit,
            tag=self.metadata.tag,
            # Replica fields
            replicas=self.replica.replica_count,
            desired_replicas=self.replica.desired_replica_count,
            # Network fields
            open_to_public=self.network.open_to_public,
            url=self.network.url,
            # Revision fields - image
            image=self.revision.image_id,
            # Revision fields - resource
            cluster_mode=self.revision.resource.cluster_mode,
            cluster_size=self.revision.resource.cluster_size,
            resource_slots=self.revision.resource.resource_slots,
            resource_opts=self.revision.resource.resource_opts or {},
            # Revision fields - mounts
            model=self.revision.mounts.model_vfolder_id,
            model_mount_destination=self.revision.mounts.model_mount_destination,
            model_definition_path=self.revision.mounts.model_definition_path,
            extra_mounts=list(self.revision.mounts.extra_mounts),
            # Revision fields - execution
            runtime_variant=self.revision.execution.runtime_variant,
            startup_command=self.revision.execution.startup_command,
            bootstrap_script=self.revision.execution.bootstrap_script,
            environ=dict(self.revision.execution.environ)
            if self.revision.execution.environ
            else {},
            callback_url=self.revision.execution.callback_url,
            # Default state fields
            lifecycle_stage=EndpointLifecycle.PENDING,
            retries=0,
        )
