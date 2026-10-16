from collections.abc import Sequence
from dataclasses import dataclass
from typing import override

from ai.backend.common.data.entity.container_registry import ContainerRegistryID
from ai.backend.common.data.entity.project import ProjectID
from ai.backend.common.data.entity.types import EntityIdentifier
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.actions.v2.relation.base import BaseRelationAction


@dataclass(frozen=True)
class SetProjectDefaultRegistryAction(BaseRelationAction):
    project_id: ProjectID
    previous_registry_id: ContainerRegistryID | None
    registry_id: ContainerRegistryID | None

    @override
    @classmethod
    def action_name(cls) -> str:
        return "set_project_default_registry"

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.UPDATE

    @override
    def scope_targets(self) -> Sequence[EntityIdentifier]:
        return list(
            dict.fromkeys(
                entity
                for entity in (self.project_id, self.previous_registry_id, self.registry_id)
                if entity is not None
            )
        )


@dataclass(frozen=True)
class SetProjectDefaultRegistryActionResult:
    registry_id: ContainerRegistryID | None
