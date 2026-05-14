"""Types for session controller."""

from dataclasses import dataclass
from typing import Any, Self

from ai.backend.common.exception import InvalidAPIParameters
from ai.backend.common.identifier.image import ImageID
from ai.backend.common.types import MountInfoEntry, MountPermission, ResourceSlot, SessionTypes
from ai.backend.manager.data.deployment.types import (
    ExecutionSpec,
    ModelRevisionData,
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
    def from_revision(cls, model_revision: ModelRevisionData) -> Self:
        if model_revision.image_id is None:
            raise InvalidAPIParameters(
                f"Revision {model_revision.id} has no image_id; cannot build session spec"
            )
        if model_revision.model_mount_config.vfolder_id is None:
            raise InvalidAPIParameters(
                f"Revision {model_revision.id} has no model vfolder; cannot build session spec"
            )
        return cls(
            mount_entries=[
                MountInfoEntry(
                    vfolder_id=model_revision.model_mount_config.vfolder_id,
                    mount_destination=(
                        model_revision.model_mount_config.mount_destination or "/models"
                    ),
                    mount_perm=MountPermission.READ_ONLY,
                ),
                *model_revision.model_mount_config.extra_mounts,
            ],
            resource_spec=ResourceSpec(
                cluster_mode=model_revision.cluster_config.mode,
                cluster_size=model_revision.cluster_config.size,
                resource_slots=dict(model_revision.resource_config.resource_slot),
                resource_opts=dict(model_revision.resource_config.resource_opts) or None,
            ),
            image_id=model_revision.image_id,
            execution_spec=ExecutionSpec(
                startup_command=model_revision.execution.startup_command,
                bootstrap_script=model_revision.execution.bootstrap_script,
                environ=(
                    {k: str(v) for k, v in model_revision.model_runtime_config.environ.items()}
                    if model_revision.model_runtime_config.environ
                    else None
                ),
                runtime_variant_id=model_revision.model_runtime_config.runtime_variant_id,
                callback_url=model_revision.execution.callback_url,
                inference_runtime_config=(
                    model_revision.model_runtime_config.inference_runtime_config
                ),
            ),
            session_type=SessionTypes.INFERENCE,
        )

    @classmethod
    def from_revision_spec(cls, model_revision: ModelRevisionSpec) -> Self:
        # Write-side counterpart for the legacy bridge: the draft pipeline
        # builds a ``ModelRevisionSpec`` before any row is persisted, so
        # there is no ``ModelRevisionData`` to validate against yet.
        mount_entries: list[MountInfoEntry] = [
            MountInfoEntry(
                vfolder_id=model_revision.mounts.model_vfolder_id,
                mount_destination=model_revision.mounts.model_mount_destination,
                mount_perm=MountPermission.READ_ONLY,
            )
        ]
        mount_entries.extend(model_revision.mounts.extra_mounts)
        return cls(
            mount_entries=mount_entries,
            resource_spec=model_revision.resource_spec,
            image_id=model_revision.image_id,
            execution_spec=model_revision.execution,
            session_type=SessionTypes.INFERENCE,
        )
