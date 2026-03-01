"""Inference session validation rule."""

from typing import override

from ai.backend.common.types import RuntimeVariant, SessionTypes, VFolderUsageMode
from ai.backend.manager.errors.api import InvalidAPIParameters
from ai.backend.manager.repositories.scheduler.types.session_creation import (
    SessionCreationContext,
    SessionCreationSpec,
)

from .base import SessionValidatorRule


class InferenceModelFolderRule(SessionValidatorRule):
    """Validates that inference sessions have at least one model-type virtual folder mounted."""

    @override
    def name(self) -> str:
        return "inference_model_folder"

    @override
    def validate(
        self,
        spec: SessionCreationSpec,
        context: SessionCreationContext,
    ) -> None:
        if spec.session_type != SessionTypes.INFERENCE:
            return

        runtime_variant = spec.creation_spec.get("runtime_variant")
        if runtime_variant == RuntimeVariant.CUSTOM.value:
            return

        model_folders = [
            m for m in context.vfolder_mounts if m.usage_mode == VFolderUsageMode.MODEL
        ]
        if len(model_folders) == 0:
            raise InvalidAPIParameters(
                "At least one model-type virtual folder must be mounted for inference sessions."
            )
