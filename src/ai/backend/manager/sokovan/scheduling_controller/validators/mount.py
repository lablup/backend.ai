"""Mount name validation rule."""

from typing import Any

from ai.backend.manager.errors.api import InvalidAPIParameters
from ai.backend.manager.models import verify_vfolder_name
from ai.backend.manager.repositories.scheduler.types.session_creation import (
    AllowedScalingGroup,
    SessionCreationContext,
    SessionCreationSpec,
)

from .base import SessionValidatorRule


class MountNameValidationRule(SessionValidatorRule):
    """Validates vfolder mount names and aliases."""

    def name(self) -> str:
        return "mount_name_validation"

    def validate(
        self,
        spec: SessionCreationSpec,
        context: SessionCreationContext,
        allowed_groups: list[AllowedScalingGroup],
    ) -> None:
        """Validate mount names if mount map is provided."""
        mount_map = spec.creation_spec.get("mount_map") or {}
        mount_id_map = spec.creation_spec.get("mount_id_map") or {}
        combined_mount_map = {**mount_map, **mount_id_map}

        if combined_mount_map:
            self._validate_mount_names(combined_mount_map)

    def _validate_mount_names(
        self,
        mount_map: dict[str, Any],
    ) -> None:
        """Validate mount alias names."""
        original_folders = list(mount_map.keys())
        alias_folders = list(mount_map.values())

        # Check for duplicate aliases
        if len(alias_folders) != len(set(alias_folders)):
            raise InvalidAPIParameters("Duplicate alias folder name exists.")

        for alias_name in alias_folders:
            if alias_name is None:
                continue

            # Remove work directory prefix if present
            if alias_name.startswith("/home/work/"):
                alias_name = alias_name.replace("/home/work/", "")

            # Validate alias name
            if alias_name == "":
                raise InvalidAPIParameters("Alias name cannot be empty.")

            if not verify_vfolder_name(alias_name):
                raise InvalidAPIParameters(f"{alias_name} is reserved for internal path.")

            # Check if alias conflicts with original folder names
            if alias_name in original_folders:
                raise InvalidAPIParameters(
                    f"Alias name cannot be set to an existing folder name: {alias_name}"
                )
