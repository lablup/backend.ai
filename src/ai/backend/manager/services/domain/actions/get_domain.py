"""Get domain action and result types."""

from __future__ import annotations

from dataclasses import dataclass
from typing import override

from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.data.domain.types import DomainData
from ai.backend.manager.services.domain.actions.base import DomainAction


@dataclass
class GetDomainAction(DomainAction):
    """Action to get a single domain by name.

    Args:
        domain_name: Name of the domain to retrieve.

    Raises:
        DomainNotFound: If domain does not exist.
    """

    domain_name: str

    @override
    def entity_id(self) -> str | None:
        return self.domain_name

    @override
    @classmethod
    def operation_type(cls) -> str:
        return "get"


@dataclass
class GetDomainActionResult(BaseActionResult):
    """Result of GetDomainAction.

    Args:
        data: Domain data retrieved from repository.
    """

    data: DomainData

    @override
    def entity_id(self) -> str | None:
        return self.data.name
