from __future__ import annotations

from dataclasses import dataclass
from typing import override

from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.actions.types import ActionOperationType

from .base import ScalingGroupAction


@dataclass
class GetWsproxyVersionAction(ScalingGroupAction):
    """Action to get wsproxy version for a scaling group."""

    scaling_group_name: str
    domain_name: str
    group: str
    access_key: str

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.GET

    @override
    def entity_id(self) -> str | None:
        return self.scaling_group_name


@dataclass
class GetWsproxyVersionActionResult(BaseActionResult):
    """Result of getting wsproxy version."""

    wsproxy_version: str

    @override
    def entity_id(self) -> str | None:
        return None
