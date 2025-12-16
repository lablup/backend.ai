from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, override

from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.data.artifact.types import ArtifactRevisionData
from ai.backend.manager.repositories.base import BatchQuerier
from ai.backend.manager.services.artifact_revision.actions.base import ArtifactRevisionAction


@dataclass
class SearchArtifactRevisionsAction(ArtifactRevisionAction):
    querier: BatchQuerier

    @override
    def entity_id(self) -> Optional[str]:
        return None

    @override
    @classmethod
    def operation_type(cls) -> str:
        return "search_revisions"


@dataclass
class SearchArtifactRevisionsActionResult(BaseActionResult):
    data: list[ArtifactRevisionData]
    total_count: int
    has_next_page: bool
    has_previous_page: bool

    @override
    def entity_id(self) -> Optional[str]:
        return None
