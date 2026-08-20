from __future__ import annotations

from dataclasses import dataclass
from typing import override

from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.data.artifact.types import ArtifactRevisionData
from ai.backend.manager.repositories.base import BatchQuerier
from ai.backend.manager.services.artifact.revision.actions.base import ArtifactRevisionAction


@dataclass
class SearchArtifactRevisionsAction(ArtifactRevisionAction):
    querier: BatchQuerier

    @override
    @classmethod
    def action_name(cls) -> str:
        return "search_artifact_revisions"

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.SEARCH


@dataclass
class SearchArtifactRevisionsActionResult:
    data: list[ArtifactRevisionData]
    total_count: int
    has_next_page: bool
    has_previous_page: bool
