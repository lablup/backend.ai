from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, override

from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.data.artifact.types import ArtifactData
from ai.backend.manager.repositories.base import BatchQuerier
from ai.backend.manager.services.artifact.actions.base import ArtifactAction


@dataclass
class SearchArtifactsAction(ArtifactAction):
    querier: BatchQuerier

    @override
    def entity_id(self) -> Optional[str]:
        return None

    @override
    @classmethod
    def operation_type(cls) -> str:
        return "search"


@dataclass
class SearchArtifactsActionResult(BaseActionResult):
    data: list[ArtifactData]
    total_count: int
    has_next_page: bool
    has_previous_page: bool

    @override
    def entity_id(self) -> Optional[str]:
        return None
