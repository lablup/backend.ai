from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import override

from ai.backend.common.data.entity.types import EntityType
from ai.backend.common.identifier.entity import EntityID
from ai.backend.common.identifier.idle_checker import IdleCheckerID
from ai.backend.common.identifier.session import SessionID
from ai.backend.manager.actions.run_status import ActionRunStatus
from ai.backend.manager.actions.types import ActionOperationType, OperationStatus
from ai.backend.manager.actions.v2.bulk.base import BaseBulkAction
from ai.backend.manager.actions.v2.bulk.result import BaseBulkActionResult, BulkEntityResult


@dataclass(frozen=True)
class ExcludeSessionIdleChecksAction(BaseBulkAction):
    checker_id: IdleCheckerID
    session_ids: list[SessionID]

    @classmethod
    @override
    def entity_type(cls) -> EntityType:
        return EntityType("session")

    @classmethod
    @override
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.UPDATE

    @classmethod
    @override
    def action_name(cls) -> str:
        return "exclude_session_idle_checks"

    @override
    def entity_ids(self) -> Sequence[EntityID]:
        return self.session_ids


@dataclass(frozen=True)
class ExcludeSessionIdleChecksActionResult(BaseBulkActionResult):
    checker_id: IdleCheckerID
    success: Sequence[SessionID]
    errors: Mapping[SessionID, Exception]

    @override
    def entity_results(self) -> Sequence[BulkEntityResult]:
        """Successes first, then errors, classified by :class:`ActionRunStatus` so a
        bulk entity's error reads exactly like a single run's."""
        results = [
            BulkEntityResult(
                entity_id=session_id,
                status=OperationStatus.SUCCESS,
                description=f"Excluded from idle checks by checker {self.checker_id}.",
                error_code=None,
            )
            for session_id in self.success
        ]
        for session_id, exception in self.errors.items():
            failure = ActionRunStatus.of_failure(exception, during_validation=False)
            results.append(
                BulkEntityResult(
                    entity_id=session_id,
                    status=failure.status,
                    description=failure.description,
                    error_code=failure.error_code,
                )
            )
        return results
