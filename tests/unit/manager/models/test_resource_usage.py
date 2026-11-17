from __future__ import annotations

from datetime import UTC, datetime, timedelta, timezone, tzinfo
from unittest.mock import AsyncMock
from uuid import UUID

import pytest

from ai.backend.common.clients.valkey_client.valkey_stat.client import ValkeyStatClient
from ai.backend.common.types import KernelId, SessionId
from ai.backend.manager.data.kernel.types import KernelStatus
from ai.backend.manager.models.kernel.row import KernelRow
from ai.backend.manager.models.resource_usage import parse_resource_usage_groups
from ai.backend.manager.models.session.row import SessionRow

_CREATED_AT = datetime(2026, 1, 1, 23, 30, tzinfo=UTC)
_KST = timezone(timedelta(hours=9))
_SESSION_ID = SessionId(UUID("00000000-0000-0000-0000-0000000000b1"))


@pytest.fixture
def session_row() -> SessionRow:
    return SessionRow(
        id=_SESSION_ID,
        name="session",
        access_key="access-key",
        domain_name="default",
        user_uuid=UUID("00000000-0000-0000-0000-0000000000c1"),
    )


@pytest.fixture
def terminated_kernel(session_row: SessionRow) -> KernelRow:
    return KernelRow(
        id=KernelId(UUID("00000000-0000-0000-0000-0000000000a1")),
        session_id=_SESSION_ID,
        session=session_row,
        status=KernelStatus.TERMINATED,
        created_at=_CREATED_AT,
        terminated_at=_CREATED_AT + timedelta(hours=1),
    )


@pytest.fixture
def running_kernel(session_row: SessionRow) -> KernelRow:
    return KernelRow(
        id=KernelId(UUID("00000000-0000-0000-0000-0000000000a2")),
        session_id=_SESSION_ID,
        session=session_row,
        status=KernelStatus.RUNNING,
        created_at=_CREATED_AT,
        terminated_at=None,
    )


@pytest.fixture
def valkey_stat_client() -> AsyncMock:
    client = AsyncMock(spec=ValkeyStatClient)
    client.get_user_kernel_statistics_batch.return_value = [None]
    return client


class TestParseResourceUsageGroups:
    @pytest.mark.parametrize(
        ("local_tz", "used_days"),
        [(UTC, 2), (_KST, 1)],
        ids=["crosses_midnight_in_utc", "same_day_in_kst"],
    )
    async def test_a_terminated_kernel_counts_its_time_and_local_days(
        self,
        terminated_kernel: KernelRow,
        valkey_stat_client: AsyncMock,
        local_tz: tzinfo,
        used_days: int,
    ) -> None:
        groups = await parse_resource_usage_groups(
            [terminated_kernel], {}, valkey_stat_client, local_tz
        )

        assert len(groups) == 1
        assert groups[0].used_time == "1:00:00"
        assert groups[0].used_days == used_days

    async def test_a_running_kernel_has_no_used_time(
        self,
        running_kernel: KernelRow,
        valkey_stat_client: AsyncMock,
    ) -> None:
        groups = await parse_resource_usage_groups([running_kernel], {}, valkey_stat_client, UTC)

        assert len(groups) == 1
        assert groups[0].used_time is None
        assert groups[0].used_days is None
