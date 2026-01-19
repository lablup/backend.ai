from __future__ import annotations

from dataclasses import dataclass
from typing import override
from uuid import UUID

from ai.backend.common.data.user.types import UserData
from ai.backend.common.resource.types import TotalResourceData
from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.services.agent.actions.base import AgentAction


@dataclass
class GetScalingGroupResourcesAction(AgentAction):
    """Action to get aggregated resource stats for a specific scaling group."""

    user_data: UserData
    scaling_group_name: str
    project_id: UUID
    domain_name: str

    @override
    def entity_id(self) -> str | None:
        return self.scaling_group_name

    @override
    @classmethod
    def operation_type(cls) -> str:
        return "get_scaling_group_resources"


@dataclass
class GetScalingGroupResourcesActionResult(BaseActionResult):
    """Result containing aggregated resource data for a scaling group."""

    total_resources: TotalResourceData

    @override
    def entity_id(self) -> str | None:
        return None
