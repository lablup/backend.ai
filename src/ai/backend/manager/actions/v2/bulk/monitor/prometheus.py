from __future__ import annotations

from collections.abc import Sequence
from typing import override

from ai.backend.common.metrics.metric import (
    ACTION_STATUS_PARTIAL,
    ActionMetricObserver,
)
from ai.backend.manager.actions.action import BaseActionTriggerMeta
from ai.backend.manager.actions.types import OperationStatus
from ai.backend.manager.actions.v2.bulk.base import BaseBulkAction
from ai.backend.manager.actions.v2.bulk.monitor.base import BulkActionMonitor
from ai.backend.manager.actions.v2.bulk.result import (
    BulkActionProcessResult,
    BulkEntityResult,
)

__all__ = ("BulkActionPrometheusMonitor",)


class BulkActionPrometheusMonitor(BulkActionMonitor):
    """Observes bulk action outcomes into the Prometheus action metrics.

    One observation per run — the action metric is keyed by (entity_type,
    operation, status), not by target, so a bulk run does not fan out.
    """

    _observer: ActionMetricObserver

    def __init__(self) -> None:
        self._observer = ActionMetricObserver.instance()

    @override
    async def prepare(self, action: BaseBulkAction, meta: BaseActionTriggerMeta) -> None:
        return

    @override
    async def done(self, action: BaseBulkAction, result: BulkActionProcessResult) -> None:
        meta = result.meta
        failed = [r for r in meta.entity_results if r.status is not OperationStatus.SUCCESS]
        self._observer.observe_action(
            entity_type=action.entity_type(),
            operation_type=action.operation_type(),
            status=self._run_status_label(meta.entity_results, failed),
            duration=meta.duration.total_seconds(),
            error_code=failed[0].error_code if failed else None,
        )
        for entity_result in meta.entity_results:
            self._observer.observe_action_entity(
                entity_type=action.entity_type(),
                operation_type=action.operation_type(),
                status=entity_result.status,
                error_code=entity_result.error_code,
            )

    def _run_status_label(
        self,
        entity_results: Sequence[BulkEntityResult],
        failed: Sequence[BulkEntityResult],
    ) -> str:
        """The status label for the run, seen from the request's side.

        A run that reached some entities but not others is ``partial`` — a label, not
        an :class:`OperationStatus`, because no audit row is ever partly done. When a
        run was rejected or raised, every entity carries the same status and the run
        reports it as-is, so a denial does not read as a generic error.
        """
        if not entity_results:
            return OperationStatus.UNKNOWN
        if not failed:
            return OperationStatus.SUCCESS
        if len(failed) < len(entity_results):
            return ACTION_STATUS_PARTIAL
        return str(failed[0].status)
