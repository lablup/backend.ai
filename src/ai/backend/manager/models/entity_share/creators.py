"""Insert spec for entity invitations."""

from __future__ import annotations

from collections.abc import Collection, Sequence
from dataclasses import dataclass
from datetime import datetime
from typing import Any, override

import sqlalchemy as sa

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
from ai.backend.manager.models.virtual_entity.virtual_entity import VirtualEntityRow


@dataclass
class EntityShareCreator(EntityCreator[EntityShareRow, EntityShareData]):
    """An offer of one existing entity to one scope, or to an address with no account.

    It joins the entity it offers: who may read and withdraw the offer is answered by
    that entity, while the recipient reaches their own through the scope it names.

    The recipient is recorded as it was named, a person or a project alike, and the
    node it holds is selected as the row is written rather than read first. Where an
    accepted offer lands is the answering side's to decide. An address with no account
    yet has no node, so it stays an email until it is answered.
    """

    sharer_user_id: UserID
    target: EntityIdentifier
    recipient: EntityIdentifier | None = None
    recipient_email: str | None = None
    permission_cap: Permission | None = None
    expires_at: datetime | None = None

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
            recipient_virtual_entity_id=self._recipient_node(),
            recipient_email=self.recipient_email,
            target_entity_type=self.target.entity_type(),
            target_entity_id=self.target,
            permission_cap=self.permission_cap,
            expires_at=self.expires_at,
            status=EntityShareStatus.PENDING,
        )

    def _recipient_node(self) -> Any:
        """The node the recipient holds, as a value the insert selects.

        A recipient that has none leaves NULL, which the row's check refuses unless an
        address stands in its place.
        """
        recipient = self.recipient
        if recipient is None:
            return None
        return (
            sa.select(VirtualEntityRow.id)
            .where(
                VirtualEntityRow.entity_type == recipient.entity_type(),
                VirtualEntityRow.entity_id == recipient,
            )
            .scalar_subquery()
        )

    @override
    def to_data(self, row: EntityShareRow) -> EntityShareData:
        return row.to_data()
