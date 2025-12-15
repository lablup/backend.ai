from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Optional, override

if TYPE_CHECKING:
    from ai.backend.manager.repositories.base import BatchQuerier

from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.data.artifact.types import (
    ArtifactDataWithRevisions,
    ArtifactFilterOptions,
    ArtifactOrderingOptions,
)
from ai.backend.manager.services.artifact.actions.base import ArtifactAction
from ai.backend.manager.types import PaginationOptions


@dataclass
class ListArtifactsWithRevisionsAction(ArtifactAction):
    # Support both new BatchQuerier pattern (for GraphQL) and old style (for REST API)
    querier: Optional[BatchQuerier] = None
    # Old-style parameters (deprecated, kept for REST API compatibility)
    pagination: Optional[PaginationOptions] = None
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
