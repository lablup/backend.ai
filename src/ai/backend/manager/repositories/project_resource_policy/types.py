from __future__ import annotations

from dataclasses import dataclass

from ai.backend.manager.data.resource.types import ProjectResourcePolicyData

__all__ = ("ProjectResourcePolicySearchResult",)


@dataclass
class ProjectResourcePolicySearchResult:
    """Result from searching project resource policies."""

    items: list[ProjectResourcePolicyData]
    total_count: int
    has_next_page: bool
    has_previous_page: bool
