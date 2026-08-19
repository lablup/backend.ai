from __future__ import annotations

from dataclasses import dataclass
from typing import override

from ai.backend.common.data.artifact.types import CombinedDownloadProgress
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.services.artifact_revision.actions.base import (
    ArtifactRevisionSingleEntityAction,
)


@dataclass
class GetDownloadProgressAction(ArtifactRevisionSingleEntityAction):
    @override
    @classmethod
    def action_name(cls) -> str:
        return "get_download_progress"

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.GET


@dataclass
class GetDownloadProgressActionResult:
    download_progress: CombinedDownloadProgress
