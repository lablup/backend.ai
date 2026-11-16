from collections.abc import Sequence
from dataclasses import dataclass
from typing import override

from ai.backend.common.data.entity.container_registry import ContainerRegistryID
from ai.backend.common.data.entity.project import ProjectID
from ai.backend.common.data.entity.types import EntityIdentifier
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.actions.v2.relation.base import BaseRelationAction


@dataclass(frozen=True)
class SwitchProjectDefaultRegistryAction(BaseRelationAction):
    """Make ``registry_id``, which the project must already be allowed on, the project's
    default registry."""

    project_id: ProjectID
    registry_id: ContainerRegistryID

    @override
    @classmethod
    def action_name(cls) -> str:
        return "switch_project_default_registry"

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.UPDATE

    @override
    def scope_targets(self) -> Sequence[EntityIdentifier]:
        return [self.project_id, self.registry_id]


@dataclass(frozen=True)
class SwitchProjectDefaultRegistryActionResult:
    registry_id: ContainerRegistryID
