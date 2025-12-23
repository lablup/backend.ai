"""CreatorSpec for deployment revision creation."""

from __future__ import annotations

import uuid
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Any, Optional

from typing_extensions import override

from ai.backend.common.types import (
    ResourceSlot,
    RuntimeVariant,
    VFolderMount,
)
from ai.backend.manager.models.deployment_revision import DeploymentRevisionRow
from ai.backend.manager.repositories.base import CreatorSpec


@dataclass
class DeploymentRevisionCreatorSpec(CreatorSpec[DeploymentRevisionRow]):
    """CreatorSpec for deployment revision creation.

    Note: revision_number must be provided by the service layer after
    calculating from get_latest_revision_number().
    """

    endpoint_id: uuid.UUID
    revision_number: int
    image_id: uuid.UUID
    resource_group: str
    resource_slots: ResourceSlot
    resource_opts: Mapping[str, Any]
    cluster_mode: str
    cluster_size: int
    model_id: Optional[uuid.UUID]
    model_mount_destination: str
    model_definition_path: Optional[str]
    model_definition: Optional[Mapping[str, Any]]
    startup_command: Optional[str]
    bootstrap_script: Optional[str]
    environ: Mapping[str, Any]
    callback_url: Optional[str]
    runtime_variant: RuntimeVariant
    extra_mounts: Sequence[VFolderMount]

    @override
    def build_row(self) -> DeploymentRevisionRow:
        return DeploymentRevisionRow(
            endpoint=self.endpoint_id,
            revision_number=self.revision_number,
            image=self.image_id,
            model=self.model_id,
            model_mount_destination=self.model_mount_destination,
            model_definition_path=self.model_definition_path,
            model_definition=self.model_definition,
            resource_group=self.resource_group,
            resource_slots=self.resource_slots,
            resource_opts=self.resource_opts,
            cluster_mode=self.cluster_mode,
            cluster_size=self.cluster_size,
            startup_command=self.startup_command,
            bootstrap_script=self.bootstrap_script,
            environ=self.environ,
            callback_url=self.callback_url,
            runtime_variant=self.runtime_variant,
            extra_mounts=list(self.extra_mounts),
        )
