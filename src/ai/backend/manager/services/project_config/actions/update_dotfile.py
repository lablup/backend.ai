from __future__ import annotations

import uuid
from dataclasses import dataclass
from typing import Optional, override

from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.services.project_config.actions.base import ProjectConfigAction


@dataclass
class UpdateDotfileAction(ProjectConfigAction):
    path: str
    data: str
    permission: str

    @override
    def entity_id(self) -> Optional[str]:
        return str(self.project_id_or_name)

    @override
    @classmethod
    def operation_type(cls) -> str:
        return "update_dotfile"


@dataclass
class UpdateDotfileActionResult(BaseActionResult):
    project_id: uuid.UUID

    @override
    def entity_id(self) -> Optional[str]:
        return str(self.project_id)
