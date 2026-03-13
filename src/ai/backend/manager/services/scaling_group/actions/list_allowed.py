from __future__ import annotations

from dataclasses import dataclass
from typing import override

from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.actions.types import ActionOperationType

from .base import ScalingGroupAction


@dataclass
class ListAllowedScalingGroupsAction(ScalingGroupAction):
    """Action to list scaling groups allowed for a user."""

    domain_name: str
    group: str
    access_key: str
    is_admin: bool

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.SEARCH

    @override
    def entity_id(self) -> str | None:
        return None


@dataclass
class ListAllowedScalingGroupsActionResult(BaseActionResult):
    """Result of listing allowed scaling groups."""

    scaling_group_names: list[str]

    @override
    def entity_id(self) -> str | None:
        return None
