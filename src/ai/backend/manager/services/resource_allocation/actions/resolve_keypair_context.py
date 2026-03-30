"""Action for resolving keypair context (access_key + resource_policy) from user_id."""

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any, override
from uuid import UUID

from ai.backend.common.types import AccessKey
from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.services.resource_allocation.actions.base import (
    ResourceAllocationAction,
)


@dataclass
class ResolveKeypairContextAction(ResourceAllocationAction):
    user_id: UUID

    @override
    def entity_id(self) -> str | None:
        return str(self.user_id)

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.GET


@dataclass
class ResolveKeypairContextActionResult(BaseActionResult):
    access_key: AccessKey
    resource_policy: Mapping[str, Any]

    @override
    def entity_id(self) -> str | None:
        return str(self.access_key)
