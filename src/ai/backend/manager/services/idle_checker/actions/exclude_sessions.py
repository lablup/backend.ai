from collections.abc import Sequence
from dataclasses import dataclass
from typing import override

from ai.backend.common.data.entity.session import SessionID
from ai.backend.common.data.entity.types import EntityIdentifier
from ai.backend.common.data.entity.user import UserID
from ai.backend.manager.actions.run_status import ActionRunStatus
from ai.backend.manager.actions.types import ActionOperationType, OperationStatus
from ai.backend.manager.actions.v2.bulk.base import BaseBulkAction
from ai.backend.manager.actions.v2.bulk.result import BasePartialBulkActionResult, BulkEntityResult
from ai.backend.manager.repositories.idle_checker.types import (
    SessionIdleCheckPair,
    SessionIdleCheckPairResult,
)


@dataclass(frozen=True)
class ExcludeSessionIdleChecksAction(BaseBulkAction):
    targets: list[SessionIdleCheckPair]
    user_id: UserID

    @classmethod
    @override
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.UPDATE

    @classmethod
    @override
    def action_name(cls) -> str:
        return "exclude_session_idle_checks"

    @override
    def entity_ids(self) -> Sequence[EntityIdentifier]:
        return [SessionID(target.session_id) for target in self.targets]


@dataclass(frozen=True)
class ExcludeSessionIdleChecksActionResult(BasePartialBulkActionResult):
    results: Sequence[SessionIdleCheckPairResult]

    @override
    def entity_results(self) -> Sequence[BulkEntityResult]:
        """One entry per pair the caller named, in that order, so a bulk entity's
        error reads exactly like a single run's."""
        entries: list[BulkEntityResult] = []
        for item in self.results:
            if item.error is not None:
                failure = ActionRunStatus.of_failure(item.error, during_validation=False)
                entries.append(
                    BulkEntityResult(
                        entity_id=SessionID(item.pair.session_id),
                        status=failure.status,
                        description=f"{failure.description} (checker {item.pair.checker_id})",
                        error_code=failure.error_code,
                    )
                )
                continue
            entries.append(
                BulkEntityResult(
                    entity_id=SessionID(item.pair.session_id),
                    status=OperationStatus.SUCCESS,
                    description=(
                        f"Excluded from idle checks by checker {item.pair.checker_id}."
                        if item.applied
                        else f"Checker {item.pair.checker_id} does not apply to this session."
                    ),
                    error_code=None,
                )
            )
        return entries
