"""Actions for searching projects."""

from __future__ import annotations

from dataclasses import dataclass
from typing import override
from uuid import UUID

from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.data.group.types import GroupData
from ai.backend.manager.repositories.base.querier import BatchQuerier
from ai.backend.manager.repositories.group.types import (
    DomainProjectSearchScope,
    UserProjectSearchScope,
)
from ai.backend.manager.services.group.actions.base import GroupAction


@dataclass
class SearchProjectsAction(GroupAction):
    """Search all projects (admin scope - no scope filter)."""

    querier: BatchQuerier

    @override
    def entity_id(self) -> str | None:
        return None

    @override
    @classmethod
    def operation_type(cls) -> str:
        return "search"


@dataclass
class SearchProjectsByDomainAction(GroupAction):
    """Search projects within a domain."""

    scope: DomainProjectSearchScope
    querier: BatchQuerier

    @override
    def entity_id(self) -> str | None:
        return None

    @override
    @classmethod
    def operation_type(cls) -> str:
        return "search"


@dataclass
class SearchProjectsByUserAction(GroupAction):
    """Search projects a user is member of."""

    scope: UserProjectSearchScope
    querier: BatchQuerier

    @override
    def entity_id(self) -> str | None:
        return None

    @override
    @classmethod
    def operation_type(cls) -> str:
        return "search"


@dataclass
class GetProjectAction(GroupAction):
    """Get a single project by UUID."""

    project_id: UUID

    @override
    def entity_id(self) -> str | None:
        return str(self.project_id)

    @override
    @classmethod
    def operation_type(cls) -> str:
        return "get"


# Result types


@dataclass
class SearchProjectsActionResult(BaseActionResult):
    """Result from searching projects."""

    items: list[GroupData]
    total_count: int
    has_next_page: bool
    has_previous_page: bool

    @override
    def entity_id(self) -> str | None:
        return None


@dataclass
class GetProjectActionResult(BaseActionResult):
    """Result from getting a single project."""

    data: GroupData

    @override
    def entity_id(self) -> str | None:
        return str(self.data.id)
