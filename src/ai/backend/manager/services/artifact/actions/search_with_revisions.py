from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, override

from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.data.artifact.types import ArtifactDataWithRevisions
from ai.backend.manager.repositories.base import BatchQuerier

from .base import ArtifactAction


@dataclass
class SearchArtifactsWithRevisionsAction(ArtifactAction):
    """Action to search artifacts with their revisions."""

    querier: BatchQuerier

    @override
    @classmethod
    def operation_type(cls) -> str:
        return "search_with_revisions"

    @override
    def entity_id(self) -> Optional[str]:
        return None


@dataclass
class SearchArtifactsWithRevisionsActionResult(BaseActionResult):
    """Result of searching artifacts with revisions."""

    data: list[ArtifactDataWithRevisions]
    total_count: int
    has_next_page: bool
    has_previous_page: bool

    @override
    def entity_id(self) -> Optional[str]:
        return None
