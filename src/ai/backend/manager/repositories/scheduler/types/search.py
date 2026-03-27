"""Search result types for scheduler repository."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from ai.backend.manager.sokovan.data import (
    ImageConfigData,
    SessionDataForPull,
    SessionDataForStart,
)

if TYPE_CHECKING:
    from ai.backend.manager.sokovan.scheduler.results import HandlerSessionData


@dataclass
class SessionSearchResult:
    """Result of searching sessions (basic session info only)."""

    items: list[HandlerSessionData]
    total_count: int
    has_next_page: bool = False
    has_previous_page: bool = False


@dataclass
class SessionWithKernelsSearchResult:
    """Result of searching sessions with kernel data and image configs."""

    sessions: list[SessionDataForPull]
    image_configs: dict[str, ImageConfigData] = field(default_factory=dict)
    total_count: int = 0
    has_next_page: bool = False
    has_previous_page: bool = False


@dataclass
class SessionWithKernelsAndUserSearchResult:
    """Result of searching sessions with kernel data, user info, and image configs."""

    sessions: list[SessionDataForStart]
    image_configs: dict[str, ImageConfigData] = field(default_factory=dict)
    total_count: int = 0
    has_next_page: bool = False
    has_previous_page: bool = False
