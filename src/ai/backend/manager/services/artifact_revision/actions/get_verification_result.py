from __future__ import annotations

from dataclasses import dataclass
from typing import override

from ai.backend.common.data.artifact.types import VerificationStepResult
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.services.artifact_revision.actions.base import (
    ArtifactRevisionSingleEntityAction,
)


@dataclass
class GetArtifactRevisionVerificationResultAction(ArtifactRevisionSingleEntityAction):
    @override
    @classmethod
    def action_name(cls) -> str:
        return "get_artifact_revision_verification_result"

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.GET


@dataclass
class GetArtifactRevisionVerificationResultActionResult:
    verification_result: VerificationStepResult | None
