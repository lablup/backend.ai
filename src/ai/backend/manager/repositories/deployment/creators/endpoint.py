"""CreatorSpec for endpoint. This is mainly for legacy support."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from typing import Any, Optional, Self, override
from uuid import UUID

import yarl

from ai.backend.common.types import (
    ClusterMode,
    ResourceSlot,
    RuntimeVariant,
    VFolderMount,
)
from ai.backend.manager.data.deployment.creator import DeploymentCreator
from ai.backend.manager.models.endpoint import EndpointLifecycle, EndpointRow
from ai.backend.manager.repositories.base import CreatorSpec

from .policy import DeploymentPolicyCreatorSpec


@dataclass
class LegacyEndpointCreatorSpec(CreatorSpec[EndpointRow]):
    """CreatorSpec for legacy endpoint creation.

    This spec is used for backward compatibility with legacy DeploymentCreator.
    Unlike DeploymentCreatorSpec which uses field groups, this spec takes
    an already-resolved image_id (UUID) and creates an EndpointRow directly.
    """

    # Metadata fields (from DeploymentMetadata)
    name: str
    domain: str
    project: UUID
    resource_group: str
    created_user: UUID
    session_owner: UUID
    revision_history_limit: int = 10
    tag: Optional[str] = None

    # Replica fields (from ReplicaSpec)
    replicas: int = 0
    desired_replicas: Optional[int] = None

    # Network fields (from DeploymentNetworkSpec)
    open_to_public: bool = False
    url: Optional[str] = None

    # Model revision fields - image (resolved UUID, not ImageIdentifier)
    image_id: Optional[UUID] = None

    # Model revision fields - resource (from ResourceSpec)
    cluster_mode: ClusterMode = ClusterMode.SINGLE_NODE
    cluster_size: int = 1
    resource_slots: ResourceSlot = field(default_factory=ResourceSlot)
    resource_opts: Optional[Mapping[str, Any]] = None

    # Model revision fields - mounts (from MountMetadata)
    model: Optional[UUID] = None
    model_mount_destination: str = "/models"
    model_definition_path: Optional[str] = None
    extra_mounts: Sequence[VFolderMount] = field(default_factory=list)

    # Model revision fields - execution (from ExecutionSpec)
    runtime_variant: RuntimeVariant = RuntimeVariant.CUSTOM
    startup_command: Optional[str] = None
    bootstrap_script: Optional[str] = None
    environ: Optional[Mapping[str, str]] = None
    callback_url: Optional[yarl.URL] = None

    policy: DeploymentPolicyCreatorSpec | None = None

    @classmethod
    def from_deployment_creator(
        cls,
        creator: DeploymentCreator,
        image_id: UUID,
    ) -> Self:
        """Create a spec from DeploymentCreator with resolved image_id.

        Args:
            creator: Legacy DeploymentCreator containing deployment configuration.
            image_id: Resolved image UUID (from ImageRow.lookup).

        Returns:
            LegacyEndpointCreatorSpec instance.
        """
        return cls(
            # Metadata
            name=creator.metadata.name,
            domain=creator.metadata.domain,
            project=creator.metadata.project,
            resource_group=creator.metadata.resource_group,
            created_user=creator.metadata.created_user,
            session_owner=creator.metadata.session_owner,
            revision_history_limit=creator.metadata.revision_history_limit,
            tag=creator.metadata.tag,
            # Replica
            replicas=creator.replica_spec.replica_count,
            desired_replicas=creator.replica_spec.desired_replica_count,
            # Network
            open_to_public=creator.network.open_to_public,
            url=creator.network.url,
            # Image (resolved)
            image_id=image_id,
            # Resource
            cluster_mode=creator.model_revision.resource_spec.cluster_mode,
            cluster_size=creator.model_revision.resource_spec.cluster_size,
            resource_slots=ResourceSlot(creator.model_revision.resource_spec.resource_slots),
            resource_opts=creator.model_revision.resource_spec.resource_opts,
            # Mounts
            model=creator.model_revision.mounts.model_vfolder_id,
            model_mount_destination=creator.model_revision.mounts.model_mount_destination,
            model_definition_path=creator.model_revision.mounts.model_definition_path,
            extra_mounts=creator.model_revision.mounts.extra_mounts,
            # Execution
            runtime_variant=creator.model_revision.execution.runtime_variant,
            startup_command=creator.model_revision.execution.startup_command,
            bootstrap_script=creator.model_revision.execution.bootstrap_script,
            environ=creator.model_revision.execution.environ,
            callback_url=creator.model_revision.execution.callback_url,
        )

    @override
    def build_row(self) -> EndpointRow:
        return EndpointRow(
            # Metadata fields
            name=self.name,
            domain=self.domain,
            project=self.project,
            resource_group=self.resource_group,
            created_user=self.created_user,
            session_owner=self.session_owner,
            revision_history_limit=self.revision_history_limit,
            tag=self.tag,
            # Replica fields
            replicas=self.replicas,
            desired_replicas=self.desired_replicas,
            # Network fields
            open_to_public=self.open_to_public,
            url=self.url,
            # Image
            image=self.image_id,
            # Resource fields
            cluster_mode=self.cluster_mode.value,
            cluster_size=self.cluster_size,
            resource_slots=self.resource_slots,
            resource_opts=dict(self.resource_opts) if self.resource_opts else {},
            # Mount fields
            model=self.model,
            model_mount_destination=self.model_mount_destination,
            model_definition_path=self.model_definition_path,
            extra_mounts=list(self.extra_mounts),
            # Execution fields
            runtime_variant=self.runtime_variant,
            startup_command=self.startup_command,
            bootstrap_script=self.bootstrap_script,
            environ=dict(self.environ) if self.environ else {},
            callback_url=self.callback_url,
            # Default state fields
            lifecycle_stage=EndpointLifecycle.PENDING,
            retries=0,
        )
