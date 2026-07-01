from dataclasses import dataclass
from typing import override

from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.data.login_client_type.types import LoginClientTypeData
from ai.backend.manager.repositories.base import BatchQuerier
from ai.backend.manager.services.login_client_type.actions.base import LoginClientTypeAction


@dataclass
class SearchLoginClientTypesAction(LoginClientTypeAction):
    """Search login client types with filtering, ordering, and pagination."""

    querier: BatchQuerier

    @override
    def entity_id(self) -> str | None:
        return None

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.SEARCH


@dataclass
class SearchLoginClientTypesActionResult(BaseActionResult):
    items: list[LoginClientTypeData]
    total_count: int
    has_next_page: bool
    has_previous_page: bool

    @override
    def entity_id(self) -> str | None:
        return None
