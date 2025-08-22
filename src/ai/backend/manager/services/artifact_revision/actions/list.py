from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, override

from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.data.artifact.types import ArtifactRevisionData
from ai.backend.manager.repositories.artifact.types import (
    ArtifactRevisionFilterOptions,
    ArtifactRevisionOrderingOptions,
)
from ai.backend.manager.repositories.types import PaginationOptions
from ai.backend.manager.services.artifact_revision.actions.base import ArtifactRevisionAction


@dataclass
class ListArtifactRevisionsAction(ArtifactRevisionAction):
    pagination: PaginationOptions
    ordering: Optional[ArtifactRevisionOrderingOptions] = None
    filters: Optional[ArtifactRevisionFilterOptions] = None

    @override
    def entity_id(self) -> Optional[str]:
        return None

    @override
    @classmethod
    def operation_type(cls) -> str:
        return "list_revisions"


@dataclass
class ListArtifactRevisionsActionResult(BaseActionResult):
    data: list[ArtifactRevisionData]
    # Note: Total number of artifact revisions, this is not equals to len(data)
    total_count: int

    @override
    def entity_id(self) -> Optional[str]:
        return None
