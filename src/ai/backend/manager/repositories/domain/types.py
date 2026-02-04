"""Types for domain repository operations."""

from __future__ import annotations

from dataclasses import dataclass

from ai.backend.manager.data.domain.types import DomainData

__all__ = ("DomainSearchResult",)


@dataclass
class DomainSearchResult:
    """Result from searching domains."""

    items: list[DomainData]
    total_count: int
    has_next_page: bool
    has_previous_page: bool
