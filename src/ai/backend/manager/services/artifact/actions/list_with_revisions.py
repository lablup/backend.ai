from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, override

from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.data.artifact.types import ArtifactDataWithRevisions
from ai.backend.manager.repositories.artifact.repository import (
    ArtifactFilterOptions,
    ArtifactOrderingOptions,
    PaginationOptions,
)
from ai.backend.manager.services.artifact.actions.base import ArtifactAction


@dataclass
class ListArtifactsWithRevisionsAction(ArtifactAction):
    pagination: PaginationOptions
    ordering: Optional[ArtifactOrderingOptions] = None
    filters: Optional[ArtifactFilterOptions] = None

    @override
    def entity_id(self) -> Optional[str]:
        return None

    @override
    @classmethod
    def operation_type(cls) -> str:
        return "list_with_revisions"


@dataclass
class ListArtifactsWithRevisionsActionResult(BaseActionResult):
    data: list[ArtifactDataWithRevisions]
    # Note: Total number of artifacts, this is not equals to len(data)
    total_count: int

    @override
    def entity_id(self) -> Optional[str]:
        return None
