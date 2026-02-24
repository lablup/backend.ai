from __future__ import annotations

from dataclasses import dataclass

from ai.backend.manager.data.resource.types import UserResourcePolicyData

__all__ = ("UserResourcePolicySearchResult",)


@dataclass
class UserResourcePolicySearchResult:
    """Result from searching user resource policies."""

    items: list[UserResourcePolicyData]
    total_count: int
    has_next_page: bool
    has_previous_page: bool
