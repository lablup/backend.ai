from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, override

from ai.backend.common.data.artifact.types import DownloadProgressData
from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.services.artifact_revision.actions.base import ArtifactRevisionAction


@dataclass
class GetDownloadProgressAction(ArtifactRevisionAction):
    model_id: str
    revision: str

    @override
    def entity_id(self) -> Optional[str]:
        return f"{self.model_id}:{self.revision}"

    @override
    @classmethod
    def operation_type(cls) -> str:
        return "get_download_progress"


@dataclass
class GetDownloadProgressActionResult(BaseActionResult):
    download_progress: DownloadProgressData

    @override
    def entity_id(self) -> Optional[str]:
        return None
