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
    IdleCheckerContext,
    IdleJudgment,
)
from ai.backend.manager.sokovan.idle_check.types import IdleCheckReconcileInfo, IdleCheckResult
from ai.backend.manager.sokovan.reconciler.base import ReconcilerHandler


class IdleCheckReconcileHandler(ReconcilerHandler[IdleCheckReconcileInfo, IdleCheckResult]):
    """Drive checker-axis judgments for persistence by the applier."""

    _checkers: Mapping[CheckerType, IdleChecker]

    def __init__(self, checkers: Mapping[CheckerType, IdleChecker]) -> None:
        self._checkers = checkers

    @override
    async def execute(self, reconcile_info: IdleCheckReconcileInfo) -> IdleCheckResult:
        assignments_by_type = self._assignments_by_type(reconcile_info.batch)
        context = IdleCheckerContext(current_time=reconcile_info.current_time)
        all_judgments: list[IdleJudgment] = []
        for checker_type, assignments in assignments_by_type.items():
            checker = self._checkers.get(checker_type)
            if checker is None:
                continue
            judgments = await checker.judge(
                assignments,
                context=context,
            )
            all_judgments.extend(judgments)
        return IdleCheckResult(judgments=all_judgments)

    def _assignments_by_type(
        self, batch: IdleCheckBatchData
    ) -> dict[CheckerType, list[CheckerAssignment]]:
        """Pivot the session-axis batch into per-type checker assignments."""
        definitions: dict[IdleCheckerID, IdleCheckerDefinitionData] = {}
        sessions_by_checker: defaultdict[IdleCheckerID, dict[SessionId, IdleCheckSession]] = (
            defaultdict(dict)
        )
        for assignment in batch.assignments:
            checker_id = assignment.checker.checker_id
            definitions[checker_id] = assignment.checker
            sessions_by_checker[checker_id][assignment.session.session_id] = assignment.session
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
