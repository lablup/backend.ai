from dataclasses import dataclass
from typing import override

from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.services.domain.base import DomainAction


@dataclass
class DeleteDomainAction(DomainAction):
    _name: str

    def __init__(self, name: str) -> None:
        self._name = name

    @override
    def entity_id(self) -> str:
        return self._name

    @override
    def operation_type(self) -> str:
        return "delete"

    @property
    def name(self) -> str:
        return self._name


@dataclass
class DeleteDomainActionResult(BaseActionResult):
    _status: str
    _description: str

    def __init__(self, status: str, description: str) -> None:
        self._status = status
        self._description = description

    @override
    def entity_id(self) -> str:
        return ""

    @override
    def status(self) -> str:
        return self._status

    @override
    def description(self) -> str:
        return self._description

    @property
    def ok(self) -> bool:
        return self._status == "success"
