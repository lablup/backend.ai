from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, override

from ai.backend.common.data.artifact.types import VerificationStepResult
from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.services.artifact_revision.actions.base import ArtifactRevisionAction


@dataclass
class GetArtifactRevisionVerificationResultAction(ArtifactRevisionAction):
    model_id: str
    revision: str

    @override
    def entity_id(self) -> Optional[str]:
        return None

    @override
    @classmethod
    def operation_type(cls) -> str:
        return "get_verification_result"


@dataclass
class GetArtifactRevisionVerificationResultActionResult(BaseActionResult):
    verification_result: Optional[VerificationStepResult]

    @override
    def entity_id(self) -> Optional[str]:
        return None
