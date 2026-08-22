from __future__ import annotations

from dataclasses import dataclass
from typing import override

from ai.backend.manager.actions.types import ActionOperationType

from .base import ResourceGroupGlobalAction


@dataclass(frozen=True)
class GetWsproxyVersionAction(ResourceGroupGlobalAction):
    """Action to get wsproxy version for a resource group."""

    resource_group_name: str
    domain_name: str
    group: str
    access_key: str

    @override
    @classmethod
    def action_name(cls) -> str:
        return "global_get_wsproxy_version"

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.GET


@dataclass(frozen=True)
class GetWsproxyVersionActionResult:
    """Result of getting wsproxy version."""

    wsproxy_version: str
