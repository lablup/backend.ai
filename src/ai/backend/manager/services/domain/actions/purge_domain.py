from dataclasses import dataclass

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
