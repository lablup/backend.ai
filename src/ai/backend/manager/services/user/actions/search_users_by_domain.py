from __future__ import annotations

from dataclasses import dataclass
from typing import override

from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.data.user.types import UserData
from ai.backend.manager.repositories.base.querier import BatchQuerier
from ai.backend.manager.repositories.user.types import DomainUserSearchScope
from ai.backend.manager.services.user.actions.base import UserAction


@dataclass
class SearchUsersByDomainAction(UserAction):
    """Action for searching users within a domain."""

    scope: DomainUserSearchScope
    querier: BatchQuerier

    @override
    def entity_id(self) -> str | None:
        return None

    @override
    @classmethod
    def operation_type(cls) -> str:
        return "search"


@dataclass
class SearchUsersByDomainActionResult(BaseActionResult):
    """Result of searching users within a domain."""

    users: list[UserData]
    total_count: int
    has_next_page: bool
    has_previous_page: bool

    @override
    def entity_id(self) -> str | None:
        return None
