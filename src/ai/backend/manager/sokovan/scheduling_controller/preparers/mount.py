"""Mount data preparation rule."""

from typing import Any

from ai.backend.manager.repositories.scheduler.types.session_creation import (
    SessionCreationContext,
    SessionCreationSpec,
)

from .base import SessionPreparerRule


class MountPreparationRule(SessionPreparerRule):
    """Prepares mount data for the session."""

    def name(self) -> str:
        return "mount_preparation"

    def prepare(
        self,
        spec: SessionCreationSpec,
        context: SessionCreationContext,
        preparation_data: dict[str, Any],
    ) -> None:
        """Prepare mount data."""
        mount_map = spec.creation_spec.get("mount_map") or {}
        mount_id_map = spec.creation_spec.get("mount_id_map") or {}
        combined_mount_map = {**mount_map, **mount_id_map}

        # Validation is now handled by MountNameValidationRule
        preparation_data["mount_map_prepared"] = True
        preparation_data["combined_mount_map"] = combined_mount_map
