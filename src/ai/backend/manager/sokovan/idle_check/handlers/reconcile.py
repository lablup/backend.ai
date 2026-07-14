from __future__ import annotations

from collections import defaultdict
from collections.abc import Mapping
from typing import override

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
    """Drive checker-axis judgments and merge idle reasons into session reports."""

    _checkers: Mapping[CheckerType, IdleChecker]

    def __init__(self, checkers: Mapping[CheckerType, IdleChecker]) -> None:
        self._checkers = checkers

    @override
    async def execute(self, reconcile_info: IdleCheckReconcileInfo) -> IdleCheckResult:
        assignments_by_type = self._assignments_by_type(reconcile_info.batch)
        reasons_by_session: defaultdict[SessionId, list[IdleReason]] = defaultdict(list)
        for checker_type, assignments in assignments_by_type.items():
            checker = self._checkers.get(checker_type)
            if checker is None:
                continue
            judgments = await checker.judge(
                assignments,
                current_time=reconcile_info.current_time,
            )
            for judgment in judgments:
                if not judgment.is_idle:
                    continue
                reasons_by_session[judgment.session_id].append(
                    IdleReason(checker_id=judgment.checker_id, message=judgment.message)
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
        sessions_by_checker: defaultdict[IdleCheckerID, dict[SessionId, IdleCheckSession]] = (
            defaultdict(dict)
        )
        for target in batch.targets:
            for bound in target.checkers:
                definitions[bound.checker.checker_id] = bound.checker
                sessions_by_checker[bound.checker.checker_id][target.session.session_id] = (
                    target.session
                )
        assignments_by_type: defaultdict[CheckerType, list[CheckerAssignment]] = defaultdict(list)
        for checker_id, definition in definitions.items():
            assignments_by_type[definition.checker_type].append(
                CheckerAssignment(
                    definition=definition,
                    sessions=tuple(sessions_by_checker[checker_id].values()),
                )
            )
        return dict(assignments_by_type)

    @override
    async def post_process(self, result: IdleCheckResult) -> None:
        pass
