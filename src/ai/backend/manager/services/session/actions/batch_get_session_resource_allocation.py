from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, replace
from typing import Self, override

from ai.backend.common.data.entity.session import SessionID
from ai.backend.common.data.entity.types import EntityIdentifier
from ai.backend.common.types import SessionId
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.actions.v2.bulk.base import BasePartialBulkAction


@dataclass
class BatchGetSessionResourceAllocationAction(BasePartialBulkAction):
    """Aggregate the slot amounts recorded against the sessions the caller named.

    Answered for by each session the ids name.
    """

    session_ids: list[SessionId]

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.SEARCH

    @override
    @classmethod
    def action_name(cls) -> str:
        return "batch_get_session_resource_allocation"

    @override
    def entity_ids(self) -> Sequence[EntityIdentifier]:
        return [SessionID(_id) for _id in self.session_ids]

    @override
    def narrowed_to(self, entity_ids: Sequence[EntityIdentifier]) -> Self:
        allowed = frozenset(entity_ids)
        return replace(
            self,
            session_ids=[sid for sid in self.session_ids if SessionID(sid) in allowed],
        )
