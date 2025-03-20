from dataclasses import dataclass
from typing import override

from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.services.domain.base import DomainAction


@dataclass
class PurgeDomainAction(DomainAction):
    _name: str

    def __init__(self, name: str) -> None:
        self._name = name

    def entity_id(self):
        return self._name

    def operation_type(self):
        return "purge"

    @property
    def name(self):
        return self._name


@dataclass
class PurgeDomainActionResult(BaseActionResult):
    _status: str
    _description: str

    def __init__(self, status: str, description: str) -> None:
        self._status = status
        self._description = description

    @override
    def entity_id(self):
        return ""

    @override
    def status(self):
        return self._status

    @override
    def description(self):
        return self._description

    @property
    def ok(self):
        return self._status == "success"
