from __future__ import annotations

from collections.abc import Sequence
from datetime import UTC, datetime
from typing import Final, override
from uuid import uuid4

import pytest

from ai.backend.common.data.idle_checker.types import (
    CheckerType,
    IdleCheckerSpec,
    IdleCheckPhase,
    NetworkTimeoutSpec,
    SessionLifetimeSpec,
)
from ai.backend.common.identifier.idle_checker import IdleCheckerID
from ai.backend.common.types import SessionId, SessionTypes
from ai.backend.manager.data.idle_checker.types import IdleCheckSession
from ai.backend.manager.errors.common import InternalServerError
from ai.backend.manager.repositories.idle_checker.types import (
    IdleCheckAssignmentData,
    IdleCheckBatchData,
    IdleCheckerDefinitionData,
)
from ai.backend.manager.sokovan.idle_check.checkers.base import (
    CheckerAssignment,
    IdleChecker,
    IdleCheckerContext,
    IdleJudgment,
)
from ai.backend.manager.sokovan.idle_check.handlers.reconcile import IdleCheckReconcileHandler
from ai.backend.manager.sokovan.idle_check.types import IdleCheckReconcileInfo

_NOW = datetime(2026, 1, 2, tzinfo=UTC)

_SPECS: Final[dict[CheckerType, IdleCheckerSpec]] = {
    CheckerType.SESSION_LIFETIME: IdleCheckerSpec(
        type=CheckerType.SESSION_LIFETIME,
        session_lifetime=SessionLifetimeSpec(max_lifetime_seconds=3600),
    ),
    CheckerType.NETWORK_TIMEOUT: IdleCheckerSpec(
        type=CheckerType.NETWORK_TIMEOUT,
        network=NetworkTimeoutSpec(),
    ),
}


class FakeChecker(IdleChecker):
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
        self.judge_calls.append([
            (
                assignment.definition.checker_id,
                [session.session_id for session in assignment.sessions],
            )
            for assignment in assignments
        ])
        if self.should_fail:
            raise InternalServerError("Fake checker failed")
        return [
            IdleJudgment(
                checker_id=assignment.definition.checker_id,
                session_id=session.session_id,
                expire_at=_NOW,
                status=(
                    IdleCheckPhase.IDLE
                    if session.session_id in self.idle_session_ids
                    else IdleCheckPhase.ACTIVE
                ),
                message=self._message,
            )
            for assignment in assignments
            for session in assignment.sessions
        ]


def _checker_definition(checker_type: CheckerType) -> IdleCheckerDefinitionData:
    return IdleCheckerDefinitionData(
        checker_id=IdleCheckerID(uuid4()),
        checker_type=checker_type,
        target_session_types=frozenset({SessionTypes.INTERACTIVE}),
        spec=_SPECS[checker_type],
    )


def _assignment(
    session_id: SessionId,
    checker: IdleCheckerDefinitionData,
) -> IdleCheckAssignmentData:
    return IdleCheckAssignmentData(
        session=IdleCheckSession(
            session_id=session_id,
            created_at=datetime(2026, 1, 1, tzinfo=UTC),
            starts_at=None,
        ),
        checker=checker,
    )


class TestIdleCheckReconcileHandler:
    @pytest.fixture()
    def first_session_id(self) -> SessionId:
        return SessionId(uuid4())

    @pytest.fixture()
    def second_session_id(self) -> SessionId:
        return SessionId(uuid4())

    @pytest.fixture()
    def lifetime_definition(self) -> IdleCheckerDefinitionData:
        return _checker_definition(CheckerType.SESSION_LIFETIME)

    @pytest.fixture()
    def second_lifetime_definition(self) -> IdleCheckerDefinitionData:
        return _checker_definition(CheckerType.SESSION_LIFETIME)

    @pytest.fixture()
    def network_definition(self) -> IdleCheckerDefinitionData:
        return _checker_definition(CheckerType.NETWORK_TIMEOUT)

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
        lifetime_definition: IdleCheckerDefinitionData,
        second_lifetime_definition: IdleCheckerDefinitionData,
        network_definition: IdleCheckerDefinitionData,
        lifetime_checker: FakeChecker,
        network_checker: FakeChecker,
    ) -> None:
        reconcile_info = IdleCheckReconcileInfo(
            batch=IdleCheckBatchData(
                assignments=[
                    _assignment(first_session_id, lifetime_definition),
                    _assignment(second_session_id, lifetime_definition),
                    _assignment(second_session_id, second_lifetime_definition),
                    _assignment(second_session_id, network_definition),
                ]
            ),
            current_time=_NOW,
        )

        await handler.execute(reconcile_info)

        assert lifetime_checker.judge_calls == [
            [
                (lifetime_definition.checker_id, [first_session_id, second_session_id]),
                (second_lifetime_definition.checker_id, [second_session_id]),
            ]
        ]
        assert network_checker.judge_calls == [
            [(network_definition.checker_id, [second_session_id])]
        ]
        expected_context = IdleCheckerContext(current_time=_NOW)
        assert lifetime_checker.judge_contexts == [expected_context]
        assert network_checker.judge_contexts == [expected_context]

    async def test_returns_all_judgments(
        self,
        handler: IdleCheckReconcileHandler,
        first_session_id: SessionId,
        second_session_id: SessionId,
        lifetime_definition: IdleCheckerDefinitionData,
        network_definition: IdleCheckerDefinitionData,
        lifetime_checker: FakeChecker,
        network_checker: FakeChecker,
    ) -> None:
        lifetime_checker.idle_session_ids = {first_session_id, second_session_id}
        network_checker.idle_session_ids = {first_session_id}
        reconcile_info = IdleCheckReconcileInfo(
            batch=IdleCheckBatchData(
                assignments=[
                    _assignment(first_session_id, lifetime_definition),
                    _assignment(first_session_id, network_definition),
                    _assignment(second_session_id, lifetime_definition),
                ]
            ),
            current_time=_NOW,
        )

        result = await handler.execute(reconcile_info)

        assert result.judgments == [
            IdleJudgment(
                checker_id=lifetime_definition.checker_id,
                session_id=first_session_id,
                expire_at=_NOW,
                status=IdleCheckPhase.IDLE,
                message="max lifetime exceeded",
            ),
            IdleJudgment(
                checker_id=lifetime_definition.checker_id,
                session_id=second_session_id,
                expire_at=_NOW,
                status=IdleCheckPhase.IDLE,
                message="max lifetime exceeded",
            ),
            IdleJudgment(
                checker_id=network_definition.checker_id,
                session_id=first_session_id,
                expire_at=_NOW,
                status=IdleCheckPhase.IDLE,
                message="no network activity",
            ),
        ]
        assert result.processed_count() == 3

    async def test_returns_non_idle_judgments(
        self,
        handler: IdleCheckReconcileHandler,
        first_session_id: SessionId,
        lifetime_definition: IdleCheckerDefinitionData,
        network_definition: IdleCheckerDefinitionData,
        lifetime_checker: FakeChecker,
        network_checker: FakeChecker,
    ) -> None:
        reconcile_info = IdleCheckReconcileInfo(
            batch=IdleCheckBatchData(
                assignments=[
                    _assignment(first_session_id, lifetime_definition),
                    _assignment(first_session_id, network_definition),
                ]
            ),
            current_time=_NOW,
        )

        result = await handler.execute(reconcile_info)

        assert len(result.judgments) == 2
        assert all(judgment.status is IdleCheckPhase.ACTIVE for judgment in result.judgments)
        assert all(judgment.expire_at == _NOW for judgment in result.judgments)
        expected_call = [(lifetime_definition.checker_id, [first_session_id])]
        assert lifetime_checker.judge_calls == [expected_call]
        assert network_checker.judge_calls == [
            [(network_definition.checker_id, [first_session_id])]
        ]

    async def test_skips_unimplemented_checker_types(
        self,
        first_session_id: SessionId,
        lifetime_definition: IdleCheckerDefinitionData,
        network_definition: IdleCheckerDefinitionData,
        lifetime_checker: FakeChecker,
    ) -> None:
        lifetime_checker.idle_session_ids = {first_session_id}
        handler = IdleCheckReconcileHandler({CheckerType.SESSION_LIFETIME: lifetime_checker})
        reconcile_info = IdleCheckReconcileInfo(
            batch=IdleCheckBatchData(
                assignments=[
                    _assignment(first_session_id, network_definition),
                    _assignment(first_session_id, lifetime_definition),
                ]
            ),
            current_time=_NOW,
        )

        result = await handler.execute(reconcile_info)

        assert len(result.judgments) == 1
        assert result.judgments[0].checker_id == lifetime_definition.checker_id
