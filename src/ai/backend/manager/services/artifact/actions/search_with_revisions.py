from __future__ import annotations

from dataclasses import dataclass
from typing import override

from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.data.artifact.types import ArtifactDataWithRevisions
from ai.backend.manager.repositories.base import BatchQuerier

from .base import ArtifactAction


@dataclass
class SearchArtifactsWithRevisionsAction(ArtifactAction):
    """Action to search artifacts with their revisions."""

    querier: BatchQuerier

    @override
    @classmethod
    def action_name(cls) -> str:
        return "search_artifacts_with_revisions"

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.SEARCH


@dataclass
class SearchArtifactsWithRevisionsActionResult:
    """Result of searching artifacts with revisions."""

    data: list[ArtifactDataWithRevisions]
    total_count: int
    has_next_page: bool
    has_previous_page: bool
