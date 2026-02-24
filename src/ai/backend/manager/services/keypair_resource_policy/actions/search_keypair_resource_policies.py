from dataclasses import dataclass
from typing import override

from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.data.resource.types import KeyPairResourcePolicyData
from ai.backend.manager.repositories.base.querier import BatchQuerier
from ai.backend.manager.services.keypair_resource_policy.actions.base import (
    KeypairResourcePolicyAction,
)


@dataclass
class SearchKeyPairResourcePoliciesAction(KeypairResourcePolicyAction):
    querier: BatchQuerier

    @override
    def entity_id(self) -> str | None:
        return None

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.SEARCH


@dataclass
class SearchKeyPairResourcePoliciesActionResult(BaseActionResult):
    items: list[KeyPairResourcePolicyData]
    total_count: int
    has_next_page: bool
    has_previous_page: bool

    @override
    def entity_id(self) -> str | None:
        return None
