from __future__ import annotations

import uuid
from dataclasses import dataclass
from typing import override

from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.actions.types import ActionOperationType

from .base import DotfileAction


@dataclass
class CheckGroupMembershipAction(DotfileAction):
    """Action to get the list of group IDs a user belongs to."""

    user_uuid: uuid.UUID

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.GET

    @override
    def entity_id(self) -> str | None:
        return str(self.user_uuid)


@dataclass
class CheckGroupMembershipActionResult(BaseActionResult):
    """Result of checking group membership."""

    group_ids: list[uuid.UUID]

    @override
    def entity_id(self) -> str | None:
        return None
