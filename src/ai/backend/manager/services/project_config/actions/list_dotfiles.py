from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, override

from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.models.group import GroupDotfile
from ai.backend.manager.services.project_config.actions.base import ProjectConfigAction


@dataclass
class ListDotfilesAction(ProjectConfigAction):
    @override
    def entity_id(self) -> Optional[str]:
        return str(self.project_id_or_name)

    @override
    @classmethod
    def operation_type(cls) -> str:
        return "list_dotfiles"


@dataclass
class ListDotfilesActionResult(BaseActionResult):
    dotfiles: list[GroupDotfile]

    @override
    def entity_id(self) -> Optional[str]:
        return None
