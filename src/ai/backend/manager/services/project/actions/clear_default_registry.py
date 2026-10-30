from collections.abc import Sequence
from dataclasses import dataclass
from typing import override

from ai.backend.common.data.entity.project import ProjectID
from ai.backend.common.data.entity.types import EntityIdentifier
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.actions.v2.relation.base import BaseRelationAction


@dataclass(frozen=True)
class ClearProjectDefaultRegistryAction(BaseRelationAction):
    """Clear a project's default registry. The project stays allowed on it."""

    project_id: ProjectID

    @override
    @classmethod
    def action_name(cls) -> str:
        return "clear_project_default_registry"

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.UPDATE

    @override
    def scope_targets(self) -> Sequence[EntityIdentifier]:
        return [self.project_id]


@dataclass(frozen=True)
class ClearProjectDefaultRegistryActionResult:
    project_id: ProjectID
