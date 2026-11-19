from __future__ import annotations

import importlib
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Any
from unittest.mock import AsyncMock, MagicMock

import pytest

from ai.backend.common.clients.valkey_client.reconnect import ValkeyReconnectErrorClassifier
from ai.backend.common.clients.valkey_client.valkey_session.client import ValkeySessionClient
from ai.backend.common.exception import ClientNotConnectedError
from ai.backend.common.resilience import Resilience
from ai.backend.common.resilience.policies.retry import ReconnectRetryPolicy, RetryPolicy

RECONNECT_MODULES = [
    "valkey_artifact",
    "valkey_artifact_registries",
    "valkey_bgtask",
    "valkey_container_log",
    "valkey_image",
    "valkey_live",
    "valkey_rate_limit",
    "valkey_schedule",
    "valkey_session",
    "valkey_stat",
    "valkey_storage_volume",
    "valkey_stream",
    "valkey_tus",
    "valkey_volume_stats",
]


def _resilience_of(module_name: str) -> Resilience:
    module = importlib.import_module(
        f"ai.backend.common.clients.valkey_client.{module_name}.client"
    )
    resilience = getattr(module, f"{module_name}_resilience")
    assert isinstance(resilience, Resilience)
    return resilience


def _policies_of(module_name: str) -> list[Any]:
    return list(_resilience_of(module_name)._policies)


class TestReconnectDeclaration:
    @pytest.mark.parametrize("module_name", RECONNECT_MODULES)
    def test_uses_reconnect_retry_policy(self, module_name: str) -> None:
        policies = _policies_of(module_name)
        reconnect = [p for p in policies if isinstance(p, ReconnectRetryPolicy)]
        assert len(reconnect) == 1
        assert isinstance(reconnect[0]._classifier, ValkeyReconnectErrorClassifier)
        assert not any(type(p) is RetryPolicy for p in policies)

    def test_valkey_leader_keeps_retry_policy(self) -> None:
        policies = _policies_of("valkey_leader")
        assert any(type(p) is RetryPolicy for p in policies)
        assert not any(isinstance(p, ReconnectRetryPolicy) for p in policies)

    def test_valkey_lock_has_no_retry(self) -> None:
        policies = _policies_of("valkey_lock")
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
