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
from ai.backend.manager.data.project.types import ProjectType
from ai.backend.manager.errors.entity_share import (
    DuplicateEntityShareError,
    ShareToAPersonalProject,
    ShareToTheOwningScope,
)
from ai.backend.manager.errors.repository import UniqueConstraintViolationError
from ai.backend.manager.models.entity_share.row import EntityShareRow
from ai.backend.manager.models.project.row import ProjectRow
from ai.backend.manager.models.specs.creator import GuardedEntityCreator
from ai.backend.manager.models.specs.types import IntegrityErrorCheck, PreconditionCheck
from ai.backend.manager.models.virtual_entity.entity_membership import EntityMembershipRow
from ai.backend.manager.models.virtual_entity.virtual_entity import VirtualEntityRow


@dataclass
class EntityShareCreator(GuardedEntityCreator[EntityShareRow, EntityShareData]):
    """An offer of one existing entity to one scope, or to an address with no account.

    It joins the entity it offers: who may read and withdraw the offer is answered by
    that entity, while the recipient reaches their own through the scope it names.

    The recipient is recorded as the scope an accepted offer would land in: naming a
    person is normalised to the project that is theirs alone before the spec is built,
    so one person reached two ways is one row rather than two. An address with no
    account yet names no scope, so it stays an email until the offer is answered.
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
    def precondition_checks(self) -> Sequence[PreconditionCheck]:
        """Two states the graph can be in that make this offer wrong.

        A scope that already owns the entity would come away with a capped edge where
        it had an outright one, because lending states what holds now. A project that
        is one person's own is that person under another name, and naming them twice
        would stand two live rows where the graph holds one edge.
        """
        recipient = self.recipient
        if recipient is None:
            return ()
        return (
            PreconditionCheck(
                finder=sa.select(EntityMembershipRow.id).where(
                    EntityMembershipRow.virtual_entity_id == self._node_of(recipient),
                    EntityMembershipRow.member_entity_id == self._node_of(self.target),
                    EntityMembershipRow.capped.is_(False),
                ),
                error=ShareToTheOwningScope(
                    f"{recipient.entity_type()} {recipient} already owns this entity"
                ),
            ),
            PreconditionCheck(
                finder=sa.select(ProjectRow.id).where(
                    ProjectRow.id == recipient,
                    ProjectRow.type == ProjectType.PERSONAL,
                ),
                error=ShareToAPersonalProject(
                    f"Project {recipient} is one person's own; offer it to the person instead"
                ),
            ),
        )

    def _node_of(self, entity: EntityIdentifier) -> sa.ScalarSelect[Any]:
        return (
            sa.select(VirtualEntityRow.id)
            .where(
                VirtualEntityRow.entity_type == entity.entity_type(),
                VirtualEntityRow.entity_id == entity,
            )
            .scalar_subquery()
        )

    @override
    def integrity_error_checks(self) -> Sequence[IntegrityErrorCheck]:
        conflict = DuplicateEntityShareError(
            f"{self.recipient_email} already holds an open offer of this entity"
        )
        return (
            IntegrityErrorCheck(
                violation_type=UniqueConstraintViolationError,
                constraint_name="uq_entity_shares_live_email",
                error=conflict,
            ),
            IntegrityErrorCheck(
                violation_type=UniqueConstraintViolationError,
                constraint_name="uq_entity_shares_live_recipient",
                error=conflict,
            ),
        )

    @override
    def build_row(self) -> EntityShareRow:
        return EntityShareRow(
            sharer_user_id=self.sharer_user_id,
            recipient_entity_type=(
                self.recipient.entity_type() if self.recipient is not None else None
            ),
            recipient_entity_id=self.recipient,
            recipient_email=self.recipient_email,
            target_entity_type=self.target.entity_type(),
            target_entity_id=self.target,
            permission_cap=self.permission_cap,
            expires_at=self.expires_at,
            status=EntityShareStatus.PENDING,
        )

    @override
    def to_data(self, row: EntityShareRow) -> EntityShareData:
        return row.to_data()
