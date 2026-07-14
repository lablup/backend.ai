from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest
from pytest_mock import MockerFixture

from ai.backend.common.data.idle_checker.types import (
    CheckerType,
    IdleCheckerSpec,
    SessionLifetimeSpec,
)
from ai.backend.common.data.permission.types import ScopeType
from ai.backend.common.identifier.idle_checker import IdleCheckerID
from ai.backend.common.types import SessionId, SessionTypes
from ai.backend.manager.data.idle_checker.types import IdleCheckSession
from ai.backend.manager.data.permission.id import ScopeId
from ai.backend.manager.defs import LockID
from ai.backend.manager.repositories.idle_checker.repository import IdleCheckerRepository
from ai.backend.manager.repositories.idle_checker.types import (
    BoundCheckerData,
    IdleCheckBatchData,
    IdleCheckerDefinitionData,
    IdleCheckTargetData,
)
from ai.backend.manager.sokovan.idle_check.checkers.session_lifetime import (
    SessionLifetimeChecker,
)
from ai.backend.manager.sokovan.reconciler.base import ReconcilerStageRegistration
from ai.backend.manager.sokovan.stages.factory import build_reconciler_coordinator
from ai.backend.manager.sokovan.stages.idle_check import build_idle_check_stage


@dataclass(frozen=True)
class SessionLifetimeStageSetup:
    registration: ReconcilerStageRegistration
    checker: AsyncMock


class TestBuildIdleCheckStage:
    @pytest.fixture()
    def idle_check_batch(self) -> IdleCheckBatchData:
        checker_id = IdleCheckerID(uuid4())
        session = IdleCheckSession(
            session_id=SessionId(uuid4()),
            created_at=datetime(2026, 1, 1, tzinfo=UTC),
            starts_at=datetime(2026, 1, 1, tzinfo=UTC),
        )
        definition = IdleCheckerDefinitionData(
            checker_id=checker_id,
            checker_type=CheckerType.SESSION_LIFETIME,
            target_session_types=frozenset({SessionTypes.INTERACTIVE}),
            spec=IdleCheckerSpec(
                type=CheckerType.SESSION_LIFETIME,
                session_lifetime=SessionLifetimeSpec(max_lifetime_seconds=3600),
            ),
        )
        return IdleCheckBatchData(
            targets=(
                IdleCheckTargetData(
                    session=session,
                    checkers=(
                        BoundCheckerData(
                            scope=ScopeId(ScopeType.DOMAIN, str(uuid4())),
                            binding_created_at=datetime(2026, 1, 1, tzinfo=UTC),
                            checker=definition,
                        ),
                    ),
                ),
            )
        )

    @pytest.fixture()
    def idle_checker_repository(self, idle_check_batch: IdleCheckBatchData) -> AsyncMock:
        repository = AsyncMock(spec=IdleCheckerRepository)
        repository.fetch_idle_check_batch.return_value = idle_check_batch
        return repository

    @pytest.fixture()
    def session_lifetime_stage(
        self,
        mocker: MockerFixture,
        idle_checker_repository: AsyncMock,
    ) -> SessionLifetimeStageSetup:
        checker = AsyncMock(spec=SessionLifetimeChecker)
        checker.judge.return_value = ()
        mocker.patch(
            "ai.backend.manager.sokovan.stages.idle_check.SessionLifetimeChecker",
            return_value=checker,
        )
        return SessionLifetimeStageSetup(
            registration=build_idle_check_stage(idle_checker_repository),
            checker=checker,
        )

    def test_registration_metadata(self) -> None:
        registration = build_idle_check_stage(MagicMock())
        assert registration.reconcile_type == "idle_check"
        assert registration.stage.lock_id == LockID.LOCKID_IDLE_CHECK_RECONCILE
        assert registration.task_spec.reconcile_type == "idle_check"
        assert registration.task_spec.short_interval == 10.0
        assert registration.task_spec.long_interval == 60.0

    async def test_runs_session_lifetime_checker(
        self, session_lifetime_stage: SessionLifetimeStageSetup
    ) -> None:
        await session_lifetime_stage.registration.stage.run()

        session_lifetime_stage.checker.judge.assert_awaited_once()


class TestFactoryRegistration:
    def test_idle_check_is_registered(self) -> None:
        _, task_specs = build_reconciler_coordinator(
            replica_group_repository=MagicMock(),
            idle_checker_repository=MagicMock(),
            valkey_schedule=MagicMock(),
            lock_factory=MagicMock(),
            config_provider=MagicMock(),
        )
        assert "idle_check" in {task_spec.reconcile_type for task_spec in task_specs}
