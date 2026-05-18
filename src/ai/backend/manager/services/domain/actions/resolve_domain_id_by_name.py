from __future__ import annotations

from dataclasses import dataclass
from typing import override

from ai.backend.common.identifier.domain import DomainID, DomainName
from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.services.domain.actions.base import DomainAction


@dataclass
class ResolveDomainIDByNameAction(DomainAction):
    name: DomainName

    @override
    def entity_id(self) -> str | None:
        return str(self.name)

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.GET


@dataclass
class ResolveDomainIDByNameActionResult(BaseActionResult):
    domain_id: DomainID

    @override
    def entity_id(self) -> str | None:
        return str(self.domain_id)
