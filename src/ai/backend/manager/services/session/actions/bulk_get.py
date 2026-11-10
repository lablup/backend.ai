from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, replace
from typing import Self, override

from ai.backend.common.data.entity.session import SessionID
from ai.backend.common.data.entity.types import EntityIdentifier
from ai.backend.manager.actions.v2.ops.base import PartialBulkGetEntityOpsAction
from ai.backend.manager.data.session.types import SessionEntityData
from ai.backend.manager.models.session.queriers import BulkSessionQuerier
from ai.backend.manager.models.session.row import SessionRow


@dataclass
class BulkGetSessionsAction(PartialBulkGetEntityOpsAction[SessionRow, SessionEntityData]):
    """Read the sessions the caller named, answering for each id."""

    ids: Sequence[SessionID]

    @override
    @classmethod
    def action_name(cls) -> str:
        return "bulk_get_sessions"

    @override
    def entity_ids(self) -> Sequence[EntityIdentifier]:
        return tuple(self.ids)

    @override
    def to_querier(self) -> BulkSessionQuerier:
        return BulkSessionQuerier()

    @override
    def narrowed_to(self, entity_ids: Sequence[EntityIdentifier]) -> Self:
        allowed = frozenset(entity_ids)
        return replace(self, ids=[entity_id for entity_id in self.ids if entity_id in allowed])
