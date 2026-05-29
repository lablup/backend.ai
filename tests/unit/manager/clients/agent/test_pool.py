"""
Tests for ``AgentClient.connect()`` atomicity and ``AgentClientPool``
caching when peer creation fails before the connection becomes healthy.

Regression: each PeerInvoker allocates a ``zmq.asyncio.Context`` that
owns OS-level IO threads. If ``connect()`` fails after that allocation
and the partially-initialized peer is not released, every retry against
an unreachable agent leaks one ``zmq.asyncio.Context`` plus its
background IO thread.

The fix has two responsibilities, tested independently:

- ``AgentClient.connect()`` is *atomic*: it must release the peer on
  ``__aenter__`` failure so callers never have to remember cleanup on
  every error path.
- ``AgentClientPool._create_entry`` must cache an unhealthy
  ``_CachedEntry`` on failure so subsequent ``acquire()`` calls
  short-circuit via the existing unhealthy-cache branch in
  ``_get_or_create``, instead of repeatedly re-creating peers.
"""

from __future__ import annotations

from typing import Any, cast
from unittest.mock import AsyncMock, MagicMock

import pytest

from ai.backend.common.types import AgentId
from ai.backend.manager.agent_cache import PeerInvoker
from ai.backend.manager.clients.agent.client import AgentClient
from ai.backend.manager.clients.agent.pool import AgentClientPool
from ai.backend.manager.clients.agent.types import AgentPoolSpec
from ai.backend.manager.errors.agent import AgentConnectionUnavailable


class _StubPeer:
    """Stand-in for callosum ``PeerInvoker`` that never opens real zmq.

    ``AgentClient.connect()`` delegates to ``self._peer.__aenter__()`` and
    ``AgentClient.close()`` delegates to ``self._peer.__aexit__(...)``,
    so making this object mimic those hooks lets us drive the pool's
    failure paths without standing up an actual ZMQ transport.
    """

    def __init__(self) -> None:
        self.enter_called = 0
        self.exit_called = 0

    async def __aenter__(self) -> _StubPeer:
        self.enter_called += 1
        raise ConnectionRefusedError("simulated agent unreachable")

    async def __aexit__(self, exc_type: Any, exc: Any, tb: Any) -> None:
        self.exit_called += 1


def _make_pool() -> AgentClientPool:
    agent_cache = MagicMock()
    agent_cache.get_rpc_args = AsyncMock(return_value=("tcp://127.0.0.1:65535", None))
    agent_cache.manager_public_key = b"pk"
    agent_cache.manager_secret_key = b"sk"
    agent_cache.rpc_keepalive_timeout = 60
    spec = AgentPoolSpec(
        health_check_interval=3600.0,
        failure_threshold=3,
        recovery_timeout=60.0,
    )
    return AgentClientPool(agent_cache, spec)


class TestAgentClientConnectAtomicity:
    """``AgentClient.connect()`` releases the peer on failure."""

    async def test_connect_failure_releases_peer(self) -> None:
        stub_peer = _StubPeer()
        client = AgentClient(cast(PeerInvoker, stub_peer), AgentId("i-test"))

        with pytest.raises(ConnectionRefusedError):
            await client.connect()

        # The peer's ``__aexit__`` must run so its ``zmq.asyncio.Context``
        # (and the background IO thread the context owns) is destroyed;
        # otherwise every connect failure leaks one IO thread.
        assert stub_peer.enter_called == 1
        assert stub_peer.exit_called == 1, (
            "connect() must release the partially-initialized peer when "
            "__aenter__ raises, so callers don't need a separate cleanup"
        )


class TestCreateEntryConnectFailure:
    """Covers the connect-failure path of ``AgentClientPool._create_entry``."""

    async def test_caches_unhealthy_entry_on_connect_failure(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        pool = _make_pool()
        stub_peer = _StubPeer()
        monkeypatch.setattr(pool, "_create_peer", lambda *a, **kw: stub_peer)

        agent_id = AgentId("i-dead")

        with pytest.raises(AgentConnectionUnavailable):
            async with pool.acquire(agent_id):
                pass

        # The failure must be cached so the existing unhealthy short-circuit
        # in _get_or_create takes effect on subsequent calls (avoiding
        # repeated peer creation on each retry).
        assert agent_id in pool._entries
        assert pool._entries[agent_id].is_healthy is False

        await pool.close()

    async def test_subsequent_acquire_short_circuits_without_recreating_peer(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        pool = _make_pool()

        peers_created: list[_StubPeer] = []

        def _track_create_peer(*_args: Any, **_kwargs: Any) -> _StubPeer:
            peer = _StubPeer()
            peers_created.append(peer)
            return peer

        monkeypatch.setattr(pool, "_create_peer", _track_create_peer)

        agent_id = AgentId("i-dead")

        with pytest.raises(AgentConnectionUnavailable):
            async with pool.acquire(agent_id):
                pass
        assert len(peers_created) == 1

        # Second acquire must hit the cached-unhealthy branch and refuse
        # immediately, without constructing a fresh peer (no new zmq.Context).
        with pytest.raises(AgentConnectionUnavailable):
            async with pool.acquire(agent_id):
                pass
        assert len(peers_created) == 1, (
            "subsequent acquire must short-circuit via cached unhealthy entry, "
            "not create another PeerInvoker (each one allocates a zmq.Context)"
        )

        await pool.close()
