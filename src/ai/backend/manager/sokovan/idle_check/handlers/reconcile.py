from __future__ import annotations

from collections import defaultdict
from collections.abc import Mapping
from typing import Any, override

from ai.backend.common.data.idle_checker.types import CheckerType
from ai.backend.common.identifier.idle_checker import IdleCheckerID
from ai.backend.common.types import SessionId
from ai.backend.manager.data.idle_checker.types import IdleCheckSession
from ai.backend.manager.repositories.idle_checker.types import (
    IdleCheckBatchData,
    IdleCheckerDefinitionData,
)
from ai.backend.manager.sokovan.idle_check.checkers.base import (
    CheckerAssignment,
    IdleChecker,
)
from ai.backend.manager.sokovan.idle_check.types import (
    IdleCheckReconcileInfo,
    IdleCheckReport,
    IdleCheckResult,
    IdleReason,
)
from ai.backend.manager.sokovan.reconciler.base import ReconcilerHandler


class IdleCheckReconcileHandler(ReconcilerHandler[IdleCheckReconcileInfo, IdleCheckResult]):
    """Pivots the batch to checker-axis assignments, drives each type's batched prepare
    (the only I/O) and judgment, then merges idle judgments into per-session reports."""

    _checkers: Mapping[CheckerType, IdleChecker[Any]]

    def __init__(self, checkers: Mapping[CheckerType, IdleChecker[Any]]) -> None:
        self._checkers = checkers

    @override
    async def execute(self, reconcile_info: IdleCheckReconcileInfo) -> IdleCheckResult:
        assignments_by_type = self._assignments_by_type(reconcile_info.batch)
        reasons_by_session: defaultdict[SessionId, list[IdleReason]] = defaultdict(list)
        for checker_type, assignments in assignments_by_type.items():
            checker = self._checkers.get(checker_type)
            if checker is None:
                continue
            states = await checker.prepare(assignments)
            for checker_id, session_states in states.items():
                for judgment in checker.judge(session_states):
                    if not judgment.is_idle:
                        continue
                    reasons_by_session[judgment.session_id].append(
                        IdleReason(checker_id=checker_id, message=judgment.message)
                    )
        reports: list[IdleCheckReport] = []
        for session_id, reasons in reasons_by_session.items():
            reports.append(IdleCheckReport(session_id=session_id, reasons=reasons))
        return IdleCheckResult(reports=reports)

    def _assignments_by_type(
        self, batch: IdleCheckBatchData
    ) -> dict[CheckerType, list[CheckerAssignment]]:
        """Pivot the session-axis batch into per-type checker assignments."""
        definitions: dict[IdleCheckerID, IdleCheckerDefinitionData] = {}
        sessions_by_checker: defaultdict[IdleCheckerID, list[IdleCheckSession]] = defaultdict(list)
        for target in batch.targets:
            for bound in target.checkers:
                definitions[bound.checker.checker_id] = bound.checker
                sessions_by_checker[bound.checker.checker_id].append(target.session)
        assignments_by_type: defaultdict[CheckerType, list[CheckerAssignment]] = defaultdict(list)
        for checker_id, definition in definitions.items():
            assignments_by_type[definition.checker_type].append(
                CheckerAssignment(
                    definition=definition,
                    sessions=sessions_by_checker[checker_id],
                )
            )
        return dict(assignments_by_type)

    @override
    async def post_process(self, result: IdleCheckResult) -> None:
        pass
