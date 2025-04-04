from dataclasses import dataclass
from typing import Optional, override

from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.services.domain.actions.base import DomainAction


@dataclass
class PurgeDomainAction(DomainAction):
    name: str

    @override
    def entity_id(self) -> Optional[str]:
        return None

    @override
    def operation_type(self) -> str:
        return "purge"


@dataclass
class PurgeDomainActionResult(BaseActionResult):
    success: bool
    description: str

    @override
    def entity_id(self) -> Optional[str]:
        return None
