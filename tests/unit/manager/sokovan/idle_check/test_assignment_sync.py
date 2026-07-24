from __future__ import annotations

from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from ai.backend.common.identifier.idle_checker import IdleCheckerID
from ai.backend.common.types import SessionId
from ai.backend.manager.repositories.idle_checker.repository import IdleCheckerRepository
from ai.backend.manager.repositories.idle_checker.types import SessionIdleCheckPair
from ai.backend.manager.sokovan.idle_check.assignment_sync.applier import (
    IdleCheckAssignmentSyncApplier,
)
from ai.backend.manager.sokovan.idle_check.assignment_sync.types import (
    IdleCheckAssignmentSyncReconcileInfo,
    IdleCheckAssignmentSyncResult,
)
from ai.backend.manager.sokovan.idle_check.handlers.assignment_sync import (
    IdleCheckAssignmentSyncHandler,
)


@pytest.fixture
def current_time() -> datetime:
    return datetime(2026, 1, 1, tzinfo=UTC)


@pytest.fixture
def pair_to_create() -> SessionIdleCheckPair:
    return SessionIdleCheckPair(
        session_id=SessionId(uuid4()),
        checker_id=IdleCheckerID(uuid4()),
    )


@pytest.fixture
def pair_to_delete() -> SessionIdleCheckPair:
    return SessionIdleCheckPair(
        session_id=SessionId(uuid4()),
        checker_id=IdleCheckerID(uuid4()),
    )


@pytest.fixture
def pair_to_keep() -> SessionIdleCheckPair:
    return SessionIdleCheckPair(
        session_id=SessionId(uuid4()),
        checker_id=IdleCheckerID(uuid4()),
    )


class TestIdleCheckAssignmentSyncHandler:
    @pytest.fixture
    def handler(self) -> IdleCheckAssignmentSyncHandler:
        return IdleCheckAssignmentSyncHandler()

    async def test_computes_create_and_delete_pairs(
        self,
        handler: IdleCheckAssignmentSyncHandler,
        current_time: datetime,
        pair_to_create: SessionIdleCheckPair,
        pair_to_delete: SessionIdleCheckPair,
        pair_to_keep: SessionIdleCheckPair,
    ) -> None:
        result = await handler.execute(
            IdleCheckAssignmentSyncReconcileInfo(
                desired_pairs=[pair_to_create, pair_to_keep, pair_to_keep],
                current_pairs=[pair_to_delete, pair_to_keep],
                current_time=current_time,
            )
        )

        assert set(result.pairs_to_create) == {pair_to_create}
        assert set(result.pairs_to_delete) == {pair_to_delete}
        assert result.current_time == current_time
        assert result.processed_count() == 2


class TestIdleCheckAssignmentSyncApplier:
    @pytest.fixture
    def repository(self) -> AsyncMock:
        return AsyncMock(spec=IdleCheckerRepository)

    @pytest.fixture
    def applier(self, repository: AsyncMock) -> IdleCheckAssignmentSyncApplier:
        return IdleCheckAssignmentSyncApplier(repository)

    async def test_applies_assignment_changes(
        self,
        applier: IdleCheckAssignmentSyncApplier,
        repository: AsyncMock,
        current_time: datetime,
        pair_to_create: SessionIdleCheckPair,
        pair_to_delete: SessionIdleCheckPair,
    ) -> None:
        apply_input = MagicMock()
        apply_input.result = IdleCheckAssignmentSyncResult(
            current_time=current_time,
            pairs_to_create=[pair_to_create],
            pairs_to_delete=[pair_to_delete],
        )

        await applier.apply(apply_input)

        repository.sync_session_idle_check_assignments.assert_awaited_once_with(
            [pair_to_create],
            [pair_to_delete],
            current_time,
        )

    async def test_skips_empty_assignment_changes(
        self,
        applier: IdleCheckAssignmentSyncApplier,
        repository: AsyncMock,
        current_time: datetime,
    ) -> None:
        apply_input = MagicMock()
        apply_input.result = IdleCheckAssignmentSyncResult(current_time=current_time)

        await applier.apply(apply_input)

        repository.sync_session_idle_check_assignments.assert_not_awaited()
