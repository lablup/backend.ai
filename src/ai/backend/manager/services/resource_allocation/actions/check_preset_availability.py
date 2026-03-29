from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any, override
from uuid import UUID

from ai.backend.common.types import AccessKey
from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.data.resource_allocation.types import PresetAvailabilityData
from ai.backend.manager.services.resource_allocation.actions.base import (
    ResourceAllocationAction,
)


@dataclass
class CheckPresetAvailabilityAction(ResourceAllocationAction):
    access_key: AccessKey
    user_id: UUID
    project_id: UUID
    domain_name: str
    resource_policy: Mapping[str, Any]
    rg_name: str
    group_resource_visibility: bool
    hide_agents: bool
    is_admin: bool
    scaling_group: str | None

    @override
    def entity_id(self) -> str | None:
        return None

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.SEARCH


@dataclass
class CheckPresetAvailabilityActionResult(BaseActionResult):
    presets: list[PresetAvailabilityData]

    @override
    def entity_id(self) -> str | None:
        return None
