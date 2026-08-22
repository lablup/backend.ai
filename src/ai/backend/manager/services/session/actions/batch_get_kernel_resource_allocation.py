from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import override

from ai.backend.common.data.entity.session import SessionID
from ai.backend.common.data.entity.types import EntityIdentifier
from ai.backend.common.types import KernelId
from ai.backend.manager.actions.types import ActionOperationType, OperationStatus
from ai.backend.manager.actions.v2.bulk.base import BaseBulkAction
from ai.backend.manager.actions.v2.bulk.result import BasePartialBulkActionResult, BulkEntityResult
from ai.backend.manager.data.resource_slot.types import ResourceAllocationAggregate


@dataclass
class BatchGetKernelResourceAllocationAction(BaseBulkAction):
    """Aggregate the slot amounts recorded against the kernels the caller named.

    A kernel runs under a session, so the session is what answers for the read; the ids are read back as the sessions they belong to.
    """

    kernel_ids: list[KernelId]

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.SEARCH

    @override
    @classmethod
    def action_name(cls) -> str:
        return "batch_get_kernel_resource_allocation"

    @override
    def entity_ids(self) -> Sequence[EntityIdentifier]:
        return [SessionID(_id) for _id in self.kernel_ids]


@dataclass
class BatchGetKernelResourceAllocationActionResult(BasePartialBulkActionResult):
    data: dict[KernelId, ResourceAllocationAggregate]

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
