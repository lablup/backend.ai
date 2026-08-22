from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import override

from ai.backend.common.data.entity.session import SessionID
from ai.backend.common.data.entity.types import EntityIdentifier
from ai.backend.common.types import SessionId
from ai.backend.manager.actions.types import ActionOperationType, OperationStatus
from ai.backend.manager.actions.v2.bulk.base import BaseBulkAction
from ai.backend.manager.actions.v2.bulk.result import BasePartialBulkActionResult, BulkEntityResult
from ai.backend.manager.data.resource_slot.types import ResourceAllocationAggregate


@dataclass
class BatchGetSessionResourceAllocationAction(BaseBulkAction):
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


@dataclass
class BatchGetSessionResourceAllocationActionResult(BasePartialBulkActionResult):
    data: dict[SessionId, ResourceAllocationAggregate]

    @override
    def entity_results(self) -> Sequence[BulkEntityResult]:
        return [
            BulkEntityResult(
                entity_id=SessionID(_id),
                status=OperationStatus.SUCCESS,
                description="aggregated",
                error_code=None,
            )
            for _id in self.data
        ]
