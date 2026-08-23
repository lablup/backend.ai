"""Types for group repository operations."""

from __future__ import annotations

from dataclasses import dataclass

from ai.backend.manager.data.project.types import ProjectData

__all__ = ("ProjectSearchResult",)


@dataclass
class ProjectSearchResult:
    """Result from searching groups/projects."""

    items: list[ProjectData]
    total_count: int
    has_next_page: bool
    has_previous_page: bool
