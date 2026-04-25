"""Types for session controller."""

from dataclasses import dataclass
from typing import Any, Self

from ai.backend.common.identifier.image import ImageID
from ai.backend.common.types import MountInfoEntry, MountPermission, ResourceSlot, SessionTypes
from ai.backend.manager.data.deployment.types import (
    ExecutionSpec,
    ModelRevisionSpec,
    ResourceSpec,
)


@dataclass
class KernelResourceInfo:
    """Calculated resource information for a kernel."""

    requested_slots: ResourceSlot
    resource_opts: dict[str, Any]


@dataclass
class CalculatedResources:
    """Pre-calculated resources for session creation."""

    session_requested_slots: ResourceSlot
    kernel_resources: list[KernelResourceInfo]


@dataclass
class SessionValidationSpec:
    # Typed carrier replacing the legacy ``MountSpec`` 3-dict split.
    # The model vfolder is always first (read-only), extra mounts follow.
    mount_entries: list[MountInfoEntry]
    resource_spec: ResourceSpec
    image_id: ImageID
    execution_spec: ExecutionSpec
    session_type: SessionTypes

    @classmethod
    def from_revision(cls, model_revision: ModelRevisionSpec) -> Self:
        return cls(
            mount_entries=[
                MountInfoEntry(
                    vfolder_id=model_revision.mounts.model_vfolder_id,
                    mount_destination=model_revision.mounts.model_mount_destination,
                    mount_perm=MountPermission.READ_ONLY,
                ),
                *model_revision.mounts.extra_mounts,
            ],
            resource_spec=model_revision.resource_spec,
            image_id=model_revision.image_id,
            execution_spec=model_revision.execution,
            session_type=SessionTypes.INFERENCE,
        )
