"""Insert spec for entity invitations."""

from __future__ import annotations

from collections.abc import Collection, Sequence
from dataclasses import dataclass
from typing import override

from ai.backend.common.data.entity.entity_invitation import EntityInvitationID
from ai.backend.common.data.entity.types import EntityIdentifier
from ai.backend.common.data.entity.user import UserID
from ai.backend.common.data.permission.types import Permission
from ai.backend.manager.data.entity_invitation.types import (
    EntityInvitationData,
    EntityInvitationStatus,
)
from ai.backend.manager.errors.entity_invitation import DuplicateEntityInvitationError
from ai.backend.manager.errors.repository import UniqueConstraintViolationError
from ai.backend.manager.models.entity_invitation.row import EntityInvitationRow
from ai.backend.manager.models.specs.creator import EntityCreator
from ai.backend.manager.models.specs.types import IntegrityErrorCheck


@dataclass
class EntityInvitationCreator(EntityCreator[EntityInvitationRow, EntityInvitationData]):
    """An offer of one existing entity to one email address.

    It joins the entity it offers: who may read and withdraw the invitation is
    answered by that entity, and the invitee reaches their own by email instead.
    """

    inviter_user_id: UserID
    invitee_email: str
    target: EntityIdentifier
    permission_cap: Permission | None = None

    @override
    def entity_id(self, row: EntityInvitationRow) -> EntityInvitationID:
        return EntityInvitationID(row.id)

    @override
    def created_in(self, row: EntityInvitationRow) -> Collection[EntityIdentifier]:
        return (self.target,)

    @override
    def integrity_error_checks(self) -> Sequence[IntegrityErrorCheck]:
        return (
            IntegrityErrorCheck(
                violation_type=UniqueConstraintViolationError,
                constraint_name="uq_entity_invitations_pending",
                error=DuplicateEntityInvitationError(
                    f"{self.invitee_email} already holds an open invitation to this entity"
                ),
            ),
        )

    @override
    def build_row(self) -> EntityInvitationRow:
        return EntityInvitationRow(
            inviter_user_id=self.inviter_user_id,
            invitee_email=self.invitee_email,
            target_entity_type=self.target.entity_type(),
            target_entity_id=self.target,
            permission_cap=self.permission_cap,
            status=EntityInvitationStatus.PENDING,
        )

    @override
    def to_data(self, row: EntityInvitationRow) -> EntityInvitationData:
        return row.to_data()
