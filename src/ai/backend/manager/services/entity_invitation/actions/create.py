"""Offer one existing entity to one email address."""

from __future__ import annotations

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
from ai.backend.common.data.entity.user import UserID
from ai.backend.common.data.permission.types import Permission
from ai.backend.manager.actions.v2.ops.base import CreateEntityOpsAction
from ai.backend.manager.data.entity_invitation.types import EntityInvitationData
from ai.backend.manager.models.entity_invitation.creators import EntityInvitationCreator
from ai.backend.manager.models.entity_invitation.row import EntityInvitationRow

__all__ = ("CreateEntityInvitationAction",)


@dataclass
class CreateEntityInvitationAction(
    CreateEntityOpsAction[EntityInvitationRow, EntityInvitationData]
):
    """Offer an entity, answered for by that entity.

    The scope is what is being offered rather than who it goes to: the invitee is an
    email that may belong to nobody yet, while the entity is what the caller has to be
    allowed to hand out.
    """

    inviter_user_id: UserID
    invitee_email: str
    target: EntityIdentifier
    permission_cap: Permission | None

    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return ENTITY_INVITATION_ENTITY_TYPE

    @override
    @classmethod
    def action_name(cls) -> str:
        return "create_entity_invitation"

    @override
    def scope_targets(self) -> Sequence[ScopeRef]:
        return (ScopeRef(scope_type=ScopeType(self.target.entity_type()), scope_id=self.target),)

    @override
    def to_creator(self) -> EntityInvitationCreator:
        return EntityInvitationCreator(
            inviter_user_id=self.inviter_user_id,
            invitee_email=self.invitee_email,
            target=self.target,
            permission_cap=self.permission_cap,
        )
