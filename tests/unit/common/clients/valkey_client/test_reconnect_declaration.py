from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Any
from unittest.mock import AsyncMock, MagicMock

import pytest

from ai.backend.common.clients.valkey_client.reconnect import ValkeyReconnectErrorClassifier
from ai.backend.common.clients.valkey_client.valkey_artifact.client import (
    valkey_artifact_resilience,
)
from ai.backend.common.clients.valkey_client.valkey_artifact_registries.client import (
    valkey_artifact_registries_resilience,
)
from ai.backend.common.clients.valkey_client.valkey_bgtask.client import valkey_bgtask_resilience
from ai.backend.common.clients.valkey_client.valkey_container_log.client import (
    valkey_container_log_resilience,
)
from ai.backend.common.clients.valkey_client.valkey_image.client import valkey_image_resilience
from ai.backend.common.clients.valkey_client.valkey_leader.client import valkey_leader_resilience
from ai.backend.common.clients.valkey_client.valkey_live.client import valkey_live_resilience
from ai.backend.common.clients.valkey_client.valkey_lock.client import valkey_lock_resilience
from ai.backend.common.clients.valkey_client.valkey_rate_limit.client import (
    valkey_rate_limit_resilience,
)
from ai.backend.common.clients.valkey_client.valkey_schedule.client import (
    valkey_schedule_resilience,
)
from ai.backend.common.clients.valkey_client.valkey_session.client import (
    ValkeySessionClient,
    valkey_session_resilience,
)
from ai.backend.common.clients.valkey_client.valkey_stat.client import valkey_stat_resilience
from ai.backend.common.clients.valkey_client.valkey_storage_volume.client import (
    valkey_storage_volume_resilience,
)
from ai.backend.common.clients.valkey_client.valkey_stream.client import valkey_stream_resilience
from ai.backend.common.clients.valkey_client.valkey_tus.client import valkey_tus_resilience
from ai.backend.common.clients.valkey_client.valkey_volume_stats.client import (
    valkey_volume_stats_resilience,
)
from ai.backend.common.exception import ClientNotConnectedError
from ai.backend.common.resilience import Resilience
from ai.backend.common.resilience.policies.retry import ReconnectRetryPolicy, RetryPolicy

RECONNECT_RESILIENCES: dict[str, Resilience] = {
    "valkey_artifact": valkey_artifact_resilience,
    "valkey_artifact_registries": valkey_artifact_registries_resilience,
    "valkey_bgtask": valkey_bgtask_resilience,
    "valkey_container_log": valkey_container_log_resilience,
    "valkey_image": valkey_image_resilience,
    "valkey_live": valkey_live_resilience,
    "valkey_rate_limit": valkey_rate_limit_resilience,
    "valkey_schedule": valkey_schedule_resilience,
    "valkey_session": valkey_session_resilience,
    "valkey_stat": valkey_stat_resilience,
    "valkey_storage_volume": valkey_storage_volume_resilience,
    "valkey_stream": valkey_stream_resilience,
    "valkey_tus": valkey_tus_resilience,
    "valkey_volume_stats": valkey_volume_stats_resilience,
}


def _policies_of(resilience: Resilience) -> list[Any]:
    return list(resilience._policies)


class TestReconnectDeclaration:
    @pytest.mark.parametrize(
        "resilience", list(RECONNECT_RESILIENCES.values()), ids=list(RECONNECT_RESILIENCES)
    )
    def test_uses_reconnect_retry_policy(self, resilience: Resilience) -> None:
        policies = _policies_of(resilience)
        reconnect = [p for p in policies if isinstance(p, ReconnectRetryPolicy)]
        assert len(reconnect) == 1
        assert isinstance(reconnect[0]._classifier, ValkeyReconnectErrorClassifier)
        assert not any(type(p) is RetryPolicy for p in policies)

    def test_valkey_leader_keeps_retry_policy(self) -> None:
        policies = _policies_of(valkey_leader_resilience)
        assert any(type(p) is RetryPolicy for p in policies)
        assert not any(isinstance(p, ReconnectRetryPolicy) for p in policies)

    def test_valkey_lock_has_no_retry(self) -> None:
        policies = _policies_of(valkey_lock_resilience)
        assert not any(isinstance(p, (RetryPolicy, ReconnectRetryPolicy)) for p in policies)


class TestReconnectRetryBehavior:
    async def test_call_is_retried_after_client_not_connected(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        sleep = AsyncMock()
        monkeypatch.setattr("ai.backend.common.resilience.policies.retry.asyncio.sleep", sleep)
        conn = MagicMock()
        conn.get = AsyncMock(return_value=b"history")
        attempts = 0

        @asynccontextmanager
        async def fake_client() -> AsyncIterator[MagicMock]:
            nonlocal attempts
            attempts += 1
            if attempts <= 2:
                raise ClientNotConnectedError()
            yield conn

        raw_client = MagicMock()
        raw_client.client = fake_client
        session_client = ValkeySessionClient(raw_client)

        result = await session_client.get_login_history("user")

        assert result == b"history"
        assert attempts == 3
        assert sleep.await_count == 2
