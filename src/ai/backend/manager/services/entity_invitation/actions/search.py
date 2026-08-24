"""Listing invitations, from whichever side the reader stands on."""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Sequence
from dataclasses import dataclass
from typing import override

from ai.backend.common.data.entity.entity_invitation import ENTITY_INVITATION_ENTITY_TYPE
from ai.backend.common.data.entity.types import (
    EntityIdentifier,
    EntityType,
    ScopeRef,
    ScopeType,
)
from ai.backend.common.data.entity.user import USER_SCOPE_TYPE, UserID
from ai.backend.manager.actions.v2.ops.base import OperationScopeOpsAction
from ai.backend.manager.data.entity_invitation.types import EntityInvitationData
from ai.backend.manager.models.entity_invitation.row import EntityInvitationRow
from ai.backend.manager.models.entity_invitation.scopes import (
    EntityInvitationInviteeScope,
    EntityInvitationInviterScope,
    EntityInvitationTargetScope,
)
from ai.backend.manager.models.entity_invitation.searchers import EntityInvitationSearcher
from ai.backend.manager.models.scopes import OperationScope

__all__ = (
    "EntityInvitationScopeItem",
    "ReceivedEntityInvitationScopeItem",
    "SearchEntityInvitationsAction",
    "SentEntityInvitationScopeItem",
    "TargetEntityInvitationScopeItem",
)


class EntityInvitationScopeItem(ABC):
    """One side invitations are read from.

    The scope the read is answered for and the rows it is restricted to are declared
    together, so a read cannot be authorized against one thing and served another.
    """

    @abstractmethod
    def scope_ref(self) -> ScopeRef:
        """The scope the read is answered for."""
        raise NotImplementedError

    @abstractmethod
    def operation_scope(self) -> OperationScope:
        """The rows the read is restricted to."""
        raise NotImplementedError


@dataclass(frozen=True)
class ReceivedEntityInvitationScopeItem(EntityInvitationScopeItem):
    """The invitations addressed to one person's own email."""

    user_id: UserID

    @override
    def scope_ref(self) -> ScopeRef:
        return ScopeRef(scope_type=USER_SCOPE_TYPE, scope_id=self.user_id)

    @override
    def operation_scope(self) -> OperationScope:
        return EntityInvitationInviteeScope(invitee_user_id=self.user_id)


@dataclass(frozen=True)
class SentEntityInvitationScopeItem(EntityInvitationScopeItem):
    """The invitations one person sent."""

    user_id: UserID

    @override
    def scope_ref(self) -> ScopeRef:
        return ScopeRef(scope_type=USER_SCOPE_TYPE, scope_id=self.user_id)

    @override
    def operation_scope(self) -> OperationScope:
        return EntityInvitationInviterScope(inviter_user_id=self.user_id)


@dataclass(frozen=True)
class TargetEntityInvitationScopeItem(EntityInvitationScopeItem):
    """The invitations offering one entity."""

    target: EntityIdentifier

    @override
    def scope_ref(self) -> ScopeRef:
        return ScopeRef(scope_type=ScopeType(self.target.entity_type()), scope_id=self.target)

    @override
    def operation_scope(self) -> OperationScope:
        return EntityInvitationTargetScope(target=self.target)


@dataclass
class SearchEntityInvitationsAction(
    OperationScopeOpsAction[EntityInvitationRow, EntityInvitationData]
):
    """Page through the invitations the named sides reach, combined with OR.

    Every side is authorized before the read runs, so a caller reaching for one they
    cannot see is refused rather than served the rest.
    """

    items: Sequence[EntityInvitationScopeItem]
    searcher: EntityInvitationSearcher

    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return ENTITY_INVITATION_ENTITY_TYPE

    @override
    @classmethod
    def action_name(cls) -> str:
        return "search_entity_invitations"

    @override
    def scope_targets(self) -> Sequence[ScopeRef]:
        return [item.scope_ref() for item in self.items]

    @override
    def operation_scopes(self) -> Sequence[OperationScope]:
        return [item.operation_scope() for item in self.items]

    @override
    def to_searcher(self) -> EntityInvitationSearcher:
        return self.searcher
