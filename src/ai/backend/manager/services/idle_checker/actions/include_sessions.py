from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import override

from ai.backend.common.data.entity.session import SessionID
from ai.backend.common.data.entity.types import EntityIdentifier, EntityType
from ai.backend.common.data.entity.user import UserID
from ai.backend.manager.actions.run_status import ActionRunStatus
from ai.backend.manager.actions.types import ActionOperationType, OperationStatus
from ai.backend.manager.actions.v2.bulk.base import BaseBulkAction
from ai.backend.manager.actions.v2.bulk.result import BaseBulkActionResult, BulkEntityResult
from ai.backend.manager.repositories.idle_checker.types import SessionIdleCheckPair


@dataclass(frozen=True)
class IncludeSessionIdleChecksAction(BaseBulkAction):
    targets: list[SessionIdleCheckPair]
    user_id: UserID

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
        return "include_session_idle_checks"

    @override
    def entity_ids(self) -> Sequence[EntityIdentifier]:
        return [SessionID(target.session_id) for target in self.targets]


@dataclass(frozen=True)
class IncludeSessionIdleChecksActionResult(BaseBulkActionResult):
    success: Sequence[SessionIdleCheckPair]
    errors: Mapping[SessionIdleCheckPair, Exception]

    @override
    def entity_results(self) -> Sequence[BulkEntityResult]:
        """Successes first, then errors, classified by :class:`ActionRunStatus` so a
        bulk entity's error reads exactly like a single run's."""
        results = [
            BulkEntityResult(
                entity_id=SessionID(pair.session_id),
                status=OperationStatus.SUCCESS,
                description=f"Included into idle checks by checker {pair.checker_id}.",
                error_code=None,
            )
            for pair in self.success
        ]
        for pair, exception in self.errors.items():
            failure = ActionRunStatus.of_failure(exception, during_validation=False)
            results.append(
                BulkEntityResult(
                    entity_id=SessionID(pair.session_id),
                    status=failure.status,
                    description=f"{failure.description} (checker {pair.checker_id})",
                    error_code=failure.error_code,
                )
            )
        return results
