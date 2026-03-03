"""Inference session validation rule."""

from typing import override

from ai.backend.common.types import SessionTypes, VFolderUsageMode
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

        if not any(m.usage_mode == VFolderUsageMode.MODEL for m in context.vfolder_mounts):
            raise InvalidAPIParameters(
                "At least one model-type virtual folder must be mounted for inference sessions."
            )
