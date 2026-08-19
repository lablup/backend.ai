from __future__ import annotations

from dataclasses import dataclass
from typing import override

from ai.backend.common.data.entity.project import ProjectID
from ai.backend.common.data.entity.types import EntityIdentifier
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.actions.v2.single_entity.base import BaseSingleEntityAction
from ai.backend.manager.data.resource_slot.types import ResourceOccupancy


@dataclass(frozen=True)
class GetProjectResourceOverviewAction(BaseSingleEntityAction):
    """Read what a project currently occupies, summed across its sessions."""

    project_id: ProjectID

    @override
    def entity_id(self) -> EntityIdentifier:
        return self.project_id

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.GET

    @override
    @classmethod
    def action_name(cls) -> str:
        return "get_project_resource_overview"


@dataclass(frozen=True)
class GetProjectResourceOverviewResult:
    item: ResourceOccupancy
