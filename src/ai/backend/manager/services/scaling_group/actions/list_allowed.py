from __future__ import annotations

from dataclasses import dataclass
from typing import override

from ai.backend.manager.actions.types import ActionOperationType

from .base import ScalingGroupGlobalAction


@dataclass(frozen=True)
class ListAllowedScalingGroupsAction(ScalingGroupGlobalAction):
    """Action to list scaling groups allowed for a user."""

    domain_name: str
    group: str
    access_key: str
    is_admin: bool

    @override
    @classmethod
    def action_name(cls) -> str:
        return "global_list_allowed_resource_groups"

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.SEARCH


@dataclass(frozen=True)
class ListAllowedScalingGroupsActionResult:
    """Result of listing allowed scaling groups."""

    scaling_group_names: list[str]
