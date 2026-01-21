from __future__ import annotations

import uuid
from dataclasses import dataclass
from typing import Optional, override

from ai.backend.common.data.artifact.types import CombinedDownloadProgress
from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.services.artifact_revision.actions.base import ArtifactRevisionAction


@dataclass
class GetDownloadProgressAction(ArtifactRevisionAction):
    artifact_revision_id: uuid.UUID

    @override
    def entity_id(self) -> Optional[str]:
        return str(self.artifact_revision_id)

    @override
    @classmethod
    def operation_type(cls) -> str:
        return "get_download_progress"


@dataclass
class GetDownloadProgressActionResult(BaseActionResult):
    download_progress: CombinedDownloadProgress

    @override
    def entity_id(self) -> Optional[str]:
        return None
