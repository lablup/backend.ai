"""Pagination specifications for artifact GraphQL queries."""

from __future__ import annotations

from functools import lru_cache

from ai.backend.manager.api.gql.adapter import PaginationSpec
from ai.backend.manager.models.artifact import ArtifactRow
from ai.backend.manager.models.artifact_revision import ArtifactRevisionRow

__all__ = (
    "get_artifact_pagination_spec",
    "get_artifact_revision_pagination_spec",
)


@lru_cache(maxsize=1)
def get_artifact_pagination_spec() -> PaginationSpec:
    """Get pagination spec for Artifact queries."""
    return PaginationSpec(
        forward_order=ArtifactRow.id.asc(),
        backward_order=ArtifactRow.id.desc(),
        forward_condition_factory=lambda cursor_value: lambda: ArtifactRow.id > cursor_value,
        backward_condition_factory=lambda cursor_value: lambda: ArtifactRow.id < cursor_value,
    )


@lru_cache(maxsize=1)
def get_artifact_revision_pagination_spec() -> PaginationSpec:
    """Get pagination spec for ArtifactRevision queries."""
    return PaginationSpec(
        forward_order=ArtifactRevisionRow.id.asc(),
        backward_order=ArtifactRevisionRow.id.desc(),
        forward_condition_factory=lambda cursor_value: lambda: ArtifactRevisionRow.id
        > cursor_value,
        backward_condition_factory=lambda cursor_value: lambda: ArtifactRevisionRow.id
        < cursor_value,
    )
