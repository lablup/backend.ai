from __future__ import annotations

import uuid
from dataclasses import dataclass
from typing import Optional, override

from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.services.group_config.actions.base import GroupConfigAction


@dataclass
class DeleteDotfileAction(GroupConfigAction):
    group_id: uuid.UUID
    path: str

    @override
    def entity_id(self) -> Optional[str]:
        return str(self.group_id)

    @override
    @classmethod
    def operation_type(cls) -> str:
        return "delete_dotfile"


@dataclass
class DeleteDotfileActionResult(BaseActionResult):
    success: bool

    @override
    def entity_id(self) -> Optional[str]:
        return None
