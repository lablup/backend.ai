from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import override

from ai.backend.common.data.entity.domain import DomainID
from ai.backend.common.data.entity.project import ProjectID
from ai.backend.common.data.entity.user import UserID
from ai.backend.manager.actions.types import ActionOperationType

from .base import ResourceGroupGlobalAction


@dataclass(frozen=True)
class GetWsproxyVersionAction(ResourceGroupGlobalAction):
    """Action to get wsproxy version for a resource group."""

    resource_group_name: str
    domain_id: DomainID
    project_ids: Sequence[ProjectID]
    user_id: UserID

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
