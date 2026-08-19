from __future__ import annotations

from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from ai.backend.common.data.idle_checker.types import IdleCheckPhase
from ai.backend.common.identifier.idle_checker import IdleCheckerID
from ai.backend.common.types import SessionId
from ai.backend.manager.repositories.idle_checker.repository import IdleCheckerRepository
from ai.backend.manager.repositories.idle_checker.types import IdleJudgmentData
from ai.backend.manager.sokovan.idle_check.applier import IdleCheckApplier
from ai.backend.manager.sokovan.idle_check.types import IdleCheckResult

_EXPIRE_AT = datetime(2026, 1, 2, tzinfo=UTC)


class TestIdleCheckApplier:
    @pytest.fixture
    def repository(self) -> AsyncMock:
        return AsyncMock(spec=IdleCheckerRepository)

    @pytest.fixture
    def applier(self, repository: AsyncMock) -> IdleCheckApplier:
        return IdleCheckApplier(repository)

    @pytest.fixture
    def judgments(self) -> list[IdleJudgmentData]:
        return [
            IdleJudgmentData(
                session_id=SessionId(uuid4()),
                checker_id=IdleCheckerID(uuid4()),
                status=IdleCheckPhase.ACTIVE,
                expire_at=_EXPIRE_AT,
                message="activity detected",
            ),
            IdleJudgmentData(
                session_id=SessionId(uuid4()),
                checker_id=IdleCheckerID(uuid4()),
                status=IdleCheckPhase.IDLE,
                expire_at=_EXPIRE_AT,
                message="no activity",
            ),
            IdleJudgmentData(
                session_id=SessionId(uuid4()),
                checker_id=IdleCheckerID(uuid4()),
                status=IdleCheckPhase.IDLE_EXPIRED,
                expire_at=_EXPIRE_AT,
                message="idle expired",
            ),
        ]

    @pytest.fixture
    def apply_input(self, judgments: list[IdleJudgmentData]) -> MagicMock:
        apply_input = MagicMock()
        apply_input.result = IdleCheckResult(judgments=judgments)
        return apply_input

    @pytest.fixture
    def empty_apply_input(self) -> MagicMock:
        apply_input = MagicMock()
        apply_input.result = IdleCheckResult()
        return apply_input

    async def test_persists_judgments(
        self,
        applier: IdleCheckApplier,
        repository: AsyncMock,
        judgments: list[IdleJudgmentData],
        apply_input: MagicMock,
    ) -> None:
        await applier.apply(apply_input)

        repository.batch_apply_session_idle_check_judgments.assert_awaited_once_with(judgments)

    async def test_skips_empty_result(
        self,
        applier: IdleCheckApplier,
        repository: AsyncMock,
        empty_apply_input: MagicMock,
    ) -> None:
        await applier.apply(empty_apply_input)

        repository.batch_apply_session_idle_check_judgments.assert_not_awaited()
