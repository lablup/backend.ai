from dataclasses import dataclass
from typing import override

from ai.backend.common.data.entity.domain import DomainID
from ai.backend.common.data.entity.types import EntityIdentifier
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.actions.v2.single_entity.base import BaseSingleEntityAction
from ai.backend.manager.data.domain.types import DomainData


@dataclass(frozen=True)
class PurgeDomainAction(BaseSingleEntityAction):
    """Remove one domain for good. The kernel rows it left are cleared in the same
    transaction, which is why this does not run straight against ops."""

    domain_id: DomainID
    name: str

    @override
    def entity_id(self) -> EntityIdentifier:
        return self.domain_id

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.PURGE

    @override
    @classmethod
    def action_name(cls) -> str:
        return "purge_domain"


@dataclass(frozen=True)
class PurgeDomainActionResult:
    domain_data: DomainData
