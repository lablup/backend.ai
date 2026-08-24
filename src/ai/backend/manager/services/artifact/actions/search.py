from __future__ import annotations

from dataclasses import dataclass
from typing import override

from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.data.artifact.types import ArtifactData
from ai.backend.manager.models.artifact.searchers import ArtifactSearcher
from ai.backend.manager.services.artifact.actions.base import ArtifactAction


@dataclass
class SearchArtifactsAction(ArtifactAction):
    searcher: ArtifactSearcher

    @override
    @classmethod
    def action_name(cls) -> str:
        return "search_artifacts"

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.SEARCH


@dataclass
class SearchArtifactsActionResult:
    data: list[ArtifactData]
    total_count: int
    has_next_page: bool
    has_previous_page: bool
