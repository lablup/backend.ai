from __future__ import annotations

from collections.abc import Sequence
from dataclasses import replace
from datetime import UTC, datetime
from typing import Final, override
from uuid import uuid4

import pytest

from ai.backend.common.data.idle_checker.types import (
    CheckerType,
    IdleCheckerSpec,
    NetworkTimeoutSpec,
    SessionLifetimeSpec,
)
from ai.backend.common.data.permission.types import ScopeType
from ai.backend.common.identifier.idle_checker import IdleCheckerID
from ai.backend.common.types import SessionId, SessionTypes
from ai.backend.manager.data.idle_checker.types import IdleCheckSession
from ai.backend.manager.data.permission.id import ScopeId
from ai.backend.manager.errors.common import InternalServerError
from ai.backend.manager.repositories.idle_checker.types import (
    BoundCheckerData,
    IdleCheckBatchData,
    IdleCheckerDefinitionData,
    IdleCheckTargetData,
)
from ai.backend.manager.sokovan.idle_check.checkers.base import (
    CheckerAssignment,
    IdleChecker,
    IdleCheckerContext,
    IdleJudgment,
)
from ai.backend.manager.sokovan.idle_check.handlers.reconcile import IdleCheckReconcileHandler
from ai.backend.manager.sokovan.idle_check.types import (
    IdleCheckReconcileInfo,
    IdleCheckReport,
    IdleReason,
)

_NOW = datetime(2026, 1, 2, tzinfo=UTC)

_SPECS: Final[dict[CheckerType, IdleCheckerSpec]] = {
    CheckerType.SESSION_LIFETIME: IdleCheckerSpec(
        type=CheckerType.SESSION_LIFETIME,
        session_lifetime=SessionLifetimeSpec(max_lifetime_seconds=3600),
    ),
    CheckerType.NETWORK_TIMEOUT: IdleCheckerSpec(
        type=CheckerType.NETWORK_TIMEOUT,
        network=NetworkTimeoutSpec(idle_timeout_seconds=3600),
    ),
}


class FakeChecker(IdleChecker):
    """Records the single batched call and returns configured session judgments."""

    idle_session_ids: set[SessionId]
    judge_calls: list[list[tuple[IdleCheckerID, list[SessionId]]]]
    judge_contexts: list[IdleCheckerContext]
    should_fail: bool
    _message: str

    def __init__(self, message: str = "idle") -> None:
        self.idle_session_ids = set()
        self.judge_calls = []
        self.judge_contexts = []
        self.should_fail = False
        self._message = message

    @override
    async def judge(
        self,
        assignments: Sequence[CheckerAssignment],
        *,
        context: IdleCheckerContext,
    ) -> Sequence[IdleJudgment]:
        self.judge_contexts.append(context)
        call_record: list[tuple[IdleCheckerID, list[SessionId]]] = []
        for assignment in assignments:
            session_ids = [session.session_id for session in assignment.sessions]
            call_record.append((assignment.definition.checker_id, session_ids))
        self.judge_calls.append(call_record)
        if self.should_fail:
            raise InternalServerError("Fake checker failed")
        judgments: list[IdleJudgment] = []
        for assignment in assignments:
            for session in assignment.sessions:
                judgments.append(
                    IdleJudgment(
                        checker_id=assignment.definition.checker_id,
                        session_id=session.session_id,
                        is_idle=session.session_id in self.idle_session_ids,
                        message=self._message,
                    )
                )
        return judgments


def _bound_checker(checker_type: CheckerType) -> BoundCheckerData:
    return BoundCheckerData(
        scope=ScopeId(ScopeType.RESOURCE_GROUP, str(uuid4())),
        binding_created_at=datetime(2026, 1, 1, tzinfo=UTC),
        checker=IdleCheckerDefinitionData(
            checker_id=IdleCheckerID(uuid4()),
            checker_type=checker_type,
            target_session_types=frozenset({SessionTypes.INTERACTIVE}),
            spec=_SPECS[checker_type],
        ),
    )


def _target(session_id: SessionId, checkers: Sequence[BoundCheckerData]) -> IdleCheckTargetData:
    return IdleCheckTargetData(
        session=IdleCheckSession(
            session_id=session_id,
            created_at=datetime(2026, 1, 1, tzinfo=UTC),
            starts_at=None,
        ),
        checkers=checkers,
    )


class TestIdleCheckReconcileHandler:
    @pytest.fixture()
    def first_session_id(self) -> SessionId:
        return SessionId(uuid4())

    @pytest.fixture()
    def second_session_id(self) -> SessionId:
        return SessionId(uuid4())

    @pytest.fixture()
    def lifetime_bound(self) -> BoundCheckerData:
        return _bound_checker(CheckerType.SESSION_LIFETIME)

    @pytest.fixture()
    def second_lifetime_bound(self) -> BoundCheckerData:
        return _bound_checker(CheckerType.SESSION_LIFETIME)

    @pytest.fixture()
    def network_bound(self) -> BoundCheckerData:
        return _bound_checker(CheckerType.NETWORK_TIMEOUT)

    @pytest.fixture()
    def lifetime_checker(self) -> FakeChecker:
        return FakeChecker(message="max lifetime exceeded")

    @pytest.fixture()
    def network_checker(self) -> FakeChecker:
        return FakeChecker(message="no network activity")

    @pytest.fixture()
    def handler(
        self,
        lifetime_checker: FakeChecker,
        network_checker: FakeChecker,
    ) -> IdleCheckReconcileHandler:
        return IdleCheckReconcileHandler({
            CheckerType.SESSION_LIFETIME: lifetime_checker,
            CheckerType.NETWORK_TIMEOUT: network_checker,
        })

    async def test_batches_judgments_by_checker_type(
        self,
        handler: IdleCheckReconcileHandler,
        first_session_id: SessionId,
        second_session_id: SessionId,
        lifetime_bound: BoundCheckerData,
        second_lifetime_bound: BoundCheckerData,
        network_bound: BoundCheckerData,
        lifetime_checker: FakeChecker,
        network_checker: FakeChecker,
    ) -> None:
        """Two sessions sharing one definition; the second adds a same-type and another-type one."""
        reconcile_info = IdleCheckReconcileInfo(
            batch=IdleCheckBatchData(
                targets=(
                    _target(first_session_id, [lifetime_bound]),
                    _target(
                        second_session_id,
                        [lifetime_bound, second_lifetime_bound, network_bound],
                    ),
                )
            ),
            current_time=_NOW,
        )

        await handler.execute(reconcile_info)

        assert lifetime_checker.judge_calls == [
            [
                (lifetime_bound.checker.checker_id, [first_session_id, second_session_id]),
                (second_lifetime_bound.checker.checker_id, [second_session_id]),
            ],
        ]
        assert network_checker.judge_calls == [
            [(network_bound.checker.checker_id, [second_session_id])],
        ]
        expected_context = IdleCheckerContext(current_time=_NOW)
        assert lifetime_checker.judge_contexts == [expected_context]
        assert network_checker.judge_contexts == [expected_context]

    async def test_deduplicates_cross_scope_assignments(
        self,
        handler: IdleCheckReconcileHandler,
        first_session_id: SessionId,
        lifetime_bound: BoundCheckerData,
        lifetime_checker: FakeChecker,
    ) -> None:
        duplicate_binding = replace(
            lifetime_bound,
            scope=ScopeId(ScopeType.DOMAIN, str(uuid4())),
        )
        reconcile_info = IdleCheckReconcileInfo(
            batch=IdleCheckBatchData(
                targets=(_target(first_session_id, [lifetime_bound, duplicate_binding]),)
            ),
            current_time=_NOW,
        )

        await handler.execute(reconcile_info)

        assert lifetime_checker.judge_calls == [
            [(lifetime_bound.checker.checker_id, [first_session_id])],
        ]

    async def test_merges_idle_reasons(
        self,
        handler: IdleCheckReconcileHandler,
        first_session_id: SessionId,
        second_session_id: SessionId,
        lifetime_bound: BoundCheckerData,
        network_bound: BoundCheckerData,
        lifetime_checker: FakeChecker,
        network_checker: FakeChecker,
    ) -> None:
        """A session idle by two checkers gets one report listing each checker's reason."""
        lifetime_checker.idle_session_ids = {first_session_id, second_session_id}
        network_checker.idle_session_ids = {first_session_id}
        reconcile_info = IdleCheckReconcileInfo(
            batch=IdleCheckBatchData(
                targets=(
                    _target(first_session_id, [lifetime_bound, network_bound]),
                    _target(second_session_id, [lifetime_bound]),
                )
            ),
            current_time=_NOW,
        )

        result = await handler.execute(reconcile_info)

        assert result.reports == [
            IdleCheckReport(
                session_id=first_session_id,
                reasons=[
                    IdleReason(
                        checker_id=lifetime_bound.checker.checker_id,
                        message="max lifetime exceeded",
                    ),
                    IdleReason(
                        checker_id=network_bound.checker.checker_id,
                        message="no network activity",
                    ),
                ],
            ),
            IdleCheckReport(
                session_id=second_session_id,
                reasons=[
                    IdleReason(
                        checker_id=lifetime_bound.checker.checker_id,
                        message="max lifetime exceeded",
                    ),
                ],
            ),
        ]
        assert result.processed_count() == 2

    async def test_active_session_has_no_report(
        self,
        handler: IdleCheckReconcileHandler,
        first_session_id: SessionId,
        lifetime_bound: BoundCheckerData,
        network_bound: BoundCheckerData,
        lifetime_checker: FakeChecker,
        network_checker: FakeChecker,
    ) -> None:
        reconcile_info = IdleCheckReconcileInfo(
            batch=IdleCheckBatchData(
                targets=(_target(first_session_id, [lifetime_bound, network_bound]),)
            ),
            current_time=_NOW,
        )

        result = await handler.execute(reconcile_info)

        assert result.reports == []
        expected_call = [(lifetime_bound.checker.checker_id, [first_session_id])]
        assert lifetime_checker.judge_calls == [expected_call]
        assert network_checker.judge_calls == [
            [(network_bound.checker.checker_id, [first_session_id])]
        ]

    async def test_skips_unimplemented_checker_types(
        self,
        first_session_id: SessionId,
        lifetime_bound: BoundCheckerData,
        network_bound: BoundCheckerData,
        lifetime_checker: FakeChecker,
    ) -> None:
        lifetime_checker.idle_session_ids = {first_session_id}
        handler = IdleCheckReconcileHandler({CheckerType.SESSION_LIFETIME: lifetime_checker})
        reconcile_info = IdleCheckReconcileInfo(
            batch=IdleCheckBatchData(
                targets=(_target(first_session_id, [network_bound, lifetime_bound]),)
            ),
            current_time=_NOW,
        )

        result = await handler.execute(reconcile_info)

        assert result.reports == [
            IdleCheckReport(
                session_id=first_session_id,
                reasons=[
                    IdleReason(
                        checker_id=lifetime_bound.checker.checker_id,
                        message="max lifetime exceeded",
                    ),
                ],
            ),
        ]
