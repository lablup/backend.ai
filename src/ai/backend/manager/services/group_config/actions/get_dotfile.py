from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, override

from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.models.group import GroupDotfile
from ai.backend.manager.services.group_config.actions.base import GroupConfigAction


@dataclass
class GetDotfileAction(GroupConfigAction):
    path: str

    @override
    def entity_id(self) -> Optional[str]:
        return str(self.group_id_or_name)

    @override
    @classmethod
    def operation_type(cls) -> str:
        return "get_dotfile"


@dataclass
class GetDotfileActionResult(BaseActionResult):
    dotfile: GroupDotfile

    @override
    def entity_id(self) -> Optional[str]:
        return None
