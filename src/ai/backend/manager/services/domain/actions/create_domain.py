from dataclasses import dataclass
from typing import override

from ai.backend.common.data.entity.domain import DOMAIN_ENTITY_TYPE
from ai.backend.common.data.entity.types import EntityType
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.actions.v2.global_scope.base import BaseGlobalAction
from ai.backend.manager.data.domain.types import DomainData, UserInfo
from ai.backend.manager.models.domain.creators import DomainCreator


@dataclass(frozen=True)
class CreateDomainAction(BaseGlobalAction):
    """Register a domain. The model-store project is created along with it, which is
    why this does not run straight against ops."""

    creator: DomainCreator
    user_info: UserInfo

    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return DOMAIN_ENTITY_TYPE

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.CREATE

    @override
    @classmethod
    def action_name(cls) -> str:
        return "global_create_domain"


@dataclass(frozen=True)
class CreateDomainActionResult:
    domain_data: DomainData
