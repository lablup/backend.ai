from dataclasses import dataclass
from typing import override

from ai.backend.common.data.entity.domain import DomainID
from ai.backend.common.data.entity.types import EntityIdentifier
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.actions.v2.single_entity.base import BaseSingleEntityAction
from ai.backend.manager.data.dotfile.types import DotfileEntry


@dataclass(frozen=True)
class CreateDomainDotfileAction(BaseSingleEntityAction):
    """Add one dotfile to a domain.

    A dotfile is a column of the domain row, so the operation is an update of the
    domain and is answered for by it.
    """

    domain_id: DomainID
    name: str
    entry: DotfileEntry

    @override
    def entity_id(self) -> EntityIdentifier:
        return self.domain_id

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.UPDATE

    @override
    @classmethod
    def action_name(cls) -> str:
        return "create_domain_dotfile"


@dataclass(frozen=True)
class CreateDomainDotfileActionResult:
    entries: tuple[DotfileEntry, ...]
