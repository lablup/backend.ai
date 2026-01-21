"""
Agent RPC connection pool.
"""

from __future__ import annotations

import asyncio
import logging
import time
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from dataclasses import dataclass
from typing import TYPE_CHECKING

import zmq
from aiotools import cancel_and_wait
from callosum.lower.zeromq import ZeroMQAddress, ZeroMQRPCTransport

from ai.backend.common import msgpack
from ai.backend.common.auth import ManagerAuthHandler
from ai.backend.common.types import AgentId
from ai.backend.logging import BraceStyleAdapter
from ai.backend.manager.errors.agent import AgentConnectionUnavailable

from .client import AgentClient
from .types import AgentPoolSpec

if TYPE_CHECKING:
    from ai.backend.manager.agent_cache import AgentRPCCache, PeerInvoker

log = BraceStyleAdapter(logging.getLogger(__spec__.name))

# Connection-related error types
CONNECTION_ERRORS = (
    ConnectionError,
    asyncio.TimeoutError,
    OSError,
)


@dataclass(slots=True)
class _CachedEntry:
    """Internal cache entry for pool management."""

    client: AgentClient
    is_healthy: bool = True
    failure_count: int = 0
    unhealthy_since: float | None = None


class AgentClientPool:
    """
    Agent RPC connection pool.

    Connection state management:
    1. Periodic health check: ping to verify connection, delete if unrecoverable
    2. Usage-time failure tracking: increment failure_count on connection error during acquire()

    Separation of concerns:
    - acquire(): client acquisition only (raise exception if unhealthy)
    - health_check_loop: connection state management and deletion
    """

    _agent_cache: AgentRPCCache
    _spec: AgentPoolSpec
    _entries: dict[AgentId, _CachedEntry]
    _lock: asyncio.Lock
    _health_check_task: asyncio.Task[None]

    def __init__(
        self,
        agent_cache: AgentRPCCache,
        spec: AgentPoolSpec,
    ) -> None:
        self._agent_cache = agent_cache
        self._spec = spec
        self._entries = {}
        self._lock = asyncio.Lock()

        # Start background task in constructor
        self._health_check_task = asyncio.create_task(
            self._health_check_loop(),
            name="AgentClientPool._health_check_loop",
        )

    async def close(self) -> None:
        """Close the pool."""
        await cancel_and_wait(self._health_check_task)

        async with self._lock:
            for entry in self._entries.values():
                await entry.client.close()
            self._entries.clear()

    @asynccontextmanager
    async def acquire(self, agent_id: AgentId) -> AsyncIterator[AgentClient]:
        """
        Acquire an agent client for use.

        On connection error during use, increment failure count and
        mark as unhealthy if threshold is exceeded.
        Unhealthy connections raise an exception (deletion is handled by health_check_loop).

        Business logic errors do not affect failure count.
        """
        client = await self._get_or_create(agent_id)
        try:
            yield client
        except CONNECTION_ERRORS:
            self._record_failure(agent_id)
            raise
        except Exception:
            # Non-connection errors don't increment failure count
            raise
        else:
            self._record_success(agent_id)

    async def _get_or_create(self, agent_id: AgentId) -> AgentClient:
        """Return healthy client, create if not exists."""
        async with self._lock:
            entry = self._entries.get(agent_id)

            # Raise exception if unhealthy (deletion is handled by health_check_loop)
            if entry is not None and not entry.is_healthy:
                raise AgentConnectionUnavailable(agent_id, "connection unhealthy")

            # Create new entry if not exists
            if entry is None:
                entry = await self._create_entry(agent_id)
                self._entries[agent_id] = entry

            return entry.client

    async def _create_entry(self, agent_id: AgentId) -> _CachedEntry:
        """Create new entry (called within lock)."""
        try:
            agent_addr, agent_public_key = await self._agent_cache.get_rpc_args(agent_id)
        except ValueError as e:
            raise AgentConnectionUnavailable(agent_id, str(e)) from e

        # Set up auth handler
        if agent_public_key:
            auth_handler = ManagerAuthHandler(
                "local",
                agent_public_key,
                self._agent_cache.manager_public_key,
                self._agent_cache.manager_secret_key,
            )
        else:
            auth_handler = None

        # Calculate keepalive settings
        keepalive_retry_count = 3
        keepalive_timeout = self._agent_cache.rpc_keepalive_timeout
        keepalive_interval = keepalive_timeout // keepalive_retry_count
        if keepalive_interval < 2:
            keepalive_interval = 2

        peer: PeerInvoker = self._create_peer(
            agent_addr,
            auth_handler,
            keepalive_timeout,
            keepalive_interval,
            keepalive_retry_count,
        )

        client = AgentClient(peer, agent_id)
        try:
            await client.connect()
        except Exception as e:
            raise AgentConnectionUnavailable(agent_id, str(e)) from e

        return _CachedEntry(
            client=client,
            is_healthy=True,
            failure_count=0,
            unhealthy_since=None,
        )

    def _create_peer(
        self,
        agent_addr: str,
        auth_handler: ManagerAuthHandler | None,
        keepalive_timeout: int,
        keepalive_interval: int,
        keepalive_retry_count: int,
    ) -> PeerInvoker:
        """Create a new PeerInvoker instance."""
        from ai.backend.manager.agent_cache import PeerInvoker

        return PeerInvoker(
            connect=ZeroMQAddress(agent_addr),
            transport=ZeroMQRPCTransport,
            authenticator=auth_handler,
            transport_opts={
                "zsock_opts": {
                    zmq.TCP_KEEPALIVE: 1,
                    zmq.TCP_KEEPALIVE_IDLE: keepalive_timeout,
                    zmq.TCP_KEEPALIVE_INTVL: keepalive_interval,
                    zmq.TCP_KEEPALIVE_CNT: keepalive_retry_count,
                },
            },
            serializer=msgpack.packb,
            deserializer=msgpack.unpackb,
        )

    def _record_failure(self, agent_id: AgentId) -> None:
        """Record connection error and mark unhealthy if threshold exceeded."""
        entry = self._entries.get(agent_id)
        if entry is None:
            return

        entry.failure_count += 1
        if entry.failure_count >= self._spec.failure_threshold:
            entry.is_healthy = False
            if entry.unhealthy_since is None:
                entry.unhealthy_since = time.perf_counter()
            log.debug(
                "Agent {} marked unhealthy after {} connection failures",
                agent_id,
                entry.failure_count,
            )

    def _record_success(self, agent_id: AgentId) -> None:
        """Reset state on success."""
        entry = self._entries.get(agent_id)
        if entry is not None:
            entry.failure_count = 0
            entry.is_healthy = True
            entry.unhealthy_since = None

    async def _health_check_loop(self) -> None:
        """Periodically check all connection health."""
        while True:
            await asyncio.sleep(self._spec.health_check_interval)
            await self._check_all_health()

    async def _check_all_health(self) -> None:
        """Check health of all connections (using asyncio.gather)."""
        async with self._lock:
            entries = list(self._entries.items())

        if not entries:
            return

        await asyncio.gather(
            *[self._check_one_health(agent_id, entry) for agent_id, entry in entries],
            return_exceptions=True,
        )

    async def _check_one_health(self, agent_id: AgentId, entry: _CachedEntry) -> None:
        """Check single connection health and delete if unrecoverable."""
        try:
            async with asyncio.timeout(5.0):
                await entry.client.ping()
            # Ping success → recover
            entry.is_healthy = True
            entry.failure_count = 0
            entry.unhealthy_since = None
        except Exception:
            # Ping failure → mark unhealthy
            entry.is_healthy = False
            if entry.unhealthy_since is None:
                entry.unhealthy_since = time.perf_counter()
                log.debug("Health check failed for agent {}", agent_id)

        # Delete if recovery_timeout exceeded
        if (
            not entry.is_healthy
            and entry.unhealthy_since is not None
            and time.perf_counter() - entry.unhealthy_since > self._spec.recovery_timeout
        ):
            async with self._lock:
                if agent_id in self._entries:
                    await entry.client.close()
                    del self._entries[agent_id]
            log.info(
                "Removed unrecoverable connection for agent {} after {}s",
                agent_id,
                self._spec.recovery_timeout,
            )
