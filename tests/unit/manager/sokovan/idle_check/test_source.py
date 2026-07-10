from __future__ import annotations

from datetime import UTC
from unittest.mock import AsyncMock, MagicMock

from ai.backend.manager.data.session.types import SessionStatus
from ai.backend.manager.sokovan.idle_check.source import IdleCheckSource
from ai.backend.manager.sokovan.idle_check.types import IdleCheckCategory, IdleCheckTargetStatuses


class TestIdleCheckSource:
    async def test_returns_fetched_batch_with_current_time(self) -> None:
        batch = MagicMock()
        repository = MagicMock()
        repository.fetch_idle_check_batch = AsyncMock(return_value=batch)
        target_statuses = IdleCheckTargetStatuses(
            session_statuses=frozenset([SessionStatus.RUNNING])
        )

        reconcile_info = await IdleCheckSource(repository).fetch_reconcile_info(
            IdleCheckCategory.IDLE, target_statuses
        )

        assert reconcile_info.batch is batch
        repository.fetch_idle_check_batch.assert_awaited_once_with(target_statuses.session_statuses)
        assert reconcile_info.current_time.tzinfo == UTC
