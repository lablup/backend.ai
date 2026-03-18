from __future__ import annotations

import uuid
from dataclasses import dataclass
from typing import override

from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.actions.types import ActionOperationType

from .base import DotfileAction


@dataclass
class ResolveGroupAction(DotfileAction):
    """Action to resolve a group identifier (name or UUID) to a (group_id, domain) pair."""

    group_id_or_name: str | uuid.UUID
    group_domain: str | None
    user_domain: str

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.GET

    @override
    def entity_id(self) -> str | None:
        return str(self.group_id_or_name)


@dataclass
class ResolveGroupActionResult(BaseActionResult):
    """Result of resolving a group identifier."""

    group_id: uuid.UUID
    domain: str

    @override
    def entity_id(self) -> str | None:
        return str(self.group_id)
