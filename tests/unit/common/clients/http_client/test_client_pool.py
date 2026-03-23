from __future__ import annotations

import time
from typing import cast
from unittest.mock import AsyncMock, MagicMock

import aiohttp

from ai.backend.common.clients.http_client.client_pool import (
    ClientKey,
    ClientPool,
    SyncClientPool,
)


def _mock_factory(key: ClientKey, /) -> aiohttp.ClientSession:
    """Create a mock aiohttp.ClientSession for testing."""
    session = MagicMock(spec=aiohttp.ClientSession)
    session.close = AsyncMock()
    return session


def _close_mock(session: aiohttp.ClientSession) -> AsyncMock:
    """Extract the AsyncMock for close() from a mock session."""
    return cast(AsyncMock, session.close)


class TestBaseClientPool:
    """Tests for shared BaseClientPool behavior."""

    def test_load_creates_new_session(self) -> None:
        pool = SyncClientPool(_mock_factory, cleanup_interval_seconds=9999)
        try:
            key = ClientKey(endpoint="http://localhost:8080", domain="test")
            session = pool.load_client_session(key)
            assert session is not None
        finally:
            pool.close()

    def test_load_reuses_existing_session(self) -> None:
        pool = SyncClientPool(_mock_factory, cleanup_interval_seconds=9999)
        try:
            key = ClientKey(endpoint="http://localhost:8080", domain="test")
            s1 = pool.load_client_session(key)
            s2 = pool.load_client_session(key)
            assert s1 is s2
        finally:
            pool.close()

    def test_different_keys_get_different_sessions(self) -> None:
        pool = SyncClientPool(_mock_factory, cleanup_interval_seconds=9999)
        try:
            k1 = ClientKey(endpoint="http://host1:8080", domain="test")
            k2 = ClientKey(endpoint="http://host2:8080", domain="test")
            s1 = pool.load_client_session(k1)
            s2 = pool.load_client_session(k2)
            assert s1 is not s2
        finally:
            pool.close()


class TestClientPool:
    """Tests for the async ClientPool."""

    async def test_close_clears_sessions(self) -> None:
        pool = ClientPool(_mock_factory)
        key = ClientKey(endpoint="http://localhost:8080", domain="test")
        session = pool.load_client_session(key)
        await pool.close()
        _close_mock(session).assert_awaited_once()

    async def test_close_is_idempotent(self) -> None:
        pool = ClientPool(_mock_factory)
        await pool.close()
        # Should not raise on second close
        await pool.close()


class TestSyncClientPool:
    """Tests for the SyncClientPool."""

    def test_close_stops_worker_thread(self) -> None:
        pool = SyncClientPool(_mock_factory, cleanup_interval_seconds=9999)
        assert pool._worker_thread.is_alive()
        pool.close()
        assert not pool._worker_thread.is_alive()

    def test_close_closes_sessions(self) -> None:
        pool = SyncClientPool(_mock_factory, cleanup_interval_seconds=9999)
        key = ClientKey(endpoint="http://localhost:8080", domain="test")
        session = pool.load_client_session(key)
        pool.close()
        _close_mock(session).assert_awaited_once()

    def test_close_is_idempotent(self) -> None:
        pool = SyncClientPool(_mock_factory, cleanup_interval_seconds=9999)
        pool.close()
        # Should not raise on second close (worker thread already stopped)
        pool.close()

    def test_repr(self) -> None:
        pool = SyncClientPool(_mock_factory)
        r = repr(pool)
        assert "SyncClientPool" in r
        pool.close()

    def test_evicts_stale_sessions_on_load(self) -> None:
        pool = SyncClientPool(_mock_factory, cleanup_interval_seconds=1)
        try:
            key = ClientKey(endpoint="http://localhost:8080", domain="test")
            stale_session = pool.load_client_session(key)

            # Simulate time passing beyond the cleanup interval
            past_time = time.perf_counter() - 2
            pool._clients[key].last_used = past_time

            # Loading a different key should trigger eviction of the stale session
            key2 = ClientKey(endpoint="http://other:8080", domain="test")
            pool.load_client_session(key2)

            assert key not in pool._clients
            _close_mock(stale_session).assert_awaited_once()
        finally:
            pool.close()

    def test_does_not_evict_fresh_sessions(self) -> None:
        pool = SyncClientPool(_mock_factory, cleanup_interval_seconds=9999)
        try:
            key = ClientKey(endpoint="http://localhost:8080", domain="test")
            session = pool.load_client_session(key)

            # Load again — session should still be there
            key2 = ClientKey(endpoint="http://other:8080", domain="test")
            pool.load_client_session(key2)

            assert key in pool._clients
            _close_mock(session).assert_not_awaited()
        finally:
            pool.close()
