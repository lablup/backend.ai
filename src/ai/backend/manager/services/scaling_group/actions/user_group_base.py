from dataclasses import dataclass
from typing import override

from ai.backend.common.data.entity.project import ProjectID
from ai.backend.common.data.entity.types import EntityIdentifier
from ai.backend.manager.actions.v2.single_entity.base import BaseSingleEntityAction


@dataclass(frozen=True)
class ScalingGroupUserGroupAction(BaseSingleEntityAction):
    """Base for an operation on the resource groups a project may schedule on."""

    project_id: ProjectID

    @override
    def entity_id(self) -> EntityIdentifier:
        return self.project_id
