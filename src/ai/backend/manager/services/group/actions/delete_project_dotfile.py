from dataclasses import dataclass
from typing import override

from ai.backend.common.data.entity.project import ProjectID
from ai.backend.common.data.entity.types import EntityIdentifier
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.actions.v2.single_entity.base import BaseSingleEntityAction
from ai.backend.manager.data.dotfile.types import DotfileEntry


@dataclass(frozen=True)
class DeleteProjectDotfileAction(BaseSingleEntityAction):
    """Drop one of a project's dotfiles.

    A dotfile is a column of the project row, so the operation is an update of the
    project and is answered for by it.
    """

    project_id: ProjectID
    path: str

    @override
    def entity_id(self) -> EntityIdentifier:
        return self.project_id

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.UPDATE

    @override
    @classmethod
    def action_name(cls) -> str:
        return "delete_project_dotfile"


@dataclass(frozen=True)
class DeleteProjectDotfileActionResult:
    entries: tuple[DotfileEntry, ...]
