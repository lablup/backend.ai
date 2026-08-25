"""Single-row read spec for entity invitations."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, override

from sqlalchemy.orm import InstrumentedAttribute

from ai.backend.common.data.entity.entity_invitation import EntityInvitationID
from ai.backend.manager.data.entity_invitation.types import EntityInvitationData
from ai.backend.manager.models.entity_invitation.row import EntityInvitationRow
from ai.backend.manager.models.specs.querier import DataQuerier


@dataclass
class EntityInvitationQuerier(DataQuerier[EntityInvitationRow, EntityInvitationData]):
    invitation_id: EntityInvitationID

    @override
    def row_class(self) -> type[EntityInvitationRow]:
        return EntityInvitationRow

    @override
    def entity_id_column(self) -> InstrumentedAttribute[Any]:
        return EntityInvitationRow.id

    @override
    def entity_id_value(self) -> EntityInvitationID:
        return self.invitation_id

    @override
    def to_data(self, row: EntityInvitationRow) -> EntityInvitationData:
        return row.to_data()
