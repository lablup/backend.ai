from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

__all__ = (
    "LoginClientTypeData",
    "LoginClientTypeSearchResult",
)


@dataclass(frozen=True)
class LoginClientTypeData:
    id: UUID
    name: str
    description: str | None
    created_at: datetime
    modified_at: datetime


@dataclass(frozen=True)
class LoginClientTypeSearchResult:
    items: list[LoginClientTypeData]
    total_count: int
    has_next_page: bool
    has_previous_page: bool
