# As there is an ongoing migration of renaming group to project,
# there are some occurrences where "group" is being used as "project"
# (e.g., GroupDotfile).
# It will be fixed in the future; for now understand them as the same concept.
from __future__ import annotations

from dataclasses import dataclass
from typing import override

from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.models.group import GroupDotfile
from ai.backend.manager.services.project_config.actions.base import ProjectConfigAction


@dataclass
class GetDotfileAction(ProjectConfigAction):
    path: str

    @override
    def entity_id(self) -> str | None:
        return str(self.project_id_or_name)

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.GET


@dataclass
class GetDotfileActionResult(BaseActionResult):
    dotfile: GroupDotfile

    @override
    def entity_id(self) -> str | None:
        return None
