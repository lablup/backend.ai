"""Internal data preparation rule."""

from typing import Any

from ai.backend.manager.repositories.scheduler.types.session_creation import (
    SessionCreationContext,
    SessionCreationSpec,
)

from .base import SessionPreparerRule


class InternalDataRule(SessionPreparerRule):
    """Prepares internal data for the session."""

    def name(self) -> str:
        return "internal_data"

    def prepare(
        self,
        spec: SessionCreationSpec,
        context: SessionCreationContext,
        preparation_data: dict[str, Any],
    ) -> None:
        """Prepare internal data."""
        # Start with provided internal data or empty dict
        internal_data = spec.internal_data.copy() if spec.internal_data else {}

        # Add dotfile data if available
        if "dotfile_data" in preparation_data:
            internal_data.update(preparation_data["dotfile_data"])

        # Add model-related fields if present
        if model_def_path := spec.creation_spec.get("model_definition_path"):
            internal_data["model_definition_path"] = model_def_path

        if runtime_variant := spec.creation_spec.get("runtime_variant"):
            internal_data["runtime_variant"] = runtime_variant

        # Add sudo session flag if enabled
        if spec.sudo_session_enabled:
            internal_data["sudo_session_enabled"] = True

        preparation_data["internal_data"] = internal_data
