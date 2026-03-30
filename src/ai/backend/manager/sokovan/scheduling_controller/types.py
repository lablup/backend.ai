"""Types for session controller."""

from dataclasses import dataclass
from typing import Any, Self

from ai.backend.common.types import ResourceSlot, SessionTypes
from ai.backend.manager.data.deployment.types import (
    ExecutionSpec,
    ModelRevisionSpec,
    MountSpec,
    ResourceSpec,
)
from ai.backend.manager.data.image.types import ImageIdentifier


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
    mount_spec: MountSpec
    resource_spec: ResourceSpec
    image_identifier: ImageIdentifier
    execution_spec: ExecutionSpec
    session_type: SessionTypes

    @classmethod
    def from_revision(cls, model_revision: ModelRevisionSpec) -> Self:
        return cls(
            mount_spec=model_revision.mounts.to_mount_spec(),
            resource_spec=model_revision.resource_spec,
            image_identifier=model_revision.image_identifier,
            execution_spec=model_revision.execution,
            session_type=SessionTypes.INFERENCE,
        )
