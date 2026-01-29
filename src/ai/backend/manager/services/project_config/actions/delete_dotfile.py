from __future__ import annotations

from dataclasses import dataclass
from typing import override

from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.services.project_config.actions.base import ProjectConfigAction


@dataclass
class DeleteDotfileAction(ProjectConfigAction):
    path: str

    @override
    def entity_id(self) -> str | None:
        return str(self.project_id_or_name)

    @override
    @classmethod
    def operation_type(cls) -> str:
        return "delete_dotfile"


@dataclass
class DeleteDotfileActionResult(BaseActionResult):
    success: bool

    @override
    def entity_id(self) -> str | None:
        return None
