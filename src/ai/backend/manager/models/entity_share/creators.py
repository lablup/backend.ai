"""Insert spec for entity invitations."""

from __future__ import annotations

from collections.abc import Collection, Sequence
from dataclasses import dataclass
from typing import override

from ai.backend.common.data.entity.entity_share import EntityShareID
from ai.backend.common.data.entity.types import EntityIdentifier
from ai.backend.common.data.entity.user import UserID
from ai.backend.common.data.permission.types import Permission
from ai.backend.manager.data.entity_share.types import (
    EntityShareData,
    EntityShareStatus,
)
from ai.backend.manager.errors.entity_share import DuplicateEntityShareError
from ai.backend.manager.errors.repository import UniqueConstraintViolationError
from ai.backend.manager.models.entity_share.row import EntityShareRow
from ai.backend.manager.models.specs.creator import EntityCreator
from ai.backend.manager.models.specs.types import IntegrityErrorCheck


@dataclass
class EntityShareCreator(EntityCreator[EntityShareRow, EntityShareData]):
    """An offer of one existing entity to one email address.

    It joins the entity it offers: who may read and withdraw the invitation is
    answered by that entity, and the invitee reaches their own by email instead.
    """

    sharer_user_id: UserID
    recipient_email: str
    target: EntityIdentifier
    permission_cap: Permission | None = None

    @override
    def entity_id(self, row: EntityShareRow) -> EntityShareID:
        return EntityShareID(row.id)

    @override
    def created_in(self, row: EntityShareRow) -> Collection[EntityIdentifier]:
        return (self.target,)

    @override
    def integrity_error_checks(self) -> Sequence[IntegrityErrorCheck]:
        conflict = DuplicateEntityShareError(
            f"{self.recipient_email} already holds an open offer of this entity"
        )
        return (
            IntegrityErrorCheck(
                violation_type=UniqueConstraintViolationError,
                constraint_name="uq_entity_shares_pending_email",
                error=conflict,
            ),
            IntegrityErrorCheck(
                violation_type=UniqueConstraintViolationError,
                constraint_name="uq_entity_shares_pending_recipient",
                error=conflict,
            ),
        )

    @override
    def build_row(self) -> EntityShareRow:
        return EntityShareRow(
            sharer_user_id=self.sharer_user_id,
            recipient_email=self.recipient_email,
            target_entity_type=self.target.entity_type(),
            target_entity_id=self.target,
            permission_cap=self.permission_cap,
            status=EntityShareStatus.PENDING,
        )

    @override
    def to_data(self, row: EntityShareRow) -> EntityShareData:
        return row.to_data()
