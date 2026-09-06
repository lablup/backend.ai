"""The invitee's two answers, and the offering side's withdrawal."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import override

from ai.backend.common.data.entity.entity_invitation import (
    ENTITY_INVITATION_ENTITY_TYPE,
    EntityInvitationID,
)
from ai.backend.common.data.entity.types import EntityIdentifier, EntityType, ScopeRef
from ai.backend.common.data.entity.user import USER_SCOPE_TYPE, UserID
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.actions.v2.scope.base import BaseScopeAction
from ai.backend.manager.actions.v2.scope.result import BaseScopeActionResult
from ai.backend.manager.actions.v2.single_entity.base import BaseSingleEntityAction
from ai.backend.manager.data.entity_invitation.types import EntityInvitationData

__all__ = (
    "AcceptEntityInvitationAction",
    "CancelEntityInvitationAction",
    "CancelEntityInvitationActionResult",
    "EntityInvitationAnswerResult",
    "RejectEntityInvitationAction",
)


@dataclass
class _InviteeAnswerAction(BaseScopeAction):
    """Base for an answer the invitee gives.

    Scoped to the answering person rather than to the invitation: they were reached by
    email and hold no permission on it, so what is checked is that they may answer
    invitations of their own at all. Which invitation is theirs is decided by the
    write, whose guard matches their address.
    """

    invitation_id: EntityInvitationID
    invitee_user_id: UserID

    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return ENTITY_INVITATION_ENTITY_TYPE

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.UPDATE

    @override
    def scope_targets(self) -> Sequence[ScopeRef]:
        return (ScopeRef(scope_type=USER_SCOPE_TYPE, scope_id=self.invitee_user_id),)


@dataclass
class AcceptEntityInvitationAction(_InviteeAnswerAction):
    @override
    @classmethod
    def action_name(cls) -> str:
        return "accept_entity_invitation"


@dataclass
class RejectEntityInvitationAction(_InviteeAnswerAction):
    @override
    @classmethod
    def action_name(cls) -> str:
        return "reject_entity_invitation"


@dataclass
class EntityInvitationAnswerResult(BaseScopeActionResult):
    """What the answer settled.

    The run was requested within the answering person's scope while what it touched is
    the invitation, so that is what the audit trail is keyed on.
    """

    data: EntityInvitationData

    @override
    def entity_ids(self) -> Sequence[EntityIdentifier]:
        return (self.data.id,)


@dataclass
class CancelEntityInvitationAction(BaseSingleEntityAction):
    """Withdraw an offer before it was answered.

    Named on the invitation itself: whoever may reach the entity it offers may reach
    the invitation, so there is a permission to check here.
    """

    invitation_id: EntityInvitationID

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.DELETE

    @override
    @classmethod
    def action_name(cls) -> str:
        return "cancel_entity_invitation"

    @override
    def entity_id(self) -> EntityInvitationID:
        return self.invitation_id


@dataclass
class CancelEntityInvitationActionResult:
    """The withdrawn invitation. The shape already names it, so nothing is restated."""

    data: EntityInvitationData
