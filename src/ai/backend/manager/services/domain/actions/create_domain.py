from dataclasses import dataclass
from typing import override

from ai.backend.common.data.entity.domain import DOMAIN_ENTITY_TYPE
from ai.backend.common.data.entity.types import EntityType
from ai.backend.manager.actions.v2.ops.base import CreateGlobalRoleManagedEntityOpsAction
from ai.backend.manager.data.domain.types import DomainData
from ai.backend.manager.models.domain.creators import DomainCreator
from ai.backend.manager.models.domain.row import DomainRow


@dataclass(frozen=True)
class CreateDomainAction(CreateGlobalRoleManagedEntityOpsAction[DomainRow, DomainData]):
    """Register a domain, the top-level scope everything else is created under."""

    creator: DomainCreator

    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return DOMAIN_ENTITY_TYPE

    @override
    @classmethod
    def action_name(cls) -> str:
        return "global_create_domain"

    @override
    def to_creator(self) -> DomainCreator:
        return self.creator
