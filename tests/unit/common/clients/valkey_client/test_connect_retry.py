from __future__ import annotations

import logging
from collections.abc import AsyncIterator
from contextlib import AbstractAsyncContextManager, asynccontextmanager
from typing import override

import pytest
from glide import GlideClient

from ai.backend.common.clients.valkey_client.client import (
    _CONNECT_MAX_ATTEMPTS,
    AbstractValkeyClient,
    MonitoringValkeyClient,
)
from ai.backend.common.exception import ClientNotConnectedError


class FakeValkeyClient(AbstractValkeyClient):
    """A connectable stub that fails its first ``fail_times`` connect attempts."""

    connect_count: int
    disconnect_count: int
    connected: bool
    _fail_times: int
    _failure: Exception

    def __init__(
        self,
        fail_times: int = 0,
        failure: Exception | None = None,
    ) -> None:
        self.connect_count = 0
        self.disconnect_count = 0
        self.connected = False
        self._fail_times = fail_times
        self._failure = failure or ClientNotConnectedError("connection refused")

    @override
    async def connect(self) -> None:
        if self.connected:
            return
        self.connect_count += 1
        if self.connect_count <= self._fail_times:
            raise self._failure
        self.connected = True

    @override
    async def disconnect(self) -> None:
        self.disconnect_count += 1
        self.connected = False

    @override
    async def ping(self) -> None:
        pass

    @override
    async def need_reconnect(self) -> bool:
        return False

    @override
    async def check_health(self) -> None:
        pass

    @override
    def client(self) -> AbstractAsyncContextManager[GlideClient]:
        raise NotImplementedError


@pytest.fixture
def recorded_delays(monkeypatch: pytest.MonkeyPatch) -> list[float]:
    """Collapse the retry backoff to zero wall-clock time, recording each delay."""
    delays: list[float] = []

    async def fake_sleep(delay: float) -> None:
        delays.append(delay)

    monkeypatch.setattr(
        "ai.backend.common.resilience.policies.retry.asyncio.sleep",
        fake_sleep,
    )
    return delays


@asynccontextmanager
async def _client(
    operation: FakeValkeyClient,
    monitor: FakeValkeyClient,
) -> AsyncIterator[MonitoringValkeyClient]:
    client = MonitoringValkeyClient(operation, monitor)
    try:
        yield client
    finally:
        if client._monitor_task is not None:
            await client.disconnect()


class TestMonitoringValkeyClientConnectRetry:
    """Initial-connection retry behavior of MonitoringValkeyClient.connect()."""

    async def test_connect_retries_until_valkey_is_reachable(
        self,
        recorded_delays: list[float],
    ) -> None:
        """Scenario 1: Valkey rejects the first attempts, then accepts."""
        operation = FakeValkeyClient(fail_times=3)
        monitor = FakeValkeyClient()

        async with _client(operation, monitor) as client:
            await client.connect()

            assert operation.connect_count == 4
            assert monitor.connected
            assert client._monitor_task is not None
            # Exponential backoff, capped at _CONNECT_RETRY_MAX_DELAY.
            assert recorded_delays == [1.0, 2.0, 4.0]

    async def test_connect_gives_up_with_the_original_error(
        self,
        recorded_delays: list[float],
    ) -> None:
        """Scenario 2: Valkey stays unreachable for the whole budget."""
        failure = ClientNotConnectedError("timed out")
        operation = FakeValkeyClient(fail_times=99, failure=failure)
        monitor = FakeValkeyClient()

        async with _client(operation, monitor) as client:
            with pytest.raises(ClientNotConnectedError) as exc_info:
                await client.connect()

        # The caller sees the underlying connection error, not a retry-wrapper error.
        assert exc_info.value is failure
        assert operation.connect_count == _CONNECT_MAX_ATTEMPTS
        assert len(recorded_delays) == _CONNECT_MAX_ATTEMPTS - 1
        # No monitor task and no open connection are left behind.
        assert monitor.connect_count == 0
        assert not operation.connected
        assert not monitor.connected

    async def test_healthy_connect_does_not_sleep(
        self,
        recorded_delays: list[float],
    ) -> None:
        """Scenario 3: no startup regression when Valkey is already up."""
        operation = FakeValkeyClient()
        monitor = FakeValkeyClient()

        async with _client(operation, monitor) as client:
            await client.connect()

            assert operation.connect_count == 1
            assert monitor.connect_count == 1
            assert recorded_delays == []

    async def test_retry_closes_the_half_connected_operation_client(
        self,
        recorded_delays: list[float],
    ) -> None:
        """Scenario 4: the monitor client fails after the operation client succeeded."""
        operation = FakeValkeyClient()
        monitor = FakeValkeyClient(fail_times=2)

        async with _client(operation, monitor) as client:
            await client.connect()

            # Each failed attempt drops the operation client that did connect,
            # so a retry never stacks a second GLIDE connection on top of it.
            assert operation.disconnect_count == 2
            assert operation.connect_count == 3
            assert operation.connected
            assert recorded_delays == [1.0, 2.0]

    async def test_exhausted_monitor_retries_leave_nothing_open(
        self,
        recorded_delays: list[float],
    ) -> None:
        """The operation client must not outlive a connect() that ultimately raises."""
        operation = FakeValkeyClient()
        monitor = FakeValkeyClient(fail_times=99)

        async with _client(operation, monitor) as client:
            with pytest.raises(ClientNotConnectedError):
                await client.connect()

        assert not operation.connected
        assert not monitor.connected
        assert operation.disconnect_count == _CONNECT_MAX_ATTEMPTS
        assert client._monitor_task is None

    async def test_non_retryable_error_fails_fast(
        self,
        recorded_delays: list[float],
    ) -> None:
        """Scenario 5: a programming error must not burn the retry budget."""
        operation = FakeValkeyClient(fail_times=99, failure=TypeError("bad target"))
        monitor = FakeValkeyClient()

        async with _client(operation, monitor) as client:
            with pytest.raises(TypeError):
                await client.connect()

        assert operation.connect_count == 1
        assert recorded_delays == []

    async def test_failed_attempts_are_logged(
        self,
        recorded_delays: list[float],
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        """Scenario 6: a multi-second startup stall must not be silent."""
        operation = FakeValkeyClient(fail_times=2)
        monitor = FakeValkeyClient()

        with caplog.at_level(
            logging.WARNING, logger="ai.backend.common.clients.valkey_client.client"
        ):
            async with _client(operation, monitor) as client:
                await client.connect()

        warnings = [r for r in caplog.records if r.levelno == logging.WARNING]
        assert len(warnings) == 2
        # The attempt number is named, and no attempt claims a retry that will
        # not happen — RetryPolicy, not this log line, decides that.
        assert "attempt 1/6" in warnings[0].getMessage()
        assert "attempt 2/6" in warnings[1].getMessage()
        assert "retrying" not in warnings[0].getMessage()
