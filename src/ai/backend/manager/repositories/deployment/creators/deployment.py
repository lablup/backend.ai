"""CreatorSpec for deployment (endpoint) creation."""

from __future__ import annotations

import uuid
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import datetime
from typing import Any, override

import yarl

from ai.backend.common.data.endpoint.types import ScalingState
from ai.backend.common.types import (
    ClusterMode,
    MountInfoEntry,
    ResourceSlot,
    RuntimeVariant,
)
from ai.backend.manager.data.deployment.types import (
    DeploymentLifecycleSubStep,
    DeploymentOptions,
)
from ai.backend.manager.models.endpoint import EndpointLifecycle, EndpointRow
from ai.backend.manager.repositories.base import CreatorSpec
from ai.backend.manager.repositories.base.updater import BatchUpdaterSpec

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
    tag: str | None = None
    created_at: datetime | None = None


@dataclass
class DeploymentReplicaFields:
    """Replica fields for deployment creation.

    Corresponds to ReplicaSpec in data layer.
    """

    replica_count: int
    desired_replica_count: int | None = None


@dataclass
class DeploymentNetworkFields:
    """Network fields for deployment creation.

    Corresponds to DeploymentNetworkSpec in data layer.
    """

    open_to_public: bool = False
    url: str | None = None


@dataclass
class DeploymentResourceFields:
    """Resource fields for deployment model revision.

    Corresponds to ResourceSpec in data layer.
    """

    cluster_mode: ClusterMode
    cluster_size: int
    resource_slots: ResourceSlot
    resource_opts: Mapping[str, Any] | None = None


@dataclass
class DeploymentMountFields:
    """Mount fields for deployment model revision.

    Corresponds to VFolderMountsCreator in data layer.
    """

    model_vfolder_id: uuid.UUID | None
    model_mount_destination: str = "/models"
    model_definition_path: str | None = None
    extra_mounts: Sequence[MountInfoEntry] = ()


@dataclass
class DeploymentExecutionFields:
    """Execution fields for deployment model revision.

    Corresponds to ExecutionSpec in data layer.
    """

    runtime_variant: RuntimeVariant
    startup_command: str | None = None
    bootstrap_script: str | None = None
    environ: Mapping[str, str] | None = None
    callback_url: yarl.URL | None = None


@dataclass
class ModelRevisionFields:
    """Model revision fields for deployment creation.

    Corresponds to ModelRevisionCreator in data layer.
    Note: image_id is a resolved UUID, not ImageIdentifier.
    """

    image_id: uuid.UUID | None
    resource: DeploymentResourceFields
    mounts: DeploymentMountFields
    execution: DeploymentExecutionFields


@dataclass
class DeploymentCreatorSpec(CreatorSpec[EndpointRow]):
    """CreatorSpec for deployment creation with nested field groups.

    Corresponds to NewDeploymentCreator in data layer.
    All external references (like image) should be already resolved to UUIDs.

    ``options`` defaults to an empty :class:`DeploymentOptions`; the
    db_source overwrites it with a snapshot of the target scaling
    group's ``default_deployment_options`` before the row is flushed
    so every endpoint persists a fully-resolved copy.
    """

    metadata: DeploymentMetadataFields
    replica: DeploymentReplicaFields
    network: DeploymentNetworkFields
    options: DeploymentOptions
    revision: ModelRevisionFields | None = None

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
            # Default state fields
            lifecycle_stage=EndpointLifecycle.PENDING,
            retries=0,
            options=self.options,
        )


@dataclass
class EndpointLifecycleBatchUpdaterSpec(BatchUpdaterSpec[EndpointRow]):
    """BatchUpdaterSpec for batch updating endpoint lifecycle status.

    Each axis is independently optional; ``None`` means "do not touch
    this column". ``sub_step`` is coupled to ``lifecycle_stage`` — it
    is written (possibly to ``None``, clearing any leftover sub-step)
    only when the lifecycle advances. Pure scaling-only transitions
    (``lifecycle_stage is None``) leave ``sub_step`` untouched so a
    ``DEPLOYING`` endpoint's sub-step survives a scaling-state flip.
    """

    lifecycle_stage: EndpointLifecycle | None = None
    sub_step: DeploymentLifecycleSubStep | None = None
    scaling_state: ScalingState | None = None

    @property
    @override
    def row_class(self) -> type[EndpointRow]:
        return EndpointRow

    @override
    def build_values(self) -> dict[str, Any]:
        values: dict[str, Any] = {}
        if self.lifecycle_stage is not None:
            values["lifecycle_stage"] = self.lifecycle_stage
            values["sub_step"] = self.sub_step
        if self.scaling_state is not None:
            values["scaling_state"] = self.scaling_state
        return values
