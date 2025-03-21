from dataclasses import dataclass
from typing import override

from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.services.domain.base import DomainAction


@dataclass
class PurgeDomainAction(DomainAction):
    name: str

    @override
    def entity_id(self):
        return self._name

    @override
    def operation_type(self):
        return "purge"


@dataclass
class PurgeDomainActionResult(BaseActionResult):
    status: str
    description: str

    @override
    def entity_id(self):
        return ""

    @property
    def ok(self):
        return self.status == "success"
