from dataclasses import dataclass
from typing import override

from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.services.domain.actions.base import DomainAction


@dataclass
class DeleteDomainAction(DomainAction):
    name: str

    @override
    def entity_id(self) -> str:
        return self.name

    @override
    def operation_type(self) -> str:
        return "delete"


@dataclass
class DeleteDomainActionResult(BaseActionResult):
    status: str
    description: str

    def __init__(self, status: str, description: str) -> None:
        self.status = status
        self.description = description

    @override
    def entity_id(self) -> str:
        return ""

    @property
    def ok(self) -> bool:
        return self.status == "success"
