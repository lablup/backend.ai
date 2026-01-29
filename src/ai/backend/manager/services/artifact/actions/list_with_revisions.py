from __future__ import annotations

from dataclasses import dataclass
from typing import override

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
    """Action to list artifacts with revisions using old-style pagination (REST API)."""

    pagination: PaginationOptions | None = None
    ordering: ArtifactOrderingOptions | None = None
    filters: ArtifactFilterOptions | None = None

    @override
    def entity_id(self) -> str | None:
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
    def entity_id(self) -> str | None:
        return None
