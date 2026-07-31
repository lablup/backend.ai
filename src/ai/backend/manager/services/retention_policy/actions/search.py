from __future__ import annotations

from dataclasses import dataclass
from typing import override

from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.data.retention.types import RetentionPolicyData
from ai.backend.manager.repositories.base import BatchQuerier
from ai.backend.manager.services.retention_policy.actions.base import RetentionPolicyAction


@dataclass
class SearchRetentionPoliciesAction(RetentionPolicyAction):
    querier: BatchQuerier

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.SEARCH

    @override
    def entity_id(self) -> str | None:
        return None


@dataclass
class SearchRetentionPoliciesActionResult(BaseActionResult):
    items: list[RetentionPolicyData]
    total_count: int
    has_next_page: bool
    has_previous_page: bool

    @override
    def entity_id(self) -> str | None:
        return None
