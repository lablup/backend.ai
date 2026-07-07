"""Drives checker-owned state prep in the Source phase."""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Sequence

from ai.backend.common.identifier.idle_checker import IdleCheckerID
from ai.backend.manager.data.idle_checker.types import IdleCheckSession
from ai.backend.manager.repositories.idle_checker.types import (
    IdleCheckBatchData,
    IdleCheckerDefinitionData,
)
from ai.backend.manager.sokovan.idle_check.checkers.base import IdleCheckContext
from ai.backend.manager.sokovan.idle_check.checkers.factory import checker_for
from ai.backend.manager.sokovan.idle_check.types import PreparedChecker, PreparedTarget


class IdleCheckPreparer:
    """Turns the repository batch into judgment-ready targets."""

    _context: IdleCheckContext

    def __init__(self, context: IdleCheckContext) -> None:
        self._context = context

    async def prepare(self, batch: IdleCheckBatchData) -> Sequence[PreparedTarget]:
        """Prepare each distinct checker definition once, then recompose per session."""
        definitions: dict[IdleCheckerID, IdleCheckerDefinitionData] = {}
        sessions_by_checker: defaultdict[IdleCheckerID, list[IdleCheckSession]] = defaultdict(list)
        for target in batch.targets:
            for bound in target.checkers:
                definitions[bound.checker.checker_id] = bound.checker
                sessions_by_checker[bound.checker.checker_id].append(target.session)
        prepared_by_id: dict[IdleCheckerID, PreparedChecker] = {}
        for checker_id, definition in definitions.items():
            checker = checker_for(definition.checker_type)
            if checker is None:
                continue
            state = await checker.prepare(
                self._context, definition, sessions_by_checker[checker_id]
            )
            prepared_by_id[checker_id] = PreparedChecker(checker=checker, state=state)
        prepared_targets: list[PreparedTarget] = []
        for target in batch.targets:
            prepared_checkers = tuple(
                prepared_by_id[bound.checker.checker_id]
                for bound in target.checkers
                if bound.checker.checker_id in prepared_by_id
            )
            if not prepared_checkers:
                continue
            prepared_targets.append(
                PreparedTarget(
                    session_id=target.session.session_id,
                    checkers=prepared_checkers,
                )
            )
        return prepared_targets
