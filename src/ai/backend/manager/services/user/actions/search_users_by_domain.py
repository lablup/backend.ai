from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import override

from ai.backend.common.data.entity.domain import DOMAIN_SCOPE_TYPE, DomainID
from ai.backend.common.data.entity.types import EntityType, ScopeRef
from ai.backend.common.data.entity.user import USER_ENTITY_TYPE
from ai.backend.manager.actions.v2.ops.base import OperationScopeOpsAction
from ai.backend.manager.data.user.types import UserData
from ai.backend.manager.models.scopes import OperationScope
from ai.backend.manager.models.user.row import UserRow
from ai.backend.manager.models.user.searchers import UserSearcher
from ai.backend.manager.repositories.user.types import DomainUserOperationScope

__all__ = ("SearchUsersByDomainAction",)


@dataclass(frozen=True)
class SearchUsersByDomainAction(OperationScopeOpsAction[UserRow, UserData]):
    """Page through the users of a domain."""

    domain_id: DomainID
    domain_name: str
    searcher: UserSearcher

    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return USER_ENTITY_TYPE

    @override
    def scope_targets(self) -> Sequence[ScopeRef]:
        return (ScopeRef(scope_type=DOMAIN_SCOPE_TYPE, scope_id=self.domain_id),)

    @override
    def operation_scopes(self) -> Sequence[OperationScope]:
        return (DomainUserOperationScope(domain_name=self.domain_name),)

    @override
    @classmethod
    def action_name(cls) -> str:
        return "search_users_by_domain"

    @override
    def to_searcher(self) -> UserSearcher:
        return self.searcher
