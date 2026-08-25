"""List-read spec for entity invitations."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, override

import sqlalchemy as sa

from ai.backend.manager.data.entity_invitation.types import EntityInvitationData
from ai.backend.manager.models.entity_invitation.row import EntityInvitationRow
from ai.backend.manager.models.specs.searcher import Searcher


@dataclass
class EntityInvitationSearcher(Searcher[EntityInvitationRow, EntityInvitationData]):
    @override
    def build_select(self) -> sa.sql.Select[Any]:
        return sa.select(EntityInvitationRow)

    @override
    def to_data(self, row: EntityInvitationRow) -> EntityInvitationData:
        return row.to_data()
