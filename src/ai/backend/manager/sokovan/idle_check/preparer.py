"""Drives checker-owned state prep in the Source phase."""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Sequence

from ai.backend.common.data.idle_checker.types import CheckerType
from ai.backend.common.identifier.idle_checker import IdleCheckerID
from ai.backend.manager.data.idle_checker.types import IdleCheckSession
from ai.backend.manager.repositories.idle_checker.types import (
    IdleCheckBatchData,
    IdleCheckerDefinitionData,
)
from ai.backend.manager.sokovan.idle_check.checkers.base import IdleCheckContext, PrepareRequest
from ai.backend.manager.sokovan.idle_check.checkers.factory import checker_for
from ai.backend.manager.sokovan.idle_check.types import PreparedChecker, PreparedTarget


class IdleCheckPreparer:
    """Turns the repository batch into judgment-ready targets."""

    _context: IdleCheckContext

    def __init__(self, context: IdleCheckContext) -> None:
        self._context = context

    async def prepare(self, batch: IdleCheckBatchData) -> Sequence[PreparedTarget]:
        """Prepare each checker type once over all its definitions, then recompose per session."""
        definitions: dict[IdleCheckerID, IdleCheckerDefinitionData] = {}
        sessions_by_checker: defaultdict[IdleCheckerID, list[IdleCheckSession]] = defaultdict(list)
        for target in batch.targets:
            for bound in target.checkers:
                definitions[bound.checker.checker_id] = bound.checker
                sessions_by_checker[bound.checker.checker_id].append(target.session)
        requests_by_type: defaultdict[CheckerType, list[PrepareRequest]] = defaultdict(list)
        for checker_id, definition in definitions.items():
            requests_by_type[definition.checker_type].append(
                PrepareRequest(
                    definition=definition,
                    sessions=tuple(sessions_by_checker[checker_id]),
                )
            )
        prepared_by_id: dict[IdleCheckerID, PreparedChecker] = {}
        for checker_type, requests in requests_by_type.items():
            checker = checker_for(checker_type)
            if checker is None:
                continue
            states = await checker.prepare(self._context, requests)
            for checker_id, state in states.items():
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
