from __future__ import annotations

from collections.abc import Sequence
from pathlib import PurePosixPath
from typing import override

from ai.backend.common.types import MountInfoEntry
from ai.backend.manager.data.deployment.types import ModelRevisionSpec
from ai.backend.manager.errors.api import InvalidAPIParameters
from ai.backend.manager.models.deployment_revision.creators import (
    DeploymentRevisionCreator,
)
from ai.backend.manager.sokovan.deployment.validators.base import (
    DeploymentRevisionValidationContext,
    DeploymentRevisionValidatorRule,
)


class NoParentSegmentInMountDestinationRule(DeploymentRevisionValidatorRule):
    @override
    def name(self) -> str:
        return "no_parent_segment_in_mount_destination"

    @override
    def validate(
        self,
        spec: DeploymentRevisionCreator,
        context: DeploymentRevisionValidationContext,
    ) -> None:
        self._reject_mount_destinations_with_parent_segment(
            spec.model_mount_destination, spec.extra_mounts
        )

    @override
    def validate_legacy_revision_spec(
        self,
        spec: ModelRevisionSpec,
        context: DeploymentRevisionValidationContext,
    ) -> None:
        self._reject_mount_destinations_with_parent_segment(
            spec.mounts.model_mount_destination, spec.mounts.extra_mounts
        )

    def _reject_mount_destinations_with_parent_segment(
        self,
        model_mount_destination: str,
        extra_mounts: Sequence[MountInfoEntry],
    ) -> None:
        if ".." in PurePosixPath(model_mount_destination).parts:
            raise InvalidAPIParameters(
                extra_msg=(
                    f"model_mount_destination '{model_mount_destination}' "
                    "must not contain a '..' segment."
                )
            )
        for mount_idx, mount in enumerate(extra_mounts):
            if mount.mount_destination is None:
                continue
            if ".." in PurePosixPath(mount.mount_destination).parts:
                raise InvalidAPIParameters(
                    extra_msg=(
                        f"extra_mounts[{mount_idx}].mount_destination "
                        f"'{mount.mount_destination}' must not contain a '..' segment."
                    )
                )
