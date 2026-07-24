from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from ai.backend.common.data.idle_checker.types import IdleCheckPhase
from ai.backend.common.identifier.idle_checker import IdleCheckerID
from ai.backend.common.types import SessionId
from ai.backend.manager.repositories.idle_checker.repository import IdleCheckerRepository
from ai.backend.manager.repositories.idle_checker.types import (
    InitialGracePeriodBatchData,
    InitialGracePeriodCheckData,
    SessionIdleCheckPair,
)
from ai.backend.manager.sokovan.idle_check.initial_grace.applier import (
    IdleCheckInitialGraceApplier,
)
from ai.backend.manager.sokovan.idle_check.initial_grace.handler import (
    IdleCheckInitialGraceHandler,
)
from ai.backend.manager.sokovan.idle_check.initial_grace.types import (
    IdleCheckInitialGraceReconcileInfo,
    IdleCheckInitialGraceResult,
)


@pytest.fixture
def now() -> datetime:
    return datetime(2026, 1, 1, 0, 1, tzinfo=UTC)


@dataclass(frozen=True)
class InitialGraceCheckParam:
    initial_grace_period_seconds: int
    elapsed_seconds: int
    expected_ready: bool


@dataclass(frozen=True)
class InitialGraceHandlerCase:
    reconcile_info: IdleCheckInitialGraceReconcileInfo
    expected_ready_pairs: list[SessionIdleCheckPair]


class TestIdleCheckInitialGraceHandler:
    @pytest.fixture
    def handler(self) -> IdleCheckInitialGraceHandler:
        return IdleCheckInitialGraceHandler()

    @pytest.fixture
    def handler_case(
        self,
        request: pytest.FixtureRequest,
        now: datetime,
    ) -> InitialGraceHandlerCase:
        param: InitialGraceCheckParam = request.param
        check = InitialGracePeriodCheckData(
            pair=SessionIdleCheckPair(
                session_id=SessionId(uuid4()),
                checker_id=IdleCheckerID(uuid4()),
            ),
            initial_grace_period_seconds=param.initial_grace_period_seconds,
            grace_started_at=now - timedelta(seconds=param.elapsed_seconds),
        )
        reconcile_info = IdleCheckInitialGraceReconcileInfo(
            batch=InitialGracePeriodBatchData(checks=[check], now=now)
        )
        expected_ready_pairs = [check.pair] if param.expected_ready else []
        return InitialGraceHandlerCase(
            reconcile_info=reconcile_info,
            expected_ready_pairs=expected_ready_pairs,
        )

    @pytest.fixture
    def mixed_reconcile_info(self, now: datetime) -> IdleCheckInitialGraceReconcileInfo:
        elapsed_check = InitialGracePeriodCheckData(
            pair=SessionIdleCheckPair(
                session_id=SessionId(uuid4()),
                checker_id=IdleCheckerID(uuid4()),
            ),
            initial_grace_period_seconds=60,
            grace_started_at=now - timedelta(seconds=60),
        )
        waiting_check = InitialGracePeriodCheckData(
            pair=SessionIdleCheckPair(
                session_id=SessionId(uuid4()),
                checker_id=IdleCheckerID(uuid4()),
            ),
            initial_grace_period_seconds=60,
            grace_started_at=now - timedelta(seconds=59),
        )
        return IdleCheckInitialGraceReconcileInfo(
            batch=InitialGracePeriodBatchData(
                checks=[elapsed_check, waiting_check],
                now=now,
            )
        )

    @pytest.fixture
    def empty_reconcile_info(self, now: datetime) -> IdleCheckInitialGraceReconcileInfo:
        return IdleCheckInitialGraceReconcileInfo(
            batch=InitialGracePeriodBatchData(checks=[], now=now)
        )

    @pytest.mark.parametrize(
        "handler_case",
        [
            pytest.param(
                InitialGraceCheckParam(
                    initial_grace_period_seconds=60,
                    elapsed_seconds=61,
                    expected_ready=True,
                ),
                id="elapsed",
            ),
            pytest.param(
                InitialGraceCheckParam(
                    initial_grace_period_seconds=60,
                    elapsed_seconds=60,
                    expected_ready=True,
                ),
                id="boundary",
            ),
            pytest.param(
                InitialGraceCheckParam(
                    initial_grace_period_seconds=60,
                    elapsed_seconds=59,
                    expected_ready=False,
                ),
                id="waiting",
            ),
            pytest.param(
                InitialGraceCheckParam(
                    initial_grace_period_seconds=0,
                    elapsed_seconds=0,
                    expected_ready=True,
                ),
                id="zero-grace",
            ),
        ],
        indirect=True,
    )
    async def test_selects_check_after_grace_period(
        self,
        handler: IdleCheckInitialGraceHandler,
        handler_case: InitialGraceHandlerCase,
    ) -> None:
        result = await handler.execute(handler_case.reconcile_info)

        assert result.pairs_to_ready == handler_case.expected_ready_pairs
        assert result.processed_count() == len(handler_case.expected_ready_pairs)

    async def test_selects_only_elapsed_checks(
        self,
        handler: IdleCheckInitialGraceHandler,
        mixed_reconcile_info: IdleCheckInitialGraceReconcileInfo,
    ) -> None:
        result = await handler.execute(mixed_reconcile_info)

        assert result.pairs_to_ready == [mixed_reconcile_info.batch.checks[0].pair]

    async def test_returns_empty_result_for_empty_batch(
        self,
        handler: IdleCheckInitialGraceHandler,
        empty_reconcile_info: IdleCheckInitialGraceReconcileInfo,
    ) -> None:
        result = await handler.execute(empty_reconcile_info)

        assert result.pairs_to_ready == []
        assert result.processed_count() == 0


class TestIdleCheckInitialGraceApplier:
    @pytest.fixture
    def repository(self) -> AsyncMock:
        return AsyncMock(spec=IdleCheckerRepository)

    @pytest.fixture
    def applier(self, repository: AsyncMock) -> IdleCheckInitialGraceApplier:
        return IdleCheckInitialGraceApplier(repository)

    @pytest.fixture
    def ready_pair(self) -> SessionIdleCheckPair:
        return SessionIdleCheckPair(
            session_id=SessionId(uuid4()),
            checker_id=IdleCheckerID(uuid4()),
        )

    @pytest.fixture
    def ready_apply_input(self, ready_pair: SessionIdleCheckPair) -> MagicMock:
        apply_input = MagicMock()
        apply_input.result = IdleCheckInitialGraceResult(pairs_to_ready=[ready_pair])
        return apply_input

    @pytest.fixture
    def empty_apply_input(self) -> MagicMock:
        apply_input = MagicMock()
        apply_input.result = IdleCheckInitialGraceResult()
        return apply_input

    async def test_marks_ready_pairs(
        self,
        applier: IdleCheckInitialGraceApplier,
        repository: AsyncMock,
        ready_pair: SessionIdleCheckPair,
        ready_apply_input: MagicMock,
    ) -> None:
        await applier.apply(ready_apply_input)

        repository.batch_update_session_idle_check_phase.assert_awaited_once_with(
            [ready_pair],
            from_phase=IdleCheckPhase.NOT_CHECKED,
            to_phase=IdleCheckPhase.READY_TO_CHECK,
        )

    async def test_skips_empty_result(
        self,
        applier: IdleCheckInitialGraceApplier,
        repository: AsyncMock,
        empty_apply_input: MagicMock,
    ) -> None:
        await applier.apply(empty_apply_input)

        repository.batch_update_session_idle_check_phase.assert_not_awaited()
